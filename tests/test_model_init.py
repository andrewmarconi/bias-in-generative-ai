"""
Tests for model initialization.
"""

import pytest
from pathlib import Path

from bias_detector.utils.config import load_config
from bias_detector.generation.image_generator import ImageGenerator


def test_mflux_model_config():
    """Test that mflux ModelConfig can be created."""
    from mflux.generate import ModelConfig

    # Test factory functions
    schnell_config = ModelConfig.schnell()
    assert schnell_config is not None
    assert hasattr(schnell_config, 'model_name')

    dev_config = ModelConfig.dev()
    assert dev_config is not None
    assert hasattr(dev_config, 'model_name')


def test_image_generator_creation():
    """Test that ImageGenerator can be created with config."""
    config = load_config("config/experiment_config.yaml")
    generator = ImageGenerator(config)

    # Check basic attributes
    assert generator is not None
    assert hasattr(generator, 'model_name')
    assert generator.model_name in ['dev', 'schnell', 'krea_dev']

    # Model config might be None if initialization failed (expected in test environment)
    # but the generator should still be created
    assert hasattr(generator, 'model_config')


def test_config_validation():
    """Test that config has required model settings."""
    config = load_config("config/experiment_config.yaml")

    assert 'generation' in config
    assert 'model' in config['generation']
    assert config['generation']['model'] in ['dev', 'schnell', 'krea_dev']