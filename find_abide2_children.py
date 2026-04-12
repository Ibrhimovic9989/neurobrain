"""Find ABIDE II children under 12 from raw BIDS participants.tsv files."""
import csv, os, json

children = []
pheno_dir = "/tmp/abide2_pheno"

for f in os.listdir(pheno_dir):
    if not f.endswith(".tsv"):
        continue
    site = f.replace(".tsv", "")
    try:
        with open(os.path.join(pheno_dir, f), newline="", encoding="utf-8", errors="replace") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                try:
                    # Column has trailing space in some files
                    age_str = (row.get("age_at_scan", "") or row.get("age_at_scan ", "") or "99").strip()
                    if age_str in ("n/a", "", "-9999"):
                        continue
                    age = float(age_str)
                    dx_str = row.get("dx_group", "0").strip()
                    if dx_str in ("n/a", "", "-9999"):
                        continue
                    dx = int(float(dx_str))
                    sub_id = row.get("participant_id", "").strip()
                    if age < 12 and dx in (1, 2) and sub_id:
                        children.append({
                            "sub_id": sub_id,
                            "age": age,
                            "dx": dx,
                            "site": site,
                        })
                except (ValueError, TypeError):
                    pass
    except Exception as e:
        print(f"Error reading {f}: {e}")

asd = [c for c in children if c["dx"] == 1]
td = [c for c in children if c["dx"] == 2]
print(f"ABIDE II children <12 with diagnosis: {len(children)}")
print(f"  ASD: {len(asd)}, TD: {len(td)}")

# Save download list
with open("/tmp/abide2_children_download.json", "w") as f:
    json.dump(children, f)

# Per-site breakdown
from collections import Counter
sites = Counter(c["site"] for c in children)
for s, n in sites.most_common():
    print(f"  {s}: {n}")
