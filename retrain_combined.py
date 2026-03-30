"""Retrain with ALL available data: ABIDE I + ds000228 + ds002345."""
import logging, numpy as np, pandas as pd, torch, json, glob
from pathlib import Path
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from nilearn import datasets as ni_datasets, maskers
atlas = ni_datasets.fetch_atlas_schaefer_2018(n_rois=100)
masker = maskers.NiftiLabelsMasker(
    labels_img=atlas.maps, standardize='zscore_sample',
    detrend=True, low_pass=0.1, high_pass=0.01, t_r=2.0,
)

all_features = []
all_labels = []

def extract(path):
    ts = masker.fit_transform(str(path))
    conn = np.corrcoef(ts.T)
    conn = np.arctanh(np.clip(conn, -0.999, 0.999))
    np.fill_diagonal(conn, 0)
    return conn[np.triu_indices(100, k=1)]

# 1. ABIDE I (already on disk)
logger.info("=== ABIDE I ===")
from nilearn.datasets import fetch_abide_pcp
abide = fetch_abide_pcp(
    data_dir=str(Path.home() / "data/abide_full"),
    pipeline='cpac', band_pass_filtering=True,
    global_signal_regression=False, derivatives=['func_preproc'],
    n_subjects=None,
)
pheno = pd.DataFrame(abide.phenotypic)
pheno['func_path'] = [str(p) for p in abide.func_preproc]
pheno['diagnosis'] = pheno['DX_GROUP'].map({1: 'ASD', 2: 'TD'})
for i, (_, row) in enumerate(pheno.iterrows()):
    try:
        all_features.append(extract(row['func_path']))
        all_labels.append(1 if row['diagnosis'] == 'ASD' else 0)
        if (i+1) % 100 == 0: logger.info(f"  ABIDE: {i+1}/{len(pheno)}")
    except: pass
logger.info(f"  ABIDE done: {len(all_features)} subjects")

# 2. ds000228 (Richardson - Pixar)
logger.info("=== ds000228 (Pixar) ===")
ds228 = Path.home() / "data/ds000228"
parts_file = ds228 / "participants.tsv"
if parts_file.exists():
    parts = pd.read_csv(parts_file, sep="\t")
    for _, row in parts.iterrows():
        sub = row.get("participant_id", "")
        diag = str(row.get("diagnosis", row.get("group", "")))
        is_asd = "asd" in diag.lower() or "autism" in diag.lower()
        bolds = list(ds228.glob(f"{sub}/**/func/*bold.nii.gz")) + list(ds228.glob(f"{sub}/func/*bold.nii.gz"))
        for bf in bolds[:1]:
            try:
                all_features.append(extract(bf))
                all_labels.append(1 if is_asd else 0)
            except: pass
    logger.info(f"  ds000228 done. Total: {len(all_features)}")

# 3. ds002345 (Byrge - Despicable Me, partial)
logger.info("=== ds002345 (Despicable Me) ===")
ds345 = Path.home() / "data/ds002345"
parts_file = ds345 / "participants.tsv"
if parts_file.exists():
    parts = pd.read_csv(parts_file, sep="\t")
    count = 0
    for _, row in parts.iterrows():
        sub = row.get("participant_id", "")
        diag = str(row.get("diagnosis", row.get("group", "")))
        is_asd = "asd" in diag.lower() or "autism" in diag.lower()
        bolds = list(ds345.glob(f"{sub}/**/func/*bold.nii.gz")) + list(ds345.glob(f"{sub}/func/*bold.nii.gz"))
        for bf in bolds[:1]:
            try:
                all_features.append(extract(bf))
                all_labels.append(1 if is_asd else 0)
                count += 1
            except: pass
    logger.info(f"  ds002345 done ({count} subjects). Total: {len(all_features)}")

# Compute transform
X = np.array(all_features)
y = np.array(all_labels)
logger.info(f"\n{'='*50}")
logger.info(f"COMBINED: {len(X)} subjects ({sum(y)} ASD, {len(y)-sum(y)} TD)")
logger.info(f"{'='*50}")

asd_c, td_c = X[y==1], X[y==0]
t_arr = np.zeros(X.shape[1])
p_arr = np.ones(X.shape[1])
for i in range(X.shape[1]):
    t_arr[i], p_arr[i] = stats.ttest_ind(asd_c[:,i], td_c[:,i])

sig = p_arr < 0.05
logger.info(f"Significant: {sig.sum()}/{len(sig)} ({sig.mean():.1%})")

n_rois = 100
roi_eff = np.zeros(n_rois)
idx = 0
for i in range(n_rois):
    for j in range(i+1, n_rois):
        if sig[idx]: roi_eff[i] += abs(t_arr[idx]); roi_eff[j] += abs(t_arr[idx])
        idx += 1
roi_eff /= (roi_eff.max() + 1e-8)

labels = [l.decode() if isinstance(l,bytes) else str(l) for l in atlas.labels[1:]]
logger.info("Top 10:")
for i in np.argsort(roi_eff)[::-1][:10]:
    logger.info(f"  {labels[i]:40s}: {roi_eff[i]:.3f}")

from nilearn.surface import vol_to_surf
from nilearn import datasets as nld
fs = nld.fetch_surf_fsaverage("fsaverage5")
sl = np.concatenate([vol_to_surf(atlas.maps, fs["pial_left"]), vol_to_surf(atlas.maps, fs["pial_right"])]).astype(int)

vs, vsh = np.ones(20484), np.zeros(20484)
for ri in range(n_rois):
    verts = np.where(sl == ri+1)[0]
    if len(verts) > 0:
        e = roi_eff[ri]
        vs[verts] = 1.0 + (e*0.3 - 0.15)
        rt, cnt = 0, 0
        k = 0
        for ii in range(n_rois):
            for jj in range(ii+1, n_rois):
                if (ii==ri or jj==ri) and sig[k]: rt += t_arr[k]; cnt += 1
                k += 1
        if cnt: rt /= cnt
        vsh[verts] = np.tanh(rt*0.1) * e * 0.15

out = Path.home() / "neurodiverse_transform_v3.pt"
torch.save({
    'vertex_scale': torch.FloatTensor(vs), 'vertex_shift': torch.FloatTensor(vsh),
    'roi_effect': torch.FloatTensor(roi_eff),
    'asd_mean_conn': torch.FloatTensor(asd_c.mean(0)), 'td_mean_conn': torch.FloatTensor(td_c.mean(0)),
    't_stats': torch.FloatTensor(t_arr), 'p_values': torch.FloatTensor(p_arr),
    'n_asd': len(asd_c), 'n_td': len(td_c), 'roi_labels': labels,
}, str(out))
logger.info(f"Saved: {out}")

try:
    from huggingface_hub import HfApi, login
    login(token="HF_TOKEN_HERE")
    HfApi().upload_file(path_or_fileobj=str(out), path_in_repo="neurodiverse_transform_v3.pt", repo_id="Ibrahim9989/neurobrain-nd-transform")
    logger.info("Uploaded to HuggingFace!")
except Exception as e:
    logger.warning(f"Upload failed: {e}")

logger.info(f"DONE: {len(asd_c)} ASD + {len(td_c)} TD = {len(X)}")
