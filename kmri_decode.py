import json
import struct
import numpy as np
import nibabel as nib
import kmri_core

MAGIC = b"KMRI"
CHUNK_ENTRY = struct.Struct("<Q I H B B")  # off, size, mid, roi, flags


def ceil(a, b):
    return (a + b - 1) // b


def decode_kmri_cpp(input_path: str, output_path: str):
    with open(input_path, "rb") as f:
        if f.read(4) != MAGIC:
            raise ValueError("Not a KMRI file")

        version = struct.unpack("<H", f.read(2))[0]
        if version != 1:
            raise ValueError(f"Unsupported KMRI version: {version}")

        header_len = struct.unpack("<I", f.read(4))[0]
        header = json.loads(f.read(header_len).decode("utf-8"))

        X, Y, Z = header["dimensions"]
        cx, cy, cz = header["chunk_size"]
        dtype_str = header["dtype"]
        is_mask = bool(header.get("is_mask", False))
        quantized = bool(header.get("quantized", False))

        if dtype_str == "uint8":
            base_dtype = np.uint8
        elif dtype_str == "uint16":
            base_dtype = np.uint16
        else:
            raise ValueError(f"Unsupported dtype in KMRI: {dtype_str}")

        nx, ny, nz = ceil(X, cx), ceil(Y, cy), ceil(Z, cz)
        num_chunks = nx * ny * nz

        table = []
        for _ in range(num_chunks):
            off, size, mid, roi, flags = CHUNK_ENTRY.unpack(f.read(CHUNK_ENTRY.size))
            is_zero = bool(flags & 1)
            table.append((off, size, is_zero))

        vol = np.zeros((X, Y, Z), dtype=base_dtype)

        idx = 0
        for ix in range(nx):
            for iy in range(ny):
                for iz in range(nz):
                    off, size, is_zero = table[idx]
                    idx += 1

                    x0, y0, z0 = ix * cx, iy * cy, iz * cz
                    x1, y1, z1 = min(x0 + cx, X), min(y0 + cy, Y), min(z0 + cz, Z)
                    shape = (x1 - x0, y1 - y0, z1 - z0)

                    if is_zero or size == 0:
                        arr = np.zeros(shape, dtype=base_dtype)
                    else:
                        f.seek(off)
                        comp = f.read(size)
                        arr = kmri_core.decompress_chunk(
                            comp,
                            shape,
                            np.dtype(base_dtype),  # IMPORTANT: pass np.dtype
                        )

                    vol[x0:x1, y0:y1, z0:z1] = arr

    # Dequantize if needed
    if quantized and not is_mask:
        bits = int(header["q_bits"])
        q_min = float(header["q_min"])
        q_max = float(header["q_max"])
        levels = (1 << bits) - 1

        vol = vol.astype(np.float32)
        vol = vol / levels
        vol = vol * (q_max - q_min) + q_min
        out_dtype = np.float32
    else:
        out_dtype = vol.dtype

    img = nib.Nifti1Image(vol.astype(out_dtype), np.eye(4))
    nib.save(img, output_path)
    print(f"[KMRI] Decoded → {output_path}")
