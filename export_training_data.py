"""Export compact per-subject training data for Colab fine-tuning.

Produces:
  colab_training_data.npz
    X: (n_subjects, 4950) connectivity features (Fisher-z harmonized)
    y: (n_subjects,) diagnosis (1=ASD, 0=TD)
    age: (n_subjects,) age in years
    sex: (n_subjects,) 1=M, 2=F
    site_idx: (n_subjects,) site index (0..35)
    site_names: list of site names
"""
import json, glob, logging, numpy as np, pandas as pd
from pathlib import Path
from nilearn.datasets import fetch_abide_pcp
from nilearn import datasets as ni_datasets, maskers
from numpy.linalg import lstsq as np_lstsq

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

# ── Load ABIDE I ──
logger.info("Loading ABIDE I...")
dataset_i = fetch_abide_pcp(
    data_dir=str(Path.home() / "data/abide_full"),
    pipeline='cpac', band_pass_filtering=True,
    global_signal_regression=False, derivatives=['func_preproc'], n_subjects=None,
)
pheno_i = pd.DataFrame(dataset_i.phenotypic)
pheno_i['func_path'] = [str(p) for p in dataset_i.func_preproc]
pheno_i['diagnosis'] = pheno_i['DX_GROUP'].map({1: 'ASD', 2: 'TD'})
pheno_i['age'] = pd.to_numeric(pheno_i['AGE_AT_SCAN'], errors='coerce')
pheno_i['sex'] = pd.to_numeric(pheno_i['SEX'], errors='coerce')
pheno_i['site'] = pheno_i['SITE_ID'].astype(str) + '_I'

# ── Load ABIDE II from raw BIDS ──
logger.info("Loading ABIDE II...")
abide2_rows = []
for meta_file, dir_name in [("/tmp/abide2_children_download.json", "abide2_children"),
                             ("/tmp/abide2_nonchildren_download.json", "abide2_rest")]:
    meta_path = Path(meta_file)
    if not meta_path.exists():
        continue
    data_dir = Path.home() / f"data/{dir_name}"
    with open(meta_path) as f:
        for subj in json.load(f):
            sub_dir = data_dir / f"sub-{subj['sub_id']}"
            bold_files = sorted(glob.glob(str(sub_dir / "*rest*bold.nii.gz")))
            if bold_files:
                abide2_rows.append({
                    'func_path': bold_files[0],
                    'diagnosis': 'ASD' if subj['dx'] == 1 else 'TD',
                    'age': subj['age'], 'sex': 1,
                    'site': subj['site'] + '_II',
                })
pheno_ii = pd.DataFrame(abide2_rows) if abide2_rows else pd.DataFrame()

all_pheno = pd.concat([pheno_i, pheno_ii], ignore_index=True)
logger.info(f"Total: {len(all_pheno)} subjects")

# ── Extract connectivity (same pipeline as v5) ──
atlas = ni_datasets.fetch_atlas_schaefer_2018(n_rois=100)
masker = maskers.NiftiLabelsMasker(
    labels_img=atlas.maps, standardize='zscore_sample',
    detrend=True, low_pass=0.1, high_pass=0.01, t_r=2.0,
)

features = []
meta = []
for i, (_, row) in enumerate(all_pheno.iterrows()):
    try:
        ts = masker.fit_transform(row['func_path'])
        if ts.shape[0] < 20:
            continue
        conn = np.corrcoef(ts.T)
        conn = np.nan_to_num(conn, nan=0.0)
        conn = np.arctanh(np.clip(conn, -0.999, 0.999))
        conn = np.nan_to_num(conn, nan=0.0)
        np.fill_diagonal(conn, 0)
        upper = conn[np.triu_indices(100, k=1)]
        if np.any(np.isnan(upper)) or np.any(np.isinf(upper)):
            continue
        features.append(upper)
        meta.append({
            'diagnosis': 1 if row['diagnosis'] == 'ASD' else 0,
            'age': row['age'], 'sex': row['sex'], 'site': row['site'],
        })
        if (i + 1) % 100 == 0:
            logger.info(f"  {i+1}/{len(all_pheno)} ({len(features)} ok)")
    except Exception as e:
        if (i + 1) % 200 == 0:
            logger.warning(f"  Skip {i}: {e}")

X = np.array(features, dtype=np.float32)
meta_df = pd.DataFrame(meta)
y = meta_df['diagnosis'].values.astype(np.int8)
logger.info(f"Extracted: {len(X)} subjects ({sum(y)} ASD, {len(y)-sum(y)} TD)")

# ── Site harmonization (same as v5) ──
logger.info("Harmonizing site effects...")
site_dummies = pd.get_dummies(meta_df['site'], drop_first=True).values.astype(np.float32)
A_site = np.column_stack([np.ones(len(X), dtype=np.float32), site_dummies])
X_harm = np.zeros_like(X)
for feat_i in range(X.shape[1]):
    coeffs, _, _, _ = np_lstsq(A_site, X[:, feat_i], rcond=None)
    residual = X[:, feat_i] - A_site @ coeffs
    X_harm[:, feat_i] = (residual + X[:, feat_i].mean()).astype(np.float32)
logger.info("Harmonization complete.")

# ── Site index + metadata ──
site_names = sorted(meta_df['site'].unique())
site_to_idx = {s: i for i, s in enumerate(site_names)}
site_idx = np.array([site_to_idx[s] for s in meta_df['site']], dtype=np.int16)
age = meta_df['age'].fillna(meta_df['age'].median()).values.astype(np.float32)
sex = meta_df['sex'].fillna(1).values.astype(np.int8)

# ── Get ROI labels and surface mapping for vertex-level use ──
roi_labels = [l.decode() if isinstance(l, bytes) else str(l) for l in atlas.labels[1:]]

# ── Save ──
output_path = Path.home() / "colab_training_data.npz"
np.savez_compressed(
    str(output_path),
    X=X_harm,
    y=y,
    age=age,
    sex=sex,
    site_idx=site_idx,
    site_names=np.array(site_names),
    roi_labels=np.array(roi_labels),
)
logger.info(f"Saved to {output_path} ({output_path.stat().st_size / 1024 / 1024:.1f} MB)")
logger.info(f"Shape: X={X_harm.shape}, y={y.shape}, age={age.shape}")
logger.info(f"DONE")
