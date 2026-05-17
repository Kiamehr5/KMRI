import os
import cv2
import nibabel as nib
import numpy as np
from glob import glob
from tqdm import tqdm
from sklearn.model_selection import train_test_split

# -----------------------------
# CONFIG
# -----------------------------
DATA_PATH = r"P:\JunkFiles\dataset\content\nnunet_workspace\hf_download\ASNR-MICCAI-BraTS2023-GLI-Challenge-TrainingData"
OUT_PATH = r"P:\brats_yolo"

IMG_OUT = os.path.join(OUT_PATH, "images")
LBL_OUT = os.path.join(OUT_PATH, "labels")

for split in ["train", "val", "test"]:
    os.makedirs(f"{IMG_OUT}/{split}", exist_ok=True)
    os.makedirs(f"{LBL_OUT}/{split}", exist_ok=True)

# -----------------------------
# UTIL: normalize MRI
# -----------------------------
def norm(img):
    img = img.astype(np.float32)
    img = (img - img.min()) / (img.max() - img.min() + 1e-8)
    return (img * 255).astype(np.uint8)

# -----------------------------
# UTIL: mask → bbox
# -----------------------------
def mask_to_bbox(mask):
    coords = np.where(mask > 0)
    if len(coords[0]) == 0:
        return None

    y1, y2 = coords[0].min(), coords[0].max()
    x1, x2 = coords[1].min(), coords[1].max()
    return x1, y1, x2, y2

# -----------------------------
# RECURSIVE FILE SCAN
# -----------------------------
all_files = []
for root, _, files in os.walk(DATA_PATH):
    for f in files:
        if f.endswith(".nii") or f.endswith(".nii.gz"):
            all_files.append(os.path.join(root, f))

print("Total files:", len(all_files))

# -----------------------------
# GROUP BY CASE
# -----------------------------
cases = {}

for f in all_files:
    name = os.path.basename(f)

    case_id = name.split("-t1")[0].split("-t2")[0].split("-seg")[0]

    if case_id not in cases:
        cases[case_id] = {}

    if "t2f" in name:
        cases[case_id]["flair"] = f
    elif "seg" in name:
        cases[case_id]["seg"] = f

# remove incomplete cases
cases = {k:v for k,v in cases.items() if "flair" in v and "seg" in v}

print("Valid cases:", len(cases))

# -----------------------------
# TRAIN/VAL/TEST SPLIT
# -----------------------------
keys = list(cases.keys())
train, temp = train_test_split(keys, test_size=0.3, random_state=42)
val, test = train_test_split(temp, test_size=0.5, random_state=42)

splits = {
    "train": train,
    "val": val,
    "test": test
}

# -----------------------------
# PROCESS CASES
# -----------------------------
def process_case(case_id, paths, split):
    flair = nib.load(paths["flair"]).get_fdata()
    seg = nib.load(paths["seg"]).get_fdata()

    depth = flair.shape[2]

    for i in range(depth):
        img = norm(flair[:, :, i])
        mask = seg[:, :, i]

        bbox = mask_to_bbox(mask)
        if bbox is None:
            continue

        x1, y1, x2, y2 = bbox

        h, w = img.shape

        # YOLO format
        cx = (x1 + x2) / 2 / w
        cy = (y1 + y2) / 2 / h
        bw = (x2 - x1) / w
        bh = (y2 - y1) / h

        name = f"{case_id}_{i}.png"

        img_path = os.path.join(IMG_OUT, split, name)
        lbl_path = os.path.join(LBL_OUT, split, name.replace(".png", ".txt"))

        cv2.imwrite(img_path, img)

        with open(lbl_path, "w") as f:
            f.write(f"0 {cx} {cy} {bw} {bh}")

# -----------------------------
# RUN PIPELINE
# -----------------------------
for split, ids in splits.items():
    print(f"\nProcessing {split}...")

    for cid in tqdm(ids):
        process_case(cid, cases[cid], split)

print("\nDONE ✔ Dataset ready at:", OUT_PATH)