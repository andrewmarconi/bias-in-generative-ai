"""
Tests for basic setup and imports.
"""

import pytest
from pathlib import Path

from bias_detector.utils.config import load_config, validate_config
from bias_detector.generation.image_generator import ImageGenerator
from bias_detector.analysis.vqa_analyzer import VQAAnalyzer
from bias_detector.statistics.bias_metrics import BiasMetrics
from bias_detector.statistics.visualizations import BiasVisualizer
from bias_detector.utils.mlflow_tracker import MLflowTracker


def test_imports():
    """Test that all main components can be imported."""
    # This test will fail if any imports are broken
    assert ImageGenerator is not None
    assert VQAAnalyzer is not None
    assert BiasMetrics is not None
    assert BiasVisualizer is not None
    assert MLflowTracker is not None


def test_config_loading():
    """Test that configuration can be loaded and validated."""
    config = load_config("config/experiment_config.yaml")

    # Should not raise an exception
    validate_config(config)

    # Check required sections exist
    required_sections = ['experiment', 'generation', 'prompts', 'vqa_analysis', 'statistics']
    for section in required_sections:
        assert section in config, f"Missing required section: {section}"


def test_config_summary():
    """Test that config has expected structure and values."""
    config = load_config("config/experiment_config.yaml")

    # Check experiment section
    assert 'experiment' in config
    assert 'name' in config['experiment']

    # Check generation section
    assert 'generation' in config
    assert 'model' in config['generation']
    assert 'num_images_per_prompt' in config['generation']

    # Check prompts section
    assert 'prompts' in config
    assert isinstance(config['prompts'], dict)
    assert len(config['prompts']) > 0

    # Check VQA section
    assert 'vqa_analysis' in config
    assert 'model' in config['vqa_analysis']

    # Check statistics section
    assert 'statistics' in config
    assert 'significance_level' in config['statistics']


def test_calculate_expected_totals():
    """Test calculation of expected totals from config."""
    config = load_config("config/experiment_config.yaml")

    num_prompts = sum(len(prompts) for prompts in config['prompts'].values())
    images_per_prompt = config['generation']['num_images_per_prompt']
    expected_images = num_prompts * images_per_prompt

    assert num_prompts > 0, "Should have at least one prompt"
    assert images_per_prompt > 0, "Should generate at least one image per prompt"
    assert expected_images > 0, "Should expect to generate some images"