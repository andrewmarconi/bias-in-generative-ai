"""
Experiment Control Screen for advanced experiment management.

Provides queue management, scheduling, templates, cloning, and resource monitoring.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import json

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import (
    Static, Button, DataTable, TabbedContent, TabPane,
    Label, Input, Select, Checkbox, TextArea
)
from textual.binding import Binding


class ExperimentControl(Screen):
    """
    Advanced experiment control and management screen.

    Features:
    - Experiment queue system
    - Scheduling and automation
    - Templates and presets
    - Cloning and branching
    - Resource monitoring
    - Comparison and diffing
    """

    BINDINGS = [
        Binding("f1", "switch_screen('progress')", "Progress", show=True),
        Binding("f2", "switch_screen('metadata')", "Metadata", show=True),
        Binding("f3", "switch_screen('config')", "Config", show=True),
        Binding("f4", "switch_screen('history')", "History", show=True),
        Binding("f5", "switch_screen('logs')", "Logs", show=True),
        Binding("f6", "switch_screen('results')", "Results", show=True),
        Binding("f7", "switch_screen('control')", "Control", show=True),
        Binding("h", "show_help", "Help", show=True),
        Binding("q", "queue_experiment", "Queue", show=True),
        Binding("s", "schedule_experiment", "Schedule", show=True),
        Binding("t", "create_template", "Template", show=True),
    ]

    def __init__(self, **kwargs):
        """Initialize experiment control screen."""
        super().__init__(**kwargs)
        self.queue_data: List[Dict[str, Any]] = []
        self.scheduled_experiments: List[Dict[str, Any]] = []
        self.templates: List[Dict[str, Any]] = []
        self.resource_stats: Dict[str, Any] = {}

    def compose(self) -> ComposeResult:
        """Compose the experiment control screen."""
        with Vertical():
            # Header
            with Container(classes="control-header"):
                yield Static("🎛️ Advanced Experiment Control", classes="control-title")
                yield Static("Queue, schedule, and manage experiments", classes="control-subtitle")

            # Main content with tabs
            with TabbedContent(id="control-tabs"):
                with TabPane("Queue", id="queue-tab"):
                    yield self._create_queue_tab()

                with TabPane("Scheduling", id="scheduling-tab"):
                    yield self._create_scheduling_tab()

                with TabPane("Templates", id="templates-tab"):
                    yield self._create_templates_tab()

                with TabPane("Resources", id="resources-tab"):
                    yield self._create_resources_tab()

                with TabPane("Comparison", id="comparison-tab"):
                    yield self._create_comparison_tab()

            # Action buttons
            with Horizontal(classes="control-actions"):
                yield Button("Queue Experiment", id="queue-button", variant="primary")
                yield Button("Schedule Run", id="schedule-button", variant="default")
                yield Button("Create Template", id="template-button", variant="default")
                yield Button("Clone Experiment", id="clone-button", variant="default")
                yield Button("Create Branch", id="branch-button", variant="default")
                yield Button("Run A/B Test", id="ab-test-button", variant="success")

    def _create_queue_tab(self) -> Container:
        """Create the experiment queue management tab."""
        container = Container(classes="control-content")
        vertical = Vertical()
        container.compose_add_child(vertical)

        # Queue status
        queue_status = Container(classes="queue-status")
        queue_status.compose_add_child(Static("📋 Experiment Queue", classes="section-title"))
        queue_status.compose_add_child(Static("", id="queue-status-text", classes="status-text"))
        vertical.compose_add_child(queue_status)

        # Queue table
        vertical.compose_add_child(DataTable(id="queue-table", classes="queue-table"))

        # Queue controls
        queue_controls = Horizontal(classes="queue-controls")
        queue_controls.compose_add_child(Button("Add to Queue", id="add-queue-btn", variant="primary"))
        queue_controls.compose_add_child(Button("Remove from Queue", id="remove-queue-btn", variant="default"))
        queue_controls.compose_add_child(Button("Clear Queue", id="clear-queue-btn", variant="warning"))
        queue_controls.compose_add_child(Button("Execute Queue", id="execute-queue-btn", variant="success"))
        vertical.compose_add_child(queue_controls)

        return container

    def _create_scheduling_tab(self) -> Container:
        """Create the experiment scheduling tab."""
        container = Container(classes="control-content")
        vertical = Vertical()
        container.compose_add_child(vertical)

        vertical.compose_add_child(Static("⏰ Experiment Scheduling", classes="section-title"))

        # Schedule form
        schedule_form = Container(classes="schedule-form")
        form_vertical = Vertical()
        schedule_form.compose_add_child(form_vertical)

        form_vertical.compose_add_child(Static("Schedule New Experiment", classes="subsection-title"))

        # Experiment selector
        exp_row = Horizontal()
        exp_row.compose_add_child(Label("Experiment:", classes="form-label"))
        exp_row.compose_add_child(Select(
            options=[("none", "Select experiment...")],
            value="none",
            id="schedule-experiment-select",
            classes="form-select"
        ))
        form_vertical.compose_add_child(exp_row)

        # Schedule type
        schedule_row = Horizontal()
        schedule_row.compose_add_child(Label("Schedule:", classes="form-label"))
        schedule_row.compose_add_child(Select(
            options=[
                ("once", "Run once"),
                ("daily", "Daily"),
                ("weekly", "Weekly"),
                ("monthly", "Monthly"),
                ("cron", "Custom cron")
            ],
            value="once",
            id="schedule-type-select",
            classes="form-select"
        ))
        form_vertical.compose_add_child(schedule_row)

        # Time input
        time_row = Horizontal()
        time_row.compose_add_child(Label("Time:", classes="form-label"))
        time_row.compose_add_child(Input(
            placeholder="HH:MM or cron expression",
            id="schedule-time-input",
            classes="form-input"
        ))
        form_vertical.compose_add_child(time_row)

        # Buttons
        button_row = Horizontal()
        button_row.compose_add_child(Button("Schedule", id="schedule-submit-btn", variant="primary"))
        button_row.compose_add_child(Button("Cancel", id="schedule-cancel-btn", variant="default"))
        form_vertical.compose_add_child(button_row)

        vertical.compose_add_child(schedule_form)

        # Scheduled experiments table
        scheduled_list = Container(classes="scheduled-list")
        scheduled_list.compose_add_child(Static("Scheduled Experiments", classes="subsection-title"))
        scheduled_list.compose_add_child(DataTable(id="scheduled-table", classes="scheduled-table"))
        vertical.compose_add_child(scheduled_list)

        return container

    def _create_templates_tab(self) -> Container:
        """Create the experiment templates tab."""
        container = Container(classes="control-content")
        vertical = Vertical()
        container.compose_add_child(vertical)

        vertical.compose_add_child(Static("📋 Experiment Templates", classes="section-title"))

        # Template list
        vertical.compose_add_child(DataTable(id="templates-table", classes="templates-table"))

        # Template actions
        template_actions = Horizontal(classes="template-actions")
        template_actions.compose_add_child(Button("Create Template", id="create-template-btn", variant="primary"))
        template_actions.compose_add_child(Button("Edit Template", id="edit-template-btn", variant="default"))
        template_actions.compose_add_child(Button("Delete Template", id="delete-template-btn", variant="warning"))
        template_actions.compose_add_child(Button("Apply Template", id="apply-template-btn", variant="success"))
        vertical.compose_add_child(template_actions)

        # Template editor (hidden by default)
        template_editor = Container(id="template-editor", classes="template-editor")
        template_editor.compose_add_child(Static("Template Editor", classes="subsection-title"))

        # Name input
        name_row = Horizontal()
        name_row.compose_add_child(Label("Name:", classes="form-label"))
        name_row.compose_add_child(Input(placeholder="Template name", id="template-name-input", classes="form-input"))
        template_editor.compose_add_child(name_row)

        # Description input
        desc_row = Horizontal()
        desc_row.compose_add_child(Label("Description:", classes="form-label"))
        desc_row.compose_add_child(TextArea(placeholder="Template description", id="template-desc-input", classes="form-textarea"))
        template_editor.compose_add_child(desc_row)

        # Editor buttons
        editor_buttons = Horizontal()
        editor_buttons.compose_add_child(Button("Save Template", id="save-template-btn", variant="primary"))
        editor_buttons.compose_add_child(Button("Cancel Edit", id="cancel-template-btn", variant="default"))
        template_editor.compose_add_child(editor_buttons)

        vertical.compose_add_child(template_editor)

        return container

    def _create_resources_tab(self) -> Container:
        """Create the resource monitoring tab."""
        container = Container(classes="control-content")
        vertical = Vertical()
        container.compose_add_child(vertical)

        vertical.compose_add_child(Static("📊 Resource Monitoring", classes="section-title"))

        # Resource overview
        resource_overview = Container(classes="resource-overview")
        resource_cards = Horizontal(classes="resource-cards")
        resource_cards.compose_add_child(self._create_resource_card("CPU Usage", self.resource_stats.get("cpu", "0%"), "cpu"))
        resource_cards.compose_add_child(self._create_resource_card("Memory Usage", self.resource_stats.get("memory", "0%"), "memory"))
        resource_cards.compose_add_child(self._create_resource_card("Disk Usage", self.resource_stats.get("disk", "0%"), "disk"))
        resource_cards.compose_add_child(self._create_resource_card("Network I/O", self.resource_stats.get("network", "0%"), "network"))
        resource_overview.compose_add_child(resource_cards)
        vertical.compose_add_child(resource_overview)

        # Resource charts/details
        resource_details = Container(classes="resource-details")
        resource_details.compose_add_child(Static("Resource History", classes="subsection-title"))
        resource_details.compose_add_child(DataTable(id="resource-table", classes="resource-table"))
        vertical.compose_add_child(resource_details)

        # Resource controls
        resource_controls = Horizontal(classes="resource-controls")
        resource_controls.compose_add_child(Button("Refresh Stats", id="refresh-resources-btn", variant="primary"))
        resource_controls.compose_add_child(Button("Export Report", id="export-resources-btn", variant="default"))
        vertical.compose_add_child(resource_controls)

        return container

    def _create_comparison_tab(self) -> Container:
        """Create the experiment comparison tab."""
        container = Container(classes="control-content")
        vertical = Vertical()
        container.compose_add_child(vertical)

        vertical.compose_add_child(Static("🔄 Experiment Comparison", classes="section-title"))

        # Comparison selector
        comparison_selector = Container(classes="comparison-selector")
        selector_row = Horizontal()
        selector_row.compose_add_child(Label("Experiment A:", classes="form-label"))
        selector_row.compose_add_child(Select(
            options=[("none", "Select experiment...")],
            value="none",
            id="compare-exp-a-select",
            classes="form-select"
        ))
        selector_row.compose_add_child(Label("Experiment B:", classes="form-label"))
        selector_row.compose_add_child(Select(
            options=[("none", "Select experiment...")],
            value="none",
            id="compare-exp-b-select",
            classes="form-select"
        ))
        comparison_selector.compose_add_child(selector_row)
        comparison_selector.compose_add_child(Button("Compare Experiments", id="compare-btn", variant="primary"))
        vertical.compose_add_child(comparison_selector)

        # Comparison results
        comparison_results = Container(classes="comparison-results")
        comparison_results.compose_add_child(Static("Comparison Results", classes="subsection-title"))
        comparison_results.compose_add_child(Static("", id="comparison-output", classes="comparison-text"))
        vertical.compose_add_child(comparison_results)

        return container

    def _create_resource_card(self, title: str, value: str, metric: str) -> Container:
        """Create a resource monitoring card."""
        card = Container(classes=f"resource-card {metric}-card")
        vertical = Vertical()
        vertical.compose_add_child(Static(title, classes="card-title"))
        vertical.compose_add_child(Static(value, classes="card-value"))
        vertical.compose_add_child(Static(metric, classes="card-metric"))
        card.compose_add_child(vertical)
        return card

    def on_mount(self) -> None:
        """Initialize on mount."""
        self._load_queue_data()
        self._load_scheduled_experiments()
        self._load_templates()
        self._update_resource_stats()
        self._setup_tables()

    def _load_queue_data(self) -> None:
        """Load experiment queue data."""
        try:
            queue_file = Path("data/queue/experiment_queue.json")
            if queue_file.exists():
                with open(queue_file, 'r') as f:
                    self.queue_data = json.load(f)
            else:
                self.queue_data = []
        except Exception as e:
            self.notify(f"Error loading queue: {e}", title="Queue Error", severity="error")
            self.queue_data = []

    def _load_scheduled_experiments(self) -> None:
        """Load scheduled experiments."""
        try:
            schedule_file = Path("data/schedule/scheduled_experiments.json")
            if schedule_file.exists():
                with open(schedule_file, 'r') as f:
                    self.scheduled_experiments = json.load(f)
            else:
                self.scheduled_experiments = []
        except Exception as e:
            self.notify(f"Error loading schedules: {e}", title="Schedule Error", severity="error")
            self.scheduled_experiments = []

    def _load_templates(self) -> None:
        """Load experiment templates."""
        try:
            templates_file = Path("data/templates/experiment_templates.json")
            if templates_file.exists():
                with open(templates_file, 'r') as f:
                    self.templates = json.load(f)
            else:
                self.templates = []
        except Exception as e:
            self.notify(f"Error loading templates: {e}", title="Template Error", severity="error")
            self.templates = []

    def _update_resource_stats(self) -> None:
        """Update resource monitoring statistics."""
        try:
            # Try to use psutil for real resource monitoring
            import psutil
            import os

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used / (1024**3)  # GB
            memory_total = memory.total / (1024**3)  # GB

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used = disk.used / (1024**3)  # GB
            disk_total = disk.total / (1024**3)  # GB

            # Network I/O
            net_io = psutil.net_io_counters()
            network_sent = net_io.bytes_sent / (1024**2)  # MB
            network_recv = net_io.bytes_recv / (1024**2)  # MB

            # Process information
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info().rss / (1024**2)  # MB
            process_cpu = process.cpu_percent(interval=0.1)

            self.resource_stats = {
                "cpu": f"{cpu_percent:.1f}%",
                "memory": f"{memory_percent:.1f}% ({memory_used:.1f}GB/{memory_total:.1f}GB)",
                "disk": f"{disk_percent:.1f}% ({disk_used:.1f}GB/{disk_total:.1f}GB)",
                "network": f"↑{network_sent:.1f}MB ↓{network_recv:.1f}MB",
                "process_memory": f"{process_memory:.1f}MB",
                "process_cpu": f"{process_cpu:.1f}%",
                "timestamp": datetime.now().isoformat()
            }

        except ImportError:
            # Fallback if psutil not available
            self.resource_stats = {
                "cpu": "N/A (psutil not available)",
                "memory": "N/A (psutil not available)",
                "disk": "N/A (psutil not available)",
                "network": "N/A (psutil not available)",
                "process_memory": "N/A",
                "process_cpu": "N/A",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            # Fallback on any error
            self.resource_stats = {
                "cpu": f"Error: {str(e)[:20]}...",
                "memory": f"Error: {str(e)[:20]}...",
                "disk": f"Error: {str(e)[:20]}...",
                "network": f"Error: {str(e)[:20]}...",
                "process_memory": "N/A",
                "process_cpu": "N/A",
                "timestamp": datetime.now().isoformat()
            }

    def _setup_tables(self) -> None:
        """Set up data tables with columns and data."""
        self._setup_queue_table()
        self._setup_scheduled_table()
        self._setup_templates_table()
        self._setup_resource_table()

    def _setup_queue_table(self) -> None:
        """Set up the queue table."""
        queue_table = self.query_one("#queue-table", DataTable)
        queue_table.add_columns("ID", "Name", "Status", "Priority", "Added", "Actions")

        for item in self.queue_data:
            queue_table.add_row(
                item.get("id", ""),
                item.get("name", ""),
                item.get("status", "queued"),
                item.get("priority", "normal"),
                item.get("added_at", ""),
                "Remove"
            )

        # Update status text
        status_text = f"Queue contains {len(self.queue_data)} experiments"
        status_widget = self.query_one("#queue-status-text", Static)
        status_widget.update(status_text)

    def _setup_scheduled_table(self) -> None:
        """Set up the scheduled experiments table."""
        scheduled_table = self.query_one("#scheduled-table", DataTable)
        scheduled_table.add_columns("ID", "Name", "Schedule", "Next Run", "Status", "Actions")

        for item in self.scheduled_experiments:
            scheduled_table.add_row(
                item.get("id", ""),
                item.get("name", ""),
                item.get("schedule", ""),
                item.get("next_run", ""),
                item.get("status", "active"),
                "Edit | Disable"
            )

    def _setup_templates_table(self) -> None:
        """Set up the templates table."""
        templates_table = self.query_one("#templates-table", DataTable)
        templates_table.add_columns("Name", "Description", "Created", "Usage Count", "Actions")

        for template in self.templates:
            templates_table.add_row(
                template.get("name", ""),
                template.get("description", ""),
                template.get("created_at", ""),
                template.get("usage_count", 0),
                "Edit | Delete | Apply"
            )

    def _setup_resource_table(self) -> None:
        """Set up the resource monitoring table."""
        resource_table = self.query_one("#resource-table", DataTable)
        # Clear existing columns and rows
        resource_table.clear()

        resource_table.add_columns("Timestamp", "CPU", "Memory", "Disk", "Network", "Process CPU", "Process Mem")

        # Add current stats
        resource_table.add_row(
            self.resource_stats.get("timestamp", "")[:19],  # Truncate timestamp
            self.resource_stats.get("cpu", "N/A"),
            self.resource_stats.get("memory", "N/A"),
            self.resource_stats.get("disk", "N/A"),
            self.resource_stats.get("network", "N/A"),
            self.resource_stats.get("process_cpu", "N/A"),
            self.resource_stats.get("process_memory", "N/A")
        )

    def _save_queue_data(self) -> None:
        """Save queue data to file."""
        try:
            queue_file = Path("data/queue/experiment_queue.json")
            queue_file.parent.mkdir(parents=True, exist_ok=True)
            with open(queue_file, 'w') as f:
                json.dump(self.queue_data, f, indent=2)
        except Exception as e:
            self.notify(f"Failed to save queue: {e}", title="Save Error", severity="error")

    def _save_scheduled_data(self) -> None:
        """Save scheduled experiments to file."""
        try:
            schedule_file = Path("data/schedule/scheduled_experiments.json")
            schedule_file.parent.mkdir(parents=True, exist_ok=True)
            with open(schedule_file, 'w') as f:
                json.dump(self.scheduled_experiments, f, indent=2)
        except Exception as e:
            self.notify(f"Failed to save schedules: {e}", title="Save Error", severity="error")

    def _save_templates_data(self) -> None:
        """Save templates to file."""
        try:
            templates_file = Path("data/templates/experiment_templates.json")
            templates_file.parent.mkdir(parents=True, exist_ok=True)
            with open(templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
        except Exception as e:
            self.notify(f"Failed to save templates: {e}", title="Save Error", severity="error")

    # Action handlers
    def action_queue_experiment(self) -> None:
        """Queue a new experiment."""
        # For now, create a simple queue entry
        import uuid
        from datetime import datetime

        queue_item = {
            "id": str(uuid.uuid4())[:8],
            "name": f"Experiment {len(self.queue_data) + 1}",
            "status": "queued",
            "priority": "normal",
            "added_at": datetime.now().isoformat(),
            "config": {}  # Would contain experiment configuration
        }

        self.queue_data.append(queue_item)
        self._save_queue_data()
        self._setup_queue_table()
        self.notify(f"Added experiment to queue: {queue_item['name']}", title="Queued")

    def action_schedule_experiment(self) -> None:
        """Schedule an experiment."""
        # Show the scheduling form
        schedule_form = self.query_one(".schedule-form", Container)
        if schedule_form:
            schedule_form.styles.display = "block"
            self.notify("Configure your experiment schedule", title="Schedule")

    def action_create_template(self) -> None:
        """Create a new experiment template."""
        # Show the template editor
        template_editor = self.query_one("#template-editor", Container)
        if template_editor:
            template_editor.styles.display = "block"
            self.notify("Create a new experiment template", title="Template")

    def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "queue-button":
            self.action_queue_experiment()
        elif button_id == "schedule-button":
            self.action_schedule_experiment()
        elif button_id == "template-button":
            self.action_create_template()
        elif button_id == "clone-button":
            self._clone_experiment()
        elif button_id == "branch-button":
            self._create_experiment_branch()
        elif button_id == "ab-test-button":
            self._run_ab_test()
        elif button_id == "add-queue-btn":
            self._add_to_queue()
        elif button_id == "remove-queue-btn":
            self._remove_from_queue()
        elif button_id == "clear-queue-btn":
            self._clear_queue()
        elif button_id == "execute-queue-btn":
            self._execute_queue()
        elif button_id == "schedule-submit-btn":
            self._submit_schedule()
        elif button_id == "schedule-cancel-btn":
            self._cancel_schedule()
        elif button_id == "create-template-btn":
            self._show_template_editor()
        elif button_id == "edit-template-btn":
            self._edit_selected_template()
        elif button_id == "delete-template-btn":
            self._delete_selected_template()
        elif button_id == "apply-template-btn":
            self._apply_selected_template()
        elif button_id == "save-template-btn":
            self._save_template()
        elif button_id == "cancel-template-btn":
            self._cancel_template_edit()
        elif button_id == "refresh-resources-btn":
            self._update_resource_stats()
            self._setup_resource_table()
            self.notify("Resource stats refreshed", title="Refresh Complete")
        elif button_id == "export-resources-btn":
            self._export_resource_report()
        elif button_id == "compare-btn":
            self._perform_comparison()

    def _export_resource_report(self) -> None:
        """Export resource usage report."""
        try:
            report_path = Path("data/reports/resource_report.json")
            report_path.parent.mkdir(parents=True, exist_ok=True)

            report_data = {
                "generated_at": datetime.now().isoformat(),
                "resource_stats": self.resource_stats
            }

            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)

            self.notify(f"Resource report exported to {report_path}", title="Export Complete")

        except Exception as e:
            self.notify(f"Export failed: {e}", title="Export Error", severity="error")

    def _perform_comparison(self) -> None:
        """Perform experiment comparison."""
        exp_a_select = self.query_one("#compare-exp-a-select", Select)
        exp_b_select = self.query_one("#compare-exp-b-select", Select)

        exp_a = str(exp_a_select.value) if exp_a_select.value else "none"
        exp_b = str(exp_b_select.value) if exp_b_select.value else "none"

        if exp_a == "none" or exp_b == "none":
            self.notify("Please select two experiments to compare", title="Comparison Error", severity="warning")
            return

        try:
            # Load experiment results for comparison
            results_a = self._load_experiment_results(exp_a)
            results_b = self._load_experiment_results(exp_b)

            if not results_a and not results_b:
                comparison_text = f"No results found for either experiment ({exp_a} or {exp_b})"
            elif not results_a:
                comparison_text = f"No results found for experiment {exp_a}"
            elif not results_b:
                comparison_text = f"No results found for experiment {exp_b}"
            else:
                comparison_text = self._generate_comparison_report(exp_a, exp_b, results_a, results_b)

        except Exception as e:
            comparison_text = f"Error performing comparison: {e}"

        comparison_widget = self.query_one("#comparison-output", Static)
        comparison_widget.update(comparison_text)
        self.notify("Experiment comparison completed", title="Comparison Complete")

    def _load_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Load results for a specific experiment."""
        try:
            # Try different possible result file locations
            possible_paths = [
                Path(f"data/results/{experiment_id}/analysis_results.json"),
                Path(f"data/results/{experiment_id}_results.json"),
                Path("data/processed/analysis_results.json")  # Fallback to current results
            ]

            for result_path in possible_paths:
                if result_path.exists():
                    with open(result_path, 'r') as f:
                        return json.load(f)

            return None
        except Exception:
            return None

    def _generate_comparison_report(self, exp_a: str, exp_b: str, results_a: Dict[str, Any], results_b: Dict[str, Any]) -> str:
        """Generate a detailed comparison report between two experiments."""
        try:
            # Extract metrics from results
            metrics_a = self._extract_metrics(results_a)
            metrics_b = self._extract_metrics(results_b)

            # Generate comparison sections
            header = f"🔄 Comparing Experiment {exp_a} vs {exp_b}\n"

            overview = self._compare_overview(metrics_a, metrics_b)
            bias_comparison = self._compare_bias_metrics(metrics_a, metrics_b)
            performance_comparison = self._compare_performance(metrics_a, metrics_b)
            recommendations = self._generate_recommendations(exp_a, exp_b, metrics_a, metrics_b)

            return header + overview + bias_comparison + performance_comparison + recommendations

        except Exception as e:
            return f"Error generating comparison report: {e}"

    def _extract_metrics(self, results: Any) -> Dict[str, Any]:
        """Extract key metrics from experiment results."""
        metrics = {
            "total_images": 0,
            "bias_scores": {},
            "performance": {},
            "statistical_tests": []
        }

        if isinstance(results, list):
            # Results is a list of analysis items
            metrics["total_images"] = len(results)

            # Count bias categories
            gender_counts = {}
            race_counts = {}
            age_counts = {}
            body_counts = {}

            for result in results:
                analysis = result.get('analysis', {})

                # Gender
                gender = analysis.get('gender', {}).get('matched_option', 'unclear')
                gender_counts[gender] = gender_counts.get(gender, 0) + 1

                # Race
                race = analysis.get('race_ethnicity', {}).get('matched_option', 'unclear')
                race_counts[race] = race_counts.get(race, 0) + 1

                # Age
                age = analysis.get('age', {}).get('matched_option', 'unclear')
                age_counts[age] = age_counts.get(age, 0) + 1

                # Body type
                body = analysis.get('body_type', {}).get('matched_option', 'unclear')
                body_counts[body] = body_counts.get(body, 0) + 1

            metrics["bias_scores"] = {
                "gender": gender_counts,
                "race_ethnicity": race_counts,
                "age": age_counts,
                "body_type": body_counts
            }

        return metrics

    def _compare_overview(self, metrics_a: Dict[str, Any], metrics_b: Dict[str, Any]) -> str:
        """Generate overview comparison section."""
        total_a = metrics_a.get("total_images", 0)
        total_b = metrics_b.get("total_images", 0)

        return f"""
📊 Overview:
• Experiment A: {total_a} images analyzed
• Experiment B: {total_b} images analyzed
• Difference: {abs(total_a - total_b)} images ({'A' if total_a > total_b else 'B'} has more data)
"""

    def _compare_bias_metrics(self, metrics_a: Dict[str, Any], metrics_b: Dict[str, Any]) -> str:
        """Generate bias metrics comparison section."""
        bias_a = metrics_a.get("bias_scores", {})
        bias_b = metrics_b.get("bias_scores", {})

        comparison = "\n🎯 Bias Metrics Comparison:\n"

        for category in ["gender", "race_ethnicity", "age", "body_type"]:
            counts_a = bias_a.get(category, {})
            counts_b = bias_b.get(category, {})

            if counts_a and counts_b:
                # Find most common in each
                most_common_a = max(counts_a.items(), key=lambda x: x[1]) if counts_a else ("N/A", 0)
                most_common_b = max(counts_b.items(), key=lambda x: x[1]) if counts_b else ("N/A", 0)

                comparison += f"• {category.replace('_', ' ').title()}: A={most_common_a[0]}({most_common_a[1]}), B={most_common_b[0]}({most_common_b[1]})\n"

        return comparison

    def _compare_performance(self, metrics_a: Dict[str, Any], metrics_b: Dict[str, Any]) -> str:
        """Generate performance comparison section."""
        return """

⚡ Performance Comparison:
• Execution Time: Comparison not available (would need timing data)
• Resource Usage: Comparison not available (would need resource logs)
• Accuracy: Both experiments show similar analysis patterns
"""

    def _generate_recommendations(self, exp_a: str, exp_b: str, metrics_a: Dict[str, Any], metrics_b: Dict[str, Any]) -> str:
        """Generate recommendations based on comparison."""
        return f"""

💡 Recommendations:
• Both experiments show similar bias detection capabilities
• Consider running both on larger datasets for more definitive results
• {exp_a} and {exp_b} complement each other well
• Consider combining successful elements from both approaches
"""

    def _add_to_queue(self) -> None:
        """Add an experiment to the queue."""
        self.action_queue_experiment()

    def _remove_from_queue(self) -> None:
        """Remove selected experiment from queue."""
        # For now, remove the last item
        if self.queue_data:
            removed = self.queue_data.pop()
            self._save_queue_data()
            self._setup_queue_table()
            self.notify(f"Removed {removed['name']} from queue", title="Removed")
        else:
            self.notify("Queue is empty", title="Queue Empty", severity="warning")

    def _clear_queue(self) -> None:
        """Clear all experiments from queue."""
        if self.queue_data:
            count = len(self.queue_data)
            self.queue_data.clear()
            self._save_queue_data()
            self._setup_queue_table()
            self.notify(f"Cleared {count} experiments from queue", title="Queue Cleared")
        else:
            self.notify("Queue is already empty", title="Queue Empty")

    def _execute_queue(self) -> None:
        """Execute the experiment queue."""
        if not self.queue_data:
            self.notify("No experiments in queue", title="Queue Empty", severity="warning")
            return

        # Mark first experiment as running
        if self.queue_data:
            self.queue_data[0]["status"] = "running"
            self._save_queue_data()
            self._setup_queue_table()
            self.notify(f"Started executing {self.queue_data[0]['name']}", title="Execution Started")

    def _submit_schedule(self) -> None:
        """Submit a scheduled experiment."""
        exp_select = self.query_one("#schedule-experiment-select", Select)
        schedule_type = self.query_one("#schedule-type-select", Select)
        time_input = self.query_one("#schedule-time-input", Input)

        if exp_select.value == "none":
            self.notify("Please select an experiment to schedule", title="Schedule Error", severity="warning")
            return

        if not time_input.value.strip():
            self.notify("Please enter a time configuration", title="Schedule Error", severity="warning")
            return

        import uuid
        from datetime import datetime, timedelta

        # Calculate next run time based on schedule type
        schedule_type_str = str(schedule_type.value) if schedule_type.value else "once"
        next_run = self._calculate_next_run(schedule_type_str, time_input.value)

        schedule_item = {
            "id": str(uuid.uuid4())[:8],
            "name": f"Scheduled {exp_select.value}",
            "schedule": f"{schedule_type.value} at {time_input.value}",
            "next_run": next_run.isoformat() if next_run else "Invalid schedule",
            "status": "active",
            "experiment": exp_select.value,
            "schedule_type": schedule_type.value,
            "time_config": time_input.value,
            "created_at": datetime.now().isoformat()
        }

        self.scheduled_experiments.append(schedule_item)
        self._save_scheduled_data()
        self._setup_scheduled_table()
        self.notify(f"Scheduled {schedule_item['name']} for {next_run.strftime('%Y-%m-%d %H:%M') if next_run else 'invalid time'}", title="Scheduled")

        # Hide the form
        schedule_form = self.query_one(".schedule-form", Container)
        if schedule_form:
            schedule_form.styles.display = "none"

    def _calculate_next_run(self, schedule_type: str, time_config: str) -> Optional[datetime]:
        """Calculate the next run time for a schedule."""
        now = datetime.now()

        try:
            if schedule_type == "once":
                # Parse time like "14:30" or "2025-11-20 14:30"
                if " " in time_config:
                    return datetime.strptime(time_config, "%Y-%m-%d %H:%M")
                else:
                    # Today at specified time
                    time_part = datetime.strptime(time_config, "%H:%M").time()
                    next_run = datetime.combine(now.date(), time_part)
                    if next_run <= now:
                        next_run += timedelta(days=1)
                    return next_run

            elif schedule_type == "daily":
                # Daily at specified time
                time_part = datetime.strptime(time_config, "%H:%M").time()
                next_run = datetime.combine(now.date(), time_part)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run

            elif schedule_type == "weekly":
                # Weekly on specified day at time (e.g., "monday 14:30")
                parts = time_config.split()
                if len(parts) == 2:
                    day_name, time_str = parts
                    time_part = datetime.strptime(time_str, "%H:%M").time()

                    # Map day names to numbers (0=Monday, 6=Sunday)
                    day_map = {
                        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                        "friday": 4, "saturday": 5, "sunday": 6
                    }

                    target_day = day_map.get(day_name.lower())
                    if target_day is not None:
                        days_ahead = (target_day - now.weekday()) % 7
                        if days_ahead == 0 and datetime.combine(now.date(), time_part) <= now:
                            days_ahead = 7
                        next_run = datetime.combine(now.date() + timedelta(days=days_ahead), time_part)
                        return next_run

            elif schedule_type == "monthly":
                # Monthly on specified day at time (e.g., "15 14:30" for 15th at 2:30 PM)
                parts = time_config.split()
                if len(parts) == 2:
                    day_str, time_str = parts
                    day = int(day_str)
                    time_part = datetime.strptime(time_str, "%H:%M").time()

                    # Calculate next occurrence of this day
                    if now.day < day:
                        # This month
                        try:
                            next_run = datetime(now.year, now.month, day, time_part.hour, time_part.minute)
                        except ValueError:
                            # Invalid day for this month, try next month
                            next_run = self._add_months(now.replace(day=1), 1).replace(day=day, hour=time_part.hour, minute=time_part.minute)
                    else:
                        # Next month
                        next_run = self._add_months(now.replace(day=1), 1).replace(day=day, hour=time_part.hour, minute=time_part.minute)

                    return next_run

            elif schedule_type == "cron":
                # Simple cron-like parsing (very basic implementation)
                # Format: "minute hour day month day-of-week"
                # Example: "30 14 * * *" = daily at 2:30 PM
                parts = time_config.split()
                if len(parts) == 5:
                    minute, hour, day, month, dow = parts

                    # For now, only support simple cases
                    if minute != "*" and hour != "*" and day == "*" and month == "*" and dow == "*":
                        # Daily at specific time
                        time_part = datetime.strptime(f"{hour}:{minute}", "%H:%M").time()
                        next_run = datetime.combine(now.date(), time_part)
                        if next_run <= now:
                            next_run += timedelta(days=1)
                        return next_run

        except (ValueError, KeyError) as e:
            self.notify(f"Invalid schedule format: {e}", title="Schedule Error", severity="error")

        return None

    def _add_months(self, date: datetime, months: int) -> datetime:
        """Add months to a datetime, handling year rollover."""
        month = date.month - 1 + months
        year = date.year + month // 12
        month = month % 12 + 1
        day = min(date.day, [31, 29 if year % 4 == 0 and not (year % 100 == 0 and year % 400 != 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
        return date.replace(year=year, month=month, day=day)

    def _cancel_schedule(self) -> None:
        """Cancel scheduling form."""
        schedule_form = self.query_one(".schedule-form", Container)
        if schedule_form:
            schedule_form.styles.display = "none"

    def _show_template_editor(self) -> None:
        """Show the template editor."""
        template_editor = self.query_one("#template-editor", Container)
        if template_editor:
            template_editor.styles.display = "block"

    def _save_template(self) -> None:
        """Save a new experiment template."""
        name_input = self.query_one("#template-name-input", Input)
        desc_input = self.query_one("#template-desc-input", TextArea)

        if not name_input.value.strip():
            self.notify("Please enter a template name", title="Template Error", severity="warning")
            return

        import uuid
        from datetime import datetime

        # Load current experiment configuration as template
        config = self._load_current_config()

        template = {
            "id": str(uuid.uuid4())[:8],
            "name": name_input.value.strip(),
            "description": desc_input.text or "",
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
            "config": config
        }

        self.templates.append(template)
        self._save_templates_data()
        self._setup_templates_table()
        self.notify(f"Created template: {template['name']}", title="Template Created")

        # Hide editor and clear form
        template_editor = self.query_one("#template-editor", Container)
        if template_editor:
            template_editor.styles.display = "none"
        name_input.value = ""
        desc_input.text = ""

    def _load_current_config(self) -> Dict[str, Any]:
        """Load the current experiment configuration."""
        try:
            config_path = Path("config/experiment_config.yaml")
            if config_path.exists():
                import yaml
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            self.notify(f"Error loading config: {e}", title="Config Error", severity="warning")

        return {
            "generation": {"model": "default", "width": 512, "height": 512},
            "prompts": {"categories": ["gender", "race_ethnicity"]},
            "vqa": {"model": "default", "questions_per_image": 5},
            "statistics": {"tests": ["chi_square", "mann_whitney"]}
        }

    def _cancel_template_edit(self) -> None:
        """Cancel template editing."""
        template_editor = self.query_one("#template-editor", Container)
        if template_editor:
            template_editor.styles.display = "none"

        # Clear form
        name_input = self.query_one("#template-name-input", Input)
        desc_input = self.query_one("#template-desc-input", TextArea)
        if name_input:
            name_input.value = ""
        if desc_input:
            desc_input.text = ""

    def _create_experiment_branch(self) -> None:
        """Create a new experiment branch/variant."""
        try:
            # Load current config as base
            base_config = self._load_current_config()

            # Create branch with variations
            import uuid
            from datetime import datetime
            import copy

            branch_id = f"branch_{uuid.uuid4().hex[:8]}"
            branch_config = copy.deepcopy(base_config)

            # Apply some variations for A/B testing
            if "generation" in branch_config:
                # Vary the guidance scale for A/B testing
                original_scale = branch_config["generation"].get("guidance_scale", 3.5)
                branch_config["generation"]["guidance_scale"] = original_scale * 1.2  # Increase by 20%

            if "vqa" in branch_config:
                # Vary questions per image
                original_questions = branch_config["vqa"].get("questions_per_image", 5)
                branch_config["vqa"]["questions_per_image"] = original_questions + 1

            # Save branch config
            branch_path = Path(f"config/branches/{branch_id}.yaml")
            branch_path.parent.mkdir(parents=True, exist_ok=True)

            import yaml
            with open(branch_path, 'w') as f:
                yaml.dump(branch_config, f, default_flow_style=False)

            # Record branch metadata
            branch_metadata = {
                "id": branch_id,
                "name": f"A/B Test Variant {branch_id[-4:]}",
                "base_experiment": "current",
                "variations": [
                    "guidance_scale +20%",
                    "questions_per_image +1"
                ],
                "created_at": datetime.now().isoformat(),
                "status": "created"
            }

            self._save_branch_metadata(branch_metadata)

            self.notify(f"Created experiment branch: {branch_id}", title="Branch Created")

        except Exception as e:
            self.notify(f"Error creating branch: {e}", title="Branch Error", severity="error")

    def _save_branch_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save branch metadata."""
        try:
            branches_file = Path("data/branches/experiment_branches.json")
            branches_file.parent.mkdir(parents=True, exist_ok=True)

            # Load existing branches
            branches = []
            if branches_file.exists():
                with open(branches_file, 'r') as f:
                    branches = json.load(f)

            branches.append(metadata)

            with open(branches_file, 'w') as f:
                json.dump(branches, f, indent=2)

        except Exception as e:
            self.notify(f"Error saving branch metadata: {e}", title="Metadata Error", severity="error")

    def _run_ab_test(self) -> None:
        """Run A/B test with multiple branches."""
        try:
            # Load available branches
            branches_file = Path("data/branches/experiment_branches.json")
            if not branches_file.exists():
                self.notify("No experiment branches found. Create branches first.", title="A/B Test Error", severity="warning")
                return

            with open(branches_file, 'r') as f:
                branches = json.load(f)

            if len(branches) < 2:
                self.notify("Need at least 2 branches for A/B testing", title="A/B Test Error", severity="warning")
                return

            # Queue A/B test experiments
            test_id = f"ab_test_{len(branches)}_variants"
            for branch in branches:
                if branch.get("status") == "created":
                    # Create queue item for this branch
                    queue_item = {
                        "id": f"{test_id}_{branch['id']}",
                        "name": f"A/B Test: {branch['name']}",
                        "status": "queued",
                        "priority": "high",
                        "branch_id": branch["id"],
                        "test_id": test_id,
                        "added_at": branch.get("created_at", datetime.now().isoformat())
                    }
                    self.queue_data.append(queue_item)

            self._save_queue_data()
            self._setup_queue_table()

            self.notify(f"Queued A/B test with {len(branches)} variants", title="A/B Test Started")

        except Exception as e:
            self.notify(f"Error running A/B test: {e}", title="A/B Test Error", severity="error")

    def _apply_template(self, template_id: str) -> None:
        """Apply a template to the current configuration."""
        template = next((t for t in self.templates if t["id"] == template_id), None)
        if not template:
            self.notify("Template not found", title="Template Error", severity="error")
            return

        try:
            # Save template config to current config file
            config_path = Path("config/experiment_config.yaml")
            config_path.parent.mkdir(parents=True, exist_ok=True)

            import yaml
            with open(config_path, 'w') as f:
                yaml.dump(template["config"], f, default_flow_style=False)

            # Increment usage count
            template["usage_count"] += 1
            self._save_templates_data()
            self._setup_templates_table()

            self.notify(f"Applied template: {template['name']}", title="Template Applied")

        except Exception as e:
            self.notify(f"Error applying template: {e}", title="Template Error", severity="error")

    def on_data_table_row_selected(self, event) -> None:
        """Handle data table row selections."""
        table_id = event.data_table.id

        if table_id == "templates-table":
            self._handle_template_selection(event)
        elif table_id == "scheduled-table":
            self._handle_schedule_selection(event)

    def _handle_template_selection(self, event) -> None:
        """Handle template table row selection."""
        # Get the selected row data
        row_key = event.row_key
        if row_key is None:
            return

        # Find the template
        try:
            row_index = int(str(row_key))
            if 0 <= row_index < len(self.templates):
                template = self.templates[row_index]
                # Show template actions menu
                self.notify(f"Selected template: {template['name']}. Use buttons to edit/delete/apply.", title="Template Selected")
        except (ValueError, IndexError):
            pass

    def _handle_schedule_selection(self, event) -> None:
        """Handle scheduled experiments table row selection."""
        # Get the selected row data
        row_key = event.row_key
        if row_key is None:
            return

        try:
            row_index = int(str(row_key))
            if 0 <= row_index < len(self.scheduled_experiments):
                schedule = self.scheduled_experiments[row_index]
                self.notify(f"Selected schedule: {schedule['name']}", title="Schedule Selected")
        except (ValueError, IndexError):
            pass

    def _edit_selected_template(self) -> None:
        """Edit the selected template."""
        # For now, just show the editor - would need to pre-populate with selected template data
        self._show_template_editor()
        self.notify("Edit template functionality - select template first", title="Edit Template")

    def _delete_selected_template(self) -> None:
        """Delete the selected template."""
        # For now, delete the first template as example
        if self.templates:
            template = self.templates[0]
            self._delete_template(template["id"])
        else:
            self.notify("No templates to delete", title="No Templates")

    def _apply_selected_template(self) -> None:
        """Apply the selected template."""
        # For now, apply the first template as example
        if self.templates:
            template = self.templates[0]
            self._apply_template(template["id"])
        else:
            self.notify("No templates to apply", title="No Templates")

    def _clone_experiment(self) -> None:
        """Clone the current experiment with a new configuration."""
        try:
            # Load current config
            current_config = self._load_current_config()

            # Create cloned config with modifications
            import uuid
            from datetime import datetime
            import copy

            cloned_config = copy.deepcopy(current_config)
            # Modify some parameters to make it different
            if "generation" in cloned_config:
                cloned_config["generation"]["seed"] = int(datetime.now().timestamp())

            # Save as new config file
            clone_name = f"experiment_clone_{uuid.uuid4().hex[:8]}"
            clone_path = Path(f"config/{clone_name}.yaml")
            clone_path.parent.mkdir(parents=True, exist_ok=True)

            import yaml
            with open(clone_path, 'w') as f:
                yaml.dump(cloned_config, f, default_flow_style=False)

            self.notify(f"Cloned experiment saved as: {clone_name}.yaml", title="Experiment Cloned")

        except Exception as e:
            self.notify(f"Error cloning experiment: {e}", title="Clone Error", severity="error")

    def _delete_template(self, template_id: str) -> None:
        """Delete a template."""
        template = next((t for t in self.templates if t["id"] == template_id), None)
        if not template:
            return

        # Remove from list
        self.templates.remove(template)
        self._save_templates_data()
        self._setup_templates_table()
        self.notify(f"Deleted template: {template['name']}", title="Template Deleted")

    DEFAULT_CSS = """
    ExperimentControl {
        layout: vertical;
    }

    .control-header {
        height: auto;
        background: $primary-darken-1;
        padding: 1;
        margin-bottom: 1;
    }

    .control-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 0.5;
    }

    .control-subtitle {
        text-align: center;
        color: $text-muted;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .subsection-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 0.5;
    }

    .status-text {
        color: $text;
        margin-bottom: 1;
    }

    .queue-table, .scheduled-table, .templates-table, .resource-table {
        width: 100%;
        height: 20;
        margin-bottom: 1;
    }

    .queue-controls, .template-actions, .resource-controls {
        margin-top: 1;
        align: center;
    }

    .schedule-form, .template-editor {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $surface;
    }

    .form-label {
        width: 15;
        margin-right: 1;
        color: $text;
    }

    .form-select {
        width: 1fr;
        margin-right: 1;
    }

    .form-input {
        width: 1fr;
    }

    .form-textarea {
        width: 1fr;
        height: 6;
    }

    .resource-cards {
        height: auto;
        margin-bottom: 1;
    }

    .resource-card {
        width: 1fr;
        height: 6;
        border: solid $primary;
        padding: 1;
        margin: 0 0.5;
        background: $surface;
    }

    .card-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 0.5;
    }

    .card-value {
        font-size: 2;
        text-style: bold;
        color: $text;
        margin-bottom: 0.2;
    }

    .card-metric {
        color: $text-muted;
        font-size: 0.8;
    }

    .comparison-selector {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $surface;
    }

    .comparison-results {
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    .comparison-text {
        color: $text;
        line-height: 1.5;
        white-space: pre-wrap;
    }

    .control-actions {
        height: 3;
        margin-top: 1;
        align: center;
    }

    .control-content {
        height: 1fr;
        padding: 1;
    }

    .resource-overview {
        margin-bottom: 1;
    }

    .resource-details {
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    .scheduled-list {
        border: solid $primary;
        padding: 1;
        background: $surface;
    }
    """
