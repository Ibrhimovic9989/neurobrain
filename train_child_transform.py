"""
Train child-specific neurodiverse transform (ages < 12).

Combines ABIDE I + ABIDE II children for maximum statistical power.
Uses FDR correction, site harmonization, age/sex covariates, bootstrap CI.

Expected: ~261 ASD + ~269 TD children under 12 (combined).
"""
import logging, numpy as np, pandas as pd, torch
from pathlib import Path
from scipy import stats
from numpy.linalg import lstsq as np_lstsq
from statsmodels.stats.multitest import multipletests

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

N_BOOTSTRAP = 200
FDR_ALPHA = 0.05
AGE_MAX = 12.0

# ── Step 1: Load ABIDE I ──
logger.info("Loading ABIDE I...")
from nilearn.datasets import fetch_abide_pcp
from nilearn import datasets as ni_datasets, maskers

dataset_i = fetch_abide_pcp(
    data_dir=str(Path.home() / "data/abide_full"),
    pipeline='cpac',
    band_pass_filtering=True,
    global_signal_regression=False,
    derivatives=['func_preproc'],
    n_subjects=None,
)

pheno_i = pd.DataFrame(dataset_i.phenotypic)
pheno_i['func_path'] = [str(p) for p in dataset_i.func_preproc]
pheno_i['diagnosis'] = pheno_i['DX_GROUP'].map({1: 'ASD', 2: 'TD'})
pheno_i['age'] = pd.to_numeric(pheno_i['AGE_AT_SCAN'], errors='coerce')
pheno_i['sex'] = pd.to_numeric(pheno_i['SEX'], errors='coerce')
pheno_i['site'] = pheno_i['SITE_ID'].astype(str) + '_I'
pheno_i['source'] = 'ABIDE_I'

# Filter children < 12
children_i = pheno_i[pheno_i['age'] < AGE_MAX].copy()
logger.info(f"ABIDE I children (<{AGE_MAX}): {len(children_i)} ({(children_i.diagnosis=='ASD').sum()} ASD, {(children_i.diagnosis=='TD').sum()} TD)")

# ── Step 2: Load ABIDE II from raw BIDS downloads ──
logger.info("Loading ABIDE II children from raw BIDS...")
import json, glob

children_ii = pd.DataFrame()
try:
    abide2_dir = Path.home() / "data/abide2_children"
    pheno_path = Path("/tmp/abide2_children_download.json")

    if pheno_path.exists() and abide2_dir.exists():
        with open(pheno_path) as f:
            abide2_meta = json.load(f)

        rows = []
        for child in abide2_meta:
            sub_dir = abide2_dir / f"sub-{child['sub_id']}"
            bold_files = sorted(glob.glob(str(sub_dir / "*rest*bold.nii.gz")))
            if bold_files:
                rows.append({
                    'func_path': bold_files[0],
                    'diagnosis': 'ASD' if child['dx'] == 1 else 'TD',
                    'age': child['age'],
                    'sex': 1,  # Default, not available in raw BIDS phenotypic
                    'site': child['site'] + '_II',
                    'source': 'ABIDE_II',
                })

        if rows:
            children_ii = pd.DataFrame(rows)
            children_ii = children_ii[children_ii['age'] < AGE_MAX].copy()
            logger.info(f"ABIDE II children (<{AGE_MAX}): {len(children_ii)} ({(children_ii.diagnosis=='ASD').sum()} ASD, {(children_ii.diagnosis=='TD').sum()} TD)")
        else:
            logger.warning("No ABIDE II fMRI files found.")
    else:
        logger.warning("ABIDE II data not found. Using ABIDE I only.")
except Exception as e:
    logger.warning(f"ABIDE II loading failed: {e}. Using ABIDE I only.")
    children_ii = pd.DataFrame()

