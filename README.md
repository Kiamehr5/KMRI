# 🚀 KMRI — Fast MRI Compression for Massive 3D Volumes

**KMRI is a high-performance compression format for .nii / .nii.gz files, designed for large 3D medical-style volumes.
It delivers significant size reduction (up to 6×–900×) with fast decoding and minimal complexity.**

## ✨ Features
• 🧱 Chunk-based compression for efficient access

• ⛔ Zero-block skipping for sparse regions

• 🎚️ 8-bit / 16-bit quantization

• ⚡ Zstandard (Zstd) backend

• 🎯 ROI-aware chunking

• 📦 Low metadata overhead

• 🚀 Fast encode/decode pipeline

### ⚡ Quick Start
``pip install -r requirements.txt``

**Run the code below to demonstrate compression and decompression**

``python test.py``

**Note that **test.py** assumes that the directory of the synthetic_realistic_hardcore.nii file is written into the input_nii variable**


## 🧠 Why KMRI?

**Standard .nii files:**

• Store raw voxel arrays
• No chunking
• No structural awareness
• Large and inefficient

Even .nii.gz:

• Applies gzip to the entire file
•No intelligent compression

**KMRI improves this with:**

• Chunk-level compression
• Structural awareness
• Quantization
• Smarter storage of empty regions

👉 Result: smaller files + faster decoding

## 📊 Benchmarks (Synthetic MRI)

All tests use realistic MRI samples from the BraTS dataset with:

Synthetic datasets include: 

• 512³ uint16	256 MB	42.1 MB	6.07×	High-entropy synthetic MRI

• 800³ uint16	1.02 GB	1.1 MB	927×	Smooth synthetic MRI

**Extremely high ratios occur in smoother volumes where zero-block skipping dominates.**

## 🧪 Reproducible Test
``python benchmark.py``

Note that benchmark.py expects the "test_nii" folder in the same working directory (otherwise specify the path in code)
(test_nii folder is to download at 

## 🧬 Synthetic MRI Generator

This project includes a fully synthetic MRI generator (no real medical data), simulating:

• White / grey matter / CSF structure

• Rician noise

• Bias field distortion

• Random lesions

• High-frequency noise

• Partial-volume blur

## 📦 Repository Contents

• Encoder / decoder implementation

• Synthetic MRI generator

• KMRI format reference

## 🎯 Use Cases
• Neuroimaging research pipelines

• Large volumetric dataset storage

• Compression experimentation

• Fast prototyping of MRI workflows

## 📜 License

**This project is licensed under the BSD 3-Clause License.**

## 📬 Contact

For questions or feedback:
📧 kiamehr13922014@gmail.com
