import os
import time
import gc
import logging
import numpy as np
import pandas as pd
import nibabel as nib
import glob
import matplotlib.pyplot as plt
from skimage.metrics import peak_signal_noise_ratio as compute_psnr
from skimage.metrics import structural_similarity as compute_ssim
from skimage.metrics import mean_squared_error as compute_mse

# Import your modules
import kmri_encode
import kmri_decode

# -------------------------------------------------------------------------
# Configuration & Setup
# -------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Set IEEE-style plotting parameters
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'legend.fontsize': 9,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

def create_synthetic_mri(shape=(128, 128, 128), filepath="synthetic_mri.nii"):
    """Generates a synthetic MRI volume with background, structure, and noise."""
    logging.info(f"Generating synthetic MRI data {shape}...")
    x, y, z = np.ogrid[-1:1:shape[0]*1j, -1:1:shape[1]*1j, -1:1:shape[2]*1j]
    
    # Create an ellipsoid mask
    r = np.sqrt(x**2 + (y/0.8)**2 + (z/1.2)**2)
    brain_mask = r < 0.8
    
    # Base intensity + structural variations + noise
    volume = np.zeros(shape, dtype=np.float32)
    volume[brain_mask] = 1500.0 - 500.0 * r[brain_mask] 
    
    # Add lesions / higher intensity regions to trigger ROI thresholds
    lesion = np.sqrt((x-0.2)**2 + (y-0.2)**2 + (z)**2) < 0.15
    volume[lesion] += 800.0
    
    # Add Gaussian noise
    noise = np.random.normal(0, 20, shape).astype(np.float32)
    volume = np.clip(volume + noise, 0, None)
    
    # Set background exactly to zero (mimicking skull-stripped MRI)
    volume[~brain_mask] = 0.0
    
    img = nib.Nifti1Image(volume, np.eye(4))
    nib.save(img, filepath)
    return filepath

def compute_metrics(original_nii, decoded_nii):
    """Computes academic image fidelity metrics."""
    orig_data = nib.load(original_nii).get_fdata()
    dec_data = nib.load(decoded_nii).get_fdata()
    
    data_range = orig_data.max() - orig_data.min()
    
    mse = compute_mse(orig_data, dec_data)
    psnr = compute_psnr(orig_data, dec_data, data_range=data_range)
    
    # 3D SSIM can be extremely slow on large volumes, computing with win_size
    # For large volumes, we set channel_axis=None for 3D grayscale
    ssim = compute_ssim(orig_data, dec_data, data_range=data_range, 
                        win_size=7, channel_axis=None)
    
    return mse, psnr, ssim

# -------------------------------------------------------------------------
# Core Benchmark Runner
# -------------------------------------------------------------------------
def run_benchmark(input_path, output_dir="benchmark_results", num_trials=3):
    os.makedirs(output_dir, exist_ok=True)
    
    # Benchmark parameters for grid search
    bits_list = [8, 10, 12, 16]
    roi_levels =[1, 5, 9]  # zstd levels
    
    raw_uncompressed_bytes = nib.load(input_path).get_fdata().nbytes
    
    results =[]
    
    # Warm-up run to initialize PyBind11 and OS file caches
    logging.info("Performing warm-up run...")
    dummy_kmri = os.path.join(output_dir, "warmup.kmri")
    dummy_dec = os.path.join(output_dir, "warmup_dec.nii")
    kmri_encode.encode_kmri_cpp(input_path, dummy_kmri, bits=10, roi_level=1)
    kmri_decode.decode_kmri_cpp(dummy_kmri, dummy_dec)
    
    total_experiments = len(bits_list) * len(roi_levels)
    idx = 1
    
    for bits in bits_list:
        for level in roi_levels:
            logging.info(f"--- Experiment {idx}/{total_experiments}: Bits={bits}, Level={level} ---")
            
            kmri_file = os.path.join(output_dir, f"enc_b{bits}_l{level}.kmri")
            dec_file = os.path.join(output_dir, f"dec_b{bits}_l{level}.nii")
            
            # --- Measure Encoding ---
            enc_times =[]
            for _ in range(num_trials):
                gc.collect()
                t0 = time.perf_counter()
                kmri_encode.encode_kmri_cpp(
                    input_path, kmri_file, bits=bits, roi_level=level, bg_level=1
                )
                enc_times.append(time.perf_counter() - t0)
            enc_time = np.median(enc_times) # Median is robust to OS jitter
            
            # --- Measure Decoding ---
            dec_times =[]
            for _ in range(num_trials):
                gc.collect()
                t0 = time.perf_counter()
                kmri_decode.decode_kmri_cpp(kmri_file, dec_file)
                dec_times.append(time.perf_counter() - t0)
            dec_time = np.median(dec_times)
            
            # --- Compute Compression Ratio ---
            kmri_bytes = os.path.getsize(kmri_file)
            compression_ratio = raw_uncompressed_bytes / kmri_bytes
            
            # --- Compute Quality Metrics ---
            mse, psnr, ssim = compute_metrics(input_path, dec_file)
            
            results.append({
                "Quant_Bits": bits,
                "Zstd_Level": level,
                "Orig_Size_MB": raw_uncompressed_bytes / 1024**2,
                "KMRI_Size_MB": kmri_bytes / 1024**2,
                "Compression_Ratio": compression_ratio,
                "Enc_Time_s": enc_time,
                "Dec_Time_s": dec_time,
                "MSE": mse,
                "PSNR_dB": psnr,
                "SSIM": ssim
            })
            
            # Cleanup to save disk space
            os.remove(kmri_file)
            os.remove(dec_file)
            idx += 1

    df = pd.DataFrame(results)
    
    # Save raw data & LaTeX table for publication
    csv_path = os.path.join(output_dir, "benchmark_metrics.csv")
    tex_path = os.path.join(output_dir, "benchmark_metrics.tex")
    df.to_csv(csv_path, index=False)
    df.to_latex(tex_path, index=False, float_format="%.3f")
    logging.info(f"Results saved to {output_dir}/")
    
    return df

