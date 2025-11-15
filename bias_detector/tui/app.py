"""
Main TUI Application for Bias Detection Framework.

Manages experiment lifecycle, screen navigation, and async-to-sync bridge.
"""

from typing import Optional, Dict, Any
from queue import Queue
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future
import logging

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer

from .screens.progress import ProgressScreen
from .screens.metadata import MetadataScreen
from .screens.config_editor import ConfigEditorScreen
from .state.manager import StateManager
from .state.callbacks import QueueProgressCallback
from .state.session import ExperimentSession
from ..experiment import BiasDetectionExperiment


logger = logging.getLogger(__name__)


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
        Binding("ctrl+n", "launch_experiment", "New Experiment", show=True),
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

        # Configuration
        self.config_path = config_path or Path("config/experiment_config.yaml")
        if sessions_dir:
            self.sessions_dir = Path(sessions_dir)
        else:
            # Default to data/sessions relative to project root
            # Detect project root by going up from bias_detector/tui/
            project_root = Path(__file__).resolve().parent.parent.parent
            self.sessions_dir = project_root / "data" / "sessions"

        # State management
        self.state_manager = StateManager(sessions_dir=self.sessions_dir)

        # Experiment execution
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="experiment")
        self.event_queue: Queue = Queue()
        self.current_experiment: Optional[BiasDetectionExperiment] = None
        self.experiment_future: Optional[Future] = None
        self.current_session: Optional[ExperimentSession] = None

        # Screens
        self.progress_screen: Optional[ProgressScreen] = None
        self.metadata_screen: Optional[MetadataScreen] = None

    def on_mount(self) -> None:
        """Initialize application on mount."""
        # Install screens
        self.progress_screen = ProgressScreen(event_queue=self.event_queue)
        self.install_screen(self.progress_screen, name="progress")
        
        # Metadata screen
        self.metadata_screen = MetadataScreen(
            config_path=str(self.config_path),
            state_manager=self.state_manager
        )
        self.install_screen(self.metadata_screen, name="metadata")
        
        # Configuration editor screen
        self.config_screen = ConfigEditorScreen(
            config_path=str(self.config_path),
            state_manager=self.state_manager
        )
        self.install_screen(self.config_screen, name="config")

        # Placeholder screens (will be implemented in later phases)
        # self.install_screen(HistoryScreen(), name="history")

        # Show progress screen by default
        self.push_screen("progress")

        # Check for active experiment and reconnect if found
        self._reconnect_to_active_experiment()

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
            Session ID of the started experiment

        Raises:
            RuntimeError: If an experiment is already running
        """
        # Check if experiment is already running
        if self.experiment_future and not self.experiment_future.done():
            raise RuntimeError("An experiment is already running")

        # Create new session
        if config is None:
            config = self._load_config(config_path or self.config_path)

        session = self.state_manager.create_session(config=config)
        self.current_session = session

        # Create callback for progress updates
        callback = QueueProgressCallback(event_queue=self.event_queue)

        # Create experiment instance
        self.current_experiment = BiasDetectionExperiment(
            config_path=str(config_path or self.config_path),
            callback=callback
        )

        # Submit experiment to executor
        self.experiment_future = self.executor.submit(
            self._run_experiment_with_state_updates,
            session.session_id
        )

        logger.info(f"Started experiment with session_id={session.session_id}")
        return session.session_id

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
            self.current_experiment.run_full_experiment(session_id=session_id)

            # Update session status to completed
            self.state_manager.update_session_status(
                session_id=session_id,
                new_status="completed"
            )

        except Exception as e:
            # Update session status to failed
            logger.exception(f"Experiment {session_id} failed")
            self.state_manager.update_session_status(
                session_id=session_id,
                new_status="failed",
                error={
                    "type": type(e).__name__,
                    "message": str(e),
                    "traceback": None  # Could capture traceback.format_exc()
                }
            )
            raise

    def _reconnect_to_active_experiment(self) -> None:
        """
        Reconnect to active experiment if one exists.

        Called on app startup to resume monitoring.

        Note: In current implementation, experiments run in-process via ThreadPoolExecutor.
        If the TUI is restarted, the experiment thread is lost. Therefore, we mark any
        "running" sessions as "cancelled" and restore their last known state to the UI.

        Future enhancement: Run experiments as separate processes for true reconnection.
        """
        active_session = self.state_manager.get_active_session()

        if not active_session:
            return

        self.current_session = active_session
        logger.info(f"Found active session: {active_session.session_id}")

        # Since experiments run in-process, a restart means the experiment thread was lost
        if active_session.status.value == "running":
            logger.warning(
                f"Session {active_session.session_id} was running but TUI was restarted. "
                "Marking as cancelled."
            )
            self.state_manager.update_session_status(
                session_id=active_session.session_id,
                new_status="cancelled"
            )
            # Reload session with updated status
            active_session = self.state_manager.get_session(active_session.session_id)

        # Restore UI state from session
        self._restore_ui_from_session(active_session)

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
                phase_num=phase.phase_num,
                status=phase.status.value
            )

            # If this was the last active phase, restore its progress
            if phase.status.value == "in_progress" or phase.items_done > 0:
                phase_name = session.phase_progress[phase.phase_num - 1].phase_name
                self.progress_screen.update_phase_progress(
                    phase_num=phase.phase_num,
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

    def action_switch_screen(self, screen_name: str) -> None:
        """
        Switch to a different screen.

        Args:
            screen_name: Name of screen to switch to
        """
        try:
            self.switch_screen(screen_name)
        except Exception as e:
            logger.error(f"Failed to switch to screen '{screen_name}': {e}")

    def action_launch_experiment(self) -> None:
        """Launch a new experiment (Ctrl+N)."""
        try:
            session_id = self.start_experiment()
            logger.info(f"Launched experiment: {session_id}")
        except RuntimeError as e:
            logger.error(f"Failed to launch experiment: {e}")
            # Could show error dialog here

    async def action_quit(self) -> None:
        """Quit the application with cleanup."""
        await self._cleanup()
        await super().action_quit()

    async def _cleanup(self) -> None:
        """Clean up resources before shutdown."""
        # Shutdown executor gracefully
        self.executor.shutdown(wait=True, cancel_futures=False)
        logger.info("TUI application shutdown complete")
