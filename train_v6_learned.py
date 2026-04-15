"""
Train v6 learned ND transform on Azure CPU VM (runs in ~5-10 min).

Same logic as aqal_finetune_colab.ipynb but as a standalone script.
Produces neurodiverse_transform_v6.pt (drop-in replacement for v5).
"""
import logging, os, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from pathlib import Path
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
logger.info(f'Device: {device}')

# ── Load data ──
data_path = Path.home() / "colab_training_data.npz"
if not data_path.exists():
    raise FileNotFoundError(f"Run export_training_data.py first to generate {data_path}")

data = np.load(str(data_path), allow_pickle=True)
X = data['X']; y = data['y']; age = data['age']; sex = data['sex']; site_idx = data['site_idx']
logger.info(f"Loaded: {X.shape[0]} subjects ({int(y.sum())} ASD, {int((1-y).sum())} TD)")

# ── Load v5 baseline ──
from huggingface_hub import hf_hub_download
v5_path = hf_hub_download('Ibrahim9989/neurobrain-nd-transform', 'neurodiverse_transform_v5.pt')
v5 = torch.load(v5_path, map_location='cpu', weights_only=False)
v5_scale = v5['vertex_scale'].numpy()
v5_shift = v5['vertex_shift'].numpy()
logger.info(f"v5 loaded: scale [{v5_scale.min():.3f}, {v5_scale.max():.3f}]")

# ── Surface mapping ──
from nilearn.surface import vol_to_surf
from nilearn import datasets as ni_datasets
atlas = ni_datasets.fetch_atlas_schaefer_2018(n_rois=100)
fsaverage = ni_datasets.fetch_surf_fsaverage('fsaverage5')
left_proj = vol_to_surf(atlas.maps, fsaverage['pial_left'])
right_proj = vol_to_surf(atlas.maps, fsaverage['pial_right'])
surface_labels = np.concatenate([left_proj, right_proj]).astype(int)

# ── Classifier ──
class ASDClassifier(nn.Module):
    def __init__(self, input_dim=4950, hidden=256, dropout=0.5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden, hidden // 2), nn.LayerNorm(hidden // 2), nn.GELU(), nn.Dropout(dropout),
            nn.Linear(hidden // 2, 1),
        )
    def forward(self, x): return self.net(x).squeeze(-1)

# ── Residual Correction ──
class ResidualCorrection(nn.Module):
    def __init__(self, n_rois=100, cond_dim=3, hidden=256):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(cond_dim, hidden), nn.LayerNorm(hidden), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(hidden, hidden), nn.LayerNorm(hidden), nn.GELU(),
        )
        self.scale_head = nn.Linear(hidden, n_rois)
        self.shift_head = nn.Linear(hidden, n_rois)
        for head in (self.scale_head, self.shift_head):
            nn.init.zeros_(head.weight); nn.init.zeros_(head.bias)
    def forward(self, cond):
        h = self.encoder(cond)
        return self.scale_head(h) * 0.05, self.shift_head(h) * 0.01

# ── Train classifier ──
logger.info("Training ASD classifier...")
X_train, X_val, y_train, y_val, age_tr, age_v, sex_tr, sex_v = train_test_split(
    X, y, age, sex, test_size=0.2, stratify=y, random_state=42
)
clf = ASDClassifier().to(device)
opt = torch.optim.AdamW(clf.parameters(), lr=1e-3, weight_decay=1e-3)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=50)
loader = DataLoader(TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train)),
                    batch_size=32, shuffle=True)
X_val_t = torch.FloatTensor(X_val).to(device); y_val_t = torch.FloatTensor(y_val).to(device)

best_acc = 0; best_state = None
for epoch in range(50):
    clf.train()
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        opt.zero_grad()
        loss = F.binary_cross_entropy_with_logits(clf(xb), yb)
        loss.backward(); opt.step()
    sched.step()
    clf.eval()
    with torch.no_grad():
        acc = ((torch.sigmoid(clf(X_val_t)) > 0.5).float() == y_val_t).float().mean().item()
    if acc > best_acc: best_acc = acc; best_state = {k: v.cpu().clone() for k, v in clf.state_dict().items()}
    if (epoch + 1) % 10 == 0: logger.info(f"  Epoch {epoch+1}/50: val_acc={acc:.3f}")
clf.load_state_dict(best_state)
logger.info(f"Best classifier val_acc: {best_acc:.3f}")

# ── Train residual correction ──
logger.info("Training residual correction...")
pair_to_roi = np.array([(i, j) for i in range(100) for j in range(i+1, 100)])
pair_idx_t = torch.LongTensor(pair_to_roi).to(device)

asd_mean = X[y == 1].mean(axis=0)
target = torch.FloatTensor(asd_mean).to(device)

