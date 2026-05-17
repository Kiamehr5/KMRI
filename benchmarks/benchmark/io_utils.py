import nibabel as nib
import numpy as np
import os

def load_nifti(filepath):
    """Loads a NIfTI file and returns the volume, affine, header, and raw uncompressed size."""
    img = nib.load(filepath)
    vol = img.get_fdata().astype(np.float32)
    raw_bytes = np.prod(img.shape) * img.get_data_dtype().itemsize
    # Fallback if nbytes isn't accurate
    if raw_bytes == 0:
        raw_bytes = vol.nbytes
    return vol, img.affine, img.header, raw_bytes

def save_nifti(volume, affine, filepath):
    """Saves a NumPy volume to a NIfTI file."""
    img = nib.Nifti1Image(volume, affine)
    nib.save(img, filepath)

def get_raw_file_bytes(filepath):
    """Returns the size of the file on disk."""
    return os.path.getsize(filepath)
