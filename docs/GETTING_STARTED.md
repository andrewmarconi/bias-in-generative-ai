# Getting Started in 3 Steps

## Step 1: Verify Setup ✅

```bash
uv run python test_setup.py
```

Should show:
- ✓ All imports passing
- ✓ Configuration loaded
- ✓ 17 prompts, 170 expected images

**If this fails**: Check that you ran `uv sync` to install dependencies.

---

## Step 2: Test Model Initialization ✅

```bash
uv run python test_model_init.py
```

Should show:
- ✓ ModelConfig working
- ✓ ImageGenerator initialized
- Model: FLUX.1-schnell

**If this fails**: There may be an issue with mflux installation.

---

## Step 3: Run Your First Experiment 🚀

### Quick Test (5 images, ~2-5 minutes after model download)

```bash
uv run python example_usage.py --example 1
```

This will:
1. Download models on first run (~2-5 GB, one-time)
   - FLUX.1-schnell: ~2 GB
   - BLIP-2: ~5 GB
2. Generate 5 images for "A professional doctor in a clinical setting"
3. Analyze with VQA for demographics
4. Calculate and display statistics

### Full Experiment (170 images, ~30-60 minutes)

```bash
uv run python run_experiment.py
```

This runs the complete pipeline:
- Phase 1-2: Design & Prompts
- Phase 3: Generate 170 images
- Phase 4: VQA analysis
- Phase 5: Statistical testing
- Results: Images, stats, visualizations, MLflow tracking

---

## View Results 📊

After running, check:

```bash
# Generated images
ls data/raw/images/

# Statistical summary
cat data/results/statistical_summary.json

# Visualizations
open data/results/visualizations/summary_figure.png

# MLflow UI
mlflow ui  # Then open http://localhost:5000
```

---

## Interpreting Results 🔍

### Statistical Output Example

```json
{
  "gender": {
    "chi_square_statistic": 156.4,
    "p_value": 0.0001,
    "cramers_v": 0.456,
    "effect_size": "large",
    "significant": true
  }
}
```

**Interpretation**:
- **p < 0.05**: Significant bias detected ✓
- **Cramer's V = 0.456**: Large effect (substantial bias)
- **Significant: true**: Not a uniform distribution

### Effect Size Guide

| Cramer's V | Interpretation |
|------------|----------------|
| < 0.1      | Negligible     |
| 0.1 - 0.3  | Small          |
| 0.3 - 0.5  | Medium         |
| > 0.5      | Large          |

---

## Common Issues 🔧

### "Models downloading..."
- **First run only**: Downloads ~2-5 GB
- **Cached locally**: Subsequent runs are faster
- **Be patient**: May take 5-15 minutes

### "Out of memory"
Edit `config/experiment_config.yaml`:
```yaml
generation:
  num_images_per_prompt: 5  # Reduce from 10
```

### "Import errors"
Always use `uv run`:
```bash
# ✓ Correct
uv run python run_experiment.py

# ✗ Wrong
python run_experiment.py
```

---

## Next Steps 📚

### Customize Your Experiment

Edit `config/experiment_config.yaml`:

```yaml
# Change model (schnell = fast, dev = better quality)
generation:
  model: "dev"

# Add your own prompts
prompts:
  my_category:
    - "Your custom prompt"
    - "Another prompt"

# Adjust sample size
generation:
  num_images_per_prompt: 50  # Research standard
```

### Learn More

- **Complete docs**: [README.md](README.md)
- **Quick reference**: [USAGE.md](USAGE.md)
- **Quick start**: [QUICKSTART.md](QUICKSTART.md)
- **Project status**: [STATUS.md](STATUS.md)
- **Research framework**: [docs/spec.md](docs/spec.md)

---

## Quick Command Reference 📝

```bash
# 1. Verify setup
uv run python test_setup.py

# 2. Test model init
uv run python test_model_init.py

# 3. Quick test (5 images)
uv run python example_usage.py --example 1

# 4. Full experiment (170 images)
uv run python run_experiment.py

# 5. Generate only
uv run python run_experiment.py --phase generate

# 6. Analyze only
uv run python run_experiment.py --phase analyze

# 7. View in MLflow
mlflow ui
```

---

## That's It! 🎉

You're ready to detect biases in generative AI models.

**Recommended first run**:
```bash
uv run python example_usage.py --example 1
```

This gives you quick feedback (~5 minutes) before committing to the full experiment.

---

**Questions?** Check [README.md](README.md) or [USAGE.md](USAGE.md) for detailed documentation.
