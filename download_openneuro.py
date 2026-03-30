"""Download OpenNeuro autism datasets and retrain with all data combined."""
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path.home() / "data"

# ============================================================
# Step 1: Download OpenNeuro datasets
# ============================================================

# ds000228 - Richardson 2018 (kids watching Pixar, ASD + TD)
logger.info("Downloading OpenNeuro ds000228 (Richardson 2018 - Pixar)...")
import openneuro
openneuro.download(
    dataset="ds000228",
    target_dir=str(DATA_DIR / "ds000228"),
    include=["sub-*/**/*bold.nii.gz", "participants.tsv"],
)
logger.info("ds000228 done")

# ds002345 - Byrge 2020 (Despicable Me)
logger.info("Downloading OpenNeuro ds002345 (Byrge 2020 - Despicable Me)...")
openneuro.download(
    dataset="ds002345",
    target_dir=str(DATA_DIR / "ds002345"),
    include=["sub-*/**/*bold.nii.gz", "participants.tsv"],
)
logger.info("ds002345 done")

# ============================================================
# Step 2: Extract connectivity from ALL datasets
# ============================================================

from nilearn import datasets as ni_datasets, maskers

atlas = ni_datasets.fetch_atlas_schaefer_2018(n_rois=100)
masker = maskers.NiftiLabelsMasker(
    labels_img=atlas.maps,
    standardize='zscore_sample',
    detrend=True,
    low_pass=0.1,
    high_pass=0.01,
    t_r=2.0,
)

all_features = []
all_labels = []

def extract_connectivity(nifti_path):
    """Extract upper-triangle connectivity from a NIfTI file."""
    ts = masker.fit_transform(str(nifti_path))
    conn = np.corrcoef(ts.T)
    conn = np.arctanh(np.clip(conn, -0.999, 0.999))
    np.fill_diagonal(conn, 0)
    return conn[np.triu_indices(100, k=1)]


# --- ABIDE I (already extracted, load from existing transform) ---
logger.info("Loading ABIDE I features...")
import torch
existing = torch.load(str(Path.home() / "neurodiverse_transform_v3.pt"), map_location="cpu", weights_only=True)
logger.info(f"  ABIDE I: {existing['n_asd']} ASD + {existing['n_td']} TD")

# We need raw features, not just the transform. Re-extract from ABIDE.
from nilearn.datasets import fetch_abide_pcp
abide = fetch_abide_pcp(
    data_dir=str(DATA_DIR / "abide_full"),
    pipeline='cpac',
    band_pass_filtering=True,
    global_signal_regression=False,
    derivatives=['func_preproc'],
    n_subjects=None,
)
abide_pheno = pd.DataFrame(abide.phenotypic)
abide_pheno['func_path'] = [str(p) for p in abide.func_preproc]
abide_pheno['diagnosis'] = abide_pheno['DX_GROUP'].map({1: 'ASD', 2: 'TD'})

n = len(abide_pheno)
for i, (_, row) in enumerate(abide_pheno.iterrows()):
    try:
        feat = extract_connectivity(row['func_path'])
        all_features.append(feat)
        all_labels.append(1 if row['diagnosis'] == 'ASD' else 0)
        if (i + 1) % 100 == 0:
            logger.info(f"  ABIDE: {i+1}/{n} ({len(all_features)} ok)")
    except:
        pass

logger.info(f"  ABIDE done: {len(all_features)} subjects")


# --- OpenNeuro ds000228 (Richardson 2018) ---
logger.info("Extracting ds000228 (Richardson - Pixar)...")
ds228_dir = DATA_DIR / "ds000228"
participants_file = ds228_dir / "participants.tsv"
if participants_file.exists():
    parts = pd.read_csv(participants_file, sep="\t")
    for _, row in parts.iterrows():
        sub_id = row.get("participant_id", "")
        diagnosis = str(row.get("diagnosis", row.get("group", "")))
        is_asd = "asd" in diagnosis.lower() or "autism" in diagnosis.lower()

        # Find bold files
        bold_files = list(ds228_dir.glob(f"{sub_id}/**/func/*bold.nii.gz"))
        if not bold_files:
            bold_files = list(ds228_dir.glob(f"{sub_id}/func/*bold.nii.gz"))

        for bf in bold_files:
            try:
                feat = extract_connectivity(bf)
                all_features.append(feat)
                all_labels.append(1 if is_asd else 0)
            except:
                pass
    logger.info(f"  ds000228 done. Total: {len(all_features)}")
else:
    logger.warning("  ds000228 participants.tsv not found")


# --- OpenNeuro ds002345 (Byrge 2020) ---
logger.info("Extracting ds002345 (Byrge - Despicable Me)...")
ds345_dir = DATA_DIR / "ds002345"
participants_file = ds345_dir / "participants.tsv"
if participants_file.exists():
    parts = pd.read_csv(participants_file, sep="\t")
    for _, row in parts.iterrows():
        sub_id = row.get("participant_id", "")
        diagnosis = str(row.get("diagnosis", row.get("group", "")))
        is_asd = "asd" in diagnosis.lower() or "autism" in diagnosis.lower()

        bold_files = list(ds345_dir.glob(f"{sub_id}/**/func/*bold.nii.gz"))
        if not bold_files:
            bold_files = list(ds345_dir.glob(f"{sub_id}/func/*bold.nii.gz"))

        for bf in bold_files:
            try:
                feat = extract_connectivity(bf)
                all_features.append(feat)
                all_labels.append(1 if is_asd else 0)
            except:
                pass
    logger.info(f"  ds002345 done. Total: {len(all_features)}")
