# Behavioral Validation Protocol for AQAL Predictions

**Status: Design document, not yet executed. Awaiting IRB approval and participant recruitment.**

This document specifies the study protocol for validating that AQAL's predicted neurodiverse divergence correlates with real behavioral, physiological, and caregiver-reported outcomes in autistic individuals.

The protocol addresses roadmap item **P6**. Without this study, AQAL remains a **visualization engine** — a tool that *looks* scientifically principled but has not demonstrated that its predictions reflect any measurable reality.

---

## 1. Research question

> For a given stimulus, does AQAL's predicted neurodiverse divergence (in a specific sensory network) correlate with the real sensory distress that an autistic subject experiences when exposed to that stimulus?

Operationalized:

- **Primary hypothesis**: higher AQAL-predicted divergence → greater physiological arousal (pupil dilation, skin conductance response)
- **Secondary hypothesis**: higher AQAL-predicted divergence → higher self-reported discomfort (1–10 Likert)
- **Tertiary hypothesis**: higher AQAL-predicted divergence → more avoidance behavior (gaze aversion, shorter dwell time)

---

## 2. Study design

**Type**: Within-subjects, stimulus-matched validation.  
**Duration**: 60 minutes per participant (single session).  
**Setting**: Quiet room with standardized lighting, eye tracker, GSR sensors, video recording of participant.

### Participant eligibility

| Criterion | Value |
|---|---|
| Age | 12–35 years (to avoid confounds with developmental change) |
| Diagnosis | ADOS-2 or ADI-R confirmed ASD diagnosis, moderate to severe |
| Comparison group | Age/sex/IQ-matched neurotypical controls |
| N per group | ≥ 20 ASD + ≥ 20 TD = 40 total (for ~80% power to detect r = 0.4 at α = 0.05) |
| Exclusion | Uncorrected vision/hearing deficit, unmanaged epilepsy, motor disorder preventing eye tracking |

### Stimulus set

12 standardized ~30-second video clips spanning 6 categories × 2 examples each:

1. **Low-stimulation baseline**: quiet library, empty park (control condition)
2. **Visual-heavy**: rotating colorful patterns, flashing retail displays
3. **Auditory-heavy**: overlapping conversations, dishwasher cycles
4. **Social-heavy**: crowded cafeteria, family dinner scene
5. **Multi-modal demanding**: busy shopping mall, school hallway during transition
6. **Unpredictable temporal**: intermittent loud sounds, sudden motion

Each clip is pre-processed through AQAL to generate per-network divergence predictions. These predictions are blinded from the experimenter during data collection.

### Order of clip presentation

Latin-square counterbalanced across subjects (blocked by category, randomized within category). Baseline clips always appear first and last to establish physiological baseline.

---

## 3. Measurements

### Per-trial measurements (12 trials × 40 participants = 480 observations)

| Measure | Instrument | Sampling | Target network |
|---|---|---|---|
| Pupil dilation | Tobii Pro Spectrum (300 Hz) | Continuous during clip | General arousal + visual network |
| Skin conductance (GSR) | BIOPAC MP160 (2 kHz) | Continuous during clip | Autonomic/salience network |
| Gaze fixation patterns | Same eye tracker | Continuous during clip | Attention networks (DAN/VAN) |
| Heart rate variability | BIOPAC ECG | Continuous | Emotional regulation (limbic/DMN) |
| Self-reported discomfort | 1–10 Likert slider | Immediately post-clip | Overall subjective |
| "Would-you-leave" forced choice | Binary | Immediately post-clip | Behavioral avoidance |
| Open-response 1-sentence | Audio recorded | Immediately post-clip | Qualitative |

### Post-session caregiver/self-report battery

- **Sensory Profile 2** (Dunn) — parent/self report of sensory sensitivities
- **Social Responsiveness Scale 2** (Constantino) — social communication difficulties
- **AQ-50** (Baron-Cohen) — autism quotient for self-report validity
- **Environmental audit questionnaire** — 5 open-ended questions about real-world accommodation needs

---

## 4. Analysis plan

### Primary analysis

For each subject × clip observation, compute:

- `AQAL_divergence_visual`, `AQAL_divergence_auditory`, `AQAL_divergence_social`, ..., per the 7-network profile
- `behavioral_arousal` = mean z-scored pupil dilation + GSR amplitude over clip duration
- `subjective_discomfort` = Likert rating

**Mixed-effects model** with subject-random-intercept:

```
behavioral_arousal ~ AQAL_divergence_relevant_network 
                     + age + sex + IQ + baseline_GSR
                     + (1 | subject_id)
```

