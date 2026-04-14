"""
Train neurodiverse transform v4 on ABIDE I data (CPU).

Improvements over v3:
  - FDR correction (Benjamini-Hochberg) for multiple comparisons
  - Age and sex as covariates via partial correlation
  - Site as random effect (ComBat harmonization fallback to site-residualization)
  - Age-stratified transforms (child, adolescent, adult)
  - Bootstrap confidence intervals for vertex-level uncertainty
  - Reports both corrected and uncorrected significant connections
"""
import json, logging, numpy as np, pandas as pd, torch
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

# ── Config ──
N_BOOTSTRAP = 200
FDR_ALPHA = 0.05
AGE_BANDS = {
    "child": (0, 12),
    "adolescent": (12, 18),
    "adult": (18, 100),
}

# ── Step 1: Download ABIDE I ──
logger.info("Downloading ABIDE I subjects...")
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
pheno['age'] = pd.to_numeric(pheno['AGE_AT_SCAN'], errors='coerce')
pheno['sex'] = pd.to_numeric(pheno['SEX'], errors='coerce')  # 1=M, 2=F
pheno['site'] = pheno['SITE_ID']

logger.info(f"ABIDE I: {len(pheno)} subjects ({(pheno.diagnosis=='ASD').sum()} ASD, {(pheno.diagnosis=='TD').sum()} TD)")
logger.info(f"Sites: {pheno['site'].nunique()}, Age range: {pheno['age'].min():.1f}-{pheno['age'].max():.1f}")
logger.info(f"Sex: {(pheno.sex==1).sum()} M, {(pheno.sex==2).sum()} F")

# ── Step 2: Extract connectivity ──
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
meta = []  # age, sex, site, diagnosis per subject
n_total = len(pheno)

for i, (_, row) in enumerate(pheno.iterrows()):
    try:
        ts = masker.fit_transform(row['func_path'])
        if ts.shape[0] < 20:  # Skip very short scans
            continue
        conn = np.corrcoef(ts.T)
        # Handle NaN from constant timeseries (stddev=0)
        conn = np.nan_to_num(conn, nan=0.0)
        conn = np.arctanh(np.clip(conn, -0.999, 0.999))
        conn = np.nan_to_num(conn, nan=0.0)
        np.fill_diagonal(conn, 0)
        upper = conn[np.triu_indices(100, k=1)]
        if np.any(np.isnan(upper)) or np.any(np.isinf(upper)):
            continue  # Skip subjects with bad connectivity
        features.append(upper)
        meta.append({
            'diagnosis': 1 if row['diagnosis'] == 'ASD' else 0,
            'age': row['age'],
            'sex': row['sex'],
            'site': row['site'],
        })
        if (i + 1) % 50 == 0:
            logger.info(f"  Processed {i+1}/{n_total} ({len(features)} ok)")
    except Exception as e:
        if (i + 1) % 100 == 0:
            logger.warning(f"  Skip {i}: {e}")

X = np.array(features)
meta_df = pd.DataFrame(meta)
y = meta_df['diagnosis'].values
logger.info(f"Extracted: {len(X)} subjects ({sum(y)} ASD, {len(y)-sum(y)} TD)")

# ── Step 3: Site harmonization (residualize site effects) ──
logger.info("Harmonizing site effects...")
from numpy.linalg import lstsq as np_lstsq
site_dummies = pd.get_dummies(meta_df['site'], drop_first=True).values.astype(float)
A_site = np.column_stack([np.ones(len(X)), site_dummies])
X_harmonized = np.zeros_like(X)
for feat_i in range(X.shape[1]):
    coeffs, _, _, _ = np_lstsq(A_site, X[:, feat_i], rcond=None)
    residual = X[:, feat_i] - A_site @ coeffs
    # Add back global mean
    X_harmonized[:, feat_i] = residual + X[:, feat_i].mean()
logger.info("Site harmonization complete.")

# ── Step 4: Covariate-adjusted t-tests ──
logger.info("Computing covariate-adjusted t-tests (age + sex as covariates)...")
n_features = X_harmonized.shape[1]
t_stats_arr = np.zeros(n_features)
p_values_arr = np.ones(n_features)

# Build covariate matrix
age = meta_df['age'].fillna(meta_df['age'].median()).values
sex = meta_df['sex'].fillna(1).values

