import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from PIL import Image
import torch

logger = logging.getLogger(__name__)


class ImageGenerator:
    """
    Generate images using HuggingFace diffusers.

    Supports multiple diffusion models for systematic image generation with version control
    and metadata tracking as specified in the research framework (Phase 3).
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

        # Output directory
        output_config = config.get('output', {})
        if not isinstance(output_config, dict):
            logger.error(f"Output config must be a dictionary, got: {type(output_config)}")
            output_config = {}
        self.output_dir = Path(output_config.get('image_dir', 'data/raw/images'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.progress_callback = progress_callback

        # Device
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        logger.info(f"Image generation device: {self.device}")

        self.model_id = self.generation_config.get('model', 'stabilityai/stable-diffusion-2-1')
        self.pipeline = None
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Initialize the diffusion pipeline with lazy import and offline support."""
        offline = bool(self.config.get('generation', {}).get('offline', False)) or bool(self.config.get('mlflow', {}).get('offline', False))
        try:
            # Try dynamic import to avoid static import issues in build env
            from diffusers import DiffusionPipeline
            DiffusionPipelineAvailable = True
        except Exception as e:
            logger.warning(f"DiffusionPipeline import failed: {e}")
            DiffusionPipelineAvailable = False
            DiffusionPipeline = None  # type: ignore

        if not DiffusionPipelineAvailable or offline:
            logger.info("Offline mode or DiffusionPipeline unavailable; skipping real diffusion load.")
            self.pipeline = None
            return

        try:
            logger.info(f"Loading diffusion model: {self.model_id}")
            self.pipeline = DiffusionPipeline.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
                safety_checker=None,
                requires_safety_checker=False
            )
            self.pipeline.to(self.device)
            if hasattr(self.pipeline, 'enable_attention_slicing'):
                self.pipeline.enable_attention_slicing()
            if self.device == "cuda" and hasattr(self.pipeline, 'enable_xformers_memory_efficient_attention'):
                try:
                    self.pipeline.enable_xformers_memory_efficient_attention()
                except Exception:
                    logger.warning("xformers not available, using standard attention")
            logger.info(f"Diffusion pipeline loaded successfully: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to load diffusion model {self.model_id}: {e}")
            self.pipeline = None

    def _initialize_model(self):
        """Return whether pipeline is loaded."""
        return self.pipeline is not None

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
        offline = bool(self.config.get('generation', {}).get('offline', False)) or bool(self.config.get('mlflow', {}).get('offline', False))
        if not self._initialize_model():
            if offline:
                # generate a placeholder image
                try:
                    width = int(self.config.get('generation', {}).get('width', 512))
                    height = int(self.config.get('generation', {}).get('height', 512))
                    image_path = self.output_dir / f"{prompt_id}_offline.png"
                    from PIL import Image
                    img = Image.new('RGB', (width, height), color=(128, 128, 128))
                    img.save(image_path)
                    seed = 0
                    return [{
                        'image_path': str(image_path),
                        'seed': seed,
                        'prompt': prompt,
                        'prompt_id': prompt_id,
                        'generation_time': datetime.now().isoformat()
                    }]
                except Exception as e:
                    logger.error(f"Offline placeholder generation failed: {e}")
                    return []
            logger.error("Diffusion pipeline not available - cannot generate image")
            return []

        if num_images is None:
            num_images = self.generation_config.get('num_images_per_prompt', 10)
        logger.info(f"Generating {num_images} images for prompt: '{prompt}'")
        results: List[Dict[str, Any]] = []
        seed_strategy = self.generation_config.get('seed_strategy', 'fixed')
        base_seed = self.generation_config.get('base_seed', 42)

        for i in range(int(num_images)):
            seed = base_seed + i if seed_strategy == 'fixed' else __import__('random').randint(0, 2**32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            try:
                outputs = self.pipeline(
                    prompt=prompt,
                    num_inference_steps=self.generation_config.get('num_inference_steps', 20),
                    width=self.generation_config.get('width', 512),
                    height=self.generation_config.get('height', 512),
                    guidance_scale=self.generation_config.get('guidance', 7.5),
                    generator=generator,
                    output_type="pil"
                )
                image = outputs.images[0]
                image_path = self.output_dir / f"{prompt_id}_{seed}.png"
                image.save(image_path)
                results.append({
                    'image_path': str(image_path),
                    'seed': seed,
                    'prompt': prompt,
                    'prompt_id': prompt_id,
                    'generation_time': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Image generation failed for {prompt_id}: {e}")
                continue
        return results

    def generate_for_all_prompts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate images for all prompts defined in configuration."""
        if not self._initialize_model():
            logger.error("Diffusion pipeline not initialized - cannot generate images")
            return {}
        all_results: Dict[str, List[Dict[str, Any]]] = {}
        prompts_config = self.config['prompts']
        all_prompts = []
        for category, prompts in prompts_config.items():
            for idx, prompt in enumerate(prompts):
                prompt_id = f"{category}_{idx:02d}"
                all_prompts.append((prompt_id, prompt))
        logger.info(f"Generating images for {len(all_prompts)} prompts...")
        for prompt_id, prompt in all_prompts:
            results = self.generate_images_for_prompt(prompt, prompt_id)
            all_results[prompt_id] = results
        return all_results
