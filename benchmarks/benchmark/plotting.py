import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd

def set_publication_style():
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

def plot_rate_distortion(df, metric="PSNR", output_path="rate_distortion_psnr.pdf"):
    """Plot Compression Ratio vs a fidelity metric (PSNR or SSIM)."""
    set_publication_style()
    fig, ax = plt.subplots(figsize=(6, 4))
    
    unique_methods = df['method'].unique()
    markers = ['o', 's', '^', 'D', 'v', 'p']
    
    for idx, method in enumerate(unique_methods):
        subset = df[df['method'] == method]
        # Filter out infinite PSNR (lossless methods) for cleaner plots
        if metric == "PSNR":
            subset = subset[subset['psnr_mean'] != float('inf')]
            y_val = subset['psnr_mean']
        else:
            y_val = subset['ssim_mean']
            
        x_val = subset['compression_ratio']
        
        if len(subset) > 0:
            ax.plot(x_val, y_val, marker=markers[idx % len(markers)], linestyle='-', label=method)
            
    ax.set_xlabel('Compression Ratio (Raw Size / Compressed Size)')
    ylabel = 'PSNR (dB)' if metric == "PSNR" else 'Structural Similarity Index (SSIM)'
    ax.set_ylabel(ylabel)
    ax.set_title(f'Rate-Distortion Performance: {metric}')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='lower right' if metric == "PSNR" else 'lower right')
    
    fig.savefig(output_path)
    plt.close(fig)

def plot_latency_profile(df, output_path="latency_profile.pdf"):
    """Bar chart comparing encode vs decode times across methods."""
    set_publication_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # We will pick the first configuration of each method representative for latency
    representative = df.groupby('method').first().reset_index()
    
    x = np.arange(len(representative['method']))
    width = 0.35
    
    ax.bar(x - width/2, representative['encode_time_ms_mean'], width, yerr=representative['encode_time_ms_std'], label='Encoding Time', capsize=5)
    ax.bar(x + width/2, representative['decode_time_ms_mean'], width, yerr=representative['decode_time_ms_std'], label='Decoding Time', capsize=5)
    
    ax.set_xlabel('Compression Method')
    ax.set_ylabel('Latency (ms)')
    ax.set_title('Computational Complexity')
    ax.set_xticks(x)
    ax.set_xticklabels(representative['method'], rotation=45, ha="right")
    ax.legend()
    
    fig.savefig(output_path)
    plt.close(fig)

def plot_baseline_comparison(df, output_path="baseline_comparison.pdf"):
    """Comprehensive comparison table + plot."""
    set_publication_style()
    
    # Render table to a plot view
    fig, ax = plt.subplots(figsize=(10, round(len(df) * 0.4) + 2))
    ax.axis('off')
    ax.axis('tight')
    
    display_df = df[['method', 'compression_ratio', 'encode_time_ms_mean', 'decode_time_ms_mean', 'psnr_mean', 'peak_memory_mb_mean']].copy()
    display_df = display_df.round(2)
    display_df.columns = ['Method', 'Comp. Ratio', 'Enc (ms)', 'Dec (ms)', 'PSNR (dB)', 'Peak Mem (MB)']
    
    table = ax.table(cellText=display_df.values, colLabels=display_df.columns, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    ax.set_title("Benchmarking Aggregated Results", pad=20)
    fig.savefig(output_path)
    plt.close(fig)
