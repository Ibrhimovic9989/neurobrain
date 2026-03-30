"""Train neurodiverse transform on ALL ABIDE data (CPU)."""
import json, logging, numpy as np, pandas as pd
from pathlib import Path
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Step 1: Download ALL ABIDE I
logger.info("Downloading ALL ABIDE I subjects...")
from nilearn.datasets import fetch_abide_pcp

dataset = fetch_abide_pcp(
    data_dir=str(Path.home() / "data/abide_full"),
    pipeline='cpac',
    band_pass_filtering=True,
    global_signal_regression=False,
    derivatives=['func_preproc'],
    n_subjects=None,
)

pheno = pd.DataFrame(dataset.phenotypic)
pheno['func_path'] = [str(p) for p in dataset.func_preproc]
pheno['diagnosis'] = pheno['DX_GROUP'].map({1: 'ASD', 2: 'TD'})
logger.info(f"ABIDE I: {len(pheno)} subjects ({(pheno.diagnosis=='ASD').sum()} ASD, {(pheno.diagnosis=='TD').sum()} TD)")
logger.info(f"Sites: {pheno['SITE_ID'].nunique()}")

# Step 2: Extract connectivity features
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

features = []
labels_list = []
n_total = len(pheno)

for i, (_, row) in enumerate(pheno.iterrows()):
    try:
        ts = masker.fit_transform(row['func_path'])
        conn = np.corrcoef(ts.T)
        conn = np.arctanh(np.clip(conn, -0.999, 0.999))
        np.fill_diagonal(conn, 0)
        upper = conn[np.triu_indices(100, k=1)]
        features.append(upper)
        labels_list.append(1 if row['diagnosis'] == 'ASD' else 0)
        if (i + 1) % 50 == 0:
            logger.info(f"  Processed {i+1}/{n_total} subjects ({len(features)} successful)")
    except Exception as e:
        if (i + 1) % 100 == 0:
            logger.warning(f"  Skip {i}: {e}")

X = np.array(features)
y = np.array(labels_list)
logger.info(f"Extracted: {len(X)} subjects ({sum(y)} ASD, {len(y)-sum(y)} TD)")

# Step 3: Statistical transform
asd_conns = X[y == 1]
td_conns = X[y == 0]

n_features = X.shape[1]
t_stats_arr = np.zeros(n_features)
p_values_arr = np.ones(n_features)

logger.info("Computing t-tests for %d connectivity features...", n_features)
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

atlas_img = atlas.maps
fsaverage = nld.fetch_surf_fsaverage("fsaverage5")
left_proj = vol_to_surf(atlas_img, fsaverage["pial_left"])
right_proj = vol_to_surf(atlas_img, fsaverage["pial_right"])
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

logger.info(f"Vertex-level transform computed:")
logger.info(f"  Scale range: [{vertex_scale.min():.3f}, {vertex_scale.max():.3f}]")
logger.info(f"  Shift range: [{vertex_shift.min():.4f}, {vertex_shift.max():.4f}]")
logger.info(f"  Vertices affected: {(np.abs(vertex_scale - 1.0) > 0.01).sum()}")

# Save
import torch
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

logger.info(f"Saved to {output_path} ({output_path.stat().st_size / 1024:.0f} KB)")
logger.info(f"DONE: {len(asd_conns)} ASD + {len(td_conns)} TD = {len(X)} total subjects")

# Upload to HuggingFace
try:
    from huggingface_hub import HfApi, login
    login(token="HF_TOKEN_HERE")
    api = HfApi()
    api.create_repo("Ibrahim9989/neurobrain-nd-transform", repo_type="model", exist_ok=True)
    api.upload_file(
        path_or_fileobj=str(output_path),
        path_in_repo="neurodiverse_transform_v3.pt",
        repo_id="Ibrahim9989/neurobrain-nd-transform",
    )
    logger.info("Uploaded to HuggingFace!")
except Exception as e:
    logger.warning(f"HF upload failed: {e}. File saved locally.")
