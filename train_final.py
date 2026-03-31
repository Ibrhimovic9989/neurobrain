"""Final training: ABIDE I + ds000228 Pixar (skip ds002345)."""
import numpy as np, torch, logging, pandas as pd
from pathlib import Path
from scipy import stats
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from nilearn import datasets as nd, maskers
atlas = nd.fetch_atlas_schaefer_2018(n_rois=100)
masker = maskers.NiftiLabelsMasker(labels_img=atlas.maps, standardize="zscore_sample", detrend=True, low_pass=0.1, high_pass=0.01, t_r=2.0)
feats, labs = [], []

# ABIDE I
from nilearn.datasets import fetch_abide_pcp
ab = fetch_abide_pcp(data_dir=str(Path.home() / "data/abide_full"), pipeline="cpac", band_pass_filtering=True, global_signal_regression=False, derivatives=["func_preproc"], n_subjects=None)
ph = pd.DataFrame(ab.phenotypic)
ph["fp"] = [str(p) for p in ab.func_preproc]
ph["dx"] = ph["DX_GROUP"].map({1: "ASD", 2: "TD"})
for i, (_, r) in enumerate(ph.iterrows()):
    try:
        ts = masker.fit_transform(r["fp"])
        c = np.corrcoef(ts.T)
        c = np.arctanh(np.clip(c, -0.999, 0.999))
        np.fill_diagonal(c, 0)
        feats.append(c[np.triu_indices(100, k=1)])
        labs.append(1 if r["dx"] == "ASD" else 0)
        if (i + 1) % 100 == 0:
            logger.info(f"ABIDE {i+1}/{len(ph)}")
    except:
        pass
logger.info(f"ABIDE done: {len(feats)}")

# ds000228 Pixar
ds = Path.home() / "data/ds000228"
pf = ds / "participants.tsv"
if pf.exists():
    pts = pd.read_csv(pf, sep="\t")
    for _, r in pts.iterrows():
        sub = r.get("participant_id", "")
        dx = str(r.get("diagnosis", r.get("group", "")))
        asd = "asd" in dx.lower() or "autism" in dx.lower()
        bfs = list(ds.glob(f"{sub}/**/func/*bold.nii.gz")) + list(ds.glob(f"{sub}/func/*bold.nii.gz"))
        for bf in bfs[:1]:
            try:
                ts = masker.fit_transform(str(bf))
                c = np.corrcoef(ts.T)
                c = np.arctanh(np.clip(c, -0.999, 0.999))
                np.fill_diagonal(c, 0)
                feats.append(c[np.triu_indices(100, k=1)])
                labs.append(1 if asd else 0)
            except:
                pass
    logger.info(f"ds000228 done. Total: {len(feats)}")

# Compute
X = np.array(feats)
y = np.array(labs)
logger.info(f"COMBINED: {len(X)} ({sum(y)} ASD, {len(y)-sum(y)} TD)")
ac, tc = X[y == 1], X[y == 0]
ta, pa = np.zeros(X.shape[1]), np.ones(X.shape[1])
for i in range(X.shape[1]):
    ta[i], pa[i] = stats.ttest_ind(ac[:, i], tc[:, i])
sig = pa < 0.05
logger.info(f"Significant: {sig.sum()}/{len(sig)} ({sig.mean():.1%})")

re = np.zeros(100)
idx = 0
for i in range(100):
    for j in range(i + 1, 100):
        if sig[idx]:
            re[i] += abs(ta[idx])
            re[j] += abs(ta[idx])
        idx += 1
re /= (re.max() + 1e-8)
ls = [l.decode() if isinstance(l, bytes) else str(l) for l in atlas.labels[1:]]
logger.info("Top 5:")
for i in np.argsort(re)[::-1][:5]:
    logger.info(f"  {ls[i]:40s}: {re[i]:.3f}")

from nilearn.surface import vol_to_surf
from nilearn import datasets as nld
fs = nld.fetch_surf_fsaverage("fsaverage5")
sl = np.concatenate([vol_to_surf(atlas.maps, fs["pial_left"]), vol_to_surf(atlas.maps, fs["pial_right"])]).astype(int)
vs, vsh = np.ones(20484), np.zeros(20484)
for ri in range(100):
    vv = np.where(sl == ri + 1)[0]
    if len(vv) > 0:
        e = re[ri]
        vs[vv] = 1.0 + (e * 0.3 - 0.15)
        rt, cnt, k = 0, 0, 0
        for ii in range(100):
            for jj in range(ii + 1, 100):
                if (ii == ri or jj == ri) and sig[k]:
                    rt += ta[k]
                    cnt += 1
                k += 1
        if cnt:
            rt /= cnt
        vsh[vv] = np.tanh(rt * 0.1) * e * 0.15

out = Path.home() / "neurodiverse_transform_v3.pt"
torch.save({
    "vertex_scale": torch.FloatTensor(vs),
    "vertex_shift": torch.FloatTensor(vsh),
    "roi_effect": torch.FloatTensor(re),
    "asd_mean_conn": torch.FloatTensor(ac.mean(0)),
    "td_mean_conn": torch.FloatTensor(tc.mean(0)),
    "t_stats": torch.FloatTensor(ta),
    "p_values": torch.FloatTensor(pa),
    "n_asd": len(ac),
    "n_td": len(tc),
    "roi_labels": ls,
}, str(out))
logger.info(f"Saved: {out}")

from huggingface_hub import HfApi, login
login(token="HF_TOKEN_HERE")
HfApi().upload_file(path_or_fileobj=str(out), path_in_repo="neurodiverse_transform_v3.pt", repo_id="Ibrahim9989/neurobrain-nd-transform")
logger.info("Uploaded to HuggingFace!")
logger.info(f"DONE: {len(ac)} ASD + {len(tc)} TD = {len(X)}")
