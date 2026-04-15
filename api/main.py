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
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cortex v1 — separate model family for brain pattern recognition
try:
    from api.cortex_routes import router as cortex_router
    app.include_router(cortex_router)
    logger.info("Cortex routes mounted at /api/cortex/*")
except Exception as _e:
    logger.warning(f"Cortex routes not mounted: {_e}")

# Calibration — per-person OLS behavioral calibration
try:
    from api.calibration import router as calibration_router, apply_profile_to_network
    app.include_router(calibration_router)
    logger.info("Calibration routes mounted at /api/calibrate/*")
except Exception as _e:
    logger.warning(f"Calibration routes not mounted: {_e}")
    apply_profile_to_network = None

# Guardrails — disclaimer text attached to prediction responses
try:
    from api.guardrails import attach_to_response as _attach_disclaimer
    logger.info("Guardrails module loaded")
except Exception as _e:
    logger.warning(f"Guardrails not loaded: {_e}")
    def _attach_disclaimer(resp, keys=None): return resp

# Global model instances (loaded once at startup)
_model = None
_analyzer = None
_abide_results = None


def get_model():
    global _model
    if _model is None:
        import torch
        from tribev2 import TribeModel
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading TRIBE v2 on {device}...")

        # Force all feature extractors to use the same device
        config_update = {}
        if device == "cpu":
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
            config_update = {
                "data.text_feature.device": "cpu",
                "data.audio_feature.device": "cpu",
                "data.num_workers": 0,
            }

        _model = TribeModel.from_pretrained(
            "facebook/tribev2",
            cache_folder="./cache",
            device=device,
            config_update=config_update,
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
    from nilearn import datasets, plotting

    fsaverage = datasets.fetch_surf_fsaverage("fsaverage5")
    data = preds[timestep] if preds.ndim == 2 else preds

    # Use per-timestep adaptive threshold for better contrast
    abs_data = np.abs(data)
    vmax = np.percentile(abs_data, 98)
    threshold = np.percentile(abs_data, 60)

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
            bg_map=bg, colorbar=False,
            threshold=threshold, vmax=vmax,
            cmap="cold_hot", symmetric_cbar=True,
            axes=ax,
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
            "stimulus_text": text,
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

    # Check disk cache first
    cache_file = Path.home() / "neurobrain_connectivity_cache.json"
    if _abide_results is not None:
        return _abide_results
    if cache_file.exists():
        import json
        _abide_results = json.loads(cache_file.read_text())
        return _abide_results

    try:
        from tribev2.neurodiverse.download import AbideDownloader
        from nilearn import datasets

        # Use existing data or download
        data_dir = Path.home() / "data" / "abide"
        abide = AbideDownloader(output_dir=str(data_dir))
        phenotypic = abide.download_abide1(n_subjects=n_subjects * 3)

        # Compute connectivity
        analyzer = get_analyzer()
        connectivity = analyzer.batch_project_and_connect(
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

        # Cache to disk so it survives restarts
        import json
        cache_file.write_text(json.dumps(_abide_results))
        logger.info("Connectivity results cached to %s", cache_file)

        return _abide_results
    except Exception as e:
        logger.error(f"Connectivity failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


_nd_transform = None


def get_nd_transform():
    """Load the neurodiverse transform trained on ABIDE data.
    Tries v4 (FDR-corrected) first, falls back to v3."""
    global _nd_transform
    if _nd_transform is None:
        import torch
        from huggingface_hub import hf_hub_download
        # Try v6 learned first, fall back to v5 statistical, then v4, then v3
        for fname in ["neurodiverse_transform_v6.pt", "neurodiverse_transform_v5.pt", "neurodiverse_transform_v4.pt"]:
            try:
                path = hf_hub_download("Ibrahim9989/neurobrain-nd-transform", fname)
                _nd_transform = torch.load(path, map_location="cpu", weights_only=False)
                logger.info("Neurodiverse transform %s loaded (%d ASD, %d TD subjects)",
                             _nd_transform.get("version", fname), _nd_transform["n_asd"], _nd_transform["n_td"])
                return _nd_transform
            except Exception as e:
                logger.info(f"  Skip {fname}: {e}")
        try:
            path = hf_hub_download("Ibrahim9989/neurobrain-nd-transform", "neurodiverse_transform_v5.pt")
            _nd_transform = torch.load(path, map_location="cpu", weights_only=False)
            logger.info("Neurodiverse transform v5 loaded (ABIDE I+II, %d ASD, %d TD subjects)",
                         _nd_transform["n_asd"], _nd_transform["n_td"])
            if "sig_fdr" in _nd_transform:
                logger.info("  FDR-significant: %d, Uncorrected: %d, Bonferroni: %d",
                             _nd_transform["sig_fdr"], _nd_transform["sig_uncorrected"], _nd_transform["sig_bonferroni"])
        except Exception:
            path = hf_hub_download("Ibrahim9989/neurobrain-nd-transform", "neurodiverse_transform_v3.pt")
            _nd_transform = torch.load(path, map_location="cpu", weights_only=True)
            logger.info("Neurodiverse transform v3 loaded (uncorrected, %d ASD, %d TD subjects)",
                         _nd_transform["n_asd"], _nd_transform["n_td"])
    return _nd_transform


@app.post("/api/compare")
async def compare_models(
    text: str = Form(...),
    age_band: str = Form(None),
    calibration_profile: str = Form(None),
):
    """Compare neurotypical vs neurodiverse brain predictions.

    Optional params:
      age_band: 'child' (0-12), 'adolescent' (12-18), 'adult' (18+), or None for all-ages.
      calibration_profile: JSON-encoded calibration profile from /api/calibrate/fit.
        When provided, the 7-network sensory profile is modulated by per-person
        sensitivity factors, turning the group-average prediction into a
        first-order individualized one.
    """
    try:
        model = get_model()
        transform = get_nd_transform()

        # Get NT prediction
        os.makedirs("./tmp", exist_ok=True)
        text_path = "./tmp/compare_input.txt"
        with open(text_path, "w") as f:
            f.write(text)

        events = model.get_events_dataframe(text_path=text_path)
        nt_preds, segments = model.predict(events, verbose=False)

        # Select age-appropriate transform if available
        if age_band and "age_transforms" in transform and age_band in transform["age_transforms"]:
            age_t = transform["age_transforms"][age_band]
            scale = age_t["vertex_scale"].numpy()
            shift = age_t.get("vertex_shift", transform["vertex_shift"]).numpy()
            age_info = {"age_band": age_band, "n_asd": int(age_t["n_asd"]), "n_td": int(age_t["n_td"]),
                        "sig_connections_fdr": int(age_t.get("sig_connections_fdr", 0))}
        else:
            scale = transform["vertex_scale"].numpy()
            shift = transform["vertex_shift"].numpy()
            age_info = {"age_band": "all", "n_asd": int(transform["n_asd"]), "n_td": int(transform["n_td"])}

        # Apply transform: NT -> ND
        nd_preds = nt_preds * scale + shift

        # Compute divergence
        divergence = np.mean((nt_preds - nd_preds) ** 2, axis=0)

        # Compute uncertainty if available (v4)
        uncertainty = {}
        if "vertex_ci_lower" in transform and "vertex_ci_upper" in transform:
            ci_lower = transform["vertex_ci_lower"].numpy()
            ci_upper = transform["vertex_ci_upper"].numpy()
            ci_width = ci_upper - ci_lower
            uncertainty = {
                "mean_ci_width": float(ci_width.mean()),
                "max_ci_width": float(ci_width.max()),
                "high_confidence_vertices_pct": float((ci_width < ci_width.mean()).sum() / len(ci_width) * 100),
            }

        # Network-level divergence profile
        roi_effect = transform["roi_effect"].numpy()
        roi_labels = transform["roi_labels"]
        network_map = {
            "Vis": "visual", "SomMot": "motor", "DorsAttn": "attention",
            "SalVentAttn": "salience", "Limbic": "emotional",
            "Cont": "control", "Default": "default_mode",
        }
        network_effects: dict = {}
        for label, effect in zip(roi_labels, roi_effect):
            for short, full in network_map.items():
                if short in label:
                    network_effects.setdefault(full, []).append(float(effect))
                    break
        profile = {k: float(np.mean(v)) for k, v in network_effects.items()}
        max_p = max(profile.values()) or 1.0
        profile = {k: v / max_p for k, v in profile.items()}

        # Per-network confidence intervals — within-network std of ROI effects,
        # normalized against the same max_p as the mean profile so error bars
        # render on the same 0-1 scale.
        sensory_profile_ci = {}
        for net, effs in network_effects.items():
            arr = np.array(effs, dtype=np.float32)
            if len(arr) <= 1:
                # Single-ROI network — no within-network variance. Use mean vertex
                # CI as proxy so bars still show a range.
                ci_half = float(uncertainty.get("mean_ci_width", 0.05)) / 2.0 / max_p
            else:
                # Standard error of the mean: std / sqrt(n). Use 1.96·SE as half-CI.
                ci_half = float(1.96 * np.std(arr, ddof=1) / np.sqrt(len(arr))) / max_p
            center = profile[net]
            sensory_profile_ci[net] = {
                "mean": center,
                "lower": max(0.0, center - ci_half),
                "upper": min(1.0, center + ci_half),
                "half_width": ci_half,
                "n_rois": len(arr),
            }

        # Apply per-person calibration if provided
        calibration_info = None
        if calibration_profile and apply_profile_to_network:
            try:
                import json as _json
                cal = _json.loads(calibration_profile)
                net_mod = cal.get("network_modulation") or cal.get("profile", {}).get("network_modulation")
                if net_mod:
                    profile = apply_profile_to_network(net_mod, profile)
                    calibration_info = {
                        "applied": True,
                        "axis_sensitivity": cal.get("axis_sensitivity"),
                        "n_stimuli_rated": cal.get("n_stimuli_rated"),
                    }
            except Exception as _ce:
                logger.warning(f"Calibration profile invalid, ignoring: {_ce}")
                calibration_info = {"applied": False, "error": str(_ce)}

        # Generate brain images for both
        n_steps = min(nt_preds.shape[0], 8)
        nt_images = [brain_to_image(nt_preds, t) for t in range(n_steps)]
        nd_images = [brain_to_image(nd_preds, t) for t in range(n_steps)]

        # Transform version info
        version_info = {"version": transform.get("version", "v3")}
        if "sig_fdr" in transform:
            version_info["sig_fdr"] = int(transform["sig_fdr"])
            version_info["sig_uncorrected"] = int(transform["sig_uncorrected"])
            version_info["corrections"] = transform.get("corrections", [])

        response = {
            "status": "real",
            "stimulus_text": text,
            "sensory_profile": profile,
            "sensory_profile_ci": sensory_profile_ci,
            "divergence_stats": {
                "mean": float(divergence.mean()),
                "max": float(divergence.max()),
            },
            "uncertainty": uncertainty,
            "age_info": age_info,
            "transform_version": version_info,
            "calibration": calibration_info,
            "nt_images": nt_images,
            "nd_images": nd_images,
            "timesteps": n_steps,
            "n_asd_subjects": age_info["n_asd"],
            "n_td_subjects": age_info["n_td"],
        }
        # Attach structured disclaimers — escalated keys if no calibration provided
        disclaimer_keys = ["not_diagnostic", "cohort_limitations", "escalation"]
        if calibration_info and calibration_info.get("applied"):
            disclaimer_keys = ["not_diagnostic", "cohort_limitations"]
        else:
            disclaimer_keys.append("population_average")
        return _attach_disclaimer(response, disclaimer_keys)
    except Exception as e:
        logger.error(f"Comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def generate_interpretation(data: dict, context: str = "predict") -> str:
    """Generate plain-language interpretation of brain results using Azure OpenAI."""
    from openai import AzureOpenAI

    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
    )
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5.2-chat")

    if context == "predict":
        stimulus = data.get('stimulus_text', 'unknown stimulus')
        regions = data.get('top_active_regions', [{}])
        hemi = regions[0].get('hemisphere', 'right') if regions else 'right'
        prompt = f"""You are a neuroscientist explaining brain scan results to a non-expert.

The stimulus was: "{stimulus}"

A brain encoding model (TRIBE v2, 177M parameters) predicted how a neurotypical brain responds. Results:
- {data.get('timesteps', 0)} seconds of brain activity predicted across {data.get('vertices', 20484):,} brain surface points
- Mean activation level: {data.get('mean_activation', 0):.4f}
- Value range: {data.get('value_range', [0,0])}
- Most active regions are in the {hemi} hemisphere

Explain in 4-5 simple sentences:
1. What the stimulus "{stimulus}" would trigger in the brain specifically (which regions and why)
2. What the activation pattern tells us about how the brain processes this specific input
3. How an autistic brain might process this same stimulus differently (be specific to this stimulus)
4. What accommodation might help if this stimulus is part of daily life

Be specific to the stimulus. Don't be generic. Keep it warm and simple."""

    elif context == "compare":
        profile = data.get("estimated_divergence", data.get("sensory_profile", {}))
        sorted_nets = sorted(profile.items(), key=lambda x: -x[1])
        top_3 = ", ".join([f"{k} ({v:.0%})" for k, v in sorted_nets[:3]])
        bottom_2 = ", ".join([f"{k} ({v:.0%})" for k, v in sorted_nets[-2:]])

        prompt = f"""You are a neuroscientist explaining how autistic brains process information differently.

A brain model comparison shows these divergence scores between neurotypical and neurodiverse processing:
- Highest differences: {top_3}
- Lowest differences: {bottom_2}

Full scores: {dict(sorted_nets)}

Explain in 4-5 simple sentences:
1. Which sensory systems show the biggest differences
2. What this means in daily life (concrete examples)
3. How this knowledge could help design better accommodations
4. Frame this positively - different processing, not deficient

Keep it warm, hopeful, and practical. Like explaining to a parent."""

    elif context == "connectivity":
        net_diffs = data.get("network_differences", {})
        n_asd = data.get("asd_subjects", 0)
        n_td = data.get("td_subjects", 0)
        sorted_nets = sorted(net_diffs.items(), key=lambda x: -x[1])

        network_names = {
            "Vis": "Visual", "SomMot": "Somatomotor (body/movement)",
            "DorsAttn": "Dorsal Attention (focus)", "SalVentAttn": "Salience (what matters)",
            "Limbic": "Limbic (emotions)", "Cont": "Control (planning)",
            "Default": "Default Mode (daydreaming/self)",
        }
        readable = [(network_names.get(k, k), v) for k, v in sorted_nets]

        prompt = f"""You are a neuroscientist explaining brain connectivity differences in autism.

We analyzed real fMRI brain scans from {n_asd} autistic and {n_td} non-autistic people (ABIDE dataset).
We measured how strongly different brain networks communicate with each other.

Network connectivity differences (higher = more different in autism):
{chr(10).join([f"- {name}: {val:.4f}" for name, val in readable])}

Explain in 5-6 simple sentences:
1. Which brain networks show the biggest wiring differences
2. What each network does in plain language
3. What these differences mean for daily life
4. Why this matters for understanding autism
5. How this could help (therapy, accommodations, tools)

Be warm, practical, and frame neurodiversity positively."""

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a neuroscientist who explains brain science in simple, warm language. Be concise, practical, and frame neurodiversity positively."},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"LLM interpretation failed: {e}")
        return ""


@app.post("/api/interpret")
async def interpret_results(request: dict):
    """Generate plain-language interpretation of brain analysis results."""
    try:
        context = request.get("context", "predict")
        data = request.get("data", {})
        interpretation = generate_interpretation(data, context)
        if not interpretation:
            interpretation = _fallback_interpretation(data, context)
        return {"interpretation": interpretation}
    except Exception as e:
        logger.error(f"Interpretation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _fallback_interpretation(data: dict, context: str) -> str:
    """Generate interpretation without LLM if API fails."""
    if context == "connectivity":
        net_diffs = data.get("network_differences", {})
        names = {
            "Vis": "Visual", "SomMot": "Movement", "DorsAttn": "Attention",
            "SalVentAttn": "Salience", "Limbic": "Emotional",
            "Cont": "Control", "Default": "Default Mode",
        }
        sorted_nets = sorted(net_diffs.items(), key=lambda x: -x[1])
        top = sorted_nets[0] if sorted_nets else ("", 0)
        n_asd = data.get("asd_subjects", 0)
        n_td = data.get("td_subjects", 0)
        return (
            f"Analysis of {n_asd} autistic and {n_td} non-autistic brain scans "
            f"reveals that the {names.get(top[0], top[0])} network shows the "
            f"largest connectivity differences (score: {top[1]:.4f}). "
            f"This means autistic brains organize communication between "
            f"{names.get(top[0], top[0]).lower()} regions differently. "
            f"These differences aren't deficits -- they represent alternative "
            f"neural wiring that can bring unique strengths in perception, "
            f"pattern recognition, and focused attention. Understanding these "
            f"patterns helps design better accommodations and learning tools."
        )
    elif context == "predict":
        regions = data.get("top_active_regions", [])
        hemi = regions[0].get("hemisphere", "right") if regions else "right"
        return (
            f"The brain model predicted activity across {data.get('vertices', 20484):,} "
            f"surface points over {data.get('timesteps', 0)} seconds. "
            f"The strongest activation is in the {hemi} hemisphere, "
            f"in regions associated with language and auditory processing. "
            f"In autistic brains, these same regions may activate with "
            f"different intensity or timing, reflecting unique sensory "
            f"processing patterns."
        )
    elif context == "compare":
        profile = data.get("estimated_divergence", data.get("sensory_profile", {}))
        sorted_p = sorted(profile.items(), key=lambda x: -x[1])
        top3 = [f"{k} ({v:.0%})" for k, v in sorted_p[:3]]
        return (
            f"The biggest processing differences are in: {', '.join(top3)}. "
            f"This means autistic brains handle these types of sensory "
            f"information most differently. For example, higher social "
            f"processing divergence may explain why social cues feel "
            f"overwhelming. These insights can guide personalized "
            f"accommodations -- like quieter environments for high auditory "
            f"divergence, or visual schedules for those with different "
            f"default mode processing."
        )
    return "Interpretation unavailable."


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
