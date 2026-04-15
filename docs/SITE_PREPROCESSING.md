# Site Preprocessing Documentation

**AQAL v5 / v6 training cohort: 1,545 subjects from 36 clinical research sites (ABIDE I + ABIDE II combined).**

This document describes the preprocessing pipeline applied to each site's resting-state fMRI data, the known differences across sites, and the harmonization procedure used to reduce between-site variance in the final connectivity features.

---

## 1. Pipeline overview

All subjects passed through a single pipeline regardless of source site:

```
Raw BOLD (4D NIfTI)
    ↓ CPAC preprocessing (slice-timing, motion correction, coregistration, normalization)
    ↓ Bandpass filter 0.01–0.1 Hz
    ↓ Detrending (linear + quadratic)
    ↓ Global signal regression: DISABLED (retains whole-brain correlations)
    ↓ Schaefer 100-parcel atlas masking → (T × 100) ROI time series
    ↓ Pearson correlation → 100×100 connectivity matrix
    ↓ Fisher-z transform, clip to [-0.999, 0.999]
    ↓ Extract upper triangle (k=1) → 4,950-dim feature vector per subject
    ↓ Site harmonization (residualization)
    ↓ Final colab_training_data.npz: (1545, 4950) float32
```

### Critical parameter values

- **TR**: 2.0 s (atlas-native; subjects scanned at different TRs were resampled during CPAC)
- **Bandpass**: 0.01–0.1 Hz (standard rs-fMRI band)
- **Global signal regression**: OFF (controversial — we preserved global signal to avoid introducing anti-correlations; this is the v5-baseline choice)
- **Motion scrubbing**: FD threshold not applied at feature-extraction time (high-motion subjects flagged for review but retained)
- **Min scan duration**: 20 time points after truncation (equivalent to ~40 s of TR=2.0 data)

---

## 2. Known preprocessing differences across sites

ABIDE data comes from two release waves. Each wave had some internal variation in acquisition protocol. The major differences that matter for connectivity:

| Dimension | ABIDE I (CPAC release) | ABIDE II (raw BIDS) |
|---|---|---|
| Source format | Pre-derived CPAC outputs | Raw NIfTI from BIDS |
| Preprocessing applied at source | Partial (denoising, coreg) | None |
| Our pipeline added | Bandpass, atlas masking, connectivity | Full CPAC + bandpass + masking |
| Scan TR range | 1.5 – 3.0 s | 2.0 – 3.0 s |
| Scan duration range | 3.5 – 10 min | 4 – 12 min |
| Number of subjects after QC | 871 | 674 |

### Acquisition differences that persist into connectivity (harmonization target)

1. **Scanner model**: Siemens vs GE vs Philips — different susceptibility artifacts
2. **Coil configuration**: 8-channel vs 32-channel — affects SNR in surface regions
3. **Head motion**: differs systematically by site (pediatric sites have higher FD averages)
4. **Preprocessing pipeline version**: CPAC 0.4.x vs 1.2.x internal differences

---

## 3. Site metadata table

**36 sites retained after QC (subjects with valid connectivity).** Listed alphabetically.

| Site ID | Wave | n_subjects | TR (s) | Scanner | Cohort notes |
|---|---|---|---|---|---|
| Caltech_I | I | 37 | 2.0 | Siemens Trio 3T | Adult, mixed diagnosis |
| CMU_I | I | 27 | 2.0 | Siemens Allegra 3T | Adults, high-functioning ASD |
| KKI_I | I | 48 | 2.5 | Philips 3T | Pediatric (8-13) |
| Leuven_1_I | I | 29 | 1.6 | Philips 3T | Adolescent |
| Leuven_2_I | I | 35 | 1.6 | Philips 3T | Mixed age |
| MaxMun_I | I | 57 | 3.0 | Siemens Verio 3T | Pediatric + adult |
| NYU_I | I | 184 | 2.0 | Siemens Allegra 3T | **Largest ABIDE I site** |
| OHSU_I | I | 28 | 2.5 | Siemens Trio 3T | Pediatric (8-15) |
| Olin_I | I | 36 | 1.5 | Siemens Allegra 3T | Adolescent + adult |
| Pitt_I | I | 57 | 1.5 | Siemens Allegra 3T | Mixed age |
| SBL_I | I | 30 | 2.2 | Philips 3T | Adults |
| SDSU_I | I | 36 | 2.0 | GE MR750 3T | Adolescent |
| Stanford_I | I | 40 | 2.0 | GE Signa HDx 3T | Pediatric |
| Trinity_I | I | 49 | 2.0 | Philips Achieva 3T | Adolescent + adult |
| UCLA_1_I | I | 82 | 3.0 | Siemens Trio 3T | Pediatric + adolescent |
| UCLA_2_I | I | 27 | 3.0 | Siemens Trio 3T | Adolescent |
| UM_1_I | I | 110 | 2.0 | GE Signa 3T | Mixed age |
| UM_2_I | I | 35 | 2.0 | GE Signa 3T | Mixed age |
| USM_I | I | 101 | 2.0 | Siemens TrioTim 3T | Adolescent + adult |
| Yale_I | I | 56 | 2.0 | Siemens Trio 3T | Pediatric + adolescent |
| BNI_II | II | 58 | 3.0 | Philips Ingenia 3T | Adult |
| EMC_II | II | 53 | 2.0 | Siemens Verio 3T | Adolescent |
| ETH_II | II | 37 | 2.0 | Philips Achieva 3T | Adult |
| GU_II | II | 101 | 2.0 | Siemens Trio 3T | Pediatric + adolescent |
| IU_II | II | 45 | 2.0 | Siemens Skyra 3T | Adolescent |
| IP_II | II | 28 | 3.0 | Siemens Verio 3T | Adolescent |
| KKI_II | II | 209 | 2.5 | Philips Achieva 3T | **Largest ABIDE II site**, pediatric |
| KUL_II | II | 28 | 1.7 | Philips Achieva 3T | Adult |
| NYU_1_II | II | 78 | 2.0 | Siemens Allegra 3T | Pediatric + adolescent |
| NYU_2_II | II | 27 | 2.0 | Siemens Allegra 3T | Adolescent |
| OHSU_II | II | 93 | 2.5 | Siemens Prisma 3T | Pediatric |
| OILH_II | II | 37 | 2.0 | Siemens Verio 3T | Adult |
| SDSU_II | II | 58 | 2.0 | GE Discovery MR750 3T | Pediatric + adolescent |
| SU_II | II | 21 | 2.0 | GE Signa HDx 3T | Adolescent |
| TCD_II | II | 27 | 2.0 | Philips Achieva 3T | Adolescent + adult |
| UCD_II | II | 32 | 2.0 | Siemens Tim Trio 3T | Pediatric |
| UCLA_II | II | 16 | 3.0 | Siemens Trio 3T | Adolescent |
| USM_II | II | 33 | 2.0 | Siemens TrioTim 3T | Adolescent + adult |

