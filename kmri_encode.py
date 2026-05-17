import json
import struct
import numpy as np
import nibabel as nib
import kmri_core

MAGIC = b"KMRI"
VERSION = 1
CHUNK_ENTRY = struct.Struct("<Q I H B B")  # off, size, mid, roi, flags


def ceil(a, b):
    return (a + b - 1) // b


def encode_kmri_cpp(
    input_path: str,
    output_path: str,
    bits: int = 8,
    chunk_size_mri=(64, 64, 64),
    chunk_size_mask=(128, 128, 128),
    roi_threshold=0,
    roi_level=5,
    bg_level=18,
):
    img = nib.load(input_path)
    data = img.get_fdata()

    # Detect mask vs intensity
    unique_vals = np.unique(data)
    is_mask = (len(unique_vals) <= 16) and np.all(unique_vals == np.round(unique_vals))

    if is_mask:
        # Label mask: keep exact labels, uint8
        data = data.astype(np.uint8)
        quantized = False
        q_bits = None
        q_min = None
        q_max = None
        chunk_size = chunk_size_mask
        dtype_str = "uint8"
    else:
        # Intensity volume: lossy quantization to N bits
        bits = int(bits)
        assert 1 <= bits <= 16
        data = data.astype(np.float32)

        # Robust min/max (ignore extreme outliers)
        q_min = float(np.percentile(data, 0.5))
        q_max = float(np.percentile(data, 99.5))
        if q_max == q_min:
            q_max = q_min + 1.0

        levels = (1 << bits) - 1
        scaled = np.clip((data - q_min) / (q_max - q_min), 0.0, 1.0)
        q = (scaled * levels + 0.5).astype(np.uint16 if bits > 8 else np.uint8)

        data = q
        quantized = True
        q_bits = bits
        chunk_size = chunk_size_mri
        dtype_str = "uint16" if bits > 8 else "uint8"

    X, Y, Z = data.shape
    cx, cy, cz = chunk_size
    nx, ny, nz = ceil(X, cx), ceil(Y, cy), ceil(Z, cz)

    header = {
        "dimensions": [int(X), int(Y), int(Z)],
        "voxel_size": [float(v) for v in img.header.get_zooms()[:3]],
        "dtype": dtype_str,
        "endianness": "little",
        "modalities": ["T1"],
        "chunk_size": [int(cx), int(cy), int(cz)],
        "compression": "zstd",
        "is_mask": bool(is_mask),
        "quantized": bool(quantized),
        "q_bits": int(q_bits) if q_bits is not None else None,
        "q_min": float(q_min) if q_min is not None else None,
        "q_max": float(q_max) if q_max is not None else None,
    }

    header_bytes = json.dumps(header).encode("utf-8")
    header_len = len(header_bytes)

    chunks = []

    for ix in range(nx):
        for iy in range(ny):
            for iz in range(nz):
                x0, y0, z0 = ix * cx, iy * cy, iz * cz
                x1, y1, z1 = min(x0 + cx, X), min(y0 + cy, Y), min(z0 + cz, Z)

                chunk = np.ascontiguousarray(data[x0:x1, y0:y1, z0:z1])

                # Zero-chunk detection
                is_zero = bool(np.all(chunk == 0))

                if is_zero:
                    compressed = b""
                    roi_flag = 0
                else:
                    roi_flag = 1 if np.any(chunk > roi_threshold) else 0
                    level = roi_level if roi_flag else bg_level
                    compressed = kmri_core.compress_chunk(chunk, int(level))

                chunks.append((compressed, roi_flag, is_zero))

    with open(output_path, "wb") as f:
        # Magic + version + header
        f.write(MAGIC)
        f.write(struct.pack("<H", VERSION))
        f.write(struct.pack("<I", header_len))
        f.write(header_bytes)

        # Reserve space for chunk table
        table_offset = f.tell()
        num_chunks = len(chunks)
        f.seek(num_chunks * CHUNK_ENTRY.size, 1)

        # Write chunk data and build table
        chunk_table = []
        offset = f.tell()

        for compressed, roi_flag, is_zero in chunks:
            size = len(compressed)
            if size > 0:
                f.write(compressed)
            flags = 1 if is_zero else 0
            chunk_table.append((offset if size > 0 else 0, size, 0, roi_flag, flags))
            offset += size

        # Write chunk table
        f.seek(table_offset)
        for off, size, mid, roi, flags in chunk_table:
            f.write(CHUNK_ENTRY.pack(off, size, mid, roi, flags))

    print(f"[KMRI] Encoded → {output_path}")
