import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity
import time
import tracemalloc
import gc

def compute_fidelity(orig, decoded):
    """Computes PSNR and SSIM. Safely handles identical arrays."""
    data_range = orig.max() - orig.min()
    if data_range == 0:
        data_range = 1e-8
        
    mse = np.mean((orig.astype(np.float64) - decoded.astype(np.float64)) ** 2)
    if mse == 0:
        return float('inf'), 1.0

    psnr = peak_signal_noise_ratio(orig, decoded, data_range=data_range)
    # Using channel_axis=None for 3D single channel volumes, with small win_size for performance
    ssim = structural_similarity(orig, decoded, data_range=data_range, win_size=7, channel_axis=None)
    
    return psnr, ssim

def measure_execution(func, *args, **kwargs):
    """Executes a function, returns the result with elapsed ms and peak memory in bytes."""
    gc.collect() # Disable caching effects prior to timing
    tracemalloc.start()
    t0 = time.perf_counter()
    
    res = func(*args, **kwargs)
    
    t1 = time.perf_counter()
    _, peak_mem_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    latency_ms = (t1 - t0) * 1000.0
    return res, latency_ms, peak_mem_bytes
