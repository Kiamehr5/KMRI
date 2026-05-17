import numpy as np
import kmri_core
from kmri_encode import encode_kmri_cpp
from kmri_decode import decode_kmri_cpp

# --- 1. Core C++ sanity check ---
print("[TEST] C++ core round-trip")
arr = np.ones((4, 4, 4), dtype=np.int16)
c = kmri_core.compress_chunk(arr, 3)
d = kmri_core.decompress_chunk(c, (4, 4, 4), arr.dtype)
print(d)

# --- 2. File-level test (set your own paths) ---
# Replace these with real files on your machine
input_nii = r"<BraTS_sample.nii"
output_kmri = r"output.kmri"
decoded_nii = r"decoded.nii"

print("[TEST] Encoding KMRI…")
encode_kmri_cpp(input_nii, output_kmri)

print("[TEST] Decoding KMRI…")
decode_kmri_cpp(output_kmri, decoded_nii)

print("[TEST] Done.")