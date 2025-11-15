"""
Main experiment runner for bias detection framework.

Orchestrates all phases of the bias detection pipeline.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bias_detector.utils.config import load_config, validate_config
from bias_detector.generation.image_generator import ImageGenerator
from bias_detector.analysis.vqa_analyzer import VQAAnalyzer
from bias_detector.statistics.bias_metrics import BiasMetrics
from bias_detector.utils.mlflow_tracker import MLflowTracker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BiasDetectionExperiment:
    """
    Main experiment orchestrator for bias detection in generative AI.

    Implements the complete research framework from Phase 1 through Phase 10.
    """

    def __init__(self, config_path: str = "config/experiment_config.yaml"):
        """
        Initialize experiment.

        Args:
            config_path: Path to experiment configuration file
        """
        logger.info("=" * 80)
        logger.info("Bias Detection Framework for Generative AI Image Models")
        logger.info("=" * 80)

        # Load and validate configuration
        self.config = load_config(config_path)
        validate_config(self.config)

        logger.info(f"Experiment: {self.config['experiment']['name']}")
        logger.info(f"Description: {self.config['experiment']['description']}")

        # Initialize components
        self.generator = None
        self.analyzer = None
        self.metrics = None
        self.tracker = None

        # Results storage
        self.generation_results = {}
        self.analysis_results = []
        self.statistical_summary = {}

    def setup(self):
        """Initialize all experiment components."""
        logger.info("\n" + "=" * 80)
        logger.info("Setting up experiment components...")
        logger.info("=" * 80)

        # Initialize image generator
        logger.info("\n[1/4] Initializing Image Generator (mflux)...")
        self.generator = ImageGenerator(self.config)

        # Initialize VQA analyzer
        logger.info("\n[2/4] Initializing VQA Analyzer...")
        self.analyzer = VQAAnalyzer(self.config)

        # Initialize statistical metrics
        logger.info("\n[3/4] Initializing Statistical Analysis...")
        self.metrics = BiasMetrics(self.config)

        # Initialize MLflow tracker
        logger.info("\n[4/4] Initializing MLflow Tracker...")
        self.tracker = MLflowTracker(self.config)

        logger.info("\nSetup complete!")

    def run_phase_1_design(self):
        """
        Phase 1: Experimental Design and Setup

        Log experimental design decisions.
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: Experimental Design and Setup")
        logger.info("=" * 80)

        logger.info(f"Primary Hypothesis: Text-to-image models exhibit statistically "
                   f"significant demographic biases")
        logger.info(f"Bias Categories: {', '.join(self.config['bias_categories'])}")
        logger.info(f"Sample Size: {self.config['generation']['num_images_per_prompt']} "
                   f"images per prompt")
        logger.info(f"Significance Level: α = {self.config['statistics']['significance_level']}")

    def run_phase_2_prompts(self):
        """
        Phase 2: Prompt Engineering

        Display and validate prompts.
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: Prompt Engineering Strategy")
        logger.info("=" * 80)

        total_prompts = sum(len(prompts) for prompts in self.config['prompts'].values())
        logger.info(f"Total prompts: {total_prompts}")

        for category, prompts in self.config['prompts'].items():
            logger.info(f"\n{category.upper()} ({len(prompts)} prompts):")
            for i, prompt in enumerate(prompts, 1):
                logger.info(f"  {i}. {prompt}")

    def run_phase_3_generation(self):
        """
        Phase 3: Image Generation Protocol

        Generate images using mflux.
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: Image Generation Protocol")
        logger.info("=" * 80)

        logger.info(f"Model: FLUX.1-{self.config['generation']['model']}")
        logger.info(f"Images per prompt: {self.config['generation']['num_images_per_prompt']}")
        logger.info(f"Seed strategy: {self.config['generation']['seed_strategy']}")
        logger.info("\nGenerating images...")

        self.generation_results = self.generator.generate_for_all_prompts()

        total_images = sum(len(results) for results in self.generation_results.values())
        logger.info(f"\nGeneration complete! Total images: {total_images}")

        # Log to MLflow
        if self.tracker:
            self.tracker.log_generation_results(self.generation_results)

    def run_phase_4_analysis(self):
        """
        Phase 4: Image Analysis using VQA

        Analyze images for demographic characteristics.
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 4: Image Analysis - VQA Pipeline")
        logger.info("=" * 80)

        logger.info(f"VQA Model: {self.config['vqa_analysis']['model']}")
        logger.info(f"Analyzing {len(self.config['vqa_analysis']['questions'])} demographic categories")

        # Flatten all image metadata
        all_images = []
        for results in self.generation_results.values():
            all_images.extend(results)

        logger.info(f"\nAnalyzing {len(all_images)} images...")

        # Analyze all images
        self.analysis_results = self.analyzer.analyze_batch(all_images)

        logger.info(f"Analysis complete!")

        # Save results
        self.analyzer.save_results(
            self.analysis_results,
            "data/processed/analysis_results.json"
        )

        # Log to MLflow
        if self.tracker:
            self.tracker.log_analysis_results(self.analysis_results)

    def run_phase_5_statistics(self):
        """
        Phase 5: Statistical Analysis and Bias Quantification

        Calculate statistical metrics and test hypotheses.
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 5: Statistical Analysis and Bias Quantification")
        logger.info("=" * 80)

        logger.info("Calculating statistical metrics...")

        # Generate comprehensive summary
        self.statistical_summary = self.metrics.generate_summary_report(
            self.analysis_results
        )

        # Display key findings
        logger.info("\n" + "-" * 80)
        logger.info("KEY FINDINGS")
        logger.info("-" * 80)

        for category, analysis in self.statistical_summary['bias_analyses'].items():
            logger.info(f"\n{category.upper()}:")
            logger.info(f"  Sample size: {analysis['sample_size']}")

            chi_square = analysis['chi_square_test']
            logger.info(f"  χ² = {chi_square['chi_square_statistic']:.2f}, "
                       f"p = {chi_square['p_value']:.4f}")
            logger.info(f"  Cramer's V = {chi_square['cramers_v']:.3f} "
                       f"({chi_square['effect_size']})")
            logger.info(f"  Significant: {'YES' if chi_square['significant'] else 'NO'}")

            parity = analysis['demographic_parity']
            logger.info(f"  Max deviation from uniform: {parity['max_deviation']:.3f}")
            logger.info(f"  Demographic parity: {'SATISFIED' if parity['parity_satisfied'] else 'VIOLATED'}")

        # Save statistical summary
        import json
        stats_path = Path("data/results/statistical_summary.json")
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        with open(stats_path, 'w') as f:
            json.dump(self.statistical_summary, f, indent=2)

        logger.info(f"\nStatistical summary saved to {stats_path}")

        # Log to MLflow
        if self.tracker:
            self.tracker.log_statistical_results(self.statistical_summary)

    def run_phase_6_counterfactual(self):
        """
        Phase 6: Counterfactual Analysis

        Generate and analyze counterfactual images with explicit demographics.
        """
        if not self.config.get('counterfactual', {}).get('enabled', False):
            logger.info("\nPhase 6: Counterfactual Analysis - SKIPPED (disabled in config)")
            return

        logger.info("\n" + "=" * 80)
        logger.info("PHASE 6: Counterfactual and Sensitivity Analysis")
        logger.info("=" * 80)

        logger.info("Counterfactual analysis not yet implemented in this run.")
        # TODO: Implement counterfactual generation and analysis

    def run_full_experiment(self):
        """Run the complete experiment pipeline."""
        try:
            # Start MLflow run
            if self.tracker:
                self.tracker.start_run()
                self.tracker.log_configuration()

            # Run all phases
            self.run_phase_1_design()
            self.run_phase_2_prompts()
            self.run_phase_3_generation()
            self.run_phase_4_analysis()
            self.run_phase_5_statistics()
            self.run_phase_6_counterfactual()

            logger.info("\n" + "=" * 80)
            logger.info("EXPERIMENT COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Total images generated: {sum(len(r) for r in self.generation_results.values())}")
            logger.info(f"Total images analyzed: {len(self.analysis_results)}")
            logger.info(f"Results saved to: data/results/")

            if self.tracker:
                logger.info(f"MLflow tracking: {self.config['mlflow']['tracking_uri']}")

        except Exception as e:
            logger.error(f"Experiment failed: {e}", exc_info=True)
            raise

        finally:
            # End MLflow run
            if self.tracker:
                self.tracker.end_run()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Bias Detection Framework for Generative AI Image Models"
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/experiment_config.yaml',
        help='Path to experiment configuration file'
    )
    parser.add_argument(
        '--phase',
        type=str,
        choices=['all', 'setup', 'generate', 'analyze', 'statistics'],
        default='all',
        help='Which phase to run'
    )

    args = parser.parse_args()

    # Create and run experiment
    experiment = BiasDetectionExperiment(config_path=args.config)
    experiment.setup()

    if args.phase == 'all':
        experiment.run_full_experiment()
    elif args.phase == 'setup':
        logger.info("Setup complete!")
    elif args.phase == 'generate':
        experiment.run_phase_1_design()
        experiment.run_phase_2_prompts()
        experiment.run_phase_3_generation()
    elif args.phase == 'analyze':
        experiment.run_phase_4_analysis()
    elif args.phase == 'statistics':
        experiment.run_phase_5_statistics()


if __name__ == "__main__":
    main()
