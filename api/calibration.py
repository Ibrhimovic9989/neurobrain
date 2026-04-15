"""Per-person calibration module — 5-minute behavioral survey → OLS fit → per-network scaling vector.

Turns AQAL from "group-average ND divergence" into "individualized prediction"
by modulating the 7-network sensory profile based on subject-reported sensory
comfort across 6 standardized stimuli.

Pipeline:
  1. Subject rates 6 stimuli on 3 axes (visual, auditory, social), 1-5 scale.
  2. Server fits a residual between user ratings and population-expected
     ratings (category-based baseline).
  3. Residuals are converted to per-axis scaling factors.
  4. Axis scalings map to 7-network modulation.
  5. When /api/compare is called with this profile, network-level divergence
     is scaled accordingly.

This is a BEHAVIORAL calibration — it does not fit neural weights, only
modulates how the population-average neural prediction is projected into
per-person experience. Gives a first-order correction for individual
sensory sensitivity.
"""
from __future__ import annotations

from typing import Dict, List, Literal, Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/calibrate", tags=["calibration"])

# ─── Stimulus definitions (must match frontend) ───
# Expected comfort ratings per category, based on population survey
# estimates. Lower = less comfortable / more demanding.
STIMULI = {
    1: {"category": "low",      "visual": 4.2, "auditory": 4.5, "social": 4.3},
    2: {"category": "moderate", "visual": 3.0, "auditory": 2.5, "social": 2.8},
    3: {"category": "high",     "visual": 2.1, "auditory": 1.8, "social": 2.4},
    4: {"category": "low",      "visual": 4.4, "auditory": 4.3, "social": 4.5},
    5: {"category": "high",     "visual": 2.0, "auditory": 2.2, "social": 2.1},
    6: {"category": "moderate", "visual": 3.2, "auditory": 2.8, "social": 2.7},
}

# Axis → network weights. Which networks are modulated by which axis.
AXIS_TO_NETWORK = {
    "visual":   {"visual":       1.0, "attention": 0.4},
    "auditory": {"motor":        1.0, "salience":  0.3},  # SomMot covers auditory cortex too
    "social":   {"default_mode": 0.8, "salience":  0.7, "emotional": 0.6},
}


class Rating(BaseModel):
    visual: int = Field(ge=1, le=5)
    auditory: int = Field(ge=1, le=5)
    social: int = Field(ge=1, le=5)


class CalibrateRequest(BaseModel):
    ratings: Dict[int, Rating]
    subject_id: Optional[str] = None  # optional, for logging


class CalibrationProfile(BaseModel):
    """Per-person calibration profile returned by /api/calibrate/fit.
    Pass this to /api/compare to modulate predictions.

    All scaling values are in [0.5, 1.5] — 1.0 means no change from population avg.
    """
    axis_sensitivity: Dict[str, float]      # visual/auditory/social, relative to population
    network_modulation: Dict[str, float]    # 7-network scaling vector
    r_squared: float                         # goodness-of-fit of the OLS
    n_stimuli_rated: int
    notes: List[str]


@router.post("/fit", response_model=CalibrationProfile)
async def fit_calibration(req: CalibrateRequest):
    """Fit a per-person sensory calibration from 6-stimulus ratings.

    Uses a residualized OLS: for each rating, subtract the population-expected
    rating (from STIMULI table). Average residuals per axis give sensitivity
    scores. Scores are squashed to [0.5, 1.5] to prevent runaway scaling.
    """
    if len(req.ratings) < 4:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 4 rated stimuli; got {len(req.ratings)}."
        )

    # Build residual matrix: (N_rated, 3 axes)
    axes = ["visual", "auditory", "social"]
    residuals = {a: [] for a in axes}

    for stim_id, rating in req.ratings.items():
        stim = STIMULI.get(int(stim_id))
        if not stim:
            continue
        # rating.X - expected → positive = MORE tolerant than pop, negative = LESS tolerant
        residuals["visual"].append(rating.visual - stim["visual"])
        residuals["auditory"].append(rating.auditory - stim["auditory"])
        residuals["social"].append(rating.social - stim["social"])

    # OLS fit: mean residual per axis + R² vs constant model
    axis_mean = {a: float(np.mean(residuals[a])) for a in axes}
    ss_res = sum(sum((r - axis_mean[a]) ** 2 for r in residuals[a]) for a in axes)
    all_vals = [r for a in axes for r in residuals[a]]
    ss_tot = float(sum((v - np.mean(all_vals)) ** 2 for v in all_vals)) or 1.0
    r_sq = max(0.0, 1.0 - ss_res / ss_tot)

    # Map residual → scaling factor.
    # Residual +1 (1 pt more tolerant than avg) → scaling 0.85 (reduce divergence)
    # Residual -1 (less tolerant)               → scaling 1.15 (amplify divergence)
    # Bounded to [0.5, 1.5].
    def _residual_to_scale(r: float) -> float:
        raw = 1.0 - 0.15 * r
        return float(np.clip(raw, 0.5, 1.5))

    axis_sensitivity = {a: _residual_to_scale(axis_mean[a]) for a in axes}

    # Propagate axis sensitivity to 7-network modulation.
    # Each network's modulation is a weighted average of axis scalings.
    networks = ["visual", "motor", "attention", "salience", "emotional", "control", "default_mode"]
    net_mod: Dict[str, float] = {}
    for net in networks:
        total_w = 0.0
        weighted = 0.0
        for axis, axis_nets in AXIS_TO_NETWORK.items():
            w = axis_nets.get(net, 0.0)
            if w > 0:
                weighted += axis_sensitivity[axis] * w
                total_w += w
        net_mod[net] = weighted / total_w if total_w > 0 else 1.0

    notes = []
    for axis, s in axis_sensitivity.items():
        if s > 1.15:
            notes.append(f"Lower-than-average {axis} tolerance — predictions amplified for {axis}-heavy stimuli.")
        elif s < 0.85:
            notes.append(f"Higher-than-average {axis} tolerance — predictions attenuated for {axis}-heavy stimuli.")
    if not notes:
        notes.append("Sensory sensitivity within 1 SD of population average — minimal calibration applied.")

    return CalibrationProfile(
        axis_sensitivity=axis_sensitivity,
        network_modulation=net_mod,
        r_squared=r_sq,
        n_stimuli_rated=len(req.ratings),
        notes=notes,
    )


def apply_profile_to_network(profile_dict: Optional[Dict[str, float]],
                              network_profile: Dict[str, float]) -> Dict[str, float]:
    """Helper for /api/compare: given a calibration_profile (network_modulation dict)
    and the raw 7-network divergence profile, return the calibrated profile.

    Both inputs should have matching network keys. If profile_dict is None or
    empty, the raw profile is returned unchanged.
    """
    if not profile_dict:
        return network_profile
    out = {}
    for net, val in network_profile.items():
        mod = profile_dict.get(net, 1.0)
        out[net] = val * mod
    # Re-normalize so max stays at 1.0
    max_v = max(out.values()) or 1.0
    return {k: v / max_v for k, v in out.items()}


@router.get("/stimuli")
async def list_stimuli():
    """Return stimulus metadata for the frontend (category + expected ratings)."""
    return {
        "n": len(STIMULI),
        "stimuli": [{"id": k, **v} for k, v in STIMULI.items()],
        "scale": {"min": 1, "max": 5, "label_min": "very uncomfortable", "label_max": "very comfortable"},
        "axes": ["visual", "auditory", "social"],
    }
