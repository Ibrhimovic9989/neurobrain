import json, logging, numpy as np, pandas as pd
from pathlib import Path
logging.basicConfig(level=logging.INFO)

pheno = pd.read_csv(Path.home() / "data/abide/abide1_phenotypic.csv")
print(f"Subjects: {len(pheno)}")
print(pheno.groupby("diagnosis").size())

from tribev2.neurodiverse.resting_state import RestingStateAnalyzer
analyzer = RestingStateAnalyzer(n_parcels=100)
conn = analyzer.batch_project_and_connect(pheno, max_subjects=10)
n_asd = len(conn["ASD"])
n_td = len(conn["TD"])
print(f"ASD: {n_asd}, TD: {n_td}")

if n_asd >= 2 and n_td >= 2:
    results = analyzer.compare_groups(conn["ASD"], conn["TD"])

    from nilearn import datasets
    atlas = datasets.fetch_atlas_schaefer_2018(n_rois=100)
    labels = [l.decode() if isinstance(l, bytes) else str(l) for l in atlas.labels]
    diff = results["difference"]
    networks = {}
    for i, label in enumerate(labels[1:]):
        for net in ["Vis", "SomMot", "DorsAttn", "SalVentAttn", "Limbic", "Cont", "Default"]:
            if net in label:
                networks.setdefault(net, []).append(i)
                break
    network_diffs = {}
    for net, idx in networks.items():
        network_diffs[net] = float(np.mean([np.abs(diff[i]).mean() for i in idx]))
    network_diffs = dict(sorted(network_diffs.items(), key=lambda x: -x[1]))

    out = {
        "asd_subjects": n_asd,
        "td_subjects": n_td,
        "network_differences": network_diffs,
        "asd_mean": results["asd_mean"].tolist(),
        "td_mean": results["td_mean"].tolist(),
        "difference": results["difference"].tolist(),
    }
    cache = Path.home() / "neurobrain_connectivity_cache.json"
    cache.write_text(json.dumps(out))
    print(f"Cached to {cache} ({cache.stat().st_size / 1024:.0f} KB)")
    print("Network differences:", network_diffs)
else:
    print("Not enough subjects per group")
