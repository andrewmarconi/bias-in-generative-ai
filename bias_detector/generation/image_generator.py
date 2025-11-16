"""
Image generation module using mflux (FLUX models on Apple Silicon).

Implements Phase 3 of the research framework: Image Generation Protocol.
Implements systematic image generation with version control and metadata tracking.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from tqdm import tqdm

from mflux.generate import Flux1
from mflux.config.config import Config
from mflux.config.model_config import ModelConfig as FluxModelConfig

logger = logging.getLogger(__name__)


class ImageGenerator:
    """
    Generate images using mflux FLUX models.
    
    Implements systematic image generation with version control and metadata tracking
    as specified in the research framework (Phase 3).
    """

    def __init__(self, config: Dict[str, Any], progress_callback=None):
        """
        Initialize image generator.

        Args:
            config: Experiment configuration dictionary
            progress_callback: Optional callback for progress updates
        """
        self.config = config
        self.generation_config = config['generation']
        
        # Get output directory safely
        output_config = config.get('output', {})
        if not isinstance(output_config, dict):
            logger.error(f"Output config must be a dictionary, got: {type(output_config)}")
            output_config = {}
        self.output_dir = Path(output_config.get('image_dir', 'data/raw/images'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Progress callback for UI updates
        self.progress_callback = progress_callback
        
        # Initialize FLUX model
        self.model_name = self.generation_config.get('model', 'dev')
        logger.info(f"Initializing FLUX.1-{self.model_name} model with mflux...")
        
        # Map model names to ModelConfig factory functions
        model_map = {
            'dev': FluxModelConfig.dev,
            'schnell': FluxModelConfig.schnell,
            'krea_dev': FluxModelConfig.krea_dev
        }
        
        # Get factory function and call it to get the actual ModelConfig instance
        model_factory = model_map.get(self.model_name, FluxModelConfig.dev)
        try:
            self.model_config = model_factory()
            # Initialize model immediately during setup to avoid threading issues
            logger.info(f"Loading FLUX.1-{self.model_name} model...")
            self.flux = Flux1(model_config=self.model_config)
            logger.info(f"FLUX.1-{self.model_name} model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FLUX.1-{self.model_name} model: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            self.model_config = None
            self.flux = None

    def _initialize_model(self):
        """Check if FLUX model is initialized (models are loaded during __init__ now)."""
        if self.flux is None:
            logger.error("FLUX model not available - initialization failed during setup")
        return self.flux is not None

    def generate_images_for_prompt(self, prompt: str, prompt_id: str, num_images: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate multiple images for a single prompt.
        
        Args:
            prompt: Text prompt for image generation
            prompt_id: Unique identifier for this prompt
            num_images: Number of images to generate (uses config if None)
            
        Returns:
            List of dictionaries containing image paths and metadata
        """
        if not self._initialize_model():
            logger.error("FLUX model not initialized - cannot generate image")
            return []
            
        if num_images is None:
            num_images = self.generation_config.get('num_images_per_prompt', 10)
        
        logger.info(f"Generating {num_images} images for prompt: '{prompt}'")
        results = []
        
        seed_strategy = self.generation_config.get('seed_strategy', 'fixed')
        base_seed = self.generation_config.get('base_seed', 42)
        
        for i in range(num_images or 10):
            # Determine seed based on strategy
            if seed_strategy == 'fixed':
                seed = base_seed + i
            else:  # random
                import random
                seed = random.randint(0, 2**32 - 1)
            
            # Generate image
            generation_config = Config(
                num_inference_steps=self.generation_config.get('num_inference_steps', 4),
                width=self.generation_config.get('width', 1024),
                height=self.generation_config.get('height', 1024),
                guidance=self.generation_config.get('guidance', 3.5)
            )
            
            if self.flux is None:
                logger.error("FLUX model not available - skipping image generation")
                continue
                
            result = self.flux.generate_image(
                seed=seed,
                prompt=prompt,
                config=generation_config
            )
            
            # Save the image and get the path
            output_dir = Path(self.config['data']['output_dirs']['images'])
            output_dir.mkdir(parents=True, exist_ok=True)
            image_path = output_dir / f"{prompt_id}_{seed}.png"
            result.save(image_path)
            
            results.append({
                'path': str(image_path),
                'seed': seed,
                'prompt': prompt,
                'prompt_id': prompt_id,
                'generation_time': datetime.now().isoformat()
            })
        
        return results

    def generate_for_all_prompts(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate images for all prompts defined in configuration.
        
        Returns:
            Dictionary mapping prompt IDs to lists of image metadata
        """
        if not self._initialize_model():
            logger.error("FLUX model not initialized - cannot generate images")
            return {}
            
        all_results = {}
        prompts_config = self.config['prompts']
        
        # Flatten prompts from all categories
        all_prompts = []
        for category, prompts in prompts_config.items():
            for idx, prompt in enumerate(prompts):
                prompt_id = f"{category}_{idx:02d}"
                all_prompts.append((prompt_id, prompt))
        
        logger.info(f"Generating images for {len(all_prompts)} prompts...")

        try:
            total_prompts = len(all_prompts)
            for i, (prompt_id, prompt) in enumerate(tqdm(all_prompts, desc="Processing prompts", unit="prompt")):
                results = self.generate_images_for_prompt(prompt, prompt_id)
                all_results[prompt_id] = results

                # Report progress to callback
                if self.progress_callback:
                    self.progress_callback.on_progress(
                        phase_num=3,  # Phase 3: Image Generation
                        items_done=i + 1,
                        items_total=total_prompts,
                        message=f"Generated images for prompt: {prompt[:50]}..."
                    )

            logger.info(f"Image generation complete. Total images: {sum(len(r) for r in all_results.values())}")
            return all_results
        except Exception as e:
            logger.error(f"Error during image generation: {e}")
            # Return whatever we have so far instead of None
            return all_results

    def generate_counterfactual_images(
        self,
        base_prompt: str,
        prompt_id: str,
        demographic_modifiers: Dict[str, List[str]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate counterfactual images with explicit demographic modifiers.
        
        Implements Phase 6: Counterfactual and Sensitivity Analysis.
        
        Args:
            base_prompt: Original ambiguous prompt
            prompt_id: Identifier for the base prompt
            demographic_modifiers: Dictionary of demographic categories and their values
            
        Returns:
            Dictionary mapping modified prompts to image metadata
        """
        if not self._initialize_model():
            logger.error("FLUX model not initialized - cannot generate image")
            return {}
            
        logger.info(f"Generating counterfactual images for: '{base_prompt}'")
        
        results = {}
        seed_strategy = self.generation_config.get('seed_strategy', 'fixed')
        base_seed = self.generation_config.get('base_seed', 42)
        
        # Generate images
        num_images = self.generation_config.get('num_images_per_prompt', 10)  # Fewer for counterfactuals
        
        for demographic, values in demographic_modifiers.items():
            modified_prompt = f"{base_prompt} with {demographic}: {', '.join(values)}"
            modified_id = f"{prompt_id}_{demographic}"
            
            for i in tqdm(range(num_images), desc=f"Generating {demographic} images"):
                # Determine seed based on strategy
                if seed_strategy == 'fixed':
                    seed = base_seed + i
                else:  # random
                    import random
                    seed = random.randint(0, 2**32 - 1)
                
                # Generate image
                generation_config = Config(
                    num_inference_steps=self.generation_config.get('num_inference_steps', 4),
                    width=self.generation_config.get('width', 1024),
                    height=self.generation_config.get('height', 1024),
                    guidance=self.generation_config.get('guidance', 3.5)
                )
                
                if self.flux is None:
                    logger.error("FLUX model not available - skipping counterfactual image generation")
                    continue
                    
                result = self.flux.generate_image(
                    seed=seed,
                    prompt=modified_prompt,
                    config=generation_config
                )
                
                # Save the image and get the path
                output_dir = Path(self.config['data']['output_dirs']['images'])
                output_dir.mkdir(parents=True, exist_ok=True)
                image_path = output_dir / f"{modified_id}_{seed}.png"
                result.save(image_path)
                
                if modified_id not in results:
                    results[modified_id] = []
                
                results[modified_id].append({
                    'path': str(image_path),
                    'seed': seed,
                    'prompt': modified_prompt,
                    'prompt_id': modified_id,
                    'demographic': demographic,
                    'base_prompt': base_prompt,
                    'generation_time': datetime.now().isoformat()
                })
        
        return results