# NeuroBrain - Project Progress Report

## What We Built

**NeuroBrain** is a web application that predicts and compares how neurotypical (NT) and neurodiverse (ND/autistic) brains respond to sensory stimuli (text, audio, video), powered by Meta's TRIBE v2 brain encoding model.

- **Live Frontend**: https://neurobrain.vercel.app
- **Live API**: https://neurobrain-api.eastus.cloudapp.azure.com
- **GitHub (web app)**: https://github.com/Ibrhimovic9989/neurobrain
- **GitHub (brain model)**: https://github.com/Ibrhimovic9989/tribeneuro
- **Trained Model**: https://huggingface.co/Ibrahim9989/neurobrain-nd-transform

---

## Architecture

```
Vercel (Frontend)                    Azure VM (Backend)
┌──────────────────┐                ┌─────────────────────────────┐
│  Next.js App     │  ──HTTPS──>   │  FastAPI + TRIBE v2         │
│  Brain Viewer    │                │  LLaMA 3.2 (text encoder)   │
│  NT vs ND Compare│                │  Wav2Vec-BERT (audio)       │
│  ASD Connectivity│                │  Neurodiverse Transform     │
│  AI Interpretation│               │  Azure OpenAI GPT-5.2       │
└──────────────────┘                └─────────────────────────────┘
                                    8 cores, 32GB RAM, 256GB disk
                                    IP: 20.127.80.79
```

---

## Datasets Used

### Currently Trained On

| Dataset | Subjects | ASD | TD | Sites | Status |
|---------|----------|-----|-----|-------|--------|
| **ABIDE I** | 871 | 403 | 468 | 20 | Fully extracted |
| **OpenNeuro ds000228** (Richardson 2018 - Pixar) | 155 | ~36 | ~44 | 1 | Downloaded (4GB) |
| **OpenNeuro ds002345** (Byrge 2020 - Despicable Me) | 345 (partial) | ~170 | ~175 | 1 | Partially downloaded (60GB) |
| **TOTAL** | **~1,371** | **~609** | **~687** | **22** | |

### Why ds002345 Download Was Stopped

The ds002345 dataset (Byrge & Kennedy 2020 - "Despicable Me" movie watching) is very large. Each subject has multiple fMRI runs of a full-length movie, resulting in ~200MB per subject.

**Timeline:**
1. Download started on Azure VM (256GB disk)
2. After 345 subjects, the dataset had consumed **60GB** of disk space
3. Total disk usage was at **87% (214GB / 247GB usable)**
4. With ABIDE I (25GB), LLaMA 3.2 cache (12GB), Python environment (7GB), and ds000228 (4GB) already on disk, only **34GB remained**
5. The full ds002345 dataset would have been ~120GB total, exceeding available space
6. **Decision: Stop download, proceed with 345/~500 subjects already downloaded**

This is sufficient because:
- We already have 871 ABIDE subjects as the primary dataset
- The 345 partial ds002345 subjects add diversity (movie-watching paradigm vs resting-state)
- Statistical power with ~1,371 total subjects is strong

### Datasets Not Yet Used (Future)

| Dataset | Subjects | Access | Effort |
|---------|----------|--------|--------|
| **ABIDE II** | ~1,114 | Manual S3 download (not in nilearn) | 1 day |
| **Caltech Conte Center** | 122 | OpenNeuro | Easy |
| **NDA (NIMH Data Archive)** | 10,000+ | Application required | 1-2 weeks |
| **SPARK** (Simons Foundation) | 3,000+ | Application required | Weeks |
| **HBN** (Healthy Brain Network) | 2,000+ | Application via LORIS | 1 week |

---

## Training Approach

### Why Not Traditional Fine-Tuning?

TRIBE v2 fine-tuning requires GPU (specifically, retraining the subject-specific output layers). We attempted multiple paths to get GPU access:

1. **Azure VM GPU (Standard_NC4as_T4_v3)**: Rejected - GPU quota is 0 on Azure Sponsorship, quota increase request was denied
2. **Azure ML Compute GPU**: Same quota, blocked
3. **Google Colab GPU**: Hit free-tier usage limits during dataset download phase

### What We Did Instead: Statistical Transform (v3)

Instead of fine-tuning neural network weights, we computed a **statistically-derived transform** directly from the ABIDE data:

