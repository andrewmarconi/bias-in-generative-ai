#!/usr/bin/env python3
"""
Test that the basic setup works without loading models.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing imports...")

try:
    from bias_detector.utils.config import load_config, validate_config
    print("✓ Config utilities")

    from bias_detector.generation.image_generator import ImageGenerator
    print("✓ ImageGenerator")

    from bias_detector.analysis.vqa_analyzer import VQAAnalyzer
    print("✓ VQAAnalyzer")

    from bias_detector.statistics.bias_metrics import BiasMetrics
    print("✓ BiasMetrics")

    from bias_detector.statistics.visualizations import BiasVisualizer
    print("✓ BiasVisualizer")

    from bias_detector.utils.mlflow_tracker import MLflowTracker
    print("✓ MLflowTracker")

    print("\nLoading configuration...")
    config = load_config("config/experiment_config.yaml")
    validate_config(config)
    print("✓ Configuration loaded and validated")

    print("\nConfiguration Summary:")
    print(f"  Experiment: {config['experiment']['name']}")
    print(f"  Model: FLUX.1-{config['generation']['model']}")
    print(f"  Images per prompt: {config['generation']['num_images_per_prompt']}")
    print(f"  VQA Model: {config['vqa_analysis']['model']}")
    print(f"  Bias categories: {', '.join(config['bias_categories'])}")

    num_prompts = sum(len(prompts) for prompts in config['prompts'].values())
    total_images = num_prompts * config['generation']['num_images_per_prompt']
    print(f"  Total prompts: {num_prompts}")
    print(f"  Expected images: {total_images}")

    print("\n✅ All tests passed! Setup is working correctly.")
    print("\nNext steps:")
    print("  1. Test model initialization: uv run python test_model_init.py")
    print("  2. Run a quick test: uv run python example_usage.py --example 1")
    print("  3. Run full experiment: uv run python run_experiment.py")
    print("\nNote: First run will download model weights (~2-5 GB) which may take time.")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
