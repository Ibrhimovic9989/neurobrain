# AQAL Fine-Tuning on Google Colab

This directory contains notebooks for training the next generation of AQAL's neurodiverse transform on Google Colab.

## Quick Start

1. **Open in Colab:** Click the "Open in Colab" badge or upload `aqal_finetune_colab.ipynb` to [colab.research.google.com](https://colab.research.google.com)
2. **Enable GPU:** Runtime → Change runtime type → T4 GPU
3. **Run all cells:** Runtime → Run all

Expected runtime: **~30 minutes** on free-tier T4.

## What the Notebooks Do

### `aqal_finetune_colab.ipynb` — Basic Learned Transform

Replaces the statistical v5 transform with a learned neural network. Trains two models:

1. **ASD Classifier** (MLP on 4,950-dim connectivity) — baseline that validates the signal exists
2. **Conditional Transform** (encoder–decoder) — maps NT connectivity → ND-like connectivity, conditioned on age and sex, trained adversarially against the classifier

**Training data:** 1,545 subjects (693 ASD + 852 TD) across 36 clinical sites, pre-extracted Fisher-z connectivity features, site-harmonized.

**Outputs:**
- `neurodiverse_transform_v6_learned.pt` — checkpoint with both models
- Held-out accuracy report (2 unseen sites)
- Comparison vs statistical v5

## Why Colab?

Fine-tuning the full 177M-parameter encoder is GPU-blocked on our Azure sponsorship (no GPU quota). Colab's free T4 (16 GB VRAM) lets us:

- Train small-to-medium neural networks (our 256-latent conditional transform fits easily)
- Experiment with architectures without infrastructure overhead
- Share reproducible notebooks with the broader research community

For full TRIBE v2 LoRA fine-tuning (the roadmap's ultimate goal), we need Colab Pro (A100) or a dedicated research cluster.

## Roadmap

| Step | Notebook | Status |
|---|---|---|
| Learned connectivity-level transform | `aqal_finetune_colab.ipynb` | Ready |
| Vertex-level mapping from Schaefer 100 | TBD | Planned |
| Age-stratified learned transforms | TBD | Planned |
| LoRA fine-tuning of 177M encoder | TBD | Needs A100 + task fMRI |
| Infant/toddler developmental models | TBD | Needs NDA/SPARK approval |

## Integrating the Trained Model

Once training completes, the notebook uploads `neurodiverse_transform_v6_learned.pt` to HuggingFace. The production API auto-loads new versions on startup:

```python
# neuro-app/api/main.py
try:
    path = hf_hub_download("Ibrahim9989/neurobrain-nd-transform", "neurodiverse_transform_v6_learned.pt")
    # Load learned model
except Exception:
    # Fall back to v5 statistical
    ...
```

Test locally with `age_band=child|adolescent|adult&mode=learned` on `/api/compare`.

## Citation & Methodology

Full methodology in the technical paper at [mind.new/paper](https://mind.new/paper).

The training data (`colab_training_data.npz`) is derived from publicly available neuroimaging research datasets, Fisher-z transformed, and harmonized across clinical sites via residualization. All individual subject data is de-identified.

## Contact

Questions: ibrahim.raza@leeza.app