def build_cond(age_arr, sex_arr):
    return np.stack([(age_arr - 18) / 20, (sex_arr == 1).astype(np.float32), (sex_arr == 2).astype(np.float32)], axis=-1).astype(np.float32)

cond = build_cond(age, sex)
td_mask = y == 0
td_X = torch.FloatTensor(X[td_mask]); td_cond = torch.FloatTensor(cond[td_mask])

model = ResidualCorrection().to(device)
opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=60)
loader = DataLoader(TensorDataset(td_X, td_cond), batch_size=64, shuffle=True)

for epoch in range(60):
    model.train()
    total = 0
    for xb, cb in loader:
        xb, cb = xb.to(device), cb.to(device)
        opt.zero_grad()
        ds, sh = model(cb)
        s_i = ds[:, pair_idx_t[:, 0]]; s_j = ds[:, pair_idx_t[:, 1]]
        avg_scale = 1.0 + (s_i + s_j) / 2
        b_i = sh[:, pair_idx_t[:, 0]]; b_j = sh[:, pair_idx_t[:, 1]]
        avg_shift = (b_i + b_j) / 2
        corrected = xb * avg_scale + avg_shift
        loss = F.mse_loss(corrected.mean(dim=0), target) + F.mse_loss(corrected, xb) * 0.05
        loss.backward(); opt.step()
        total += loss.item()
    sched.step()
    if (epoch + 1) % 10 == 0: logger.info(f"  Epoch {epoch+1}/60: loss={total/len(loader):.6f}")

# ── Build vertex-level v6 ──
logger.info("Building vertex-level v6...")
model.eval()
bands = {'child': (0, 12), 'adolescent': (12, 18), 'adult': (18, 100)}
band_transforms = {}
for band_name, (lo, hi) in bands.items():
    band_mask = (age >= lo) & (age < hi)
    if band_mask.sum() < 20: continue
    with torch.no_grad():
        c_t = torch.FloatTensor(cond[band_mask]).to(device)
        ds, sh = model(c_t)
        rs = ds.mean(dim=0).cpu().numpy()
        rh = sh.mean(dim=0).cpu().numpy()
    vs = v5_scale.copy(); vh = v5_shift.copy()
    for roi in range(100):
        verts = np.where(surface_labels == roi + 1)[0]
        if len(verts) > 0:
            vs[verts] += rs[roi]; vh[verts] += rh[roi]
    band_transforms[band_name] = {
        'vertex_scale': torch.FloatTensor(vs), 'vertex_shift': torch.FloatTensor(vh),
        'n_subjects': int(band_mask.sum()),
    }
    logger.info(f"  {band_name}: {int(band_mask.sum())} subjects")

# All-ages
with torch.no_grad():
    ds, sh = model(torch.FloatTensor(cond).to(device))
    rs_all = ds.mean(dim=0).cpu().numpy()
    rh_all = sh.mean(dim=0).cpu().numpy()
vs_final = v5_scale.copy(); vh_final = v5_shift.copy()
for roi in range(100):
    verts = np.where(surface_labels == roi + 1)[0]
    if len(verts) > 0:
        vs_final[verts] += rs_all[roi]; vh_final[verts] += rh_all[roi]

# ── Save ──
out = {
    'vertex_scale': torch.FloatTensor(vs_final), 'vertex_shift': torch.FloatTensor(vh_final),
    'roi_effect': v5['roi_effect'],
    'vertex_ci_lower': v5['vertex_ci_lower'], 'vertex_ci_upper': v5['vertex_ci_upper'],
    't_stats': v5['t_stats'], 'p_values_fdr': v5['p_values_fdr'],
    'n_asd': int(y.sum()), 'n_td': int((1-y).sum()),
    'sig_uncorrected': int(v5.get('sig_uncorrected', 0)),
    'sig_fdr': int(v5.get('sig_fdr', 0)),
    'sig_bonferroni': int(v5.get('sig_bonferroni', 0)),
    'roi_labels': v5['roi_labels'],
    'age_transforms': band_transforms,
    'classifier_state_dict': {k: v.cpu() for k, v in clf.state_dict().items()},
    'learned_model_state': {k: v.cpu() for k, v in model.state_dict().items()},
    'classifier_val_accuracy': best_acc,
    'version': 'v6_learned',
    'corrections': ['site_harmonization', 'age_sex_covariates', 'fdr_bh', 'bootstrap_ci', 'learned_residual'],
    'trained_at': datetime.utcnow().isoformat(),
}
output = Path.home() / "neurodiverse_transform_v6.pt"
torch.save(out, str(output))
logger.info(f"Saved v6 to {output} ({output.stat().st_size / 1024:.0f} KB)")
logger.info(f"DONE. Classifier val_acc={best_acc:.3f}")