- **Relevant network** selected per stimulus category (e.g., visual clips → visual network divergence).
- Report standardized beta coefficient, 95 % CI, p-value, pseudo-R².
- **Pre-registered primary outcome**: is `beta_AQAL_divergence > 0` (p < 0.05) for at least 4 of 6 stimulus categories? If yes → AQAL predictions are physiologically grounded.

### Secondary analyses

- **Sensitivity / specificity** of AQAL predictions using ROC analysis: treat "high physiological arousal" (top tertile) as positive class, binned AQAL divergence as predictor.
- **Calibration curves**: do subjects for whom AQAL predicts HIGH divergence actually show higher arousal than those predicted LOW? Use reliability diagrams.
- **Per-subject variance decomposition**: how much within-subject variance does AQAL explain across clips? (Between-subject analysis conflates individual differences with stimulus-specific signal.)
- **Caregiver-rated sensory profile × AQAL correlation**: does AQAL's 7-network profile for a subject correlate with their pre-session Sensory Profile 2 scores?

### Negative controls

- **Scrambled AQAL predictions**: shuffle the predicted divergence values across clips, rerun analysis. Should show r ≈ 0.
- **Wrong-network predictor**: predict arousal for auditory clips from AQAL's visual-network divergence. Should show weaker effect than from auditory-network divergence.

---

## 5. Success criteria

The study is a **positive validation** of AQAL if:

1. Primary mixed-effects coefficient is significant at p < 0.05 in ≥ 4 of 6 stimulus categories
2. Effect size (standardized beta) ≥ 0.2 on average
3. Negative controls behave as expected (r ≈ 0 for scrambled; weaker for wrong-network)
4. Calibration is monotonic within ±20 % on reliability diagrams

The study is **inconclusive** if:

1. Coefficients are non-zero but inconsistent across categories
2. Effect sizes are small (beta < 0.2) even when significant
3. Negative controls show spurious effects

The study is a **negative validation** — and AQAL must be either retrained or repositioned — if:

1. No categories show significant AQAL → physiological correlation
2. Scrambled predictions perform as well as real ones
3. Calibration is non-monotonic

---

## 6. Ethics & regulatory

- **IRB**: application pending via [collaborating institution TBD].
- **Consent**: full informed consent + assent (for minors), with plain-language description of AQAL and the study aims.
- **Participant compensation**: $50 per session; travel reimbursement available.
- **Data sharing**: de-identified physiological traces + stimulus-locked events will be released on OSF / NDA (similar to ABIDE) after primary publication.
- **Adverse event reporting**: if any participant reports significant distress during or after the session, protocol pauses until safety review.

---

## 7. Timeline (from IRB approval)

| Month | Milestone |
|---|---|
| 0 | IRB approval secured |
| 1 | Equipment calibration + pilot on 3 subjects to validate protocol |
| 2–4 | Participant recruitment + data collection (target 40 subjects, 10/month) |
| 5 | Data preprocessing + analysis |
| 6 | Preprint + registered report submission |

Total: **6 months post-IRB approval**.

---

## 8. Pre-registration

Before data collection begins, this protocol will be pre-registered on [OSF](https://osf.io) with locked analysis plans to prevent post-hoc modifications. The pre-registration will specify:

- Hypothesis phrasing (see §1)
- Participant exclusion criteria (see §2)
- Primary analysis model (see §4)
- Success criteria (see §5)

Any deviation from the pre-registered plan is reported as such in the final publication.

---

## 9. Relation to other AQAL validations

This is Phase 1: **lab-controlled behavioral validation**. Follow-on phases:

- **Phase 2**: Naturalistic validation — AQAL predictions vs. real-world caregiver logs of sensory overload in school/work environments (see roadmap P6.2).
- **Phase 3**: Clinical utility — does AQAL-informed space redesign reduce sensory-overload incidents in a controlled workplace/school intervention? (roadmap → R7)

Each phase builds on positive outcomes from the previous one. If Phase 1 fails, Phases 2 and 3 are deferred until model retraining closes the gap.

---

## 10. What is NOT validated here

- AQAL as a **clinical diagnostic** — this study does not address whether AQAL predictions differ between diagnosed ASD and undiagnosed autistic traits. Requires a separate screening-focused study.
- **Fine-grained vertex-level** predictions — validation is at the 7-network level, not per-vertex. Vertex-level claims remain unvalidated.
- **Specific real-world interventions** — validation confirms the signal exists, not that any particular design intervention will reduce it.

---

## References (to be added during pre-registration)

Recommended priors: Green & Ben-Sasson (2010) on sensory-overload physiology in ASD; Bylsma et al. (2008) on RSA reactivity; Schaaf & Lane (2015) on sensory integration intervention; Lisk et al. (2020) on pupil dilation as arousal marker; caregiver-report validation frameworks from Dunn (2014) and Constantino (2012).