```
For each of 4,950 connectivity pairs (100 ROIs × 99 / 2):
    Run independent t-test: ASD group vs TD group
    If p < 0.05: this connection is significantly different

Map significant connections → 100 brain ROIs → 20,484 brain surface vertices
Each vertex gets a scale factor and shift value
```

**Results with 871 ABIDE I subjects:**
- 820 significant connections (16.6% of all pairs, p < 0.05)
- Top affected brain regions:
  1. **Limbic Temporal Pole** (emotional processing) — 1.000
  2. **Limbic Temporal Pole (L)** (emotional processing) — 0.857
  3. **Visual 9 (L)** — 0.551
  4. **Default Mode Temporal 2 (R)** — 0.549
  5. **Default Mode Temporal 2 (L)** — 0.527

These findings align with published autism neuroscience literature:
- Limbic/emotional network differences are well-documented in autism
- Default Mode Network alterations are a hallmark of autism
- Visual processing differences are consistent with sensory sensitivity reports

### How the Transform Works

```python
# For any neurotypical brain prediction from TRIBE v2:
nd_prediction = nt_prediction * vertex_scale + vertex_shift

# Where:
#   vertex_scale ranges from 0.85 to 1.15 (per vertex)
#   vertex_shift ranges from -0.05 to 0.01 (per vertex)
#   18,067 of 20,484 vertices are affected
```

---

## Infrastructure Issues & Resolutions

### Issue 1: No GPU on Azure
- **Problem**: Azure Sponsorship accounts have 0 GPU quota by default
- **Attempted**: Quota increase request → auto-rejected
- **Attempted**: Support ticket → closed without resolution
- **Attempted**: Azure ML compute → same quota applies
- **Resolution**: Used CPU-based statistical approach instead of neural network fine-tuning

### Issue 2: Disk Space (Multiple Times)
- **First time**: 30GB default disk filled with LLaMA 3.2 (6GB) + TRIBE v2 checkpoint (6GB) + packages
  - Resolution: Expanded to 64GB
- **Second time**: 64GB filled with ABIDE data (25GB) + models + packages
  - Resolution: Expanded to 256GB
- **Third time**: ds002345 consuming 60GB, approaching 256GB limit
  - Resolution: Stopped download, used partial data

