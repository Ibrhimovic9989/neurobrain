"""Generate connectivity heatmaps from v5 transform for the website."""
import torch, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
from collections import OrderedDict

# Load v5
t = torch.load(str(Path.home() / "neurodiverse_transform_v5.pt"), map_location="cpu", weights_only=False)
print(f"Loaded v5: {t['n_asd']} ASD, {t['n_td']} TD, {t['sig_fdr']} FDR")

t_stats = t["t_stats"].numpy()
p_fdr = t["p_values_fdr"].numpy()
labels = t["roi_labels"]

# Rebuild 100x100 matrices
n = 100
t_matrix = np.zeros((n, n))
sig_matrix = np.zeros((n, n))
idx = 0
for i in range(n):
    for j in range(i+1, n):
        t_matrix[i,j] = t_stats[idx]
        t_matrix[j,i] = t_stats[idx]
        sig_matrix[i,j] = 1 if p_fdr[idx] < 0.05 else 0
        sig_matrix[j,i] = sig_matrix[i,j]
        idx += 1

# Network grouping
networks = OrderedDict()
for i, l in enumerate(labels):
    parts = l.split("_")
    net = parts[2] if len(parts) >= 3 else "Other"
    networks.setdefault(net, []).append(i)

boundaries = []
pos = 0
net_centers = []
net_names = []
for net, indices in networks.items():
    boundaries.append(pos)
    net_centers.append(pos + len(indices)/2)
    net_names.append(net)
    pos += len(indices)

masked_t = np.where(sig_matrix > 0, t_matrix, 0)

# === HEATMAP (dark theme) ===
cmap_dark = LinearSegmentedColormap.from_list("dark_rdbu",
    ["#4d7cff", "#1a2a5a", "#050507", "#5a1a1a", "#ff6b6b"])

fig, ax = plt.subplots(figsize=(14, 12), facecolor="#050507")
ax.set_facecolor("#0c0c12")

im = ax.imshow(masked_t, cmap=cmap_dark, vmin=-5, vmax=5, aspect="equal")
ax.set_title("FDR-Significant Connectivity Differences (ASD vs TD)\n1,002 connections | 1,545 subjects | 36 sites",
             fontsize=14, pad=15, color="#d4d4d8")

cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label("t-statistic (blue = TD > ASD, red = ASD > TD)", color="#71717a", fontsize=10)
cbar.ax.yaxis.set_tick_params(color="#71717a")
plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="#71717a")

for b in boundaries[1:]:
    ax.axhline(b-0.5, color="#7c6aff", linewidth=0.3, alpha=0.4)
    ax.axvline(b-0.5, color="#7c6aff", linewidth=0.3, alpha=0.4)

ax.set_xticks(net_centers)
ax.set_xticklabels(net_names, rotation=45, ha="right", fontsize=9, color="#d4d4d8")
ax.set_yticks(net_centers)
ax.set_yticklabels(net_names, fontsize=9, color="#d4d4d8")
ax.tick_params(colors="#71717a")

fig.tight_layout()
fig.savefig("/tmp/connectivity_heatmap.png", dpi=150, bbox_inches="tight", facecolor="#050507")
print("Saved connectivity_heatmap.png")

# === NETWORK BAR CHART ===
net_diffs = {}
idx = 0
for i in range(n):
    for j in range(i+1, n):
        if sig_matrix[i,j] > 0:
            net_i = labels[i].split("_")[2] if len(labels[i].split("_")) >= 3 else "Other"
            net_j = labels[j].split("_")[2] if len(labels[j].split("_")) >= 3 else "Other"
            net_diffs[net_i] = net_diffs.get(net_i, 0) + 1
            net_diffs[net_j] = net_diffs.get(net_j, 0) + 1
        idx += 1

sorted_nets = sorted(net_diffs.items(), key=lambda x: -x[1])

net_colors = {"Limbic": "#ff6b6b", "Default": "#22c55e", "Vis": "#ef4444",
              "SalVentAttn": "#7c6aff", "DorsAttn": "#f59e0b", "Cont": "#06b6d4", "SomMot": "#ec4899"}

fig2, ax2 = plt.subplots(figsize=(10, 5), facecolor="#050507")
ax2.set_facecolor("#0c0c12")

bars = ax2.barh([n[0] for n in sorted_nets], [n[1] for n in sorted_nets],
               color=[net_colors.get(n[0], "#7c6aff") for n in sorted_nets], height=0.6)
ax2.set_xlabel("FDR-significant connections", color="#71717a", fontsize=11)
ax2.set_title("Most Affected Brain Networks (ASD vs TD)", color="#d4d4d8", fontsize=13, pad=10)
ax2.tick_params(colors="#d4d4d8")
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.spines["bottom"].set_color("#71717a")
ax2.spines["left"].set_color("#71717a")

for bar, (net, count) in zip(bars, sorted_nets):
    ax2.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, str(count),
             va="center", fontsize=9, color="#d4d4d8")

fig2.tight_layout()
fig2.savefig("/tmp/network_bars.png", dpi=150, bbox_inches="tight", facecolor="#050507")
print("Saved network_bars.png")

# === ALL CONNECTIONS (not just FDR) ===
fig3, ax3 = plt.subplots(figsize=(14, 12), facecolor="#050507")
ax3.set_facecolor("#0c0c12")

im3 = ax3.imshow(t_matrix, cmap=cmap_dark, vmin=-5, vmax=5, aspect="equal")
ax3.set_title("All Connectivity Differences (uncorrected)\n4,950 connections tested",
              fontsize=14, pad=15, color="#d4d4d8")

cbar3 = plt.colorbar(im3, ax=ax3, shrink=0.8)
cbar3.set_label("t-statistic", color="#71717a", fontsize=10)
cbar3.ax.yaxis.set_tick_params(color="#71717a")
plt.setp(plt.getp(cbar3.ax.axes, "yticklabels"), color="#71717a")

for b in boundaries[1:]:
    ax3.axhline(b-0.5, color="#7c6aff", linewidth=0.3, alpha=0.4)
    ax3.axvline(b-0.5, color="#7c6aff", linewidth=0.3, alpha=0.4)

ax3.set_xticks(net_centers)
ax3.set_xticklabels(net_names, rotation=45, ha="right", fontsize=9, color="#d4d4d8")
ax3.set_yticks(net_centers)
ax3.set_yticklabels(net_names, fontsize=9, color="#d4d4d8")
ax3.tick_params(colors="#71717a")

fig3.tight_layout()
fig3.savefig("/tmp/connectivity_all.png", dpi=150, bbox_inches="tight", facecolor="#050507")
print("Saved connectivity_all.png")

print("\nNetwork connection counts:")
for net, count in sorted_nets:
    print(f"  {net}: {count}")
print("\nDone!")
