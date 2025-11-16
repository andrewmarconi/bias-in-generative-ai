"""
Main TUI Application for Bias Detection Framework.

Manages experiment lifecycle, screen navigation, and async-to-sync bridge.
"""

from typing import Optional, Dict, Any
from queue import Queue
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime
import logging

from bias_detector.tui.state.session import ErrorInfo

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer

# Fix relative imports by using absolute imports
import sys
from pathlib import Path

# Add project root to Python path for proper imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from bias_detector.tui.utils.structured_logger import get_logger
from bias_detector.tui.screens.progress import ProgressScreen
from bias_detector.tui.screens.metadata import MetadataScreen
from bias_detector.tui.screens.config_editor import ConfigEditorScreen
from bias_detector.tui.screens.history import HistoryScreen
from bias_detector.tui.screens.help import HelpScreen
from bias_detector.tui.screens.log_screen_simple import LogScreen
from bias_detector.tui.screens.experiment_control import ExperimentControl

from bias_detector.tui.widgets.error_panel import ErrorPanel

from bias_detector.tui.state.manager import StateManager
from bias_detector.tui.state.callbacks import QueueProgressCallback
from bias_detector.tui.state.session import ExperimentSession
from bias_detector.tui.utils.file_manager import FileManager
from bias_detector.experiment import BiasDetectionExperiment


logger = get_logger("bias_detector.tui.app")