# ── Step 3: Combine ──
children = pd.concat([children_i, children_ii], ignore_index=True)
logger.info(f"Combined children: {len(children)} ({(children.diagnosis=='ASD').sum()} ASD, {(children.diagnosis=='TD').sum()} TD)")
logger.info(f"Sites: {children['site'].nunique()}")
logger.info(f"Age range: {children['age'].min():.1f} - {children['age'].max():.1f}")

if (children.diagnosis == 'ASD').sum() < 20 or (children.diagnosis == 'TD').sum() < 20:
    logger.error("Too few subjects for reliable analysis. Exiting.")
    exit(1)

# ── Step 4: Extract connectivity ──
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
meta = []
n_total = len(children)

for i, (_, row) in enumerate(children.iterrows()):
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
            'age': row['age'],
            'sex': row['sex'],
            'site': row['site'],
            'source': row['source'],
        })
        if (i + 1) % 25 == 0:
            logger.info(f"  Processed {i+1}/{n_total} ({len(features)} ok)")
    except Exception as e:
        if (i + 1) % 50 == 0:
            logger.warning(f"  Skip {i}: {e}")

X = np.array(features)
meta_df = pd.DataFrame(meta)
y = meta_df['diagnosis'].values
logger.info(f"Extracted: {len(X)} children ({sum(y)} ASD, {len(y)-sum(y)} TD)")

# ── Step 5: Site harmonization ──
logger.info("Harmonizing site effects...")
site_dummies = pd.get_dummies(meta_df['site'], drop_first=True).values.astype(float)
A_site = np.column_stack([np.ones(len(X)), site_dummies])
X_harmonized = np.zeros_like(X)
for feat_i in range(X.shape[1]):
    coeffs, _, _, _ = np_lstsq(A_site, X[:, feat_i], rcond=None)
    residual = X[:, feat_i] - A_site @ coeffs
    X_harmonized[:, feat_i] = residual + X[:, feat_i].mean()
logger.info("Site harmonization complete.")

# ── Step 6: Covariate-adjusted t-tests ──
logger.info("Computing covariate-adjusted t-tests...")
n_features = X_harmonized.shape[1]
t_stats_arr = np.zeros(n_features)
p_values_arr = np.ones(n_features)

age = meta_df['age'].fillna(meta_df['age'].median()).values
sex = meta_df['sex'].fillna(1).values

for feat_i in range(n_features):
    cov_matrix = np.column_stack([np.ones(len(X)), age, sex])
    coeffs, _, _, _ = np_lstsq(cov_matrix, X_harmonized[:, feat_i], rcond=None)
    residual = X_harmonized[:, feat_i] - cov_matrix @ coeffs
    asd_res = residual[y == 1]
    td_res = residual[y == 0]
    if len(asd_res) > 2 and len(td_res) > 2:
        t, p = stats.ttest_ind(asd_res, td_res)
        t_stats_arr[feat_i] = t
        p_values_arr[feat_i] = p

# ── Step 7: FDR correction ──
fdr_rejected, fdr_pvals, _, _ = multipletests(p_values_arr, alpha=FDR_ALPHA, method='fdr_bh')
bonf_rejected, _, _, _ = multipletests(p_values_arr, alpha=FDR_ALPHA, method='bonferroni')

sig_uncorrected = (p_values_arr < 0.05).sum()
sig_fdr = fdr_rejected.sum()
sig_bonf = bonf_rejected.sum()

logger.info(f"Significant connections (CHILDREN ONLY):")
logger.info(f"  Uncorrected (p<0.05): {sig_uncorrected} / {n_features} ({sig_uncorrected/n_features:.1%})")
logger.info(f"  FDR corrected (q<0.05): {sig_fdr} / {n_features} ({sig_fdr/n_features:.1%})")
logger.info(f"  Bonferroni (p<0.05): {sig_bonf} / {n_features} ({sig_bonf/n_features:.1%})")

sig_mask = fdr_rejected

