# KMRI

> Experimental medical imaging compression framework exploring chunked, structure-aware alternatives to `.nii.gz` (gzip-based NIfTI compression)

KMRI is a high-performance compression system for volumetric MRI/NIfTI data written in **Python + C++ (pybind11)**.

It investigates whether **structure-aware compression** (regions, sparsity, chunking, quantization) can outperform traditional general-purpose compression like gzip.

---

## ⚡ Why KMRI?

Standard `.nii.gz` compression treats medical imaging data as raw bytes.

KMRI instead asks:

> What if we compress MRI data using knowledge of its structure?

This enables:
- region-aware compression decisions
- chunk-level optimization for volumetric data
- better speed vs quality trade-offs
- adaptive handling of sparse regions

---

## 📊 Results Snapshot

KMRI has been benchmarked against:
- `.nii.gz` (GZIP)
- raw Zstandard compression
- NumPy + Zstd pipelines

Across test datasets, KMRI demonstrates:

- ✔ improved compression ratios (vs gzip baseline)
- ✔ faster decode performance via chunked design
- ✔ high reconstruction fidelity (PSNR / SSIM preserved)

Full benchmark suite included below.

---

## 🚀 Features

- ⚙ Fast C++ compression core (pybind11 + Zstd)
- 🧠 Chunk-based volumetric encoding
- 🎯 ROI-aware adaptive compression
- 📉 Sparse zero-block optimization
- 🔢 Optional N-bit quantization (8–16 bit)
- 🧬 Automatic mask vs intensity detection
- 📦 Custom `.kmri` binary container format
- 📊 Full benchmarking suite:
  - compression ratio analysis
  - latency profiling
  - PSNR / SSIM fidelity metrics
  - baseline comparisons vs gzip & zstd

---

## 📈 Benchmark Visuals

### Compression Quality (PSNR)
<p align="center">
  <img src="benchmarks/benchmark_results/rate_distortion_psnr.png" width="650"/>
</p>

### Structural Similarity (SSIM)
<p align="center">
  <img src="benchmarks/benchmark_results/rate_distortion_ssim.png" width="650"/>
</p>

### Latency Profile
<p align="center">
  <img src="benchmarks/benchmark_results/latency_profile.png" width="650"/>
</p>

### Baseline Comparison
<p align="center">
  <img src="benchmarks/benchmark_results/baseline_comparison.png" width="650"/>
</p>

---

## 🧠 How It Works

### 1. Encoding Pipeline
- Load NIfTI volume
- Detect mask vs intensity data
- Split into 3D chunks
- Apply:
  - quantization (optional)
  - ROI-aware compression levels
  - zero-block skipping
- Compress each chunk using Zstd (C++ core)
- Store in `.kmri` container format

---

### 2. Decoding Pipeline
- Read metadata header + chunk table
- Decompress chunks
- Reconstruct 3D volume
- Apply dequantization (if needed)
- Export reconstructed NIfTI file

---

## 🔧 Compression Design

### 🔢 Quantization
Intensity volumes can be reduced to:

- 8-bit
- 10-bit
- 12-bit
- up to 16-bit

This reduces storage while preserving diagnostic quality.

Segmentation masks remain lossless.

---

### 🎯 ROI-Aware Compression
Different regions are treated differently:

- ROI chunks → higher fidelity (lower compression level)
- Background chunks → higher compression (faster + smaller)

---

### 📦 Sparse Optimization
Completely empty chunks are not stored as data — only metadata flags.

This significantly reduces size for sparse scans.

---

## 🧪 Benchmarking

Run the full benchmark suite:

```bash
python KMRI/benchmarks/benchmark/run_benchmark.py --input path/to/nifti_dataset
