# Getting Started

A concise, practical guide to verify setup and run your first experiment.

## Step 1: Verify Setup
- Run: `uv run python test_setup.py`.
- Expected: all imports pass, configuration loads, and a summary showing prompts and images.
- If this fails: run `uv sync` to install dependencies.

---

## Step 2: Test Model Initialization
- Run: `uv run python test_model_init.py`.
- Expected: ModelConfig works, ImageGenerator initializes, and the model is listed (e.g. FLUX.1-schnell).
- If this fails: ensure mflux is installed correctly.

---

## Step 3: Run Your First Experiment
### Quick Test (5 images)
- Run: `uv run python example_usage.py --example 1`.
- This will download models (roughly 2-5 GB, one-time), generate 5 images for a simple prompt, analyze with VQA, and compute statistics.

### Full Experiment (170 images)
- Run: `uv run python run_experiment.py`.
- This runs the full bias-detection pipeline across prompts, images, analyses, and visualizations.

---

## View Results
- Generated images: `ls data/raw/images/`
- Statistical summary: `cat data/results/statistical_summary.json`
- Visualizations: `open data/results/visualizations/summary_figure.png`
- MLflow UI: `mlflow ui` (open http://localhost:5000)

---

## Interpreting Results
- Sample outputs show chi-square, p-values and effect sizes to indicate bias.
- Example JSON:

```
{
  "gender": {
    "chi_square_statistic": 156.4,
    "p_value": 0.0001,
    "cramers_v": 0.456,
    "significant": true
  }
}
```

---

## Common Issues
- Models downloading: first run may download ~2-5 GB; subsequent runs faster.
- Out of memory: reduce the number of images per prompt or resolution in the config.
- Import errors: always run with `uv run`.

---

## Next Steps
- Customize prompts in `config/experiment_config.yaml`.
- Try different models (dev, schnell, etc.).
- Explore MLflow for experiment tracking.