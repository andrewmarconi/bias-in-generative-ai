import logging
from typing import Dict, Any, Optional
import mlflow
from mlflow import log_metric, log_param, log_artifact
import json
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class MLflowTracker:
    """Robust MLflow tracker with offline support and safe experiment handling."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mlflow_config = config.get('mlflow', {})
        tracking_uri = self.mlflow_config.get('tracking_uri', 'sqlite:///mlflow.db')
        mlflow.set_tracking_uri(tracking_uri)

        self.experiment_name = self.mlflow_config.get('experiment_name', 'bias_detection')
        # Attempt to resolve/activate experiment
        try:
            exp = mlflow.get_experiment_by_name(self.experiment_name)
            if exp is None:
                self.experiment_id = mlflow.create_experiment(self.experiment_name)
            else:
                self.experiment_id = exp.experiment_id
            try:
                mlflow.set_experiment(self.experiment_name)
            except TypeError:
                pass
        except Exception as e:
            logger.warning(f"Could not set up experiment: {e}")
            self.experiment_id = None

        logger.info(f"MLflow tracking initialized: {tracking_uri}")

    def start_run(self, run_name: Optional[str] = None) -> str:
        if run_name is None:
            run_name = self.config.get('experiment', {}).get('name', 'bias_run')

        offline = bool(self.mlflow_config.get('offline', False))
        if offline:
            run_id = f"offline-{int(time.time())}"
            logger.info(f"Starting offline MLflow run: {run_id}")
            return run_id

        try:
            if isinstance(self.experiment_id, int) and self.experiment_id > 0:
                mlflow.start_run(experiment_id=self.experiment_id, run_name=run_name)
            else:
                mlflow.start_run(run_name=run_name)
            run = mlflow.active_run()
            run_id = run.info.run_id if run is not None else None
            if run_id is None:
                raise RuntimeError("No active MLflow run after start_run")
            logger.info(f"Started MLflow run: {run_id}")
            return run_id
        except Exception as e:
            logger.error(f"Failed to start MLflow run: {e}")
            mlflow.start_run(run_name=run_name)
            active = mlflow.active_run()
            if active is not None:
                run_id = active.info.run_id
                logger.info(f"Started MLflow run (fallback): {run_id}")
                return run_id
            else:
                logger.error("Unable to start MLflow run at all")
                raise

    def log_configuration(self):
        log_param("experiment_name", self.config['experiment']['name'])
        log_param("description", self.config['experiment'].get('description', ''))
        log_param("random_seed", self.config['experiment'].get('random_seed'))

        gen_config = self.config['generation']
        log_param("model", gen_config['model'])
        log_param("num_images_per_prompt", gen_config['num_images_per_prompt'])
        log_param("steps", gen_config.get('steps', gen_config.get('num_inference_steps', 4)))
        log_param("guidance_scale", gen_config.get('guidance', gen_config.get('guidance_scale', 3.5)))
        log_param("seed_strategy", gen_config.get('seed_strategy', 'fixed'))

        vqa_models = self.config['vqa_analysis'].get('models', [self.config['vqa_analysis'].get('model', 'unknown')])
        if len(vqa_models) > 1:
            log_param("vqa_ensemble", True)
            log_param("vqa_models", ",".join(vqa_models))
            log_param("ensemble_method", self.config['vqa_analysis'].get('ensemble_method', 'majority_vote'))
        else:
            log_param("vqa_ensemble", False)
            log_param("vqa_model", vqa_models[0])

        log_param("bias_categories", ",".join(self.config['bias_categories']))

        config_path = Path("data/processed/run_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
        log_artifact(str(config_path))
        logger.info("Configuration logged to MLflow")

    def log_generation_results(self, generation_results: Dict[str, List[Dict[str, Any]]]):
        pass

    def log_analysis_results(self, analysis_results):
        pass

    def log_statistical_results(self, statistics):
        pass

    def end_run(self):
        try:
            mlflow.end_run()
            logger.info("MLflow run ended")
        except Exception as e:
            logger.warning(f"MLflow end_run failed: {e}")
