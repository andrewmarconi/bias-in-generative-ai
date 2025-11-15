"""Configuration state management for TUI."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field


class ValidationStatus(Enum):
    """Configuration validation status."""
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class ConfigurationState(BaseModel):
    """Represents current experiment configuration with validation status and locking.
    
    Purpose: Track config changes, provide validation, and enforce locking during active experiments.
    """
    
    config_path: str = Field(..., description="Path to YAML config file")
    locked: bool = Field(False, description="True if experiment is running (read-only)")
    locked_by_session: Optional[str] = Field(None, description="Session ID that locked config")
    last_modified: datetime = Field(..., description="Last config file modification time")
    validation_status: ValidationStatus = Field(ValidationStatus.UNKNOWN, description="Config validity state")
    validation_errors: List[str] = Field(default_factory=list, description="Validation error messages")
    sections: Dict[str, Dict] = Field(default_factory=dict, description="Parsed config sections")
    
    class Config:
        """Pydantic configuration model."""
        model: str
        num_images_per_prompt: int
        steps: int
        guidance_scale: float
        width: int
        height: int
        seed_strategy: str
        output_dir: str
        image_format: str
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return self.validation_status == ValidationStatus.VALID and not self.validation_errors
    
    def has_section(self, section_name: str) -> bool:
        """Check if a configuration section exists."""
        return section_name in self.sections
    
    def get_section(self, section_name: str) -> Dict[str, Any]:
        """Get a configuration section by name."""
        return self.sections.get(section_name, {})
    
    def get_generation_config(self) -> Config:
        """Get generation configuration as Config object."""
        data = self.get_section("generation")
        return Config(**data) if data else Config()
    
    def get_prompts_config(self) -> Dict[str, Any]:
        """Get prompts configuration."""
        return self.get_section("prompts")
    
    def get_vqa_config(self) -> Dict[str, Any]:
        """Get VQA analysis configuration."""
        return self.get_section("vqa_analysis")
    
    def get_statistics_config(self) -> Dict[str, Any]:
        """Get statistics configuration."""
        return self.get_section("statistics")