# ── Step 8: Build vertex-level transform ──
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
logger.info("Top 10 most affected ROIs (children, FDR-corrected):")
for idx in np.argsort(roi_effect)[::-1][:10]:
    logger.info(f"  {labels[idx]:40s}: {roi_effect[idx]:.3f}")

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

logger.info(f"Child vertex-level transform:")
logger.info(f"  Scale range: [{vertex_scale.min():.3f}, {vertex_scale.max():.3f}]")
logger.info(f"  Shift range: [{vertex_shift.min():.4f}, {vertex_shift.max():.4f}]")
logger.info(f"  Vertices affected: {(np.abs(vertex_scale - 1.0) > 0.01).sum()}")

# ── Step 9: Bootstrap CI ──
logger.info(f"Computing {N_BOOTSTRAP} bootstrap confidence intervals...")
bootstrap_scales = np.zeros((N_BOOTSTRAP, 20484))

for b in range(N_BOOTSTRAP):
    asd_idx = np.random.choice(np.where(y == 1)[0], size=sum(y == 1), replace=True)
    td_idx = np.random.choice(np.where(y == 0)[0], size=sum(y == 0), replace=True)

    boot_t = np.zeros(n_features)
    for feat_i in range(n_features):
        t, _ = stats.ttest_ind(X_harmonized[asd_idx, feat_i], X_harmonized[td_idx, feat_i])
        boot_t[feat_i] = t

    boot_roi = np.zeros(n_rois)
    k = 0
    for i in range(n_rois):
        for j in range(i + 1, n_rois):
            if sig_mask[k]:
                boot_roi[i] += abs(boot_t[k])
                boot_roi[j] += abs(boot_t[k])
            k += 1
    if boot_roi.max() > 0:
        boot_roi = boot_roi / boot_roi.max()

    for roi_idx in range(n_rois):
        roi_id = roi_idx + 1
        verts = np.where(surface_labels == roi_id)[0]
        if len(verts) > 0:
            bootstrap_scales[b, verts] = 1.0 + (boot_roi[roi_idx] * 0.3 - 0.15)

    if (b + 1) % 50 == 0:
        logger.info(f"  Bootstrap {b+1}/{N_BOOTSTRAP}")

vertex_ci_lower = np.percentile(bootstrap_scales, 2.5, axis=0)
vertex_ci_upper = np.percentile(bootstrap_scales, 97.5, axis=0)
ci_width = vertex_ci_upper - vertex_ci_lower
logger.info(f"Uncertainty (95% CI width): mean={ci_width.mean():.4f}, max={ci_width.max():.4f}")

# ── Step 10: Save ──
output_path = Path.home() / "neurodiverse_transform_child.pt"
torch.save({
    'vertex_scale': torch.FloatTensor(vertex_scale),
    'vertex_shift': torch.FloatTensor(vertex_shift),
    'roi_effect': torch.FloatTensor(roi_effect),
    'vertex_ci_lower': torch.FloatTensor(vertex_ci_lower),
    'vertex_ci_upper': torch.FloatTensor(vertex_ci_upper),
    't_stats': torch.FloatTensor(t_stats_arr),
    'p_values_fdr': torch.FloatTensor(np.array(fdr_pvals)),
    'n_asd': int(sum(y)),
    'n_td': int(len(y) - sum(y)),
    'sig_uncorrected': int(sig_uncorrected),
    'sig_fdr': int(sig_fdr),
    'sig_bonferroni': int(sig_bonf),
    'roi_labels': labels,
    'age_range': f'0-{AGE_MAX}',
    'sources': ['ABIDE_I', 'ABIDE_II'],
    'version': 'child_v1',
    'corrections': ['site_harmonization', 'age_sex_covariates', 'fdr_bh', 'bootstrap_ci'],
}, str(output_path))

logger.info(f"\nSaved to {output_path} ({output_path.stat().st_size / 1024:.0f} KB)")
logger.info(f"DONE: Child transform ({sum(y)} ASD + {len(y)-sum(y)} TD, age <{AGE_MAX})")
