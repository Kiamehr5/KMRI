import gzip
import io
import numpy as np
try:
    import zstandard as zstd
except ImportError:
    zstd = None

def gzip_compress(data_bytes):
    return gzip.compress(data_bytes, compresslevel=6)

def gzip_decompress(data_bytes):
    return gzip.decompress(data_bytes)

def zstd_compress(data_bytes, level=3):
    if zstd is None: raise ImportError("zstandard not installed")
    cctx = zstd.ZstdCompressor(level=level)
    return cctx.compress(data_bytes)

def zstd_decompress(data_bytes):
    if zstd is None: raise ImportError("zstandard not installed")
    dctx = zstd.ZstdDecompressor()
    return dctx.decompress(data_bytes)

def numpy_zstd_compress(volume, level=3):
    if zstd is None: raise ImportError("zstandard not installed")
    buf = io.BytesIO()
    # Save uncompressed numpy array directly to buffer
    np.save(buf, volume)
    buf.seek(0)
    cctx = zstd.ZstdCompressor(level=level)
    return cctx.compress(buf.read())

def numpy_zstd_decompress(data_bytes):
    if zstd is None: raise ImportError("zstandard not installed")
    dctx = zstd.ZstdDecompressor()
    decompressed_bytes = dctx.decompress(data_bytes)
    buf = io.BytesIO(decompressed_bytes)
    return np.load(buf)