# -------------------------------------------------------------------------
# Publication Plotting
# -------------------------------------------------------------------------
def generate_ieee_plots(df, output_dir="benchmark_results"):
    # 1. Rate-Distortion Curve (Compression Ratio vs PSNR)
    fig, ax1 = plt.subplots(figsize=(6, 4))
    
    markers = {1: 'o', 5: 's', 9: '^'}
    for level in df['Zstd_Level'].unique():
        subset = df[df['Zstd_Level'] == level]
        ax1.plot(subset['Compression_Ratio'], subset['PSNR_dB'], 
                 marker=markers[level], linestyle='-', 
                 label=f'Zstd Level {level}')
        
        # Annotate Bits
        for _, row in subset.iterrows():
            ax1.annotate(f"{int(row['Quant_Bits'])}b", 
                         (row['Compression_Ratio'], row['PSNR_dB']),
                         textcoords="offset points", xytext=(0, 5), ha='center', fontsize=8)

    ax1.set_xlabel('Compression Ratio (Raw Size / Compressed Size)')
    ax1.set_ylabel('PSNR (dB)')
    ax1.set_title('Rate-Distortion Performance (KMRI)')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend()
    fig.savefig(os.path.join(output_dir, "rate_distortion_psnr.pdf"))
    
    # 2. SSIM vs Compression Ratio
    fig, ax2 = plt.subplots(figsize=(6, 4))
    for level in df['Zstd_Level'].unique():
        subset = df[df['Zstd_Level'] == level]
        ax2.plot(subset['Compression_Ratio'], subset['SSIM'], 
                 marker=markers[level], linestyle='-', 
                 label=f'Zstd Level {level}')

    ax2.set_xlabel('Compression Ratio')
    ax2.set_ylabel('Structural Similarity Index (SSIM)')
    ax2.set_title('Compression Ratio vs Structural Integrity')
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend()
    fig.savefig(os.path.join(output_dir, "rate_distortion_ssim.pdf"))
    
    # 3. Encoding & Decoding Time Trade-offs
    fig, ax3 = plt.subplots(figsize=(6, 4))
    # Using bits=10 as a standard representative to visualize speed vs zstd level
    subset_b10 = df[df['Quant_Bits'] == 10].sort_values('Zstd_Level')
    
    x = np.arange(len(subset_b10['Zstd_Level']))
    width = 0.35
    
    ax3.bar(x - width/2, subset_b10['Enc_Time_s'], width, label='Encoding Time')
    ax3.bar(x + width/2, subset_b10['Dec_Time_s'], width, label='Decoding Time')
    
    ax3.set_xlabel('Zstd Compression Level (at 10-bit Quantization)')
    ax3.set_ylabel('Latency (Seconds)')
    ax3.set_title('Computational Complexity of KMRI')
    ax3.set_xticks(x)
    ax3.set_xticklabels([f"Level {lvl}" for lvl in subset_b10['Zstd_Level']])
    ax3.legend()
    fig.savefig(os.path.join(output_dir, "latency_profile.pdf"))
    
    logging.info("IEEE plots generated successfully as PDFs.")

if __name__ == "__main__":
    # Point this to the directory containing your NIfTI files
    DATA_DIR = r"P:\Class_2026\Projects\KMRI\test_nii"
    
    # Find all .nii or .nii.gz files in that folder
    nii_files = glob.glob(os.path.join(DATA_DIR, "*.nii*"))
    
    if not nii_files:
        print(f"No .nii files found in {DATA_DIR}. Generating synthetic data...")
        TEST_NII = "test_data_mri.nii"
        create_synthetic_mri(filepath=TEST_NII)
        nii_files =[TEST_NII]
    
    all_results =[]
    
    # Loop through all found MRI scans
    for file_path in nii_files:
        print(f"\n========================================")
        print(f" Benchmarking: {os.path.basename(file_path)}")
        print(f"========================================\n")
        
        # Run the benchmark for this specific file
        df = run_benchmark(file_path)
        df['Filename'] = os.path.basename(file_path) # Keep track of which file this was
        all_results.append(df)
        
    # Combine all results into one big DataFrame
    final_df = pd.concat(all_results, ignore_index=True)
    
    # Average the metrics across all files for the final IEEE plots
    avg_df = final_df.groupby(['Quant_Bits', 'Zstd_Level']).mean(numeric_only=True).reset_index()
    
    print("\n[Average Benchmark Results Across All Scans]")
    print(avg_df[['Quant_Bits', 'Zstd_Level', 'Compression_Ratio', 'PSNR_dB', 'SSIM', 'Enc_Time_s', 'Dec_Time_s']].to_markdown())
    
    # Generate the plots using the averaged data
    generate_ieee_plots(avg_df)
    
    # Save the combined raw data just in case
    final_df.to_csv("benchmark_results/all_files_raw_metrics.csv", index=False)