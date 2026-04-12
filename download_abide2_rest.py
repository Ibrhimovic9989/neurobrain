"""Download raw resting-state fMRI for ABIDE II subjects aged 12+."""
import json, os, subprocess

os.environ["PATH"] = os.environ.get("PATH", "") + ":/home/azureuser/.local/bin"

with open("/tmp/abide2_nonchildren_download.json") as f:
    subjects = json.load(f)

out_dir = "/home/azureuser/data/abide2_rest"
os.makedirs(out_dir, exist_ok=True)

done = 0
failed = 0
skipped = 0

for i, subj in enumerate(subjects):
    site = subj["site"]
    sub_id = subj["sub_id"]
    sub_dir = f"sub-{sub_id}"
    local_dir = os.path.join(out_dir, sub_dir)
    os.makedirs(local_dir, exist_ok=True)

    existing = [f for f in os.listdir(local_dir) if f.endswith(".nii.gz")]
    if existing:
        skipped += 1
        continue

    # Try ses-1/func first, then func directly
    for func_path in [f"ses-1/func/", "func/"]:
        s3_func = f"s3://fcp-indi/data/Projects/ABIDE2/RawData/{site}/{sub_dir}/{func_path}"
        dl = subprocess.run(
            ["aws", "s3", "cp", s3_func, local_dir + "/", "--recursive",
             "--no-sign-request", "--exclude", "*", "--include", "*task-rest*bold.nii.gz"],
            capture_output=True, text=True
        )
        downloaded = [f for f in os.listdir(local_dir) if f.endswith(".nii.gz")]
        if downloaded:
            done += 1
            break
    else:
        failed += 1

    if (i + 1) % 20 == 0:
        print(f"Progress: {done} downloaded, {failed} failed, {skipped} skipped ({i+1}/{len(subjects)})")

print(f"DONE: {done} downloaded, {failed} failed, {skipped} skipped")
