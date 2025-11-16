"""
Vision-Question-Answering analysis module.

Implements Phase 4 of the research framework: Image Analysis using VQA models.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
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

    def __init__(self, config: Dict[str, Any], device: Optional[str] = None, progress_callback=None):
        """
        Initialize VQA analyzer with multi-model ensemble support.

        Args:
            config: Experiment configuration dictionary
            device: Device to run model on ('cuda', 'mps', 'cpu', or None for auto)
            progress_callback: Optional callback for progress updates
        """
        self.config = config
        self.vqa_config = config['vqa_analysis']
        self.questions = self.vqa_config['questions']
        self.progress_callback = progress_callback

        # Multi-model ensemble configuration
        self.models = self.vqa_config.get('models', [self.vqa_config.get('model', 'Salesforce/blip2-opt-2.7b')])
        self.ensemble_method = self.vqa_config.get('ensemble_method', 'majority_vote')

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

        logger.info(f"VQA device: {self.device}")
        logger.info(f"Ensemble models: {self.models}")
        logger.info(f"Ensemble method: {self.ensemble_method}")

        # Initialize ensemble of models
        self.model_ensemble = []
        self._initialize_ensemble()

    def _initialize_ensemble(self):
        """Initialize the ensemble of VQA models."""
        for model_name in self.models:
            logger.info(f"Loading model: {model_name}")

            try:
                # Load processor (shared across models if compatible)
                processor = AutoProcessor.from_pretrained(model_name, use_fast=True)

                # Load model
                model = Blip2ForConditionalGeneration.from_pretrained(
                    model_name,
                    dtype=torch.float16,
                    low_cpu_mem_usage=True
                )
                model.to(self.device)

                self.model_ensemble.append({
                    'name': model_name,
                    'model': model,
                    'processor': processor
                })

                logger.info(f"Successfully loaded {model_name}")

            except Exception as e:
                logger.error(f"Failed to load model {model_name}: {e}")
                logger.error(f"Skipping {model_name} in ensemble")

        if not self.model_ensemble:
            logger.error("No models loaded successfully - VQA analysis will not work")
            return

        logger.info("Ensemble initialization complete")

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze a single image for demographic attributes using ensemble.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary with demographic analysis results
        """
        if not self.model_ensemble:
            logger.error("No VQA models initialized")
            return {category: {'raw_answer': 'unclear', 'matched_option': 'unclear', 'confidence': 0.0}
                   for category in self.questions.keys()}

        # Load and preprocess image
        try:
            image = Image.open(image_path).convert('RGB')
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            return {category: {'raw_answer': 'unclear', 'matched_option': 'unclear', 'confidence': 0.0}
                   for category in self.questions.keys()}

        results = {}

        # Ask questions for each demographic category
        for category, question_config in self.questions.items():
            question = question_config['question']
            options = question_config['options']

            # Get ensemble prediction
            ensemble_result = self._analyze_with_ensemble(image, question, options)

            results[category] = ensemble_result

            logger.debug(f"{category}: {ensemble_result['matched_option']} (confidence: {ensemble_result['confidence']:.2f})")

        return results

    def _analyze_with_ensemble(self, image: Image.Image, question: str, options: List[str]) -> Dict[str, Any]:
        """
        Analyze using ensemble of models.

        Args:
            image: PIL Image
            question: Question text
            options: Valid answer options

        Returns:
            Dictionary with ensemble result
        """
        model_predictions = []

        # Get predictions from each model
        for model_info in self.model_ensemble:
            try:
                answer = self._ask_question_with_model(image, question, model_info)
                matched_option, confidence = self._match_to_options(answer, options)
                model_predictions.append({
                    'answer': answer,
                    'matched_option': matched_option,
                    'confidence': confidence,
                    'model': model_info['name']
                })
            except Exception as e:
                logger.warning(f"Model {model_info['name']} failed: {e}")
                continue

        if not model_predictions:
            return {
                'raw_answer': 'unclear',
                'matched_option': 'unclear',
                'confidence': 0.0
            }

        # Combine predictions using ensemble method
        if self.ensemble_method == 'majority_vote':
            return self._majority_vote(model_predictions)
        elif self.ensemble_method == 'confidence_weighted':
            return self._confidence_weighted_vote(model_predictions)
        else:  # default to majority vote
            return self._majority_vote(model_predictions)

    def _majority_vote(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine predictions using majority voting."""
        from collections import Counter

        matched_options = [p['matched_option'] for p in predictions]
        option_counts = Counter(matched_options)

        # Get most common option
        most_common = option_counts.most_common(1)[0]
        winner_option = most_common[0]
        vote_count = most_common[1]

        # Calculate confidence as fraction of votes
        confidence = vote_count / len(predictions)

        # Get raw answers from winning predictions
        winning_predictions = [p for p in predictions if p['matched_option'] == winner_option]
        raw_answers = [p['answer'] for p in winning_predictions]

        return {
            'raw_answer': '; '.join(raw_answers[:3]),  # Show up to 3 raw answers
            'matched_option': winner_option,
            'confidence': confidence
        }

    def _confidence_weighted_vote(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine predictions using confidence-weighted voting."""
        from collections import defaultdict

        # Group by option and sum confidence scores
        option_scores = defaultdict(float)
        option_answers = defaultdict(list)

        for pred in predictions:
            option = pred['matched_option']
            confidence = pred['confidence']
            option_scores[option] += confidence
            option_answers[option].append(pred['answer'])

        # Find option with highest total confidence
        best_option = max(option_scores.keys(), key=lambda x: option_scores[x])
        total_confidence = sum(option_scores.values())
        confidence = option_scores[best_option] / total_confidence if total_confidence > 0 else 0.0

        return {
            'raw_answer': '; '.join(option_answers[best_option][:3]),
            'matched_option': best_option,
            'confidence': confidence
        }

    def _ask_question_with_model(self, image: Image.Image, question: str, model_info: Dict[str, Any]) -> str:
        """
        Ask a question about an image using a specific model.

        Args:
            image: PIL Image
            question: Question text
            model_info: Dictionary with model and processor

        Returns:
            Answer text from the model
        """
        model = model_info['model']
        processor = model_info['processor']

        try:
            # Prepare inputs
            inputs = processor(image, question, return_tensors="pt").to(self.device)

            # Generate answer
            with torch.no_grad():
                generated_ids = model.generate(**inputs, max_new_tokens=20)

            # Decode answer
            answer = processor.batch_decode(
                generated_ids,
                skip_special_tokens=True
            )[0].strip()

            return answer
        except Exception as e:
            logger.warning(f"Error with model {model_info['name']}: {e}")
            return "unclear"

    def _match_to_options(self, answer: str, options: List[str]) -> Tuple[str, float]:
        """
        Match VQA answer to predefined options with confidence scoring.

        Uses fuzzy matching to handle variations in model output.

        Args:
            answer: Raw answer from VQA model
            options: List of valid options

        Returns:
            Tuple of (best_matching_option, confidence_score)
        """
        answer_lower = answer.lower().strip()

        # Handle empty or unclear answers
        if not answer_lower or answer_lower in ['unclear', 'unknown', 'not sure', 'n/a']:
            return "unclear", 0.0

        # Direct match (highest confidence)
        for option in options:
            if option.lower() == answer_lower:
                return option, 1.0  # Perfect match

        # Partial match with high confidence
        for option in options:
            if option.lower() in answer_lower or answer_lower in option.lower():
                return option, 0.8  # Good match

        # Keyword-based matching (medium confidence)
        for option in options:
            keywords = option.lower().split()
            if any(keyword in answer_lower for keyword in keywords):
                return option, 0.6  # Partial keyword match

        # Fuzzy matching for common variations
        answer_words = set(answer_lower.split())
        for option in options:
            option_words = set(option.lower().split())
            overlap = len(answer_words.intersection(option_words))
            if overlap > 0:
                confidence = min(0.5, overlap / len(option_words))  # Up to 0.5 confidence
                return option, confidence

        # Default to unclear with low confidence
        return "unclear", 0.1

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
        total_images = len(image_metadata_list)

        for i, metadata in enumerate(tqdm(image_metadata_list, desc="Analyzing images", unit="image")):
            image_path = metadata.get('image_path') or metadata.get('path')

            if image_path is None:
                logger.error(f"No image path found in metadata: {metadata}")
                continue

            # Analyze image
            analysis = self.analyze_image(image_path)

            # Combine with metadata
            result = {
                **metadata,
                'analysis': analysis
            }

            results.append(result)

            # Report progress to callback
            if self.progress_callback:
                self.progress_callback.on_progress(
                    phase_num=4,  # Phase 4: VQA Analysis
                    items_done=i + 1,
                    items_total=total_images,
                    message=f"Analyzed image {i + 1}/{total_images}"
                )

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
        if not self.model_ensemble:
            logger.error("No VQA models initialized")
            return "Unable to generate caption - no models loaded"

        try:
            image = Image.open(image_path).convert('RGB')
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            return "Failed to load image"

        # Use the first model in ensemble for captioning
        model_info = self.model_ensemble[0]

        # Use BLIP-2 for captioning without a question
        inputs = model_info['processor'](image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            generated_ids = model_info['model'].generate(**inputs, max_new_tokens=50)

        caption = model_info['processor'].batch_decode(
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
