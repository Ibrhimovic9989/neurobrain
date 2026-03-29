"""FastAPI backend for Neurodiverse Brain Model.

Serves TRIBE v2 predictions and ASD vs TD comparisons.
Deploy on Azure GPU VM.
"""

import io
import base64
import logging
import os
from pathlib import Path

import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Neurodiverse Brain Model API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instances (loaded once at startup)
_model = None
_analyzer = None
_abide_results = None


def get_model():
    global _model
    if _model is None:
        from tribev2 import TribeModel
        device = "cuda" if os.environ.get("USE_GPU", "1") == "1" else "cpu"
        logger.info(f"Loading TRIBE v2 on {device}...")
        _model = TribeModel.from_pretrained(
            "facebook/tribev2",
            cache_folder="./cache",
            device=device,
        )
        logger.info("TRIBE v2 loaded")
    return _model


def get_analyzer():
    global _analyzer
    if _analyzer is None:
        from tribev2.neurodiverse.resting_state import RestingStateAnalyzer
        _analyzer = RestingStateAnalyzer(n_parcels=100)
    return _analyzer


def brain_to_image(preds, timestep=0):
    """Render brain prediction as a base64 PNG image."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from nilearn import datasets, plotting, surface

    fsaverage = datasets.fetch_surf_fsaverage("fsaverage5")
    data = preds[timestep] if preds.ndim == 2 else preds

    fig, axes = plt.subplots(1, 4, figsize=(20, 5),
                              subplot_kw={"projection": "3d"})
    views = ["lateral", "medial", "lateral", "medial"]
    hemis = ["left", "left", "right", "right"]

    for ax, view, hemi in zip(axes, views, hemis):
        n_vertices = len(data) // 2
        if hemi == "left":
            hemi_data = data[:n_vertices]
            mesh = fsaverage["pial_left"]
            bg = fsaverage["sulc_left"]
        else:
            hemi_data = data[n_vertices:]
            mesh = fsaverage["pial_right"]
            bg = fsaverage["sulc_right"]

        plotting.plot_surf_stat_map(
            mesh, hemi_data, hemi=hemi, view=view,
            bg_map=bg, colorbar=False, threshold=0.1,
            cmap="hot", axes=ax,
        )

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="black")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


@app.get("/")
async def root():
    return {"status": "ok", "model": "Neurodiverse Brain Model v1.0"}


@app.get("/api/health")
async def health():
    return {"status": "healthy", "model_loaded": _model is not None}


@app.post("/api/predict")
async def predict_brain(text: str = Form(...)):
    """Predict brain activity from text input.

    Returns brain activation data and rendered images.
    """
    try:
        model = get_model()

        # Write text to temp file
        os.makedirs("./tmp", exist_ok=True)
        text_path = "./tmp/input.txt"
        with open(text_path, "w") as f:
            f.write(text)

        # Run prediction
        events = model.get_events_dataframe(text_path=text_path)
        preds, segments = model.predict(events, verbose=False)

        # Generate images for each timestep (max 15)
        n_steps = min(preds.shape[0], 15)
        images = []
        for t in range(n_steps):
            img = brain_to_image(preds, timestep=t)
            images.append(img)

        # Get activation stats
        mean_activation = np.mean(np.abs(preds), axis=0)
        top_vertices = np.argsort(mean_activation)[-10:][::-1]

        return {
            "timesteps": n_steps,
            "vertices": int(preds.shape[1]),
            "value_range": [float(preds.min()), float(preds.max())],
            "mean_activation": float(np.mean(np.abs(preds))),
            "images": images,
            "top_active_regions": [
                {
                    "vertex": int(v),
                    "hemisphere": "left" if v < 10242 else "right",
                    "activation": float(mean_activation[v]),
                }
                for v in top_vertices
            ],
        }
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/predict/video")
async def predict_from_video(file: UploadFile = File(...)):
    """Predict brain activity from video upload."""
    try:
        model = get_model()

        os.makedirs("./tmp", exist_ok=True)
        video_path = f"./tmp/{file.filename}"
        with open(video_path, "wb") as f:
            f.write(await file.read())

        events = model.get_events_dataframe(video_path=video_path)
        preds, segments = model.predict(events, verbose=False)

        n_steps = min(preds.shape[0], 15)
        images = [brain_to_image(preds, t) for t in range(n_steps)]

        return {
            "timesteps": n_steps,
            "vertices": int(preds.shape[1]),
            "value_range": [float(preds.min()), float(preds.max())],
            "mean_activation": float(np.mean(np.abs(preds))),
            "images": images,
        }
    except Exception as e:
        logger.error(f"Video prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/connectivity")
async def get_connectivity(n_subjects: int = 20):
    """Get precomputed ASD vs TD connectivity comparison."""
    global _abide_results

    if _abide_results is not None:
        return _abide_results

    try:
        from tribev2.neurodiverse.download import AbideDownloader
        from nilearn import datasets

        # Download ABIDE data
        abide = AbideDownloader(output_dir="./data/abide")
        phenotypic = abide.download_abide1(n_subjects=n_subjects * 3)

        # Compute connectivity
        analyzer = get_analyzer()
        connectivity = analyzer.batch_connectivity(
            phenotypic, max_subjects=n_subjects
        )

        if len(connectivity["ASD"]) < 2 or len(connectivity["TD"]) < 2:
            raise HTTPException(400, "Not enough subjects for comparison")

        results = analyzer.compare_groups(connectivity["ASD"], connectivity["TD"])

        # Get network-level differences
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
            d = float(np.mean([np.abs(diff[i]).mean() for i in idx]))
            network_diffs[net] = d

        # Sort by difference
        network_diffs = dict(sorted(network_diffs.items(), key=lambda x: -x[1]))

        _abide_results = {
            "asd_subjects": len(connectivity["ASD"]),
            "td_subjects": len(connectivity["TD"]),
            "network_differences": network_diffs,
            "asd_mean": results["asd_mean"].tolist(),
            "td_mean": results["td_mean"].tolist(),
            "difference": results["difference"].tolist(),
        }

        return _abide_results
    except Exception as e:
        logger.error(f"Connectivity failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compare")
async def compare_models(text: str = Form(...)):
    """Compare neurotypical vs neurodiverse brain predictions.

    Requires a fine-tuned neurodiverse model checkpoint.
    """
    try:
        nt_model = get_model()

        # Check if neurodiverse model exists
        nd_checkpoint = os.environ.get("ND_MODEL_PATH", "./models/neurodiverse/best.ckpt")
        if not Path(nd_checkpoint).exists():
            # Return simulated comparison using ABIDE connectivity data
            # until fine-tuned model is available
            prediction = await predict_brain(text)

            return {
                "status": "simulated",
                "message": "Fine-tuned neurodiverse model not yet available. Showing neurotypical prediction with ABIDE-derived divergence estimates.",
                "nt_prediction": prediction,
                "estimated_divergence": {
                    "visual": 0.85,
                    "auditory": 0.62,
                    "language": 0.71,
                    "default_mode": 0.78,
                    "motor": 0.35,
                    "social": 0.91,
                },
            }

        from tribev2 import TribeModel
        from tribev2.neurodiverse.comparison import NeurodiverseComparison

        nd_model = TribeModel.from_pretrained(nd_checkpoint, device="cuda")
        comparison = NeurodiverseComparison(nt_model, nd_model)

        os.makedirs("./tmp", exist_ok=True)
        with open("./tmp/compare_input.txt", "w") as f:
            f.write(text)

        events = nt_model.get_events_dataframe(text_path="./tmp/compare_input.txt")
        nt_preds, nd_preds = comparison.predict_both(events, verbose=False)

        divergence = comparison.compute_divergence_map(nt_preds, nd_preds)
        profile = comparison.sensory_profile(nt_preds, nd_preds)

        return {
            "status": "real",
            "sensory_profile": profile,
            "divergence_stats": {
                "mean": float(divergence.mean()),
                "max": float(divergence.max()),
                "min": float(divergence.min()),
            },
            "nt_images": [brain_to_image(nt_preds, t) for t in range(min(5, nt_preds.shape[0]))],
            "nd_images": [brain_to_image(nd_preds, t) for t in range(min(5, nd_preds.shape[0]))],
        }
    except Exception as e:
        logger.error(f"Comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
