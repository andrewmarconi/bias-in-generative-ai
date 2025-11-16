"""
Configuration Editor Screen for Interactive Configuration Management.

Provides real-time configuration editing with validation, lock enforcement,
and immediate feedback on configuration changes.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button, Input, Label, Static, TextArea, 
    Tabs, TabbedContent, TabPane, Select, Checkbox
)
from textual.message import Message
from textual.binding import Binding
from textual import log
from textual.geometry import Size

from ..state.manager import StateManager
from ..state.config import ConfigurationState, ValidationStatus


class ConfigEditorScreen(Screen):
    """
    Interactive configuration editor with real-time validation.
    
    Features:
    - Live configuration editing with immediate validation feedback
    - Lock enforcement during active experiments
    - Section-based editing (generation, prompts, vqa_analysis, statistics)
    - Save/cancel/reset functionality
    - Number validation for numeric fields
    - Model selection from available options
    """

    TITLE = "Configuration Editor"
    SUB_TITLE = "Interactive Configuration Management"

    BINDINGS = [
        Binding("ctrl+s", "save", "Save", show=True),
        Binding("ctrl+r", "reset", "Reset", show=True),
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("f1", "show_help", "Help", show=True),
    ]

    class ConfigChanged(Message):
        """Emitted when configuration is modified."""
        def __init__(self, config_state: ConfigurationState) -> None:
            self.config_state = config_state
            super().__init__()

    class ConfigSaved(Message):
        """Emitted when configuration is saved."""
        def __init__(self, config_path: str) -> None:
            self.config_path = config_path
            super().__init__()

    def __init__(
        self,
        config_path: str = "config/experiment_config.yaml",
        state_manager: Optional[StateManager] = None,
        **kwargs
    ):
        """
        Initialize configuration editor screen.

        Args:
            config_path: Path to configuration file
            state_manager: StateManager instance for config operations
            **kwargs: Additional arguments passed to Screen
        """
        super().__init__(**kwargs)
        
        self.config_path = config_path
        self.state_manager = state_manager or StateManager()
        
        # Configuration state
        self.config_state: Optional[ConfigurationState] = None
        self.original_config: Dict[str, Any] = {}
        self.current_config: Dict[str, Any] = {}
        self.has_unsaved_changes = False
        
        # UI components
        self.status_label: Optional[Static] = None
        self.validation_errors: Optional[Static] = None
        self.save_button: Optional[Button] = None
        self.reset_button: Optional[Button] = None

    def compose(self) -> ComposeResult:
        """Compose the configuration editor UI."""
        yield Container(
            # Header with status
            Container(
                Horizontal(
                    Label("Configuration Editor", classes="section-title"),
                    Static("", id="status-label"),
                ),
                Static("", id="validation-errors", classes="error"),
                classes="header-container",
            ),
            
            # Tabbed interface for different sections
            TabbedContent(id="config-tabs"),
            
            # Action buttons
            Horizontal(
                Button("Save (Ctrl+S)", id="save-button", variant="success"),
                Button("Reset (Ctrl+R)", id="reset-button", variant="warning"),
                Button("Cancel (Esc)", id="cancel-button", variant="error"),
                classes="button-container",
            ),
            
            id="config-editor-container",
        )

    def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        # Load configuration
        self._load_configuration()
        
        # Setup UI references
        self.status_label = self.query_one("#status-label", Static)
        self.validation_errors = self.query_one("#validation-errors", Static)
        self.save_button = self.query_one("#save-button", Button)
        self.reset_button = self.query_one("#reset-button", Button)
        
        # Setup tabbed content with panes
        self._setup_tabbed_content()
        
        # Setup tab content
        self._setup_generation_tab()
        self._setup_prompts_tab()
        self._setup_vqa_tab()
        self._setup_statistics_tab()
        
        # Update UI state
        self._update_ui_state()
    
    def _setup_tabbed_content(self) -> None:
        """Setup the tabbed content with panes."""
        tabbed_content = self.query_one("#config-tabs", TabbedContent)

        # Clear existing content
        tabbed_content.remove_children()

        # Add tab panes using the correct API
        tabbed_content.add_pane(TabPane("Generation", Container(id="generation-content"), id="generation-tab"))
        tabbed_content.add_pane(TabPane("Prompts", Container(id="prompts-content"), id="prompts-tab"))
        tabbed_content.add_pane(TabPane("VQA Analysis", Container(id="vqa-content"), id="vqa-tab"))
        tabbed_content.add_pane(TabPane("Statistics", Container(id="statistics-content"), id="statistics-tab"))

    def _load_configuration(self) -> None:
        """Load configuration from file and populate UI."""
        try:
            # Get configuration state from manager
            config_dict = self.state_manager.get_config_state(self.config_path)
            
            # Convert to ConfigurationState
            self.config_state = ConfigurationState(
                config_path=config_dict["config_path"],
                locked=config_dict["locked"],
                locked_by_session=config_dict["locked_by_session"],
                last_modified=config_dict["last_modified"],
                validation_status=config_dict["validation_status"],
                validation_errors=config_dict["validation_errors"],
                sections=config_dict["sections"]
            )
            self.original_config = config_dict["sections"].copy()
            self.current_config = config_dict["sections"].copy()
            
            log.info(f"Loaded configuration from {self.config_path}")
            
        except Exception as e:
            log.error(f"Failed to load configuration: {e}")
            self._show_error(f"Failed to load configuration: {e}")

    def _setup_generation_tab(self) -> None:
        """Setup the generation configuration tab."""
        try:
            # Get the generation content container
            content = self.query_one("#generation-content", Container)

            # Clear existing content
            content.remove_children()

            generation_config = self.current_config.get("generation", {})
            
            content.mount(
                Vertical(
                    Label("Model Configuration", classes="subsection-title"),
                    
                    # Model selection
                    Horizontal(
                        Label("Model:"),
                        Select(
                            options=[
                                ("flux1-dev", "flux1-dev"),
                                ("flux1-schnell", "flux1-schnell"),
                                ("stable-diffusion", "stable-diffusion"),
                            ],
                            value=generation_config.get("model", "flux1-dev"),
                            id="generation-model",
                        ),
                    ),
                    
                    # Image dimensions
                    Horizontal(
                        Label("Width:"),
                        Input(
                            value=str(generation_config.get("width", 512)),
                            placeholder="512",
                            id="generation-width"
                        ),
                        Label("Height:"),
                        Input(
                            value=str(generation_config.get("height", 512)),
                            placeholder="512", 
                            id="generation-height"
                        ),
                    ),
                    
                    # Generation parameters
                    Horizontal(
                        Label("Num Steps:"),
                        Input(
                            value=str(generation_config.get("num_steps", 4)),
                            placeholder="4",
                            id="generation-num-steps"
                        ),
                        Label("Guidance Scale:"),
                        Input(
                            value=str(generation_config.get("guidance_scale", 3.5)),
                            placeholder="3.5",
                            id="generation-guidance-scale"
                        ),
                    ),
                    
                    # Seed
                    Horizontal(
                        Label("Seed:"),
                        Input(
                            value=str(generation_config.get("seed", 42)),
                            placeholder="42",
                            id="generation-seed"
                        ),
                        Checkbox(
                            "Random Seed",
                            value=generation_config.get("random_seed", False),
                            id="generation-random-seed"
                        ),
                    ),
                    
                    classes="config-section",
                )
            )
        except Exception as e:
            log.error(f"Error setting up generation tab: {e}")

    def _setup_prompts_tab(self) -> None:
        """Setup the prompts configuration tab."""
        try:
            # Get prompts content container
            content = self.query_one("#prompts-content", Container)

            # Clear existing content
            content.remove_children()
            
            prompts_config = self.current_config.get("prompts", {})
            
            content.mount(
                Vertical(
                    Label("Prompt Templates", classes="subsection-title"),
                    
                    # Positive prompt
                    Vertical(
                        Label("Positive Prompt Template:"),
                        TextArea(
                            text=prompts_config.get("positive_prompt", ""),
                            id="prompts-positive"
                        ),
                    ),
                    
                    # Negative prompt
                    Vertical(
                        Label("Negative Prompt Template:"),
                        TextArea(
                            text=prompts_config.get("negative_prompt", ""),
                            id="prompts-negative"
                        ),
                    ),
                    
                    # Prompt variations
                    Horizontal(
                        Label("Variations per prompt:"),
                        Input(
                            value=str(prompts_config.get("variations_per_prompt", 1)),
                            placeholder="1",
                            id="prompts-variations"
                        ),
                    ),
                    
                    classes="config-section",
                )
            )
        except Exception as e:
            log.error(f"Error setting up prompts tab: {e}")

    def _setup_vqa_tab(self) -> None:
        """Setup the VQA analysis configuration tab."""
        try:
            # Get VQA content container
            content = self.query_one("#vqa-content", Container)

            # Clear existing content
            content.remove_children()
            
            vqa_config = self.current_config.get("vqa_analysis", {})
            
            content.mount(
                Vertical(
                    Label("VQA Model Configuration", classes="subsection-title"),
                    
                    # Model selection
                    Horizontal(
                        Label("VQA Model:"),
                        Select(
                            options=[
                                ("llava-v1.5-7b", "llava-v1.5-7b"),
                                ("llava-v1.6-34b", "llava-v1.6-34b"),
                                ("cogvlm", "cogvlm"),
                            ],
                            value=vqa_config.get("model", "llava-v1.5-7b"),
                            id="vqa-model",
                        ),
                    ),
                    
                    # Analysis parameters
                    Horizontal(
                        Label("Max Tokens:"),
                        Input(
                            value=str(vqa_config.get("max_tokens", 100)),
                            placeholder="100",
                            id="vqa-max-tokens"
                        ),
                        Label("Temperature:"),
                        Input(
                            value=str(vqa_config.get("temperature", 0.1)),
                            placeholder="0.1",
                            id="vqa-temperature"
                        ),
                    ),
                    
                    # Questions
                    Vertical(
                        Label("Analysis Questions:"),
                        TextArea(
                            text="\n".join(vqa_config.get("questions", [])),
                            id="vqa-questions"
                        ),
                        Label("Enter one question per line"),
                    ),
                    
                    classes="config-section",
                )
            )
        except Exception as e:
            log.error(f"Error setting up VQA tab: {e}")

    def _setup_statistics_tab(self) -> None:
        """Setup the statistics configuration tab."""
        try:
            # Get statistics content container
            content = self.query_one("#statistics-content", Container)

            # Clear existing content
            content.remove_children()
            
            stats_config = self.current_config.get("statistics", {})
            
            content.mount(
                Vertical(
                    Label("Statistics Configuration", classes="subsection-title"),
                    
                    # Metrics to compute
                    Vertical(
                        Label("Metrics to Compute:"),
                        Checkbox(
                            "Gender Distribution",
                            value=stats_config.get("gender_distribution", True),
                            id="stats-gender"
                        ),
                        Checkbox(
                            "Age Distribution", 
                            value=stats_config.get("age_distribution", True),
                            id="stats-age"
                        ),
                        Checkbox(
                            "Ethnicity Distribution",
                            value=stats_config.get("ethnicity_distribution", True),
                            id="stats-ethnicity"
                        ),
                        Checkbox(
                            "Bias Scores",
                            value=stats_config.get("bias_scores", True),
                            id="stats-bias"
                        ),
                    ),
                    
                    # Output settings
                    Horizontal(
                        Label("Output Format:"),
                        Select(
                            options=[
                                ("json", "JSON"),
                                ("csv", "CSV"),
                                ("both", "Both"),
                            ],
                            value=stats_config.get("output_format", "json"),
                            id="stats-output-format"
                        ),
                    ),
                    
                    # Visualization settings
                    Checkbox(
                        "Generate Visualizations",
                        value=stats_config.get("generate_visualizations", True),
                        id="stats-visualizations"
                    ),
                    
                    classes="config-section",
                )
            )
        except Exception as e:
            log.error(f"Error setting up statistics tab: {e}")

    def _update_ui_state(self) -> None:
        """Update UI based on current configuration state."""
        if not self.config_state:
            return
            
        # Update status label
        if self.config_state.locked:
            status_text = f"[LOCKED by {self.config_state.locked_by_session}]"
            status_class = "error"
        elif self.config_state.validation_status == ValidationStatus.VALID:
            status_text = "[VALID]"
            status_class = "success"
        elif self.config_state.validation_status == ValidationStatus.INVALID:
            status_text = "[INVALID]"
            status_class = "error"
        else:
            status_text = "[UNKNOWN]"
            status_class = "warning"
            
        if self.status_label:
            self.status_label.update(status_text)
            self.status_label.add_class(status_class)
        
        # Update validation errors
        if self.validation_errors:
            if self.config_state.validation_errors:
                error_text = "\n".join(self.config_state.validation_errors)
                self.validation_errors.update(error_text)
                self.validation_errors.display = True
            else:
                self.validation_errors.display = False
        
        # Update button states
        if self.save_button and self.reset_button:
            # Disable save if locked or no changes
            save_disabled = self.config_state.locked or not self.has_unsaved_changes
            self.save_button.disabled = save_disabled
            
            # Disable reset if no changes or locked
            reset_disabled = self.config_state.locked or not self.has_unsaved_changes
            self.reset_button.disabled = reset_disabled

    def _collect_current_config(self) -> Dict[str, Any]:
        """Collect current configuration values from UI widgets."""
        config = {}
        
        try:
            # Generation config
            config["generation"] = {
                "model": self.query_one("#generation-model", Select).value,
                "width": int(self.query_one("#generation-width", Input).value or "512"),
                "height": int(self.query_one("#generation-height", Input).value or "512"),
                "num_steps": int(self.query_one("#generation-num-steps", Input).value or "4"),
                "guidance_scale": float(self.query_one("#generation-guidance-scale", Input).value or "3.5"),
                "seed": int(self.query_one("#generation-seed", Input).value or "42"),
                "random_seed": self.query_one("#generation-random-seed", Checkbox).value,
            }
            
            # Prompts config
            config["prompts"] = {
                "positive_prompt": self.query_one("#prompts-positive", TextArea).text,
                "negative_prompt": self.query_one("#prompts-negative", TextArea).text,
                "variations_per_prompt": int(self.query_one("#prompts-variations", Input).value or "1"),
            }
            
            # VQA config
            questions_text = self.query_one("#vqa-questions", TextArea).text
            questions = [q.strip() for q in questions_text.split("\n") if q.strip()]
            
            config["vqa_analysis"] = {
                "model": self.query_one("#vqa-model", Select).value,
                "max_tokens": int(self.query_one("#vqa-max-tokens", Input).value or "100"),
                "temperature": float(self.query_one("#vqa-temperature", Input).value or "0.1"),
                "questions": questions,
            }
            
            # Statistics config
            config["statistics"] = {
                "gender_distribution": self.query_one("#stats-gender", Checkbox).value,
                "age_distribution": self.query_one("#stats-age", Checkbox).value,
                "ethnicity_distribution": self.query_one("#stats-ethnicity", Checkbox).value,
                "bias_scores": self.query_one("#stats-bias", Checkbox).value,
                "output_format": self.query_one("#stats-output-format", Select).value,
                "generate_visualizations": self.query_one("#stats-visualizations", Checkbox).value,
            }
            
        except Exception as e:
            log.error(f"Error collecting configuration: {e}")
            self._show_error(f"Error collecting configuration: {e}")
            return self.current_config
            
        return config

    def _validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        try:
            # Validate generation config
            gen = config.get("generation", {})
            if gen.get("width", 0) <= 0:
                errors.append("Generation width must be positive")
            if gen.get("height", 0) <= 0:
                errors.append("Generation height must be positive")
            if gen.get("num_steps", 0) <= 0:
                errors.append("Number of steps must be positive")
            if gen.get("guidance_scale", 0) < 0:
                errors.append("Guidance scale must be non-negative")
            
            # Validate prompts config
            prompts = config.get("prompts", {})
            if not prompts.get("positive_prompt", "").strip():
                errors.append("Positive prompt cannot be empty")
            if prompts.get("variations_per_prompt", 0) <= 0:
                errors.append("Variations per prompt must be positive")
            
            # Validate VQA config
            vqa = config.get("vqa_analysis", {})
            if vqa.get("max_tokens", 0) <= 0:
                errors.append("VQA max tokens must be positive")
            if vqa.get("temperature", 0) < 0:
                errors.append("VQA temperature must be non-negative")
            questions = vqa.get("questions", [])
            if not questions:
                errors.append("VQA questions list cannot be empty")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
            
        return errors

    def _show_error(self, message: str) -> None:
        """Show an error message to the user."""
        if self.validation_errors:
            self.validation_errors.update(message)
            self.validation_errors.display = True

    def _on_config_changed(self) -> None:
        """Handle configuration changes."""
        # Collect current config
        new_config = self._collect_current_config()
        
        # Check if actually changed
        if new_config != self.current_config:
            self.current_config = new_config
            self.has_unsaved_changes = True
            
            # Validate
            errors = self._validate_config(new_config)
            
            # Update config state
            if self.config_state:
                self.config_state.sections = new_config
                self.config_state.validation_errors = errors
                self.config_state.validation_status = (
                    ValidationStatus.INVALID if errors else ValidationStatus.VALID
                )

                # Update UI
                self._update_ui_state()

                # Emit change message
                self.post_message(self.ConfigChanged(self.config_state))
            else:
                # Update UI even if config_state is None
                self._update_ui_state()

    # Event handlers
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes."""
        self._on_config_changed()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text area changes."""
        self._on_config_changed()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select dropdown changes."""
        self._on_config_changed()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        self._on_config_changed()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "save-button":
            self.action_save()
        elif button_id == "reset-button":
            self.action_reset()
        elif button_id == "cancel-button":
            self.action_cancel()

    # Actions
    def action_save(self) -> None:
        """Save the current configuration."""
        if not self.has_unsaved_changes:
            return
            
        if self.config_state and self.config_state.locked:
            self._show_error("Cannot save: Configuration is locked")
            return
            
        # Validate before saving
        errors = self._validate_config(self.current_config)
        if errors:
            self._show_error(f"Cannot save: Validation errors\n" + "\n".join(errors))
            return
            
        # Save configuration
        try:
            import yaml
            config_path = Path(self.config_path)
            
            with open(config_path, 'w') as f:
                yaml.dump(self.current_config, f, default_flow_style=False, indent=2)
            
            # Update state
            self.original_config = self.current_config.copy()
            self.has_unsaved_changes = False
            
            # Reload config state to get new modification time
            self._load_configuration()
            
            # Update UI
            self._update_ui_state()
            
            # Emit saved message
            self.post_message(self.ConfigSaved(self.config_path))
            
            log.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            log.error(f"Failed to save configuration: {e}")
            self._show_error(f"Failed to save configuration: {e}")

    def action_reset(self) -> None:
        """Reset configuration to original state."""
        if not self.has_unsaved_changes:
            return
            
        # Reset to original config
        self.current_config = self.original_config.copy()
        self.has_unsaved_changes = False
        
        # Refresh UI
        self._setup_generation_tab()
        self._setup_prompts_tab()
        self._setup_vqa_tab()
        self._setup_statistics_tab()
        
        # Update state
        if self.config_state:
            self.config_state.sections = self.current_config
            self.config_state.validation_errors = []
            self.config_state.validation_status = ValidationStatus.VALID
        
        self._update_ui_state()

    def action_cancel(self) -> None:
        """Cancel editing and return to previous screen."""
        if self.has_unsaved_changes:
            # Could show confirmation dialog here
            pass
        
        self.dismiss()

    def action_show_help(self) -> None:
        """Show help information."""
        help_text = """
Configuration Editor Help:

Controls:
- Ctrl+S: Save configuration
- Ctrl+R: Reset to original
- Esc: Cancel editing
- F1: Show this help

Tabs:
- Generation: Model and image generation settings
- Prompts: Prompt templates and variations
- VQA Analysis: Visual question answering configuration
- Statistics: Metrics and output settings

Validation:
- Configuration is validated in real-time
- Errors are shown at the top of the screen
- Cannot save if configuration is invalid or locked

Locking:
- Configuration becomes locked when an experiment is running
- Locked configurations cannot be modified
        """
        
        # Could show a modal dialog with help text
        log.info(help_text)

    def handle_resize(self, size: Size) -> None:
        """Handle terminal resize events."""
        # Adjust layout based on new size
        if size.width < 100:
            # Compact layout for small terminals
            try:
                self.query_one(TextArea).styles.height = "10"
                self.query_one(TabbedContent).styles.height = "15"
            except:
                pass
        else:
            # Full layout for normal terminals
            try:
                self.query_one(TextArea).styles.height = None
                self.query_one(TabbedContent).styles.height = None
            except:
                pass
        
        # Refresh validation status
        self._update_ui_state()