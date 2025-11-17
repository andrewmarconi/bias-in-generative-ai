# Quick Start Guide (Diffusers Edition)

Get started quickly with the Bias Detection Framework using HuggingFace diffusers.

## Prerequisites
- Python 3.12+
- CUDA-capable GPU, or CPU (diffusers runs on CPU but slower)
- 8-16 GB RAM (16+ for larger models)
- ~10-20 GB disk space for models and data

## Installation
- uv sync
- Optional: install in editable mode: `pip install -e .`

## Install optional accelerations
- `uv run python -m pip install diffusers transformers accelerate`

## Model Selection (Diffusers)
- Edit `config/experiment_config.yaml` to set the model.

### Quick default (SD2.1)
```
generation:
  model: "stabilityai/stable-diffusion-2-1"
```

### Other options
```
# SD v1.5
model: "runwayml/stable-diffusion-v1-5"

# SDXL high quality
model: "stabilityai/stable-diffusion-xl-base-1.0"

# FLUX or other diffusers variants can be plugged in similarly
```

## Quick Test (5-10 minutes)
1) Edit config to set a small test prompt count:
```
generation:
  num_images_per_prompt: 5
```
2) Run a quick example:
```
uv run python example_usage.py --example 1
```
This will generate a few images, run VQA, and compute statistics.

## Phase-by-Phase Testing
```
uv run python run_experiment.py --phase setup
uv run python run_experiment.py --phase generate
uv run python run_experiment.py --phase analyze
uv run python run_experiment.py --phase statistics
```

## Viewing Results
- MLflow UI: run `mlflow ui` and visit http://localhost:5000
- For tests and quick checks, see data/ for images and results

## Next Steps
- Add more models to `config/experiment_config.yaml` and compare results
- Track experiments in MLflow for reproducibility