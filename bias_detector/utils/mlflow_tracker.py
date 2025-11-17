"""
MLflow experiment tracking integration.

Implements Phase 8 of the research framework: Documentation and Reproducibility.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import mlflow
from mlflow import log_metric, log_param, log_artifact, log_dict
import json

logger = logging.getLogger(__name__)


class MLflowTracker:
    """
    Track experiments using MLflow for reproducibility.

    Implements systematic experiment tracking with version control
    as specified in the research framework (Phase 8).
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MLflow tracker.

        Args:
            config: Experiment configuration dictionary
        """
        self.config = config
        self.mlflow_config = config.get('mlflow', {})

        # Set up MLflow
        tracking_uri = self.mlflow_config.get('tracking_uri', 'sqlite:///mlflow.db')
        mlflow.set_tracking_uri(tracking_uri)

        experiment_name = self.mlflow_config.get('experiment_name', 'bias_detection')
        self.experiment_name = experiment_name
        try:
            # Try to get existing experiment and activate it
            self.experiment = mlflow.get_experiment_by_name(experiment_name)
            if self.experiment is None:
                self.experiment_id = mlflow.create_experiment(experiment_name)
            else:
                self.experiment_id = self.experiment.experiment_id
            # Activate the experiment for runs
            try:
                mlflow.set_experiment(experiment_name)
            except TypeError:
                # Fallback for older mlflow versions that take id instead of name
                pass
        except Exception as e:
            logger.warning(f"Could not set up experiment: {e}")
            self.experiment_id = None
            self.experiment_name = experiment_name
 
        logger.info(f"MLflow tracking initialized: {tracking_uri}")
 
    def start_run(self, run_name: Optional[str] = None) -> str:
        """
        Start a new MLflow run.
 
        Args:
            run_name: Optional name for the run
 
        Returns:
            Run ID
        """
        if run_name is None:
            run_name = self.config['experiment']['name']
 
        try:
            if self.experiment_id is not None:
                mlflow.start_run(experiment_id=self.experiment_id, run_name=run_name)
            else:
                mlflow.start_run(run_name=run_name)
            run_id = mlflow.active_run().info.run_id
            logger.info(f"Started MLflow run: {run_id}")
            return run_id
        except Exception as e:
            logger.error(f"Failed to start MLflow run with explicit experiment: {e}")
            # Fallback to a run without explicit experiment linkage
            mlflow.start_run(run_name=run_name)
            active = mlflow.active_run()
            if active is not None:
                run_id = active.info.run_id
                logger.info(f"Started MLflow run (fallback): {run_id}")
                return run_id
            else:
                logger.error("Unable to start MLflow run at all")
                raise

        else:
            logger.error("Failed to start MLflow run")
            raise RuntimeError("Could not start MLflow run")

    def log_configuration(self):
        """Log experiment configuration parameters."""
        # Log experiment metadata
        log_param("experiment_name", self.config['experiment']['name'])
        log_param("description", self.config['experiment']['description'])
        log_param("random_seed", self.config['experiment']['random_seed'])

        # Log generation parameters
        gen_config = self.config['generation']
        log_param("model", gen_config['model'])
        log_param("num_images_per_prompt", gen_config['num_images_per_prompt'])
        log_param("steps", gen_config.get('steps', 4))
        log_param("guidance_scale", gen_config.get('guidance_scale', 3.5))
        log_param("seed_strategy", gen_config.get('seed_strategy', 'fixed'))

        # Log VQA model(s) - handle both single model and ensemble
        vqa_models = self.config['vqa_analysis'].get('models', [self.config['vqa_analysis'].get('model', 'unknown')])
        if len(vqa_models) > 1:
            log_param("vqa_ensemble", True)
            log_param("vqa_models", ",".join(vqa_models))
            log_param("ensemble_method", self.config['vqa_analysis'].get('ensemble_method', 'majority_vote'))
        else:
            log_param("vqa_ensemble", False)
            log_param("vqa_model", vqa_models[0])

        # Log bias categories
        log_param("bias_categories", ",".join(self.config['bias_categories']))

        # Log full config as artifact
        config_path = Path("data/processed/run_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        log_artifact(str(config_path))

        logger.info("Configuration logged to MLflow")

    def log_generation_results(
        self,
        generation_results: Dict[str, List[Dict[str, Any]]]
    ):
        """
        Log image generation results.

        Args:
            generation_results: Dictionary of generation results by prompt
        """
        total_images = sum(len(results) for results in generation_results.values())
        log_metric("total_images_generated", total_images)
        log_metric("num_prompts", len(generation_results))

        # Log sample images if configured
        if self.mlflow_config.get('log_images', True):
            max_images = self.mlflow_config.get('max_images_logged', 10)
            count = 0

            for prompt_id, results in generation_results.items():
                for result in results[:max_images]:
                    image_path = result['image_path']
                    if Path(image_path).exists():
                        mlflow.log_artifact(image_path, f"sample_images/{prompt_id}")
                        count += 1
                        if count >= max_images:
                            break
                if count >= max_images:
                    break

            logger.info(f"Logged {count} sample images to MLflow")

        # Save generation metadata
        metadata_path = Path("data/processed/generation_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(generation_results, f, indent=2)
        log_artifact(str(metadata_path))

    def log_analysis_results(
        self,
        analysis_results: List[Dict[str, Any]]
    ):
        """
        Log VQA analysis results.

        Args:
            analysis_results: List of analysis results
        """
        log_metric("total_images_analyzed", len(analysis_results))

        # Save analysis results
        results_path = Path("data/processed/analysis_results.json")
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with open(results_path, 'w') as f:
            json.dump(analysis_results, f, indent=2)
        log_artifact(str(results_path))

        logger.info("Analysis results logged to MLflow")

    def log_statistical_results(
        self,
        statistical_summary: Dict[str, Any]
    ):
        """
        Log statistical analysis results.

        Args:
            statistical_summary: Dictionary with statistical summary
        """
        # Log metrics for each bias category
        for category, analysis in statistical_summary.get('bias_analyses', {}).items():
            prefix = f"{category}_"

            # Log chi-square test results
            chi_square = analysis.get('chi_square_test', {})
            log_metric(f"{prefix}chi_square_stat", chi_square.get('chi_square_statistic', 0))
            log_metric(f"{prefix}p_value", chi_square.get('p_value', 1))
            log_metric(f"{prefix}cramers_v", chi_square.get('cramers_v', 0))

            # Log demographic parity
            parity = analysis.get('demographic_parity', {})
            log_metric(f"{prefix}max_deviation", parity.get('max_deviation', 0))
            log_metric(f"{prefix}tvd", parity.get('total_variation_distance', 0))

        # Save full statistical summary
        stats_path = Path("data/results/statistical_summary.json")
        stats_path.parent.mkdir(parents=True, exist_ok=True)
        with open(stats_path, 'w') as f:
            json.dump(statistical_summary, f, indent=2)
        log_artifact(str(stats_path))

        logger.info("Statistical results logged to MLflow")

    def log_visualizations(self, viz_dir: str = "data/results/visualizations"):
        """
        Log visualization artifacts.

        Args:
            viz_dir: Directory containing visualizations
        """
        viz_path = Path(viz_dir)
        if viz_path.exists():
            for viz_file in viz_path.glob("*.png"):
                mlflow.log_artifact(str(viz_file), "visualizations")

            logger.info(f"Visualizations logged from {viz_dir}")

    def end_run(self):
        """End the current MLflow run."""
        mlflow.end_run()
        logger.info("MLflow run ended")

    def log_tags(self, tags: Dict[str, str]):
        """
        Log custom tags to the run.

        Args:
            tags: Dictionary of tag key-value pairs
        """
        for key, value in tags.items():
            mlflow.set_tag(key, value)