else:
    logger.warning("  ds002345 participants.tsv not found")


# ============================================================
# Step 3: Compute new statistical transform
# ============================================================
X = np.array(all_features)
y = np.array(all_labels)
logger.info(f"\nCOMBINED DATASET: {len(X)} subjects ({sum(y)} ASD, {len(y)-sum(y)} TD)")

asd_conns = X[y == 1]
td_conns = X[y == 0]

n_features = X.shape[1]
t_stats_arr = np.zeros(n_features)
p_values_arr = np.ones(n_features)

logger.info("Computing t-tests...")
for i in range(n_features):
    t, p = stats.ttest_ind(asd_conns[:, i], td_conns[:, i])
    t_stats_arr[i] = t
    p_values_arr[i] = p

sig_mask = p_values_arr < 0.05
logger.info(f"Significant connections: {sig_mask.sum()} / {n_features} ({sig_mask.mean():.1%})")

# Map to ROIs
n_rois = 100
roi_effect = np.zeros(n_rois)
idx = 0
for i in range(n_rois):
    for j in range(i + 1, n_rois):
        if sig_mask[idx]:
            roi_effect[i] += abs(t_stats_arr[idx])
            roi_effect[j] += abs(t_stats_arr[idx])
        idx += 1
roi_effect = roi_effect / (roi_effect.max() + 1e-8)

labels = [l.decode() if isinstance(l, bytes) else str(l) for l in atlas.labels[1:]]
logger.info("Top 10 most affected ROIs:")
for idx in np.argsort(roi_effect)[::-1][:10]:
    logger.info(f"  {labels[idx]:40s}: {roi_effect[idx]:.3f}")

# Map to brain vertices
from nilearn.surface import vol_to_surf
from nilearn import datasets as nld

fsaverage = nld.fetch_surf_fsaverage("fsaverage5")
left_proj = vol_to_surf(atlas.maps, fsaverage["pial_left"])
right_proj = vol_to_surf(atlas.maps, fsaverage["pial_right"])
surface_labels = np.concatenate([left_proj, right_proj]).astype(int)

vertex_scale = np.ones(20484)
vertex_shift = np.zeros(20484)

for roi_idx in range(n_rois):
    roi_id = roi_idx + 1
    vertices = np.where(surface_labels == roi_id)[0]
    if len(vertices) > 0:
        effect = roi_effect[roi_idx]
        vertex_scale[vertices] = 1.0 + (effect * 0.3 - 0.15)
        roi_t = 0
        count = 0
        k = 0
        for ii in range(n_rois):
            for jj in range(ii + 1, n_rois):
                if ii == roi_idx or jj == roi_idx:
                    if sig_mask[k]:
                        roi_t += t_stats_arr[k]
                        count += 1
                k += 1
        if count > 0:
            roi_t /= count
        vertex_shift[vertices] = np.tanh(roi_t * 0.1) * effect * 0.15

logger.info(f"Scale range: [{vertex_scale.min():.3f}, {vertex_scale.max():.3f}]")
logger.info(f"Shift range: [{vertex_shift.min():.4f}, {vertex_shift.max():.4f}]")
logger.info(f"Vertices affected: {(np.abs(vertex_scale - 1.0) > 0.01).sum()}")

# Save
output_path = Path.home() / "neurodiverse_transform_v3.pt"
torch.save({
    'vertex_scale': torch.FloatTensor(vertex_scale),
    'vertex_shift': torch.FloatTensor(vertex_shift),
    'roi_effect': torch.FloatTensor(roi_effect),
    'asd_mean_conn': torch.FloatTensor(asd_conns.mean(axis=0)),
    'td_mean_conn': torch.FloatTensor(td_conns.mean(axis=0)),
    't_stats': torch.FloatTensor(t_stats_arr),
    'p_values': torch.FloatTensor(p_values_arr),
    'n_asd': len(asd_conns),
    'n_td': len(td_conns),
    'roi_labels': labels,
}, str(output_path))
logger.info(f"Saved to {output_path}")

# Upload
try:
    from huggingface_hub import HfApi, login
    login(token="HF_TOKEN_HERE")
    api = HfApi()
    api.upload_file(
        path_or_fileobj=str(output_path),
        path_in_repo="neurodiverse_transform_v3.pt",
        repo_id="Ibrahim9989/neurobrain-nd-transform",
    )
    logger.info("Uploaded to HuggingFace!")
except Exception as e:
    logger.warning(f"Upload failed: {e}")

logger.info(f"\nFINAL: {len(asd_conns)} ASD + {len(td_conns)} TD = {len(X)} total")
