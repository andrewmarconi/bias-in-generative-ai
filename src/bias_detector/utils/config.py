"""Configuration management utilities."""

import yaml
from pathlib import Path
from typing import Any, Dict


def load_config(config_path: str = "config/experiment_config.yaml") -> Dict[str, Any]:
    """
    Load experiment configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary containing configuration
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate that configuration contains required fields.

    Args:
        config: Configuration dictionary

    Returns:
        True if valid, raises ValueError otherwise
    """
    required_sections = ['experiment', 'generation', 'prompts', 'vqa_analysis', 'statistics']

    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")

    return True
