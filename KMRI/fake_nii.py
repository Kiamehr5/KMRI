import numpy as np
import nibabel as nib
from scipy.ndimage import gaussian_filter

# -----------------------------
# CONFIG
# -----------------------------
size = 512  # 512^3 uint16 ≈ 268MB raw; increase to 700–800 for ~1GB
dtype = np.float32

# -----------------------------
# BASE VOLUME (random tissue layers)
# -----------------------------
x = np.linspace(-1, 1, size)[:, None, None]
y = np.linspace(-1, 1, size)[None, :, None]
z = np.linspace(-1, 1, size)[None, None, :]

r = np.sqrt(x**2 + y**2 + z**2)

# Tissue masks
wm = (r < 0.55).astype(dtype)        # white matter core
gm = ((r >= 0.55) & (r < 0.75)).astype(dtype)  # grey matter shell
csf = (r >= 0.75).astype(dtype)      # CSF outer region

volume = (
    wm * 900 +   # white matter intensity
    gm * 600 +   # grey matter
    csf * 200    # CSF
)

# -----------------------------
# RANDOM LESIONS (high entropy)
# -----------------------------
for _ in range(20):
    cx, cy, cz = np.random.randint(0, size, 3)
    radius = np.random.randint(10, 40)
    lx, ly, lz = np.ogrid[:size, :size, :size]
    mask = (lx - cx)**2 + (ly - cy)**2 + (lz - cz)**2 < radius**2
    volume[mask] += np.random.uniform(300, 800)

# -----------------------------
# BIAS FIELD (smooth intensity warp)
# -----------------------------
bias = (
    1
    + 0.4 * gaussian_filter(np.random.randn(size, size, size), sigma=80)
)
volume *= bias

# -----------------------------
# RICIAN NOISE (real MRI noise model)
# -----------------------------
noise1 = np.random.normal(0, 40, volume.shape)
noise2 = np.random.normal(0, 40, volume.shape)
volume = np.sqrt((volume + noise1)**2 + noise2**2)

# -----------------------------
# HIGH-FREQUENCY NOISE (hard to compress)
# -----------------------------
hf_noise = gaussian_filter(np.random.randn(size, size, size), sigma=1)
volume += hf_noise * 20

# -----------------------------
# PARTIAL VOLUME BLUR
# -----------------------------
volume = gaussian_filter(volume, sigma=1.2)

# -----------------------------
# NORMALIZE + SAVE
# -----------------------------
volume = np.clip(volume, 0, 2000)
volume = volume.astype(np.uint16)

img = nib.Nifti1Image(volume, affine=np.eye(4))
nib.save(img, "synthetic_realistic_hardcore.nii")

print("Saved synthetic_realistic_hardcore.nii")
