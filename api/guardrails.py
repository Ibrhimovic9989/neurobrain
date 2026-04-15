"""Clinical guardrails and disclaimer text for AQAL responses.

AQAL is a research tool — not a medical device. Every API response that
returns predictions includes a disclaimer block so downstream consumers
cannot mistake AQAL output for diagnostic information.
"""

DISCLAIMER = {
    "not_diagnostic": (
        "AQAL predictions are research-grade and not suitable for clinical diagnosis. "
        "ADOS-2 and ADI-R remain the accepted diagnostic standards for autism."
    ),
    "population_average": (
        "Unless you have provided a calibration profile via /api/calibrate/fit, "
        "predictions reflect the POPULATION-AVERAGE neurodiverse response — not your "
        "individual neural response. Every autistic brain is different."
    ),
    "resting_state_source": (
        "The neurodiverse transform is derived from resting-state connectivity in "
        "1,545 subjects across 36 sites (ABIDE I + II). Applying this to task-evoked "
        "stimulus responses extends beyond the training distribution — treat as "
        "qualitative, not quantitative."
    ),
    "cohort_limitations": (
        "Training cohort is ~91% male, ages 5-64, primarily North American/European "
        "clinical sites. Predictions for underrepresented demographics (female autistic, "
        "early childhood, non-Western contexts) may be less accurate."
    ),
    "confidence_interpretation": (
        "When uncertainty (confidence interval width) is reported per-vertex, narrower "
        "intervals indicate more reliable predictions. Wide intervals reflect regions "
        "where our 1,545-subject statistical model cannot distinguish ND from NT with "
        "high confidence."
    ),
    "escalation": (
        "If you are considering clinical action based on these outputs — consult a "
        "licensed clinician. AQAL's validation accuracy on held-out ABIDE sites is "
        "~58-63%, well below diagnostic thresholds."
    ),
}


def attach_to_response(response: dict, keys: list[str] = None) -> dict:
    """Merge a 'disclaimer' block into any response dict.

    Default keys include the essential disclaimers for every prediction response.
    Pass a custom list of keys to include only specific disclaimers.
    """
    if keys is None:
        keys = ["not_diagnostic", "population_average"]
    response["disclaimer"] = {k: DISCLAIMER[k] for k in keys if k in DISCLAIMER}
    return response
