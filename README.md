# KMRI — High-Performance MRI Compression Format

KMRI is a fast, chunk-based, quantized compression format for large 3D medical-style volumes.  
It is designed for speed, simplicity, and significant size reduction, especially on MRI-like data.

This repository includes:
- A reference encoder/decoder
- A synthetic MRI generator (safe, no real medical data)
- Reproducible benchmarks
- A documented file format

---

## Why KMRI Exists

Standard `.nii` files store raw voxel arrays with no chunking, no entropy reduction, and no structural awareness.  
Even `.nii.gz` only applies gzip to the entire file.

KMRI improves on this with:
- Chunk-level compression  
- Zero-block skipping  
- 8-bit or 16-bit quantization  
- Zstd backend  
- ROI-aware chunking  
- Minimal metadata overhead  

The result is dramatically smaller files with fast decode paths.

---

## Benchmarks (Synthetic MRI)

All tests use a high-entropy synthetic MRI with:
- Rician noise  
- Bias field  
- Random lesions  
- High-frequency noise  
- Partial-volume blur  
- No zero regions  

| Dataset | Raw Size | KMRI | Ratio | Notes |
|--------|----------|------|-------|-------|
| 512³ uint16 | 256 MB | 42.1 MB | 6.07× | High-entropy synthetic MRI |
| 800³ uint16 | 1.02 GB | 1.1 MB | 927× | Smooth synthetic MRI (zero-block skip dominates) |

---

## Reproducible Test

``python fake_nii.py``

``python test.py``

**Note that test.py is assuming the synthetic_realistic_hardcore.nii will be saved in the same working directory!**

---

## Synthetic MRI Generator

This repository includes a fully synthetic, safe MRI-like generator that simulates:
- White/grey/CSF layers  
- Rician noise  
- Bias field  
- Random lesions  
- High-frequency noise  
- Partial-volume blur  

No real medical data is used.


---

## License & Contact

The license in this project is the **BSD 3-Clause** license

If you have any inquiries or questions, feel free to email me at kiamehr13922014@gmail.com
