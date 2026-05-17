import argparse
import os
import sys
import glob
import json
import logging
from collections import defaultdict
import numpy as np
import pandas as pd

from io_utils import load_nifti
from metrics import compute_fidelity, measure_execution
from baselines import gzip_compress, gzip_decompress, zstd_compress, zstd_decompress, numpy_zstd_compress, numpy_zstd_decompress
from plotting import plot_rate_distortion, plot_latency_profile, plot_baseline_comparison


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

# Try to import KMRI if available in working directory layout
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    import kmri_encode
    import kmri_decode
    KMRI_AVAILABLE = True
except ImportError:
    KMRI_AVAILABLE = False
    logging.warning("KMRI python modules (kmri_encode.py, kmri_decode.py) not found in root. Real KMRI benchmarking disabled.")

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def run_trial(compression_func, decompression_func, payload, requires_file=False, *args, **kwargs):
    """Measures a single encode/decode cycle."""
    # Encode
    enc_res, enc_time, enc_mem = measure_execution(compression_func, payload, *args, **kwargs)
    
    # Decode
    dec_res, dec_time, dec_mem = measure_execution(decompression_func, enc_res)
    
    return dec_res, enc_res, enc_time, dec_time, max(enc_mem, dec_mem)

def main():
    parser = argparse.ArgumentParser(description="Medical Imaging Compression Benchmark Suite")
    parser.add_argument("--input", type=str, required=True, help="Directory containing .nii/.nii.gz files")
    parser.add_argument("--trials", type=int, default=5, help="Number of trials for statistical robustness")
    parser.add_argument("--output", type=str, default="results", help="Output directory for plots and JSON")
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    nii_files = glob.glob(os.path.join(args.input, "*.nii*"))
    
    if not nii_files:
        logging.error(f"No NIfTI files found in {args.input}")
        return

    results = []

    for filepath in nii_files:
        logging.info(f"--- Benchmarking {os.path.basename(filepath)} ---")
        vol, affine, header, raw_bytes = load_nifti(filepath)
        raw_encoded_bytes = open(filepath, 'rb').read()

        targets = [
            {"name": "GZIP (Raw .nii)", "type": "bytes", "enc": gzip_compress, "dec": gzip_decompress, "payload": raw_encoded_bytes},
            {"name": "Zstd (Raw .nii)", "type": "bytes", "enc": zstd_compress, "dec": zstd_decompress, "payload": raw_encoded_bytes},
            {"name": "NumPy+Zstd Level 3", "type": "vol", "enc": numpy_zstd_compress, "dec": numpy_zstd_decompress, "payload": vol},
        ]
        
        for target in targets:
            logging.info(f"Running Baseline: {target['name']}")
            trial_metrics = defaultdict(list)
            
            for _ in range(args.trials):
                # Execute
                dec_payload, enc_payload, enc_ms, dec_ms, peak_mem = run_trial(
                    target['enc'], target['dec'], target['payload']
                )
                
                # Metric computation
                if target['type'] == 'bytes':
                    comp_ratio = raw_bytes / len(enc_payload)
                    psnr_val = float('inf') # Lossless byte compression
                    ssim_val = 1.0
                else:
                    comp_ratio = raw_bytes / len(enc_payload)
                    psnr_val, ssim_val = compute_fidelity(vol, dec_payload)

                trial_metrics['cr'].append(comp_ratio)
                trial_metrics['enc_ms'].append(enc_ms)
                trial_metrics['dec_ms'].append(dec_ms)
                trial_metrics['mem_mb'].append(peak_mem / (1024**2))
                trial_metrics['psnr'].append(psnr_val)
                trial_metrics['ssim'].append(ssim_val)
                
            results.append({
                "file": os.path.basename(filepath),
                "method": target['name'],
                "compression_ratio": np.mean(trial_metrics['cr']),
                "encode_time_ms_mean": np.mean(trial_metrics['enc_ms']),
                "encode_time_ms_std": np.std(trial_metrics['enc_ms']),
                "decode_time_ms_mean": np.mean(trial_metrics['dec_ms']),
                "decode_time_ms_std": np.std(trial_metrics['dec_ms']),
                "peak_memory_mb_mean": np.mean(trial_metrics['mem_mb']),
                "psnr_mean": np.mean(trial_metrics['psnr']),
                "ssim_mean": np.mean(trial_metrics['ssim']),
            })

        # KMRI Benchmarking block if available
        if KMRI_AVAILABLE:
            kmri_configs = [(8, 5), (10, 5), (12, 5)] # (bits, roi_level)
            for bits, roi in kmri_configs:
                method_name = f"KMRI ({bits}-bit, ROI Lvl {roi})"
                logging.info(f"Running KMRI: {method_name}")
                
                temp_kmri = os.path.join(args.output, "temp.kmri")
                temp_dec = os.path.join(args.output, "temp_dec.nii")
                
                trial_metrics = defaultdict(list)
                for _ in range(args.trials):
                    # KMRI encode
                    enc_res, enc_ms, enc_mem = measure_execution(
                        kmri_encode.encode_kmri_cpp, filepath, temp_kmri, bits=bits, roi_level=roi
                    )
                    
                    # Size calculation
                    kmri_size = os.path.getsize(temp_kmri)
                    comp_ratio = raw_bytes / kmri_size
                    
                    # KMRI decode
                    dec_res, dec_ms, dec_mem = measure_execution(
                        kmri_decode.decode_kmri_cpp, temp_kmri, temp_dec
                    )
                    
                    # Quality
                    dec_vol, _, _, _ = load_nifti(temp_dec)
                    psnr_val, ssim_val = compute_fidelity(vol, dec_vol)
                    
                    trial_metrics['cr'].append(comp_ratio)
                    trial_metrics['enc_ms'].append(enc_ms)
                    trial_metrics['dec_ms'].append(dec_ms)
                    trial_metrics['mem_mb'].append(max(enc_mem, dec_mem) / (1024**2))
                    trial_metrics['psnr'].append(psnr_val)
                    trial_metrics['ssim'].append(ssim_val)
                    
                    # Clean up temps
                    if os.path.exists(temp_kmri): os.remove(temp_kmri)
                    if os.path.exists(temp_dec): os.remove(temp_dec)
                
                results.append({
                    "file": os.path.basename(filepath),
                    "method": method_name,
                    "compression_ratio": np.mean(trial_metrics['cr']),
                    "encode_time_ms_mean": np.mean(trial_metrics['enc_ms']),
                    "encode_time_ms_std": np.std(trial_metrics['enc_ms']),
                    "decode_time_ms_mean": np.mean(trial_metrics['dec_ms']),
                    "decode_time_ms_std": np.std(trial_metrics['dec_ms']),
                    "peak_memory_mb_mean": np.mean(trial_metrics['mem_mb']),
                    "psnr_mean": np.mean(trial_metrics['psnr']),
                    "ssim_mean": np.mean(trial_metrics['ssim']),
                })
    
    # Save Outputs
    df = pd.DataFrame(results)
    
    # Avoid infinities in JSON
    df_json = df.replace([np.inf, -np.inf], "Infinity")
    
    json_path = os.path.join(args.output, "benchmark_results.json")
    with open(json_path, 'w') as f:
        json.dump({
            "metadata": {"dataset_path": args.input, "trials": args.trials},
            "results": df_json.to_dict(orient="records")
        }, f, indent=2)
        
    csv_path = os.path.join(args.output, "benchmark_results.csv")
    df.to_csv(csv_path, index=False)
    
    logging.info("Generating PDF comparative plots...")
    plot_rate_distortion(df, metric="PSNR", output_path=os.path.join(args.output, "rate_distortion_psnr.pdf"))
    plot_rate_distortion(df, metric="SSIM", output_path=os.path.join(args.output, "rate_distortion_ssim.pdf"))
    plot_latency_profile(df, output_path=os.path.join(args.output, "latency_profile.pdf"))
    plot_baseline_comparison(df, output_path=os.path.join(args.output, "baseline_comparison.pdf"))
    
    logging.info(f"Done. Benchmark outputs saved to {args.output}/")

if __name__ == "__main__":
    main()