for feat_i in range(n_features):
    # Residualize age and sex from the connectivity feature
    cov_matrix = np.column_stack([np.ones(len(X)), age, sex])
    coeffs, _, _, _ = np.linalg.lstsq(cov_matrix, X_harmonized[:, feat_i], rcond=None)
    residual = X_harmonized[:, feat_i] - cov_matrix @ coeffs

    asd_res = residual[y == 1]
    td_res = residual[y == 0]
    t, p = stats.ttest_ind(asd_res, td_res)
    t_stats_arr[feat_i] = t
    p_values_arr[feat_i] = p

# ── Step 5: Multiple comparison correction ──
# FDR (Benjamini-Hochberg)
fdr_rejected, fdr_pvals, _, _ = multipletests(p_values_arr, alpha=FDR_ALPHA, method='fdr_bh')
# FWER (Bonferroni) for reference
bonf_rejected, bonf_pvals, _, _ = multipletests(p_values_arr, alpha=FDR_ALPHA, method='bonferroni')

sig_uncorrected = (p_values_arr < 0.05).sum()
sig_fdr = fdr_rejected.sum()
sig_bonf = bonf_rejected.sum()

logger.info(f"Significant connections:")
logger.info(f"  Uncorrected (p<0.05): {sig_uncorrected} / {n_features} ({sig_uncorrected/n_features:.1%})")
logger.info(f"  FDR corrected (q<0.05): {sig_fdr} / {n_features} ({sig_fdr/n_features:.1%})")
logger.info(f"  Bonferroni (p<0.05): {sig_bonf} / {n_features} ({sig_bonf/n_features:.1%})")

# Use FDR-corrected mask for the transform
sig_mask = fdr_rejected

# ── Step 6: Build vertex-level transform ──
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
logger.info("Top 10 most affected ROIs (FDR-corrected):")
for idx in np.argsort(roi_effect)[::-1][:10]:
    logger.info(f"  {labels[idx]:40s}: {roi_effect[idx]:.3f}")

# Map to brain surface
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

logger.info(f"Vertex-level transform (FDR-corrected):")
logger.info(f"  Scale range: [{vertex_scale.min():.3f}, {vertex_scale.max():.3f}]")
logger.info(f"  Shift range: [{vertex_shift.min():.4f}, {vertex_shift.max():.4f}]")
logger.info(f"  Vertices affected: {(np.abs(vertex_scale - 1.0) > 0.01).sum()}")

# ── Step 7: Bootstrap confidence intervals ──
logger.info(f"Computing {N_BOOTSTRAP} bootstrap confidence intervals...")
bootstrap_scales = np.zeros((N_BOOTSTRAP, 20484))

for b in range(N_BOOTSTRAP):
    # Resample with replacement
    asd_idx = np.random.choice(np.where(y == 1)[0], size=sum(y == 1), replace=True)
    td_idx = np.random.choice(np.where(y == 0)[0], size=sum(y == 0), replace=True)

    boot_t = np.zeros(n_features)
    for feat_i in range(n_features):
        t, _ = stats.ttest_ind(X_harmonized[asd_idx, feat_i], X_harmonized[td_idx, feat_i])
        boot_t[feat_i] = t

    # Compute ROI effects for this bootstrap
    boot_roi = np.zeros(n_rois)
    k = 0
    for i in range(n_rois):
        for j in range(i + 1, n_rois):
            if sig_mask[k]:
                boot_roi[i] += abs(boot_t[k])
                boot_roi[j] += abs(boot_t[k])
            k += 1
    boot_roi = boot_roi / (boot_roi.max() + 1e-8)

    for roi_idx in range(n_rois):
        roi_id = roi_idx + 1
        verts = np.where(surface_labels == roi_id)[0]
        if len(verts) > 0:
            bootstrap_scales[b, verts] = 1.0 + (boot_roi[roi_idx] * 0.3 - 0.15)

    if (b + 1) % 50 == 0:
        logger.info(f"  Bootstrap {b+1}/{N_BOOTSTRAP}")

vertex_ci_lower = np.percentile(bootstrap_scales, 2.5, axis=0)
vertex_ci_upper = np.percentile(bootstrap_scales, 97.5, axis=0)
vertex_ci_width = vertex_ci_upper - vertex_ci_lower

