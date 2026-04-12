"""Download raw resting-state fMRI for ABIDE II children under 12."""
import json, os, subprocess

os.environ["PATH"] = os.environ.get("PATH", "") + ":/home/azureuser/.local/bin"

with open("/tmp/abide2_children_download.json") as f:
    children = json.load(f)

out_dir = "/home/azureuser/data/abide2_children"
os.makedirs(out_dir, exist_ok=True)

done = 0
failed = 0
skipped = 0

for i, child in enumerate(children):
    site = child["site"]
    sub_id = child["sub_id"]
    sub_dir = f"sub-{sub_id}"
    local_dir = os.path.join(out_dir, sub_dir)
    os.makedirs(local_dir, exist_ok=True)

    # Skip if already downloaded
    existing = [f for f in os.listdir(local_dir) if f.endswith(".nii.gz")]
    if existing:
        skipped += 1
        continue

    # Use aws s3 sync to download just the func directory
    s3_func = f"s3://fcp-indi/data/Projects/ABIDE2/RawData/{site}/{sub_dir}/ses-1/func/"

    dl = subprocess.run(
        ["aws", "s3", "cp", s3_func, local_dir + "/", "--recursive",
         "--no-sign-request", "--exclude", "*", "--include", "*task-rest*bold.nii.gz"],
        capture_output=True, text=True
    )

    downloaded = [f for f in os.listdir(local_dir) if f.endswith(".nii.gz")]
    if downloaded:
        done += 1
    else:
        # Try without ses-1
        s3_func2 = f"s3://fcp-indi/data/Projects/ABIDE2/RawData/{site}/{sub_dir}/func/"
        dl2 = subprocess.run(
            ["aws", "s3", "cp", s3_func2, local_dir + "/", "--recursive",
             "--no-sign-request", "--exclude", "*", "--include", "*task-rest*bold.nii.gz"],
            capture_output=True, text=True
        )
        downloaded2 = [f for f in os.listdir(local_dir) if f.endswith(".nii.gz")]
        if downloaded2:
            done += 1
        else:
            failed += 1

    if (i + 1) % 20 == 0:
        print(f"Progress: {done} downloaded, {failed} failed, {skipped} skipped ({i+1}/{len(children)})")

print(f"DONE: {done} downloaded, {failed} failed, {skipped} skipped")