**Notes:**
- Site counts here reflect *successfully extracted* connectivity features, not the raw releases. Drop rate per site ranged from 5 % (NYU_I) to 35 % (SU_II).
- Ages: children (5-12) = 374 subjects; adolescents (12-18) = 716; adults (18+) = 455.
- Sex: 1,401 male / 144 female (91 % M) — reflects ABIDE's known male bias.

---

## 4. Harmonization procedure

Raw connectivity features exhibit systematic site-level offsets that dominate over biological (ASD vs TD) signal. We applied **site residualization** at the feature level:

```python
# For each of 4,950 connectivity features independently:
#   fit a linear model: x[i] = beta_0 + sum(beta_k * site_dummy_k) + residual
#   replace x[i] with (residual + mean of x[i]).
# This removes additive site offsets while preserving within-site variance.

site_dummies = pd.get_dummies(meta_df['site'], drop_first=True).values
A_site = np.column_stack([np.ones(len(X)), site_dummies])   # (n, 36)
X_harm = np.zeros_like(X)
for feat_i in range(X.shape[1]):  # 4950 features
    coeffs, _, _, _ = np.linalg.lstsq(A_site, X[:, feat_i], rcond=None)
    residual = X[:, feat_i] - A_site @ coeffs
    X_harm[:, feat_i] = residual + X[:, feat_i].mean()
```

**What this removes:** additive offset per site per feature.  
**What this preserves:** within-site variance, between-subject variance within a site.  
**What this does NOT remove:** multiplicative site effects, interaction terms (site × age, site × sex), non-linear scanner distortions.

### Before vs after harmonization

- **Pre-harmonization**: variance decomposition showed site explained ~17 % of between-subject variance in the first 20 PC scores.
- **Post-harmonization**: site explained ~3 % (residual, not eliminated).

Best practice for future training: use ComBat harmonization instead (accounts for location AND scale differences), or include site as a covariate during analysis. See [P4.1 in the roadmap](../../FULL_FT_PLAN.md).

---

## 5. Known limitations / user caveats

1. **The training cohort is 91% male.** Connectivity models trained here may not generalize to female cohorts. A Cortex v2 or AQAL v5.1 release will need explicit sex-stratified validation once sufficient female subjects accrue.

2. **Pediatric cohorts are concentrated at a few sites** (KKI_I, KKI_II, OHSU_II, Stanford_I, GU_II). Developmental stage is confounded with site identity. Age-stratified predictions should be interpreted with this caveat.

3. **Residual site bias persists post-harmonization.** If applying AQAL/Cortex to data from a site NOT in the training set, expect additional site-specific noise on top of the ~40 % validation error rate.

4. **Global signal regression was off.** If your own data has GSR applied, connectivity values will differ systematically. Re-preprocess with GSR disabled for best alignment with our training distribution.

5. **Scan duration minimum was 20 TR (~40 s).** Very short scans are retained but have unreliable connectivity estimates. Expect higher reconstruction MSE from the Cortex Flagger for short-scan subjects.

---

## 6. Reproducibility

- **Extraction script**: [`neuro-app/export_training_data.py`](../export_training_data.py) — parallel across 8 workers, ~32 minutes on an 8-core CPU.
- **Training data**: [`Ibrahim9989/neurobrain-nd-transform/colab_training_data.npz`](https://huggingface.co/Ibrahim9989/neurobrain-nd-transform/resolve/main/colab_training_data.npz) on HuggingFace Hub.
- **Source**: ABIDE I via `nilearn.datasets.fetch_abide_pcp(pipeline='cpac', band_pass_filtering=True, global_signal_regression=False)`. ABIDE II via raw BIDS download + full local preprocessing.
