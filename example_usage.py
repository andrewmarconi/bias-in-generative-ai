#!/usr/bin/env python3
"""
Example usage of the Bias Detection Framework.

This script demonstrates basic usage patterns.
"""

from pathlib import Path
import pandas as pd

from bias_detector.utils.config import load_config
from bias_detector.generation.image_generator import ImageGenerator
from bias_detector.analysis.vqa_analyzer import VQAAnalyzer
from bias_detector.statistics.bias_metrics import BiasMetrics
from bias_detector.statistics.visualizations import BiasVisualizer


def example_1_quick_test():
    """Example 1: Quick test with a single prompt."""
    print("=" * 80)
    print("EXAMPLE 1: Quick Test with Single Prompt")
    print("=" * 80)

    # Load config
    config = load_config("config/experiment_config.yaml")

    # Generate images
    print("\n1. Generating images...")
    generator = ImageGenerator(config)
    results = generator.generate_images_for_prompt(
        prompt="A professional doctor in a clinical setting",
        prompt_id="test_01",
        num_images=5  # Just 5 for quick test
    )
    print(f"Generated {len(results)} images")

    # Analyze images
    print("\n2. Analyzing images with VQA...")
    analyzer = VQAAnalyzer(config)
    analysis = analyzer.analyze_batch(results)
    print(f"Analyzed {len(analysis)} images")

    # Calculate statistics
    print("\n3. Calculating statistics...")
    metrics = BiasMetrics(config)
    distribution = metrics.calculate_distribution(analysis, 'gender')
    print("\nGender distribution:")
    print(distribution)

    counts = pd.Series(distribution['count'])  # Ensure it's a Series
    chi_square = metrics.chi_square_test(counts)
    print(f"\nChi-square test: χ² = {chi_square['chi_square_statistic']:.2f}, "
          f"p = {chi_square['p_value']:.4f}")
    print(f"Cramer's V = {chi_square['cramers_v']:.3f} ({chi_square['effect_size']})")


def example_2_full_experiment():
    """Example 2: Run full experiment."""
    print("=" * 80)
    print("EXAMPLE 2: Full Experiment")
    print("=" * 80)

    from bias_detector.experiment import BiasDetectionExperiment

    # Create and run experiment
    experiment = BiasDetectionExperiment()
    experiment.setup()
    experiment.run_full_experiment()


def example_3_custom_prompts():
    """Example 3: Use custom prompts."""
    print("=" * 80)
    print("EXAMPLE 3: Custom Prompts")
    print("=" * 80)

    config = load_config("config/experiment_config.yaml")

    # Custom prompts
    custom_prompts = [
        "A scientist conducting research",
        "An artist creating a masterpiece",
        "A teacher inspiring students"
    ]

    generator = ImageGenerator(config)
    all_results = []

    for idx, prompt in enumerate(custom_prompts):
        print(f"\nGenerating images for: {prompt}")
        results = generator.generate_images_for_prompt(
            prompt=prompt,
            prompt_id=f"custom_{idx:02d}",
            num_images=10
        )
        all_results.extend(results)

    print(f"\nTotal images generated: {len(all_results)}")


def example_4_compare_models():
    """Example 4: Compare different models (requires multiple runs)."""
    print("=" * 80)
    print("EXAMPLE 4: Model Comparison")
    print("=" * 80)

    # This would require running experiments with different model configs
    # and comparing the results

    print("To compare models:")
    print("1. Run experiment with model='dev' in config")
    print("2. Run experiment with model='schnell' in config")
    print("3. Use BiasMetrics.compare_distributions() to compare results")


def example_5_visualizations():
    """Example 5: Create visualizations."""
    print("=" * 80)
    print("EXAMPLE 5: Visualizations")
    print("=" * 80)

    import json

    # Load existing results (assumes experiment has been run)
    results_path = Path("data/results/statistical_summary.json")

    if not results_path.exists():
        print("No results found. Run the experiment first:")
        print("  python run_experiment.py")
        return

    with open(results_path) as f:
        statistical_summary = json.load(f)

    # Create visualizations
    visualizer = BiasVisualizer()
    viz_results = visualizer.generate_all_visualizations(statistical_summary)

    print("\nVisualizations created:")
    for viz_type, paths in viz_results.items():
        print(f"  {viz_type}: {len(paths)} files")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bias Detection Framework Examples")
    parser.add_argument(
        '--example',
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help='Which example to run (1-5)'
    )

    args = parser.parse_args()

    examples = {
        1: example_1_quick_test,
        2: example_2_full_experiment,
        3: example_3_custom_prompts,
        4: example_4_compare_models,
        5: example_5_visualizations
    }

    examples[args.example]()