class TUIApp(App):
    """
    Main TUI application for bias detection experiments.

    Features:
    - Launch new experiments with real-time monitoring
    - Reconnect to running experiments
    - Multi-screen navigation (F1-F4)
    - Graceful shutdown handling
    """

    TITLE = "Bias Detection Framework - Interactive TUI"
    SUB_TITLE = "Real-Time Experiment Monitoring"

    CSS = """
    Screen {
        background: $surface;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .error {
        color: $error;
        text-style: bold;
    }

    .success {
        color: $success;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("f1", "switch_screen('progress')", "Progress", show=True),
        Binding("f2", "switch_screen('metadata')", "Metadata", show=True),
        Binding("f3", "switch_screen('config')", "Config", show=True),
        Binding("f4", "switch_screen('history')", "History", show=True),
        Binding("f5", "switch_screen('logs')", "Logs", show=True),
        Binding("h", "show_help", "Help", show=True),
        Binding("ctrl+n", "launch_experiment", "New Experiment", show=True),
        Binding("p", "pause_experiment", "Pause", show=True),
        Binding("r", "resume_experiment", "Resume", show=True),
        Binding("c", "cancel_experiment", "Cancel", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(
        self,
        config_path: Optional[Path] = None,
        sessions_dir: Optional[Path] = None,
        **kwargs
    ):
        """
        Initialize TUI application.

        Args:
            config_path: Path to experiment config (default: config/experiment_config.yaml)
            sessions_dir: Path to sessions directory (default: data/sessions)
            **kwargs: Additional arguments passed to App
        """
        super().__init__(**kwargs)

        # Enhanced boot-up messaging with progress indicators and timing
        import sys
        import time
        
        # Track timing for boot process at class level
        self.boot_start_time = time.time()
        
        def boot_step(step: str, description: str = "", show_time: bool = True) -> None:
            """Print a boot step with consistent formatting and timing."""
            elapsed = f"({time.time() - self.boot_start_time:.1f}s)" if show_time else "(--.s)"
            print(f"⏳ {step} {elapsed}- {description}")
            
        def boot_success(step: str, show_time: bool = True) -> None:
            """Print a success indicator for a boot step."""
            elapsed = f"({time.time() - self.boot_start_time:.1f}s)" if show_time else ""
            print(f"✅ {step} {elapsed}")
            
        def boot_error(step: str, error: str) -> None:
            """Print an error indicator for a boot step."""
            elapsed = f"({time.time() - self.boot_start_time:.1f}s)"
            print(f"❌ {step} {elapsed}- {error}")
            
        def boot_section(title: str) -> None:
            """Print a section header."""
            print(f"\n🔷 {title}")
            print("=" * 50)
            
        # Start boot sequence with timing
        boot_step("INIT", "Starting framework initialization", show_time=False)
        boot_section("Bias Detection Framework - Interactive TUI")
        
        try:
            # Configuration
            boot_step("CONFIG", "Loading experiment configuration")
            self.config_path = config_path or Path("config/experiment_config.yaml")
            if sessions_dir:
                self.sessions_dir = Path(sessions_dir)
            else:
                # Default to data/sessions relative to project root
                # Detect project root by going up from bias_detector/tui/
                project_root = Path(__file__).resolve().parent.parent.parent
                self.sessions_dir = project_root / "data" / "sessions"
            boot_success("Configuration loaded")

            # State management
            boot_step("SESSIONS", "Initializing session management")
            self.state_manager = StateManager(sessions_dir=self.sessions_dir)
            boot_success("Session manager initialized")

            # File management
            boot_step("FILES", "Setting up file management")
            self.file_manager = FileManager(self.sessions_dir.parent)
            boot_success("File manager initialized")

            # Experiment execution
            boot_step("EXECUTOR", "Setting up experiment executor")
            self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="experiment")
            self.event_queue: Queue = Queue()
            self.current_experiment: Optional[BiasDetectionExperiment] = None
            self.experiment_future: Optional[Future] = None
            self.current_session: Optional[ExperimentSession] = None
            boot_success("Executor ready")

            # Screen components
            boot_step("SCREENS", "Initializing UI components")
            self.progress_screen: Optional[ProgressScreen] = None
            self.metadata_screen: Optional[MetadataScreen] = None
            self.history_screen: Optional[HistoryScreen] = None
            self.help_screen: Optional[HelpScreen] = None
            self.log_screen: Optional[LogScreen] = None
            self.control_screen: Optional[ExperimentControl] = None
            boot_success("Screen components ready")
            
        except Exception as e:
            boot_error("INITIALIZATION FAILED", str(e))
            print(f"\n💡 Debug info: {e}")
            print("🔧 Try: Check file permissions and dependencies")
            print("📋 Logs available in data/logs/ for troubleshooting")
            sys.exit(1)

    def on_mount(self) -> None:
        """Initialize application on mount."""
        # Show loading message
        self.title = "Bias Detection Framework - Loading..."
        
        # Enhanced boot-up messaging with progress tracking
        import time
        start_time = time.time()
        
        def mount_step(step: str, description: str = "") -> None:
            """Print a mount step with timing."""
            elapsed = f"({time.time() - start_time:.1f}s)"
            print(f"⏳ {step} {elapsed} - {description}")
            
        def mount_success(step: str) -> None:
            """Print success for a mount step."""
            elapsed = f"({time.time() - start_time:.1f}s)"
            print(f"✅ {step} {elapsed}")
            
        # Install screens with progress feedback
        mount_step("SCREENS", "Initializing UI components")
        
        mount_step("PROGRESS", "Creating progress monitor")
        try:
            self.progress_screen = ProgressScreen(event_queue=self.event_queue)
            self.install_screen(self.progress_screen, name="progress")
            mount_success("Progress screen")
        except Exception as e:
            print(f"❌ PROGRESS - Progress screen failed: {e}")
            raise

        mount_step("METADATA", "Creating configuration inspector")
        try:
            self.metadata_screen = MetadataScreen(
                config_path=str(self.config_path),
                state_manager=self.state_manager
            )
            self.install_screen(self.metadata_screen, name="metadata")
            mount_success("Metadata screen")
        except Exception as e:
            print(f"❌ METADATA - Metadata screen failed: {e}")
            raise

        mount_step("CONFIG", "Creating configuration editor")
        try:
            self.config_screen = ConfigEditorScreen(
                config_path=str(self.config_path),
                state_manager=self.state_manager
            )
            self.install_screen(self.config_screen, name="config")
            mount_success("Config editor")
        except Exception as e:
            print(f"❌ CONFIG - Config screen failed: {e}")
            raise

        mount_step("HISTORY", "Creating experiment browser")
        try:
            self.history_screen = HistoryScreen(
                state_manager=self.state_manager
            )
            self.install_screen(self.history_screen, name="history")
            mount_success("History screen")
        except Exception as e:
            print(f"❌ HISTORY - History screen failed: {e}")
            raise
        
        mount_step("HELP", "Creating help system")
        self.help_screen = HelpScreen()
        self.install_screen(self.help_screen, name="help")
        mount_success("Help system")
        
        mount_step("LOGS", "Creating log viewer")
        try:
            self.log_screen = LogScreen()
            self.install_screen(self.log_screen, name="logs")
            mount_success("Log viewer")
        except Exception as e:
            print(f"⚠️  LOGS - Log viewer failed to initialize: {e}")
            self.log_screen = None

        mount_step("CONTROL", "Creating experiment control center")
        try:
            self.control_screen = ExperimentControl()
            self.install_screen(self.control_screen, name="control")
            mount_success("Experiment control")
        except Exception as e:
            print(f"⚠️  CONTROL - Experiment control failed to initialize: {e}")
            self.control_screen = None

        # Error panel (not installed as persistent screen, used as modal)
        self.error_panel: Optional[ErrorPanel] = None
        
        mount_step("SESSIONS", "Checking for active experiments")
        # Check for active experiment and reconnect if found
        self._reconnect_to_active_experiment()
        
        # Final setup and ready message
        total_time = time.time() - self.boot_start_time
        print(f"\n🎉 TUI initialization complete in {total_time:.1f}s")
        print("=" * 50)
        
        # Update title to indicate ready state
        self.title = "Bias Detection Framework - Interactive TUI"
        
        # Ready message with navigation hints
        print("\n✨ Framework Ready!")
        print("📊 Navigation: F1=Progress  F2=Metadata  F3=Config  F4=History  F5=Logs")
        print("🚀 Actions: Ctrl+N=New  P=Pause  R=Resume  C=Cancel  H=Help")
        print("💡 Tip: Use 'tail -f data/logs/experiment.log' to monitor real-time logs")
        print()
        
        # Show progress screen by default
        try:
            self.push_screen("progress")
            logger.info("Successfully pushed progress screen")
        except Exception as e:
            logger.error(f"Failed to push progress screen: {e}")
            print(f"❌ Failed to show progress screen: {e}")

        # Schedule periodic maintenance tasks
        self._schedule_maintenance_tasks()

    def start_experiment(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[Path] = None
    ) -> str:
        """
        Start a new experiment in background thread.

        Args:
            config: Experiment configuration dict (optional)
            config_path: Path to config file (optional, defaults to self.config_path)

        Returns:
            Session ID of started experiment

        Raises:
            RuntimeError: If an experiment is already running
        """
        import time
        start_time = time.time()
        
        # Enhanced startup messaging
        print("\n🚀 Starting New Experiment...")
        print("=" * 50)
        
        # Check if experiment is already running
        if self.experiment_future and not self.experiment_future.done():
            print("❌ Experiment already running!")
            print("💡 Complete current experiment or wait for it to finish.")
            raise RuntimeError("An experiment is already running")

        print("📋 Creating new session...")
        # Create new session
        if config is None:
            config = self._load_config(config_path or self.config_path)

        session = self.state_manager.create_session(config=config)
        self.current_session = session
        print(f"✅ Session created: {session.session_id}")

        print("🔗 Setting up progress callback...")
        # Create callback for progress updates
        callback = QueueProgressCallback(event_queue=self.event_queue)

        print("🧪 Initializing experiment components...")
        # Create experiment instance
        self.current_experiment = BiasDetectionExperiment(
            config_path=str(config_path or self.config_path),
            callback=callback
        )

        print("⚙️  Configuring experiment systems...")
        # Initialize experiment components
        try:
            setup_start = time.time()
            self.current_experiment.setup()
            setup_time = time.time() - setup_start
            print(f"✅ Experiment setup complete ({setup_time:.2f}s)")
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            logger.error(f"Failed to setup experiment: {e}")
            raise

        print("🎯 Submitting to executor...")
        # Submit experiment to executor
        self.experiment_future = self.executor.submit(
            self._run_experiment_with_state_updates,
            session.session_id
        )

        total_time = time.time() - start_time
        print(f"🎉 Experiment launched successfully! ({total_time:.2f}s)")
        print("=" * 50)
        print(f"📊 Session ID: {session.session_id}")
        print("💡 Use F1 to monitor progress, P to pause, C to cancel")
        print()

        logger.info(f"Started experiment with session_id={session.session_id}")
        return session.session_id

    def _schedule_maintenance_tasks(self) -> None:
        """Schedule periodic maintenance tasks."""
        # Run log rotation every hour
        self.set_interval(3600.0, self._perform_log_rotation)

        # Run session cleanup every 6 hours
        self.set_interval(21600.0, self._perform_session_cleanup)

        # Run temp file cleanup daily
        self.set_interval(86400.0, self._perform_temp_cleanup)

    def _perform_log_rotation(self) -> None:
        """Perform log file rotation."""
        try:
            self.file_manager.rotate_log_files()
            logger.debug("Log rotation completed")
        except Exception as e:
            logger.error(f"Log rotation failed: {e}")

    def _perform_session_cleanup(self) -> None:
        """Perform session cleanup."""
        try:
            cleaned = self.file_manager.cleanup_old_sessions()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} old sessions")
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")

    def _perform_temp_cleanup(self) -> None:
        """Perform temporary file cleanup."""
        try:
            cleaned = self.file_manager.cleanup_temp_files()
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} temporary files")
        except Exception as e:
            logger.error(f"Temp cleanup failed: {e}")

    def _run_experiment_with_state_updates(self, session_id: str) -> None:
        """
        Run experiment and update state manager.

        This runs in a background thread.

        Args:
            session_id: Session ID to update
        """
        try:
            # Update session status to running
            self.state_manager.update_session_status(
                session_id=session_id,
                new_status="running"
            )

            # Run the experiment
            if self.current_experiment is None:
                raise RuntimeError("No experiment instance available")
            self.current_experiment.run_full_experiment(session_id=session_id)

            # Update session status to completed
            self.state_manager.update_session_status(
                session_id=session_id,
                new_status="completed"
            )

        except Exception as e:
            # Update session status to failed
            logger.error(f"Experiment {session_id} failed", error=e)
            from .state.session import ErrorInfo
            error_info = ErrorInfo(
                error_type=type(e).__name__,
                error_message=str(e),
                phase=0,  # Unknown phase at this level
                timestamp=datetime.now().isoformat(),
                traceback=None  # Could capture traceback.format_exc()
            )
            self.state_manager.update_session_status(
                session_id=session_id,
                new_status="failed",
                error=error_info
            )
            raise

    def _reconnect_to_active_experiment(self) -> None:
        """
        Reconnect to active experiment if one exists.

        Called on app startup to resume monitoring.

        Enhanced session recovery:
        - Detects interrupted experiments and offers recovery options
        - Restores UI state from persisted session data
        - Provides clear feedback about session status
        """
        print("📋 Scanning for active sessions...")
        active_session = self.state_manager.get_active_session()

        if not active_session:
            print("✨ No active sessions found")
            return

        print(f"🔄 Found session {active_session.session_id} ({active_session.status.value})")
        self.current_session = active_session
        logger.info(f"Found active session: {active_session.session_id}")

        # Handle different session states
        if active_session.status.value == "running":
            print(f"⚠️ Session {active_session.session_id} was interrupted during execution")
            print("💡 Session progress has been preserved - you can resume or restart")

            # For now, mark as cancelled but preserve progress data
            # Future: Offer resume/restart options
            from bias_detector.tui.state.session import ErrorInfo
            error_info = ErrorInfo(
                error_type="TUIInterrupt",
                error_message="TUI was restarted during execution",
                phase=active_session.current_phase,
                timestamp=datetime.now().isoformat(),
                remediation_hint="Session progress has been preserved. You can restart the experiment."
            )
            self.state_manager.update_session_status(
                session_id=active_session.session_id,
                new_status="cancelled",
                error=error_info
            )
            print(f"✅ Session marked as cancelled (progress preserved)")

        elif active_session.status.value == "paused":
            print(f"⏸️ Session {active_session.session_id} was paused")
            print("💡 You can resume this session from the progress screen")

        elif active_session.status.value == "pending":
            print(f"📋 Session {active_session.session_id} is ready to start")
            print("💡 Use Ctrl+N to launch the experiment")

        # Restore UI state from session
        print("🎨 Restoring UI state from session data...")
        self._restore_ui_from_session(active_session)
        print("✅ Session state restored successfully")

    def _restore_ui_from_session(self, session: ExperimentSession) -> None:
        """
        Restore UI state from a session.

        Args:
            session: Session to restore from
        """
        if not self.progress_screen:
            return

        logger.info(f"Restoring UI from session {session.session_id}")

        # Restore phase statuses
        for phase in session.phase_progress:
            self.progress_screen.update_phase_status(
                phase_num=phase.phase,
                status=phase.status.value
            )

            # If this was the last active phase, restore its progress
            if phase.status.value == "in_progress" or phase.items_done > 0:
                phase_name = phase.name
                self.progress_screen.update_phase_progress(
                    phase_num=phase.phase,
                    phase_name=phase_name,
                    items_done=phase.items_done,
                    items_total=phase.items_total
                )

        # Start metrics tracking if session has started
        if session.start_time:
            self.progress_screen.start_experiment_tracking()
            # TODO: Update metrics with actual elapsed time from session

    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """
        Load experiment configuration from YAML file.

        Args:
            config_path: Path to config file

        Returns:
            Configuration dictionary
        """
        import yaml

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config

    async def action_switch_screen(self, screen: str) -> None:
        """
        Switch to a different screen.

        Args:
            screen: Name of screen to switch to
        """
        try:
            self.switch_screen(screen)
        except Exception as e:
            logger.error(f"Failed to switch to screen '{screen}': {e}")

    def action_launch_experiment(self) -> None:
        """Launch a new experiment (Ctrl+N)."""
        logger.user_action("launch_experiment", component="tui_app")
        
        try:
            # Check if experiment is already active
            active_session = self.state_manager.get_active_session()
            if active_session and active_session.status.value in ("pending", "running", "paused"):
                logger.error("Cannot start new experiment: another experiment is already active", component="tui_app")
                # Could show error dialog here
                return
                
            with logger.start_timer("experiment_launch"):
                session_id = self.start_experiment()
            logger.info(f"Launched experiment: {session_id}", component="tui_app")
            logger.experiment_event("started", session_id, component="tui_app")
        except RuntimeError as e:
            logger.error(f"Failed to launch experiment: {e}", component="tui_app", error=e)
            # Could show error dialog here

    def action_pause_experiment(self) -> None:
        """Pause the current experiment."""
        if not self.current_session:
            logger.warning("No active experiment to pause")
            return
            
        if self.current_session.status.value != "running":
            logger.warning(f"Cannot pause experiment: not running (status: {self.current_session.status.value})")
            return
            
        try:
            # Pause through state manager
            self.state_manager.pause_session(self.current_session.session_id)
            
            # Pause the experiment instance
            if self.current_experiment:
                self.current_experiment.pause()
                
            logger.info(f"Paused experiment: {self.current_session.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to pause experiment: {e}")

    def action_resume_experiment(self) -> None:
        """Resume the current experiment."""
        if not self.current_session:
            logger.warning("No active experiment to resume")
            return
            
        if self.current_session.status.value != "paused":
            logger.warning(f"Cannot resume experiment: not paused (status: {self.current_session.status.value})")
            return
            
        try:
            # Resume through state manager
            self.state_manager.resume_session(self.current_session.session_id)
            
            # Resume the experiment instance
            if self.current_experiment:
                self.current_experiment.resume()
                
            logger.info(f"Resumed experiment: {self.current_session.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to resume experiment: {e}")

    def action_cancel_experiment(self) -> None:
        """Cancel the current experiment with confirmation."""
        if not self.current_session:
            logger.warning("No active experiment to cancel")
            return
            
        if self.current_session.status.value in ("completed", "failed", "cancelled"):
            logger.warning(f"Cannot cancel experiment: already terminal (status: {self.current_session.status.value})")
            return
            
        # For now, just cancel without confirmation dialog
        # TODO: Add confirmation dialog in future polish phase
        try:
            # Cancel through state manager
            self.state_manager.cancel_session(self.current_session.session_id, "User cancelled from TUI")
            
            # Cancel the experiment instance
            if self.current_experiment:
                self.current_experiment.cancel("User cancelled from TUI")
                
            logger.info(f"Cancelled experiment: {self.current_session.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to cancel experiment: {e}")

    def action_show_help(self) -> None:
        """Show the help overlay screen."""
        try:
            self.push_screen("help")
        except Exception as e:
            logger.error(f"Failed to show help screen: {e}")

    def action_show_errors(self) -> None:
        """Show the error panel."""
        try:
            if not self.error_panel:
                self.error_panel = ErrorPanel()
            self.push_screen(self.error_panel)
        except Exception as e:
            logger.error(f"Failed to show error panel: {e}")

    def show_error(self, message: str, source: str = "Unknown", level: str = "ERROR", traceback: Optional[str] = None) -> None:
        """
        Show an error notification.

        Args:
            message: Error message
            source: Error source/location
            level: Error level (ERROR, WARNING, INFO)
            traceback: Optional traceback information
        """
        try:
            # Show toast notification
            severity_map = {
                "ERROR": "error",
                "WARNING": "warning",
                "INFO": "information"
            }
            severity = severity_map.get(level.upper(), "error")

            # Create notification message
            title = f"{level}: {source}"
            if len(message) > 100:
                message = message[:97] + "..."

            self.notify(
                message,
                title=title,
                severity="error",  # Use literal string
                timeout=8
            )

            # Also log to structured logger
            logger.error(f"{source}: {message}", component="tui_error")

            # For critical errors, also show error panel
            if level.upper() == "ERROR" and self.error_panel:
                if not self.error_panel:
                    self.error_panel = ErrorPanel()

                self.error_panel.add_error(message, source, level, traceback)

                # Show error panel if not already visible
                if not isinstance(self.screen, ErrorPanel):
                    self.push_screen(self.error_panel)

        except Exception as e:
            # Fallback to basic logging if notification fails
            print(f"ERROR: {source} - {message}")
            logger.error(f"Failed to show error notification: {e}")

    def show_success(self, message: str, title: str = "Success") -> None:
        """
        Show a success notification.

        Args:
            message: Success message
            title: Notification title
        """
        try:
            self.notify(
                message,
                title=title,
                severity="information",
                timeout=5
            )
        except Exception as e:
            logger.error(f"Failed to show success notification: {e}")

    def show_warning(self, message: str, title: str = "Warning") -> None:
        """
        Show a warning notification.

        Args:
            message: Warning message
            title: Notification title
        """
        try:
            self.notify(
                message,
                title=title,
                severity="warning",
                timeout=6
            )
        except Exception as e:
            logger.error(f"Failed to show warning notification: {e}")

    async def action_quit(self) -> None:
        """Quit the application with cleanup."""
        await self._cleanup()
        await super().action_quit()

    async def _cleanup(self) -> None:
        """Clean up resources before shutdown."""
        # Shutdown executor gracefully
        self.executor.shutdown(wait=True, cancel_futures=False)
        logger.info("TUI application shutdown complete")

    def on_resize(self, event) -> None:
        """Handle terminal resize events."""
        logger.debug(f"Terminal resized to {event.size.width}x{event.size.height}")
        
        # Note: Screen resize handling is delegated to individual screens
