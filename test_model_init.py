#!/usr/bin/env python3
"""
Test that model initialization works correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("Testing mflux ModelConfig...")

try:
    from mflux.generate import ModelConfig

    # Test calling the factory functions
    print("✓ Imported ModelConfig")

    schnell_config = ModelConfig.schnell()
    print(f"✓ schnell config created: {type(schnell_config)}")
    print(f"  Model name: {schnell_config.model_name}")

    dev_config = ModelConfig.dev()
    print(f"✓ dev config created: {type(dev_config)}")
    print(f"  Model name: {dev_config.model_name}")

    print("\nTesting ImageGenerator initialization...")
    from bias_detector.utils.config import load_config
    from bias_detector.generation.image_generator import ImageGenerator

    config = load_config("config/experiment_config.yaml")
    generator = ImageGenerator(config)
    print(f"✓ ImageGenerator created for model: {generator.model_name}")
    print(f"  Model config: {generator.model_config.model_name}")

    print("\n✅ All model initialization tests passed!")
    print("\nNote: Model weights will be downloaded on first image generation.")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
