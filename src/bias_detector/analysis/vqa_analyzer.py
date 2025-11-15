"""
Vision-Question-Answering analysis module.

Implements Phase 4 of the research framework: Image Analysis using VQA models.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
import torch
from transformers import AutoProcessor, Blip2ForConditionalGeneration
import json
from tqdm import tqdm

logger = logging.getLogger(__name__)


class VQAAnalyzer:
    """
    Analyze generated images using Vision-Language models.

    Implements systematic demographic classification using VQA models
    as specified in the research framework (Phase 4).
    """

    def __init__(self, config: Dict[str, Any], device: Optional[str] = None):
        """
        Initialize VQA analyzer.

        Args:
            config: Experiment configuration dictionary
            device: Device to run model on ('cuda', 'mps', 'cpu', or None for auto)
        """
        self.config = config
        self.vqa_config = config['vqa_analysis']
        self.model_name = self.vqa_config.get('model', 'Salesforce/blip2-opt-2.7b')

        # Determine device
        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        else:
            self.device = device

        logger.info(f"Initializing VQA model: {self.model_name} on {self.device}")

        # Load model and processor
        self.processor = AutoProcessor.from_pretrained(self.model_name, use_fast=True)

        # Use memory-efficient loading with float16 for GPU/MPS
        if self.device != "cpu":
            # Use float16 for memory efficiency on MPS/CUDA
            self.model = Blip2ForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )
            self.model.to(self.device)
            logger.info(f"VQA model loaded with float16 precision on {self.device}")
        else:
            # CPU mode - use full precision
            self.model = Blip2ForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            self.model.to(self.device)
            logger.info("VQA model loaded in full precision (CPU mode)")

        self.model.eval()
        logger.info("VQA model loaded successfully")

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze a single image for demographic characteristics.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing analysis results for all bias categories
        """
        image = Image.open(image_path).convert('RGB')
        results = {}

        questions = self.vqa_config['questions']

        for category, question_config in questions.items():
            question = question_config['question']
            options = question_config['options']

            # Get answer from VQA model
            answer = self._ask_question(image, question)

            # Match answer to options
            matched_option = self._match_to_options(answer, options)

            results[category] = {
                'raw_answer': answer,
                'matched_option': matched_option,
                'confidence': 1.0  # BLIP-2 doesn't provide confidence, could add later
            }

            logger.debug(f"{category}: {matched_option} (raw: {answer})")

        return results

    def _ask_question(self, image: Image.Image, question: str) -> str:
        """
        Ask a question about an image using the VQA model.

        Args:
            image: PIL Image
            question: Question text

        Returns:
            Answer text from the model
        """
        # Prepare inputs
        inputs = self.processor(image, question, return_tensors="pt").to(self.device)

        # Generate answer
        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=20)

        # Decode answer
        answer = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0].strip()

        return answer

    def _match_to_options(self, answer: str, options: List[str]) -> str:
        """
        Match VQA answer to predefined options.

        Uses fuzzy matching to handle variations in model output.

        Args:
            answer: Raw answer from VQA model
            options: List of valid options

        Returns:
            Best matching option or 'unclear'
        """
        answer_lower = answer.lower()

        # Direct match
        for option in options:
            if option.lower() in answer_lower or answer_lower in option.lower():
                return option

        # Partial match with keywords
        for option in options:
            keywords = option.lower().split()
            if any(keyword in answer_lower for keyword in keywords):
                return option

        # Default to unclear
        return "unclear"

    def analyze_batch(
        self,
        image_metadata_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze a batch of images.

        Args:
            image_metadata_list: List of image metadata dictionaries

        Returns:
            List of analysis results with metadata
        """
        results = []

        for metadata in tqdm(image_metadata_list, desc="Analyzing images", unit="image"):
            image_path = metadata['image_path']

            # Analyze image
            analysis = self.analyze_image(image_path)

            # Combine with metadata
            result = {
                **metadata,
                'analysis': analysis
            }

            results.append(result)

        return results

    def save_results(
        self,
        results: List[Dict[str, Any]],
        output_path: str
    ):
        """
        Save analysis results to JSON file.

        Args:
            results: List of analysis results
            output_path: Path to output JSON file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Analysis results saved to {output_path}")

    def generate_caption(self, image_path: str) -> str:
        """
        Generate a detailed caption for an image.

        Implements Option B: Caption-and-Extract Approach from Phase 4.

        Args:
            image_path: Path to the image file

        Returns:
            Generated caption
        """
        image = Image.open(image_path).convert('RGB')

        # Use BLIP-2 for captioning without a question
        inputs = self.processor(image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=50)

        caption = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )[0].strip()

        return caption

    def analyze_with_captions(
        self,
        image_metadata_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze images using both VQA and captioning.

        Args:
            image_metadata_list: List of image metadata dictionaries

        Returns:
            List of analysis results with both VQA and captions
        """
        results = []

        for metadata in tqdm(image_metadata_list, desc="Analyzing with captions", unit="image"):
            image_path = metadata['image_path']

            # VQA analysis
            vqa_analysis = self.analyze_image(image_path)

            # Caption generation
            caption = self.generate_caption(image_path)

            # Combine results
            result = {
                **metadata,
                'vqa_analysis': vqa_analysis,
                'caption': caption
            }

            results.append(result)

        return results
