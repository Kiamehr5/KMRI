# KMRI

> A modern medical imaging compression framework built to push beyond traditional `.nii.gz`.

KMRI is an experimental high-performance medical imaging compression system written in Python and C++.  
It combines:

- **Zstandard (Zstd)** compression
- **Chunk-based volume encoding**
- **Adaptive ROI-aware compression**
- **Quantization**
- **Sparse zero-block optimization**
- **Fast decompression pipelines**

The goal is simple:

> better compression, faster decoding, and smarter storage for MRI/NIfTI data.

---

## Why KMRI?

Traditional `.nii.gz` files rely on GZIP — a format from the 1990s that was never designed specifically for modern volumetric medical imaging workloads.

KMRI explores a more specialized approach by using:

- Zstd instead of GZIP
- chunk-aware encoding
- region-aware compression levels
- optional lossy quantization for intensity volumes
- exact preservation for segmentation masks
- low-overhead binary container structures

---

## Features

- Fast C++ compression core using pybind11
- Zstandard-based compression backend
- ROI-aware chunk compression
- Automatic mask/intensity detection
- Optional N-bit quantization
- Sparse chunk optimization
- Benchmark suite with:
  - compression ratio analysis
  - latency profiling
  - PSNR + SSIM fidelity metrics
  - baseline comparisons against GZIP and Zstd
- Native `.kmri` container format

---

# Project Structure

```text
KMRI/
│
├── kmri_encode.py
├── kmri_decode.py
├── kmri_core.cpp
│
├── benchmarks/
│   └── benchmark/
│       └── run_benchmark.py
│
└── ...
```

---

# How It Works

## Encoding Pipeline

1. Load NIfTI volume
2. Detect whether the volume is:
   - an intensity scan
   - or a segmentation mask
3. Split volume into chunks
4. Apply:
   - quantization (optional)
   - ROI-aware compression
   - zero-block skipping
5. Compress chunks using Zstd
6. Store everything in the `.kmri` binary format

---

## Decoding Pipeline

1. Read KMRI header + chunk table
2. Decompress chunk data
3. Reconstruct volume
4. Dequantize if required
5. Export reconstructed NIfTI

---

# Compression Design

## Quantization

Intensity volumes can be quantized to lower bit depths:

- 8-bit
- 10-bit
- 12-bit
- up to 16-bit

This reduces storage while preserving usable image quality.

Segmentation masks remain lossless.

---

## ROI-Aware Compression

KMRI can compress important regions differently from background regions.

Example:

- ROI chunks → lower compression level for speed/detail
- Background chunks → stronger compression

---

## Sparse Optimization

Completely empty chunks are skipped entirely and represented with metadata flags instead of compressed payloads.

This can significantly reduce storage for sparse scans.

---

# Benchmarking

Run the benchmark suite:

```bash
python KMRI/benchmarks/benchmark/run_benchmark.py --input path/to/nifti_dataset
```

Outputs include:

- JSON benchmark reports
- CSV summaries
- PSNR/SSIM plots
- latency analysis PDFs
- baseline comparison charts

---

# Benchmarked Against

KMRI compares itself against:

- GZIP (`.nii.gz`)
- Raw Zstd compression
- NumPy + Zstd pipelines

Metrics include:

- Compression ratio
- Encode/decode latency
- Peak memory usage
- PSNR
- SSIM

---

# Example Encode

```python
import kmri_encode

kmri_encode.encode_kmri_cpp(
    "brain_scan.nii",
    "brain_scan.kmri",
    bits=10
)
```

---

# Example Decode

```python
import kmri_decode

kmri_decode.decode_kmri_cpp(
    "brain_scan.kmri",
    "reconstructed_scan.nii"
)
```

---

# Tech Stack

## Python

- NumPy
- NiBabel
- Pandas
- Matplotlib
- Pybind11

## C++

- Zstandard (Zstd)
- pybind11 bindings

---

# KMRI File Format

Each `.kmri` file contains:

- magic bytes
- versioning
- metadata header
- chunk lookup table
- compressed chunk payloads

The format is designed to stay lightweight and fast to parse.

---

# Status

KMRI is currently experimental and under active development.

Areas being explored:

- GPU acceleration
- streaming decode
- better ROI detection
- entropy modeling
- parallel chunk encoding
- learned compression techniques

---

# Vision

KMRI is an attempt to rethink medical imaging compression from the ground up instead of continuing to rely on generic archival formats.

Not just smaller files.

Smarter files.

---

# License

BSD 3-Clause

---

# Author & Contact

Built by Kiamehr.
Contact at kiamehr13922014@gmail.com