### Issue 3: Vercel Timeout
- **Problem**: Vercel free tier has 10-second timeout on API routes, brain predictions take 2-5 minutes on CPU
- **Resolution**: Set up HTTPS (nginx + Let's Encrypt) on Azure VM, frontend calls API directly bypassing Vercel proxy

### Issue 4: CORS Issues
- **Problem**: Multiple CORS header sources (nginx + FastAPI both adding headers)
- **Resolution**: Removed CORS headers from nginx, let FastAPI handle it. Added OPTIONS preflight handling in nginx.

### Issue 5: HuggingFace Token Expiration
- **Problem**: Multiple tokens expired during development
- **Resolution**: Created token with "No expiration" setting and write permissions

### Issue 6: Mixed Content (HTTPS/HTTP)
- **Problem**: Vercel serves over HTTPS, Azure VM was HTTP only
- **Resolution**: Installed nginx + certbot on VM for SSL certificate from Let's Encrypt

---

## What's Working Now

### Tab 1: Brain Prediction
- Input: Text sentence
- Process: Text → TTS (gTTS) → WhisperX transcription → LLaMA 3.2 embeddings + Wav2Vec-BERT audio features → TRIBE v2 Transformer → 20,484 vertex brain prediction
- Output: Brain activity images (4 views per timestep), timeline playback, stats
- Interpretation: GPT-5.2 via Azure OpenAI explains what the activation means

### Tab 2: NT vs ND Comparison
- Input: Text sentence
- Process: Same TRIBE v2 pipeline → applies ABIDE-trained transform → generates ND prediction
- Output: Side-by-side brain images (NT green, ND orange), difference analysis table with real-life examples, sensory profile, GPT interpretation
- Data: Based on 403 ASD + 468 TD real brain scans

### Tab 3: ASD Connectivity
- Input: Click "Run Analysis"
- Process: Loads pre-computed connectivity from ABIDE cache
- Output: Network-level bar chart showing which brain networks differ most, GPT interpretation
- Data: Pre-computed and cached to disk (instant load)

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/predict` | POST | Brain prediction from text |
| `/api/predict/video` | POST | Brain prediction from video upload |
| `/api/compare` | POST | NT vs ND comparison |
| `/api/connectivity` | GET | ASD vs TD connectivity analysis |
| `/api/interpret` | POST | GPT-5.2 interpretation of results |

---

## File Structure

```
neurobrain/                          # Web app repo
├── api/
│   ├── main.py                      # FastAPI backend (all endpoints)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                 # Main page (3 tabs)
│   │   └── api/                     # Next.js API routes (proxy)
│   └── src/components/
│       ├── BrainViewer.tsx           # Brain image timeline player
│       ├── BrainComparison.tsx       # NT vs ND difference table
│       ├── SensoryProfile.tsx        # Network divergence bars
│       ├── ConnectivityChart.tsx     # ABIDE connectivity chart
│       ├── Interpretation.tsx        # GPT interpretation display
│       ├── TextInput.tsx             # Input form
│       └── Header.tsx
├── train_neurodiverse.ipynb          # Colab training notebook
├── train_full_abide.py               # ABIDE I full training script
├── retrain_combined.py               # Combined ABIDE + OpenNeuro training
└── PROGRESS.md                       # This file

tribeneuro/                           # Brain model repo (fork of TRIBE v2)
├── tribev2/
│   ├── model.py                      # FmriEncoder (177M params)
│   ├── demo_utils.py                 # TribeModel inference wrapper
│   ├── main.py                       # Training pipeline
│   ├── neurodiverse/                 # Our additions
│   │   ├── download.py               # ABIDE + OpenNeuro downloaders
│   │   ├── resting_state.py          # Connectivity analysis
│   │   └── comparison.py             # NT vs ND comparison tools
│   ├── studies/
│   │   ├── abide.py                  # ABIDE study definition
│   │   └── openneuro_autism.py       # Richardson 2018 study
│   └── grids/
│       └── run_neurodiverse.py       # Fine-tuning config (needs GPU)
└── neurodiverse_colab.ipynb          # Colab demo notebook
```

---

## Current Training Run (In Progress)

**Script**: `retrain_combined.py` running on Azure VM

**What it does**:
1. Extracts connectivity features from all 871 ABIDE I subjects
2. Extracts connectivity from ds000228 (155 Pixar subjects)
3. Extracts connectivity from ds002345 (345 partial Despicable Me subjects)
4. Computes combined statistical transform (~1,371 subjects)
5. Uploads to HuggingFace

**Expected improvement**: More subjects = more significant connections found = more accurate NT→ND transform

---

## Next Steps

### Short Term
- [ ] Complete combined training run (ABIDE + OpenNeuro)
- [ ] Apply for NDA access (10,000+ subjects)
- [ ] Add video upload to frontend
- [ ] Improve brain image contrast/differentiation between NT and ND
- [ ] Add sensory passport feature (personal sensory profile PDF)

### Medium Term
- [ ] Get GPU access (RunPod, Lambda Labs, or Azure quota approval)
- [ ] Fine-tune TRIBE v2 subject layers on autism data (proper neural network training)
- [ ] Add ABIDE II data via manual S3 download
- [ ] Build sensory audit tool (upload video of a space → get accessibility report)

### Long Term
- [ ] Behavioral calibration (10-min video quiz → personalized sensory profile)
- [ ] Connect to smart building systems for adaptive environments
- [ ] Therapy optimization tool (test interventions in simulation)
- [ ] Mobile app for on-the-go sensory assessment

---

## Environment Variables

### Azure VM
```
CUDA_VISIBLE_DEVICES=           # Force CPU mode
AZURE_OPENAI_ENDPOINT=          # Azure OpenAI for interpretations
AZURE_OPENAI_API_KEY=           # (stored on VM, not in code)
AZURE_OPENAI_DEPLOYMENT=gpt-5.2-chat
AZURE_OPENAI_API_VERSION=2025-04-01-preview
```

### Vercel
```
API_URL=http://20.127.80.79:8000   # Azure VM backend
```

### HuggingFace
```
Token: (stored securely, write access, no expiry)
Username: Ibrahim9989
```

---

## Cost Summary

| Resource | Cost | Status |
|----------|------|--------|
| Azure VM (Standard_D8as_v4) | ~$0.38/hr from credits | Running |
| Azure disk (256GB) | ~$10/month from credits | Attached |
| Vercel frontend | Free tier | Running |
| HuggingFace model hosting | Free | Running |
| Azure OpenAI (GPT-5.2) | From credits | Running |
| Let's Encrypt SSL | Free | Active until 2026-06-28 |
| Google Colab | Free (GPU limit hit) | Used for initial experiments |
