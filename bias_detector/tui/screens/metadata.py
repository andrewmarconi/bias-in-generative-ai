"""
Metadata Screen for Experiment Configuration Inspection.

Displays experiment configuration in organized tabbed sections for
generation, prompts, VQA, and statistics settings.
"""

from typing import Dict, Any
from pathlib import Path
import asyncio
import time

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Tab, Tabs, Static, Label, Pretty
)
from textual.reactive import reactive
from textual.binding import Binding

from ..state.manager import StateManager


class MetadataScreen(Screen):
    """Screen for inspecting experiment configuration metadata.
    
    Features:
    - Tabbed interface for different config sections
    - Real-time configuration display
    - Validation status indicators
    - Lock status display
    """
    
    BINDINGS = [
        Binding("f1", "switch_screen('progress')", "Progress", show=True),
        Binding("f2", "switch_screen('metadata')", "Metadata", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]
    
    config_state: reactive[Dict[str, Any]] = reactive({})
    last_modified: reactive[float] = reactive(0)
    
    def __init__(
        self,
        config_path: str = "config/experiment_config.yaml",
        state_manager: StateManager | None = None,
        **kwargs
    ):
        """Initialize metadata screen.
        
        Args:
            config_path: Path to configuration file
            state_manager: StateManager instance for loading config
            **kwargs: Additional arguments passed to Screen
        """
        super().__init__(**kwargs)
        self.config_path = config_path
        self.state_manager = state_manager or StateManager()
        self._file_watcher_task = None
        
    def compose(self) -> ComposeResult:
        """Compose the metadata screen UI."""
        yield Container(
            Vertical(
                # Header
                Container(
                    Label("📋 Experiment Configuration", classes="section-title"),
                    Label(f"Config: {self.config_path}", classes="config-path"),
                    classes="header",
                ),
                
                # Status bar
                Horizontal(
                    Label("Status: ", classes="status-label"),
                    Label("Loading...", id="validation-status", classes="status-value"),
                    Label(" | Locked: ", classes="status-label"),
                    Label("No", id="lock-status", classes="status-value"),
                    classes="status-bar",
                ),
                
                # Tabbed content
                Tabs(
                    Tab("Generation", id="generation-tab"),
                    Tab("Prompts", id="prompts-tab"),
                    Tab("VQA Analysis", id="vqa-tab"),
                    Tab("Statistics", id="statistics-tab"),
                ),
                
                # Content container
                Container(id="content-container"),
                
                classes="metadata-screen",
            )
        )
        

    
    def on_mount(self) -> None:
        """Initialize screen when mounted."""
        self.refresh_config()
        self._setup_tab_content()
        self._start_file_watcher()
    
    def on_unmount(self) -> None:
        """Cleanup when screen is unmounted."""
        self._stop_file_watcher()
    
    def watch_config_state(self, config_state: Dict[str, Any]) -> None:
        """React to configuration state changes."""
        self._update_status_display()
        self._update_tab_content()
    
    def refresh_config(self) -> None:
        """Refresh configuration from file."""
        try:
            self.config_state = self.state_manager.get_config_state(self.config_path)
        except Exception as e:
            self.config_state = {
                "validation_status": "invalid",
                "validation_errors": [f"Failed to load config: {str(e)}"],
                "sections": {}
            }
    
    def _update_status_display(self) -> None:
        """Update status bar with current config state."""
        if not self.config_state:
            return
            
        # Update validation status
        validation_status = self.config_state.get("validation_status", "unknown")
        status_widget = self.query_one("#validation-status", Label)
        
        if validation_status == "valid":
            status_widget.update("✅ Valid")
            status_widget.add_class("valid")
        elif validation_status == "invalid":
            status_widget.update("❌ Invalid")
            status_widget.add_class("invalid")
        else:
            status_widget.update("⚠️ Unknown")
            status_widget.add_class("unknown")
        
        # Update lock status
        locked = self.config_state.get("locked", False)
        lock_widget = self.query_one("#lock-status", Label)
        
        if locked:
            locked_by = self.config_state.get("locked_by_session", "unknown")
            lock_widget.update(f"🔒 Yes (by {locked_by})")
            lock_widget.add_class("locked")
        else:
            lock_widget.update("🔓 No")
            lock_widget.add_class("unlocked")
    
    def _setup_tab_content(self) -> None:
        """Setup initial tab content."""
        self._update_tab_content()
    
    def _update_tab_content(self) -> None:
        """Update content for all tabs."""
        if not self.config_state:
            return
            
        sections = self.config_state.get("sections", {})
        
        # Update each tab content
        self._update_generation_tab(sections.get("generation", {}))
        self._update_prompts_tab(sections.get("prompts", {}))
        self._update_vqa_tab(sections.get("vqa_analysis", {}))
        self._update_statistics_tab(sections.get("statistics", {}))
    
    def _update_generation_tab(self, generation_config: Dict[str, Any]) -> None:
        """Update generation settings tab."""
        content = self._create_generation_content(generation_config)
        self._set_tab_content("generation", content)
    
    def _update_prompts_tab(self, prompts_config: Dict[str, Any]) -> None:
        """Update prompts tab."""
        content = self._create_prompts_content(prompts_config)
        self._set_tab_content("prompts", content)
    
    def _update_vqa_tab(self, vqa_config: Dict[str, Any]) -> None:
        """Update VQA analysis tab."""
        content = self._create_vqa_content(vqa_config)
        self._set_tab_content("vqa", content)
    
    def _update_statistics_tab(self, statistics_config: Dict[str, Any]) -> None:
        """Update statistics tab."""
        content = self._create_statistics_content(statistics_config)
        self._set_tab_content("statistics", content)
    
    def _set_tab_content(self, tab_name: str, content) -> None:
        """Set content for a specific tab."""
        # Clear existing content
        container = self.query_one("#content-container", Container)
        container.remove_children()
        
        # Add new content
        container.mount(content)
    
    def _create_generation_content(self, config: Dict[str, Any]) -> Container:
        """Create generation settings content panel."""
        return Container(
            Vertical(
                Label("⚙️ Generation Settings", classes="panel-title"),
                
                # Model settings
                Container(
                    Label("Model Configuration", classes="subsection-title"),
                    Label(f"Model: {config.get('model', 'N/A')}"),
                    Label(f"Num Images per Prompt: {config.get('num_images_per_prompt', 'N/A')}"),
                    Label(f"Steps: {config.get('num_inference_steps', 'N/A')}"),
                    Label(f"Guidance Scale: {config.get('guidance_scale', 'N/A')}"),
                    Label(f"Seed: {config.get('seed', 'N/A')}"),
                    classes="subsection",
                ),
                
                # Output settings
                Container(
                    Label("Output Configuration", classes="subsection-title"),
                    Label(f"Output Directory: {config.get('output_dir', 'N/A')}"),
                    Label(f"Image Format: {config.get('image_format', 'N/A')}"),
                    classes="subsection",
                ),
                
                classes="content-panel",
            )
        )
    
    def _create_prompts_content(self, config: Dict[str, Any]) -> Container:
        """Create prompts content panel."""
        return Container(
            Vertical(
                Label("💬 Prompt Configuration", classes="panel-title"),
                
                # Occupational prompts
                Container(
                    Label("Occupational Prompts", classes="subsection-title"),
                    *[
                        Label(f"• {prompt}", classes="prompt-item")
                        for prompt in config.get("occupational", [])
                    ],
                    classes="subsection",
                ) if config.get("occupational") else Container(
                    Label("No occupational prompts configured", classes="empty-section"),
                    classes="subsection",
                ),
                
                # Contextual prompts
                Container(
                    Label("Contextual Prompts", classes="subsection-title"),
                    *[
                        Label(f"• {prompt}", classes="prompt-item")
                        for prompt in config.get("contextual", [])
                    ],
                    classes="subsection",
                ) if config.get("contextual") else Container(
                    Label("No contextual prompts configured", classes="empty-section"),
                    classes="subsection",
                ),
                
                # Neutral prompts
                Container(
                    Label("Neutral Prompts", classes="subsection-title"),
                    *[
                        Label(f"• {prompt}", classes="prompt-item")
                        for prompt in config.get("neutral", [])
                    ],
                    classes="subsection",
                ) if config.get("neutral") else Container(
                    Label("No neutral prompts configured", classes="empty-section"),
                    classes="subsection",
                ),
                
                classes="content-panel",
            )
        )
    
    def _create_vqa_content(self, config: Dict[str, Any]) -> Container:
        """Create VQA analysis content panel."""
        return Container(
            Vertical(
                Label("🔍 VQA Analysis Configuration", classes="panel-title"),
                
                # Model settings
                Container(
                    Label("VQA Model", classes="subsection-title"),
                    Label(f"Model: {config.get('model', 'N/A')}"),
                    Label(f"Provider: {config.get('provider', 'N/A')}"),
                    classes="subsection",
                ),
                
                # Questions
                Container(
                    Label("Analysis Questions", classes="subsection-title"),
                    *[
                        Label(f"• {question}", classes="question-item")
                        for question in config.get("questions", [])
                    ],
                    classes="subsection",
                ) if config.get("questions") else Container(
                    Label("No VQA questions configured", classes="empty-section"),
                    classes="subsection",
                ),
                
                # Response options
                Container(
                    Label("Response Options", classes="subsection-title"),
                    *[
                        Label(f"• {option}", classes="option-item")
                        for option in config.get("response_options", [])
                    ],
                    classes="subsection",
                ) if config.get("response_options") else Container(
                    Label("No response options configured", classes="empty-section"),
                    classes="subsection",
                ),
                
                classes="content-panel",
            )
        )
    
    def _create_statistics_content(self, config: Dict[str, Any]) -> Container:
        """Create statistics content panel."""
        return Container(
            Vertical(
                Label("📊 Statistics Configuration", classes="panel-title"),
                
                # Analysis settings
                Container(
                    Label("Statistical Analysis", classes="subsection-title"),
                    Label(f"Confidence Level: {config.get('confidence_level', 'N/A')}"),
                    Label(f"Significance Threshold: {config.get('significance_threshold', 'N/A')}"),
                    Label(f"Effect Size Threshold: {config.get('effect_size_threshold', 'N/A')}"),
                    classes="subsection",
                ),
                
                # Tests
                Container(
                    Label("Statistical Tests", classes="subsection-title"),
                    *[
                        Label(f"• {test}", classes="test-item")
                        for test in config.get("tests", [])
                    ],
                    classes="subsection",
                ) if config.get("tests") else Container(
                    Label("No statistical tests configured", classes="empty-section"),
                    classes="subsection",
                ),
                
                # Output settings
                Container(
                    Label("Output Settings", classes="subsection-title"),
                    Label(f"Results Format: {config.get('results_format', 'N/A')}"),
                    Label(f"Include Plots: {config.get('include_plots', 'N/A')}"),
                    Label(f"Plot Format: {config.get('plot_format', 'N/A')}"),
                    classes="subsection",
                ),
                
                classes="content-panel",
            )
        )
    
    def action_refresh(self) -> None:
        """Refresh configuration display."""
        self.refresh_config()
    
    def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle tab activation."""
        # Update content when tab is activated
        self._update_tab_content()
    
    def _start_file_watcher(self) -> None:
        """Start background task to watch for config file changes."""
        if self._file_watcher_task is None:
            self._file_watcher_task = self.set_interval(2.0, self._check_config_changes)
    
    def _stop_file_watcher(self) -> None:
        """Stop file watcher task."""
        if self._file_watcher_task:
            self._file_watcher_task.stop()
            self._file_watcher_task = None
    
    def _check_config_changes(self) -> None:
        """Check if config file has been modified."""
        try:
            config_path_obj = Path(self.config_path)
            if not config_path_obj.exists():
                return
            
            current_modified = config_path_obj.stat().st_mtime
            
            # Check if file was modified since last check
            if current_modified > self.last_modified:
                self.last_modified = current_modified
                self.refresh_config()
                
        except Exception:
            # Ignore file watching errors to avoid disrupting UI
            pass