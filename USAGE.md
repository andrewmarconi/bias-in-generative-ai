# Usage Guide

## ✅ Setup Verification

First, verify your setup is working:

```bash
uv run python test_setup.py
```

You should see all imports pass and configuration summary.

## 🚀 Running Experiments

### Option 1: Quick Test (Recommended First)

Test with a single prompt to verify everything works:

```bash
# This will generate 5 images for one prompt and analyze them
uv run python example_usage.py --example 1
```

Expected time: ~2-5 minutes (depending on model download)

### Option 2: Full Experiment

Run the complete bias detection pipeline:

```bash
# Full experiment with all prompts
uv run python run_experiment.py
```

With default config (10 images × 17 prompts = 170 images):
- Generation: ~10-20 minutes
- VQA Analysis: ~5-10 minutes
- Statistics: <1 minute
- **Total: ~20-30 minutes**

### Option 3: Phase-by-Phase

Run individual phases separately:

```bash
# Just setup
uv run python run_experiment.py --phase setup

# Just generate images
uv run python run_experiment.py --phase generate

# Just analyze existing images
uv run python run_experiment.py --phase analyze

# Just calculate statistics
uv run python run_experiment.py --phase statistics
```

## 📊 Viewing Results

### Generated Images

```bash
ls data/raw/images/
```

Each image has:
- `*.png` - The generated image
- `*.json` - Metadata (prompt, seed, parameters)

### Analysis Results

```bash
# View analysis JSON
cat data/processed/analysis_results.json | jq . | head -50

# View statistical summary
cat data/results/statistical_summary.json | jq .
```

### Visualizations

```bash
# View summary figure
open data/results/visualizations/summary_figure.png

# View all visualizations
open data/results/visualizations/
```

### MLflow UI

```bash
mlflow ui
# Then open http://localhost:5000
```

## ⚙️ Configuration

Edit `config/experiment_config.yaml`:

### Quick Test Configuration

For fast testing:

```yaml
generation:
  model: "schnell"  # Fastest model
  num_images_per_prompt: 5  # Just a few images
  steps: 4
```

### Production Configuration

For research:

```yaml
generation:
  model: "dev"  # Better quality
  num_images_per_prompt: 50  # Statistical significance
  steps: 4
```

### Model Options

- `schnell` - Fastest (4 steps), good quality
- `dev` - Slower, higher quality
- `krea_dev` - Alternative variant

## 🔍 Interpreting Results

### Example Output

```json
{
  "gender": {
    "chi_square_test": {
      "chi_square_statistic": 156.4,
      "p_value": 0.0001,
      "cramers_v": 0.456,
      "effect_size": "large",
      "significant": true
    }
  }
}
```

### What This Means

- **p-value < 0.05**: Significant bias detected ✓
- **Cramer's V = 0.456**: Large effect size (substantial bias)
- **Significant: true**: Distribution significantly different from uniform

### Effect Size Interpretation

| Cramer's V | Effect Size | Interpretation |
|------------|-------------|----------------|
| < 0.1      | Negligible  | Minimal bias   |
| 0.1 - 0.3  | Small       | Noticeable bias |
| 0.3 - 0.5  | Medium      | Substantial bias |
| > 0.5      | Large       | Very strong bias |

## 🛠️ Troubleshooting

### Models Taking Long to Download

First run will download models (~2-5 GB):
- FLUX.1-schnell: ~2 GB
- BLIP-2: ~5 GB

These are cached locally, subsequent runs are faster.

### Out of Memory

Reduce image count:

```yaml
generation:
  num_images_per_prompt: 5
```

Or reduce resolution:

```yaml
generation:
  width: 512
  height: 512
```

### Import Errors

Always use `uv run`:

```bash
# ✓ Correct
uv run python run_experiment.py

# ✗ Wrong (won't find dependencies)
python run_experiment.py
```

### Permission Errors on macOS

If you get permissions errors with mflux:

```bash
# Ensure you're on Apple Silicon
uname -m  # Should show "arm64"
```

## 📝 Custom Experiments

### Add Your Own Prompts

Edit `config/experiment_config.yaml`:

```yaml
prompts:
  my_category:
    - "Your custom prompt here"
    - "Another custom prompt"
```

### Change VQA Model

Use a larger model for better accuracy:

```yaml
vqa_analysis:
  model: "Salesforce/blip2-flan-t5-xl"  # Larger, more accurate
```

### Add New Bias Categories

```yaml
bias_categories:
  - custom_attribute

vqa_analysis:
  questions:
    custom_attribute:
      question: "What is the perceived X of the person?"
      options: ["option1", "option2", "unclear"]
```

## 🔬 Research Workflow

1. **Pilot Test** (5 images/prompt)
   ```bash
   # Edit config: num_images_per_prompt: 5
   uv run python run_experiment.py
   ```

2. **Review Results**
   ```bash
   open data/results/visualizations/summary_figure.png
   ```

3. **Full Experiment** (50-100 images/prompt)
   ```bash
   # Edit config: num_images_per_prompt: 50
   uv run python run_experiment.py
   ```

4. **Human Validation**
   - Sample images from `data/raw/images/`
   - Have raters classify demographics
   - Compare to VQA results

5. **Report Findings**
   - Use visualizations from `data/results/visualizations/`
   - Include statistical summary
   - Cite methodology from `docs/spec.md`

## 📚 More Examples

```bash
# Run different examples
uv run python example_usage.py --example 1  # Quick test
uv run python example_usage.py --example 3  # Custom prompts
uv run python example_usage.py --example 5  # Visualizations only
```

## 🆘 Getting Help

1. Check `test_setup.py` passes
2. Review `README.md` for detailed docs
3. Examine `docs/spec.md` for methodology
4. Look at `example_usage.py` for code examples

## 💡 Tips

- Start with `schnell` model and 5-10 images for quick tests
- Use MLflow UI to compare different experiment runs
- Save compute: generate images once, run analysis multiple times
- For production: use `dev` model with 50+ images per prompt