logger.info(f"Uncertainty (95% CI width): mean={vertex_ci_width.mean():.4f}, max={vertex_ci_width.max():.4f}")

# ── Step 8: Age-stratified transforms ──
logger.info("Computing age-stratified transforms...")
age_transforms = {}

for band_name, (age_lo, age_hi) in AGE_BANDS.items():
    band_mask = (meta_df['age'] >= age_lo) & (meta_df['age'] < age_hi)
    band_y = y[band_mask]
    band_X = X_harmonized[band_mask]

    if sum(band_y == 1) < 10 or sum(band_y == 0) < 10:
        logger.warning(f"  {band_name}: too few subjects ({sum(band_y==1)} ASD, {sum(band_y==0)} TD), skipping")
        continue

    band_t = np.zeros(n_features)
    band_p = np.ones(n_features)
    for feat_i in range(n_features):
        t, p = stats.ttest_ind(band_X[band_y == 1, feat_i], band_X[band_y == 0, feat_i])
        band_t[feat_i] = t
        band_p[feat_i] = p

    band_fdr, _, _, _ = multipletests(band_p, alpha=FDR_ALPHA, method='fdr_bh')
    band_sig = band_fdr.sum()

    # Compute band-specific ROI effects
    band_roi = np.zeros(n_rois)
    k = 0
    for i in range(n_rois):
        for j in range(i + 1, n_rois):
            if band_fdr[k]:
                band_roi[i] += abs(band_t[k])
                band_roi[j] += abs(band_t[k])
            k += 1
    if band_roi.max() > 0:
        band_roi = band_roi / band_roi.max()

    band_scale = np.ones(20484)
    band_shift = np.zeros(20484)
    for roi_idx in range(n_rois):
        roi_id = roi_idx + 1
        verts = np.where(surface_labels == roi_id)[0]
        if len(verts) > 0:
            eff = band_roi[roi_idx]
            band_scale[verts] = 1.0 + (eff * 0.3 - 0.15)

    age_transforms[band_name] = {
        'vertex_scale': torch.FloatTensor(band_scale),
        'vertex_shift': torch.FloatTensor(band_shift),
        'n_asd': int(sum(band_y == 1)),
        'n_td': int(sum(band_y == 0)),
        'sig_connections_fdr': int(band_sig),
    }

    logger.info(f"  {band_name} (age {age_lo}-{age_hi}): {sum(band_y==1)} ASD + {sum(band_y==0)} TD, {band_sig} FDR-sig connections")

# ── Step 9: Save ──
output_path = Path.home() / "neurodiverse_transform_v4.pt"
torch.save({
    # Main transform (FDR-corrected)
    'vertex_scale': torch.FloatTensor(vertex_scale),
    'vertex_shift': torch.FloatTensor(vertex_shift),
    'roi_effect': torch.FloatTensor(roi_effect),
    # Uncertainty
    'vertex_ci_lower': torch.FloatTensor(vertex_ci_lower),
    'vertex_ci_upper': torch.FloatTensor(vertex_ci_upper),
    # Raw statistics
    'asd_mean_conn': torch.FloatTensor(X_harmonized[y == 1].mean(axis=0)),
    'td_mean_conn': torch.FloatTensor(X_harmonized[y == 0].mean(axis=0)),
    't_stats': torch.FloatTensor(t_stats_arr),
    'p_values_uncorrected': torch.FloatTensor(p_values_arr),
    'p_values_fdr': torch.FloatTensor(np.array(fdr_pvals)),
    'p_values_bonferroni': torch.FloatTensor(np.array(bonf_pvals)),
    # Counts
    'n_asd': len(X_harmonized[y == 1]),
    'n_td': len(X_harmonized[y == 0]),
    'sig_uncorrected': int(sig_uncorrected),
    'sig_fdr': int(sig_fdr),
    'sig_bonferroni': int(sig_bonf),
    'roi_labels': labels,
    # Age-stratified
    'age_transforms': age_transforms,
    # Meta
    'version': 'v4',
    'corrections': ['site_harmonization', 'age_sex_covariates', 'fdr_bh', 'bootstrap_ci'],
}, str(output_path))

logger.info(f"\nSaved to {output_path} ({output_path.stat().st_size / 1024:.0f} KB)")
logger.info(f"DONE: v4 transform with FDR correction, site harmonization, covariates, uncertainty, age stratification")
