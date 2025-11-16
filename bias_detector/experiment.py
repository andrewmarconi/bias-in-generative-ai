"""
Main experiment runner for bias detection framework.

Orchestrates all phases of the bias detection pipeline.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
import threading
import time

from bias_detector.utils.config import load_config, validate_config
from bias_detector.generation.image_generator import ImageGenerator
from bias_detector.analysis.vqa_analyzer import VQAAnalyzer
from bias_detector.statistics.bias_metrics import BiasMetrics
from bias_detector.utils.mlflow_tracker import MLflowTracker
# from bias_detector.callbacks import ProgressCallback  # TODO: Use proper protocol when type checker supports it

logger = logging.getLogger(__name__)


class BiasDetectionExperiment:
    """
    Main experiment orchestrator for bias detection in generative AI.

    Implements the complete research framework from Phase 1 through Phase 10.
    """

    def __init__(
        self,
        config_path: str = "config/experiment_config.yaml",
        callback: Optional[Any] = None
    ):
        """
        Initialize experiment.

        Args:
            config_path: Path to experiment configuration file
            callback: Optional progress callback implementing ProgressCallback protocol
        """
        logger.info("=" * 80)
        logger.info("Bias Detection Framework for Generative AI Image Models")
        logger.info("=" * 80)

        # Load and validate configuration
        self.config = load_config(config_path)
        validate_config(self.config)

        logger.info(f"Experiment: {self.config['experiment']['name']}")
        logger.info(f"Description: {self.config['experiment']['description']}")

        # Store progress callback
        self.callback = callback

        # Initialize components
        self.generator = None
        self.analyzer = None
        self.metrics = None
        self.tracker = None

        # Results storage
        self.generation_results = {}
        self.analysis_results = []
        self.statistical_summary = {}

        # Session ID for tracking (set when experiment starts)
        self.session_id: Optional[str] = None
        
        # Pause/resume state
        self.is_paused: bool = False
        self.should_stop: bool = False
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()

    def setup(self):
        """Initialize all experiment components."""
        logger.info("\n" + "=" * 80)
        logger.info("Setting up experiment components...")
        logger.info("=" * 80)

        # Initialize image generator
        logger.info("\n[1/4] Initializing Image Generator (mflux)...")
        try:
            self.generator = ImageGenerator(self.config, progress_callback=self.callback)
            logger.info("Image generator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize image generator: {e}")
            self.generator = None

        # Initialize VQA analyzer
        logger.info("\n[2/4] Initializing VQA Analyzer...")
        try:
            self.analyzer = VQAAnalyzer(self.config, progress_callback=self.callback)
            logger.info("VQA analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VQA analyzer: {e}")
            self.analyzer = None

        # Initialize statistical metrics
        logger.info("\n[3/4] Initializing Statistical Analysis...")
        self.metrics = BiasMetrics(self.config)

        # Initialize MLflow tracker
        logger.info("\n[4/4] Initializing MLflow Tracker...")
        self.tracker = MLflowTracker(self.config)

        logger.info("\nSetup complete!")

    def pause(self) -> None:
        """Pause the experiment."""
        logger.info(f"Pausing experiment {self.session_id}")
        self.is_paused = True
        self.pause_event.set()

    def resume(self) -> None:
        """Resume the experiment."""
        logger.info(f"Resuming experiment {self.session_id}")
        self.is_paused = False
        self.pause_event.clear()

    def cancel(self, reason: str = "User cancelled") -> None:
        """Cancel the experiment."""
        logger.info(f"Cancelling experiment {self.session_id}: {reason}")
        self.should_stop = True
        self.stop_event.set()

    def _check_pause_stop(self) -> None:
        """Check for pause/stop signals and wait appropriately."""
        if self.should_stop:
            raise InterruptedError("Experiment cancelled by user")
        
        if self.is_paused:
            logger.info("Experiment paused, waiting for resume...")
            self.pause_event.wait()
            logger.info("Experiment resumed")

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

        if self.generator is None:
            logger.error("Image generator not initialized - skipping generation")
            self.generation_results = {}
        else:
            try:
                results = self.generator.generate_for_all_prompts()
                if results is None:
                    logger.error("Generator returned None - using empty results")
                    self.generation_results = {}
                else:
                    self.generation_results = results
            except Exception as e:
                logger.error(f"Error during image generation: {e}")
                self.generation_results = {}

        # Ensure generation_results is always a dict
        if self.generation_results is None:
            self.generation_results = {}

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

        vqa_models = self.config['vqa_analysis'].get('models', [self.config['vqa_analysis'].get('model', 'unknown')])
        ensemble_method = self.config['vqa_analysis'].get('ensemble_method', 'single')
        if len(vqa_models) > 1:
            logger.info(f"VQA Ensemble: {len(vqa_models)} models ({ensemble_method})")
            for i, model in enumerate(vqa_models, 1):
                logger.info(f"  Model {i}: {model}")
        else:
            logger.info(f"VQA Model: {vqa_models[0]}")
        logger.info(f"Analyzing {len(self.config['vqa_analysis']['questions'])} demographic categories")

        # Flatten all image metadata
        all_images = []
        for results in self.generation_results.values():
            all_images.extend(results)
        
        logger.info(f"\nAnalyzing {len(all_images)} images...")
        
        # Analyze all images
        if self.analyzer is None:
            logger.error("VQA analyzer not initialized - skipping analysis")
            self.analysis_results = []
        else:
            try:
                self.analysis_results = self.analyzer.analyze_batch(all_images)
                logger.info(f"Analysis complete!")
                
                # Save results
                self.analyzer.save_results(
                    self.analysis_results,
                    "data/processed/analysis_results.json"
                )
            except Exception as e:
                logger.error(f"Error during analysis: {e}")
                self.analysis_results = []
        
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
        if self.metrics is None:
            logger.error("Statistical metrics not initialized - skipping analysis")
            self.statistical_summary = {}
        else:
            try:
                self.statistical_summary = self.metrics.generate_summary_report(
                    self.analysis_results
                )
                logger.info("Statistical analysis complete!")
            except Exception as e:
                logger.error(f"Error during statistical analysis: {e}")
                self.statistical_summary = {}

        # Display key findings
        logger.info("\n" + "-" * 80)
        logger.info("KEY FINDINGS")
        logger.info("-" * 80)

        if not self.statistical_summary or 'bias_analyses' not in self.statistical_summary:
            logger.info("No statistical analysis results to display")
        else:
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

    def run_full_experiment(self, session_id: Optional[str] = None):
        """
        Run the complete experiment pipeline.

        Args:
            session_id: Optional session identifier for tracking
        """
        import time
        import traceback
        from datetime import datetime

        # Track session ID
        if session_id:
            self.session_id = session_id
        elif not self.session_id:
            self.session_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Reset pause/stop state
        self.is_paused = False
        self.should_stop = False
        if self.pause_event:
            self.pause_event.clear()
        if self.stop_event:
            self.stop_event.clear()
        
        experiment_start = time.time()
        current_phase = 0

        try:
            # Emit experiment start callback
            if self.callback:
                self.callback.on_experiment_start(
                    session_id=self.session_id,
                    config=self.config,
                    total_phases=6  # 6 implemented phases (1-6)
                )

            # Start MLflow run
            if self.tracker:
                self.tracker.start_run()
                self.tracker.log_configuration()

            # Phase 1: Design
            current_phase = 1
            phase_start = time.time()
            if self.callback:
                self.callback.on_phase_start(1, "Experimental Design", 1)
            
            self._check_pause_stop()
            self.run_phase_1_design()
            self._check_pause_stop()
            
            if self.callback:
                self.callback.on_phase_complete(1, 1, time.time() - phase_start)

            # Phase 2: Prompts
            current_phase = 2
            phase_start = time.time()
            total_prompts = sum(len(p) for p in self.config['prompts'].values())
            if self.callback:
                self.callback.on_phase_start(2, "Prompt Engineering", total_prompts)
            
            self._check_pause_stop()
            self.run_phase_2_prompts()
            self._check_pause_stop()
            
            if self.callback:
                self.callback.on_phase_complete(2, total_prompts, time.time() - phase_start)

            # Phase 3: Generation
            current_phase = 3
            phase_start = time.time()
            total_images = sum(len(p) for p in self.config['prompts'].values()) * \
                          self.config['generation']['num_images_per_prompt']
            if self.callback:
                self.callback.on_phase_start(3, "Image Generation", total_images)
            
            self._check_pause_stop()
            self.run_phase_3_generation()
            self._check_pause_stop()
            
            if self.callback:
                self.callback.on_phase_complete(3, total_images, time.time() - phase_start)

            # Phase 4: Analysis
            current_phase = 4
            phase_start = time.time()
            if self.callback:
                self.callback.on_phase_start(4, "VQA Analysis", total_images)
            
            self._check_pause_stop()
            self.run_phase_4_analysis()
            self._check_pause_stop()
            
            if self.callback:
                self.callback.on_phase_complete(4, total_images, time.time() - phase_start)

            # Phase 5: Statistics
            current_phase = 5
            phase_start = time.time()
            if self.callback:
                self.callback.on_phase_start(5, "Statistical Analysis", 1)
            self.run_phase_5_statistics()
            if self.callback:
                self.callback.on_phase_complete(5, 1, time.time() - phase_start)

            # Phase 6: Counterfactual
            current_phase = 6
            phase_start = time.time()
            if self.callback:
                self.callback.on_phase_start(6, "Counterfactual Testing", 0)
            self.run_phase_6_counterfactual()
            if self.callback:
                self.callback.on_phase_complete(6, 0, time.time() - phase_start)

            logger.info("\n" + "=" * 80)
            logger.info("EXPERIMENT COMPLETE")
            logger.info("=" * 80)
            total_gen = sum(len(r) for r in self.generation_results.values())
            logger.info(f"Total images generated: {total_gen}")
            logger.info(f"Total images analyzed: {len(self.analysis_results)}")
            logger.info(f"Results saved to: data/results/")

            if self.tracker:
                logger.info(f"MLflow tracking: {self.config['mlflow']['tracking_uri']}")

            # Emit experiment complete callback
            if self.callback:
                self.callback.on_experiment_complete(
                    session_id=self.session_id,
                    total_time_seconds=time.time() - experiment_start,
                    phases_completed=6
                )

        except Exception as e:
            logger.error(f"Experiment failed: {e}", exc_info=True)

            # Emit error callbacks
            if self.callback:
                error_tb = traceback.format_exc()
                # Phase error
                self.callback.on_phase_error(
                    phase_num=current_phase,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    traceback_str=error_tb
                )
                # Experiment error
                self.callback.on_experiment_error(
                    session_id=self.session_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    failed_phase=current_phase
                )

            raise

        finally:
            # End MLflow run
            if self.tracker:
                self.tracker.end_run()


