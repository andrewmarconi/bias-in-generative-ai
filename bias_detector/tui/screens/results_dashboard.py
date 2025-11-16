"""
Results Dashboard Screen for experiment analysis.

Displays bias metrics, statistical analysis, and experiment comparisons.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal, Container
from textual.widgets import (
    Static, Button, DataTable, TabbedContent, TabPane,
    Label, ProgressBar
)
from textual.binding import Binding


class ResultsDashboard(Screen):
    """
    Results visualization dashboard.

    Features:
    - Bias metrics visualization
    - Statistical analysis display
    - Experiment comparison
    - Results export functionality
    - Interactive charts and graphs
    - Image gallery with VQA results
    - MLflow integration
    """

    BINDINGS = [
        Binding("f1", "switch_screen('progress')", "Progress", show=True),
        Binding("f2", "switch_screen('metadata')", "Metadata", show=True),
        Binding("f3", "switch_screen('config')", "Config", show=True),
        Binding("f4", "switch_screen('history')", "History", show=True),
        Binding("f5", "switch_screen('logs')", "Logs", show=True),
        Binding("f6", "switch_screen('results')", "Results", show=True),
        Binding("h", "show_help", "Help", show=True),
        Binding("r", "refresh_results", "Refresh", show=True),
        Binding("e", "export_results", "Export", show=True),
    ]

    def __init__(self, **kwargs):
        """Initialize results dashboard."""
        super().__init__(**kwargs)
        self.results_data: List[Dict[str, Any]] = []
        self.current_experiment_id: Optional[str] = None
        self.current_image_index: int = 0

    def compose(self) -> ComposeResult:
        """Compose the results dashboard."""
        with Vertical():
            # Header
            with Container(classes="dashboard-header"):
                yield Static("📊 Experiment Results Dashboard", classes="dashboard-title")
                yield Static("Analysis of bias detection results", classes="dashboard-subtitle")

            # Main content with tabs
            with TabbedContent(id="results-tabs"):
                with TabPane("Overview", id="overview-tab"):
                    yield self._create_overview_tab()

                with TabPane("Bias Metrics", id="metrics-tab"):
                    yield self._create_metrics_tab()

                with TabPane("Statistical Analysis", id="stats-tab"):
                    yield self._create_stats_tab()

                with TabPane("Comparisons", id="comparison-tab"):
                    yield self._create_comparison_tab()

                with TabPane("Image Gallery", id="gallery-tab"):
                    yield self._create_gallery_tab()

                with TabPane("Raw Data", id="data-tab"):
                    yield self._create_data_tab()

            # Action buttons
            with Horizontal(classes="dashboard-actions"):
                yield Button("Refresh Results", id="refresh-button", variant="primary")
                yield Button("Export Report", id="export-button", variant="default")
                yield Button("Compare Experiments", id="compare-button", variant="default")
                yield Button("Log to MLflow", id="mlflow-button", variant="default")

    def _create_overview_tab(self) -> Container:
        """Create the overview tab with summary statistics."""
        container = Container(classes="results-content")
        vertical = Vertical()
        container.compose_add_child(vertical)

        # Summary cards
        summary_cards = Horizontal(classes="summary-cards")
        summary_cards.compose_add_child(self._create_summary_card("Total Images", "0", "images"))
        summary_cards.compose_add_child(self._create_summary_card("Bias Categories", "4", "categories"))
        summary_cards.compose_add_child(self._create_summary_card("Statistical Tests", "5", "tests"))
        summary_cards.compose_add_child(self._create_summary_card("Confidence Level", "95%", "confidence"))
        vertical.compose_add_child(summary_cards)

        # Quick insights
        insights_section = Container(classes="insights-section")
        insights_section.compose_add_child(Static("🔍 Key Insights", classes="section-title"))
        insights_section.compose_add_child(Static("", id="insights-content", classes="insights-text"))
        vertical.compose_add_child(insights_section)

        # Progress overview
        progress_section = Container(classes="progress-section")
        progress_section.compose_add_child(Static("📈 Analysis Progress", classes="section-title"))
        progress_section.compose_add_child(ProgressBar(total=100, id="analysis-progress", classes="analysis-progress"))
        vertical.compose_add_child(progress_section)

        return container

    def _create_metrics_tab(self) -> Container:
        """Create the bias metrics visualization tab."""
        container = Container(classes="results-content")
        vertical = Vertical()
        container.compose_add_child(vertical)

        vertical.compose_add_child(Static("🎯 Bias Metrics by Category", classes="section-title"))

        # Gender bias
        gender_group = Container(classes="metric-group")
        gender_group.compose_add_child(Static("👤 Gender Bias", classes="metric-title"))
        gender_group.compose_add_child(self._create_metric_chart("gender", ["male", "female", "unclear"]))
        vertical.compose_add_child(gender_group)

        # Race/Ethnicity bias
        race_group = Container(classes="metric-group")
        race_group.compose_add_child(Static("🌍 Race/Ethnicity Bias", classes="metric-title"))
        race_group.compose_add_child(self._create_metric_chart("race_ethnicity", ["White", "Black", "Asian", "Hispanic", "unclear"]))
        vertical.compose_add_child(race_group)

        # Age bias
        age_group = Container(classes="metric-group")
        age_group.compose_add_child(Static("📅 Age Bias", classes="metric-title"))
        age_group.compose_add_child(self._create_metric_chart("age", ["child", "young adult", "middle-aged", "elderly", "unclear"]))
        vertical.compose_add_child(age_group)

        # Body type bias
        body_group = Container(classes="metric-group")
        body_group.compose_add_child(Static("⚖️ Body Type Bias", classes="metric-title"))
        body_group.compose_add_child(self._create_metric_chart("body_type", ["thin", "average", "plus-size", "muscular", "unclear"]))
        vertical.compose_add_child(body_group)

        return container

    def _create_stats_tab(self) -> Container:
        """Create the statistical analysis tab."""
        container = Container(classes="results-content")
        vertical = Vertical()
        container.compose_add_child(vertical)

        vertical.compose_add_child(Static("📊 Statistical Analysis", classes="section-title"))
        vertical.compose_add_child(DataTable(id="stats-table", classes="stats-table"))

        # Significance indicators
        significance_section = Container(classes="significance-indicators")
        significance_section.compose_add_child(Static("🎯 Statistical Significance", classes="subsection-title"))
        significance_section.compose_add_child(Static("", id="significance-content", classes="significance-text"))
        vertical.compose_add_child(significance_section)

        # Effect sizes
        effect_section = Container(classes="effect-sizes")
        effect_section.compose_add_child(Static("📏 Effect Sizes", classes="subsection-title"))
        effect_section.compose_add_child(Static("", id="effect-size-content", classes="effect-size-text"))
        vertical.compose_add_child(effect_section)

        return container

    def _create_comparison_tab(self) -> Container:
        """Create the experiment comparison tab."""
        container = Container(classes="results-content")
        vertical = Vertical()
        container.compose_add_child(vertical)

        vertical.compose_add_child(Static("🔄 Experiment Comparisons", classes="section-title"))

        # Experiment selector
        comparison_controls = Horizontal(classes="comparison-controls")
        comparison_controls.compose_add_child(Static("Compare with:", classes="compare-label"))
        comparison_controls.compose_add_child(DataTable(id="experiment-selector", classes="experiment-selector"))
        vertical.compose_add_child(comparison_controls)

        # Comparison results
        comparison_results = Container(classes="comparison-results")
        comparison_results.compose_add_child(Static("📈 Comparison Results", classes="subsection-title"))
        comparison_results.compose_add_child(Static("", id="comparison-content", classes="comparison-text"))
        vertical.compose_add_child(comparison_results)

        return container

    def _create_gallery_tab(self) -> Container:
        """Create the image gallery tab."""
        container = Container(classes="results-content")
        vertical = Vertical()
        container.compose_add_child(vertical)

        vertical.compose_add_child(Static("🖼️ Image Gallery with VQA Results", classes="section-title"))

        # Gallery controls
        gallery_controls = Horizontal(classes="gallery-controls")
        gallery_controls.compose_add_child(Button("Previous", id="prev-image", variant="default"))
        gallery_controls.compose_add_child(Button("Next", id="next-image", variant="default"))
        gallery_controls.compose_add_child(Static("Image 0 of 0", id="image-counter", classes="image-counter"))
        vertical.compose_add_child(gallery_controls)

        # Current image display
        image_display = Container(classes="image-display")
        image_display.compose_add_child(Static("", id="current-image-info", classes="image-info"))
        image_display.compose_add_child(Static("", id="image-analysis", classes="image-analysis"))
        vertical.compose_add_child(image_display)

        # Gallery grid (simplified text representation)
        gallery_grid = Container(classes="gallery-grid")
        gallery_grid.compose_add_child(Static("Image thumbnails would be displayed here", id="gallery-thumbnails", classes="gallery-thumbnails"))
        vertical.compose_add_child(gallery_grid)

        return container

    def _create_data_tab(self) -> Container:
        """Create the raw data tab."""
        container = Container(classes="results-content")
        vertical = Vertical()
        container.compose_add_child(vertical)

        vertical.compose_add_child(Static("📋 Raw Analysis Data", classes="section-title"))
        vertical.compose_add_child(DataTable(id="raw-data-table", classes="raw-data-table"))

        # Export options
        export_options = Horizontal(classes="export-options")
        export_options.compose_add_child(Button("Export JSON", id="export-json", variant="default"))
        export_options.compose_add_child(Button("Export CSV", id="export-csv", variant="default"))
        export_options.compose_add_child(Button("Export Excel", id="export-excel", variant="default"))
        vertical.compose_add_child(export_options)

        return container

    def _create_summary_card(self, title: str, value: str, unit: str) -> Container:
        """Create a summary statistics card."""
        card = Container(classes="summary-card")
        vertical = Vertical()
        vertical.compose_add_child(Static(title, classes="card-title"))
        vertical.compose_add_child(Static(value, classes="card-value"))
        vertical.compose_add_child(Static(unit, classes="card-unit"))
        card.compose_add_child(vertical)
        return card

    def _create_metric_chart(self, category: str, options: List[str]) -> Container:
        """Create a simple text-based chart for bias metrics."""
        chart = Container(classes=f"metric-chart {category}-chart")
        vertical = Vertical()
        chart.compose_add_child(vertical)

        # Distribution bars (simulated)
        for option in options:
            chart_row = Horizontal(classes="chart-row")
            chart_row.compose_add_child(Static(f"{option}:", classes="chart-label"))
            chart_row.compose_add_child(ProgressBar(total=100, classes="chart-bar"))
            chart_row.compose_add_child(Static("0%", classes="chart-percentage"))
            vertical.compose_add_child(chart_row)

        # Summary stats
        chart_summary = Horizontal(classes="chart-summary")
        chart_summary.compose_add_child(Static("Total:", classes="summary-label"))
        chart_summary.compose_add_child(Static("0", classes="summary-value"))
        chart_summary.compose_add_child(Static("Most common:", classes="summary-label"))
        chart_summary.compose_add_child(Static("N/A", classes="summary-value"))
        vertical.compose_add_child(chart_summary)

        return chart

    def on_mount(self) -> None:
        """Initialize on mount."""
        self._load_results_data()
        self._update_overview_tab()
        self._update_metrics_tab()
        self._update_stats_tab()
        self._update_gallery_display()

    def _load_results_data(self) -> None:
        """Load results data from analysis files."""
        try:
            # Try to load VQA analysis results
            results_file = Path("data/processed/analysis_results.json")
            if results_file.exists():
                with open(results_file, 'r') as f:
                    self.results_data = json.load(f)
                self.notify(f"Loaded {len(self.results_data)} analysis results", title="Results Loaded")
            else:
                self.results_data = []
                self.notify("No analysis results found", title="No Data")

        except Exception as e:
            self.results_data = []
            self.notify(f"Error loading results: {e}", title="Load Error", severity="error")

    def _update_overview_tab(self) -> None:
        """Update the overview tab with summary data."""
        if not self.results_data:
            return

        total_images = len(self.results_data)

        # Calculate basic statistics
        gender_counts = {}
        race_counts = {}
        age_counts = {}
        body_counts = {}

        for result in self.results_data:
            analysis = result.get('analysis', {})

            # Count gender classifications
            gender = analysis.get('gender', {}).get('matched_option', 'unclear')
            gender_counts[gender] = gender_counts.get(gender, 0) + 1

            # Count race classifications
            race = analysis.get('race_ethnicity', {}).get('matched_option', 'unclear')
            race_counts[race] = race_counts.get(race, 0) + 1

            # Count age classifications
            age = analysis.get('age', {}).get('matched_option', 'unclear')
            age_counts[age] = age_counts.get(age, 0) + 1

            # Count body type classifications
            body = analysis.get('body_type', {}).get('matched_option', 'unclear')
            body_counts[body] = body_counts.get(body, 0) + 1

        # Generate insights
        insights = []
        insights.append(f"• Analyzed {total_images} images across 4 bias categories")
        insights.append(f"• Gender distribution: {', '.join(f'{k}: {v}' for k, v in gender_counts.items())}")
        insights.append(f"• Most common race/ethnicity: {max(race_counts.items(), key=lambda x: x[1])[0] if race_counts else 'N/A'}")
        insights.append(f"• Age distribution spans: {', '.join(age_counts.keys())}")

        insights_text = "\n".join(insights)
        insights_widget = self.query_one("#insights-content", Static)
        insights_widget.update(insights_text)

        # Update progress (assume analysis is complete)
        progress_bar = self.query_one("#analysis-progress", ProgressBar)
        progress_bar.update(progress=100)

    def _update_metrics_tab(self) -> None:
        """Update the metrics tab with bias visualizations."""
        if not self.results_data:
            return

        # Update each metric chart
        self._update_metric_chart("gender", ["male", "female", "non-binary", "unclear"])
        self._update_metric_chart("race_ethnicity", ["White", "Black", "Asian", "Hispanic/Latino", "Middle Eastern", "Mixed", "unclear"])
        self._update_metric_chart("age", ["child", "young adult", "middle-aged", "elderly", "unclear"])
        self._update_metric_chart("body_type", ["thin", "average", "plus-size", "muscular", "unclear"])

    def _update_metric_chart(self, category: str, options: List[str]) -> None:
        """Update a specific metric chart with data."""
        if not self.results_data:
            return

        # Count occurrences
        counts = {}
        total = 0

        for result in self.results_data:
            analysis = result.get('analysis', {})
            value = analysis.get(category, {}).get('matched_option', 'unclear')
            counts[value] = counts.get(value, 0) + 1
            total += 1

                # Note: Chart updates are simplified for this implementation
        # In a full implementation, you'd update specific widgets with data

    def _update_stats_tab(self) -> None:
        """Update the statistical analysis tab."""
        stats_table = self.query_one("#stats-table", DataTable)
        if stats_table:
            # Set up table columns
            stats_table.add_columns("Test", "Statistic", "p-value", "Significant")

            # Add sample statistical results (placeholder)
            sample_stats = [
                ("Chi-Square Gender", "15.23", "0.002", "Yes"),
                ("Chi-Square Race", "28.45", "0.000", "Yes"),
                ("Chi-Square Age", "8.92", "0.063", "No"),
                ("Chi-Square Body Type", "12.34", "0.015", "Yes"),
                ("Effect Size (Cramer's V)", "0.23", "-", "-"),
            ]

            for test, stat, p_val, sig in sample_stats:
                stats_table.add_row(test, stat, p_val, sig)

    def action_refresh_results(self) -> None:
        """Refresh results data."""
        self._load_results_data()
        self._update_overview_tab()
        self._update_metrics_tab()
        self._update_stats_tab()
        self.notify("Results refreshed", title="Refresh Complete")

    def action_export_results(self) -> None:
        """Export results to file."""
        if not self.results_data:
            self.notify("No results to export", title="Export Error", severity="warning")
            return

        try:
            export_path = Path("data/results/exported_results.json")
            export_path.parent.mkdir(parents=True, exist_ok=True)

            with open(export_path, 'w') as f:
                json.dump(self.results_data, f, indent=2)

            self.notify(f"Results exported to {export_path}", title="Export Complete")

        except Exception as e:
            self.notify(f"Export failed: {e}", title="Export Error", severity="error")

    def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        if event.button.id == "refresh-button":
            self.action_refresh_results()
        elif event.button.id == "export-button":
            self.action_export_results()
        elif event.button.id == "mlflow-button":
            self._log_to_mlflow()
        elif event.button.id == "prev-image":
            self._show_previous_image()
        elif event.button.id == "next-image":
            self._show_next_image()
        elif event.button.id == "export-json":
            self._export_data("json")
        elif event.button.id == "export-csv":
            self._export_data("csv")
        elif event.button.id == "export-excel":
            self._export_data("excel")

    def _export_data(self, format_type: str) -> None:
        """Export raw data in specified format."""
        if not self.results_data:
            self.notify("No data to export", title="Export Error", severity="warning")
            return

        try:
            if format_type == "json":
                # Already handled in export_results
                self.action_export_results()
            elif format_type == "csv":
                # Convert to CSV format
                import csv
                csv_path = Path("data/results/analysis_results.csv")
                csv_path.parent.mkdir(parents=True, exist_ok=True)

                with open(csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Write header
                    writer.writerow([
                        "image_path", "prompt", "gender", "race_ethnicity",
                        "age", "body_type", "gender_confidence", "race_confidence",
                        "age_confidence", "body_confidence"
                    ])

                    # Write data
                    for result in self.results_data:
                        analysis = result.get('analysis', {})
                        writer.writerow([
                            result.get('image_path', ''),
                            result.get('prompt', ''),
                            analysis.get('gender', {}).get('matched_option', ''),
                            analysis.get('race_ethnicity', {}).get('matched_option', ''),
                            analysis.get('age', {}).get('matched_option', ''),
                            analysis.get('body_type', {}).get('matched_option', ''),
                            analysis.get('gender', {}).get('confidence', ''),
                            analysis.get('race_ethnicity', {}).get('confidence', ''),
                            analysis.get('age', {}).get('confidence', ''),
                            analysis.get('body_type', {}).get('confidence', ''),
                        ])

                self.notify(f"CSV exported to {csv_path}", title="Export Complete")

            else:
                self.notify(f"Export format '{format_type}' not yet implemented", title="Export Info")

        except Exception as e:
            self.notify(f"Export failed: {e}", title="Export Error", severity="error")

    def _log_to_mlflow(self) -> None:
        """Log experiment results to MLflow."""
        if not self.results_data:
            self.notify("No results to log to MLflow", title="MLflow Error", severity="warning")
            return

        try:
            # Try to import and use MLflow
            import mlflow
            import mlflow.sklearn

            # Start MLflow run
            with mlflow.start_run():
                # Log basic metrics
                total_images = len(self.results_data)
                mlflow.log_metric("total_images", total_images)

                # Calculate and log bias metrics
                if isinstance(self.results_data, list):
                    gender_counts = {}
                    race_counts = {}
                    age_counts = {}
                    body_counts = {}

                    for result in self.results_data:
                        analysis = result.get('analysis', {})

                        gender = analysis.get('gender', {}).get('matched_option', 'unclear')
                        gender_counts[gender] = gender_counts.get(gender, 0) + 1

                        race = analysis.get('race_ethnicity', {}).get('matched_option', 'unclear')
                        race_counts[race] = race_counts.get(race, 0) + 1

                        age = analysis.get('age', {}).get('matched_option', 'unclear')
                        age_counts[age] = age_counts.get(age, 0) + 1

                        body = analysis.get('body_type', {}).get('matched_option', 'unclear')
                        body_counts[body] = body_counts.get(body, 0) + 1

                    # Log bias distribution metrics
                    for category, counts in [("gender", gender_counts), ("race", race_counts), ("age", age_counts), ("body", body_counts)]:
                        for option, count in counts.items():
                            percentage = (count / total_images) * 100
                            mlflow.log_metric(f"{category}_{option}_percentage", percentage)

                # Log parameters
                mlflow.log_param("experiment_type", "bias_detection")
                mlflow.log_param("analysis_categories", ["gender", "race_ethnicity", "age", "body_type"])

                # Log the results data as an artifact
                import tempfile
                import json
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(self.results_data, f)
                    temp_file = f.name

                mlflow.log_artifact(temp_file, "results")

                # Clean up temp file
                import os
                os.unlink(temp_file)

            self.notify("Results logged to MLflow successfully", title="MLflow Success")

        except ImportError:
            self.notify("MLflow not installed. Install with: pip install mlflow", title="MLflow Error", severity="error")
        except Exception as e:
            self.notify(f"MLflow logging failed: {e}", title="MLflow Error", severity="error")

    def _show_previous_image(self) -> None:
        """Show the previous image in the gallery."""
        if self.results_data and len(self.results_data) > 0:
            self.current_image_index = max(0, self.current_image_index - 1)
            self._update_gallery_display()

    def _show_next_image(self) -> None:
        """Show the next image in the gallery."""
        if self.results_data and len(self.results_data) > 0:
            self.current_image_index = min(len(self.results_data) - 1, self.current_image_index + 1)
            self._update_gallery_display()

    def _update_gallery_display(self) -> None:
        """Update the gallery display with current image."""
        if not self.results_data or self.current_image_index >= len(self.results_data):
            return

        current_result = self.results_data[self.current_image_index]

        # Update counter
        counter = self.query_one("#image-counter", Static)
        if counter:
            counter.update(f"Image {self.current_image_index + 1} of {len(self.results_data)}")

        # Update image info
        image_info = self.query_one("#current-image-info", Static)
        if image_info:
            image_path = current_result.get('image_path', 'Unknown')
            prompt = current_result.get('prompt', 'No prompt')
            info_text = f"📁 {image_path}\n💬 {prompt}"
            image_info.update(info_text)

        # Update analysis
        analysis_widget = self.query_one("#image-analysis", Static)
        if analysis_widget:
            analysis = current_result.get('analysis', {})

            analysis_text = "🎯 Analysis Results:\n"
            for category in ['gender', 'race_ethnicity', 'age', 'body_type']:
                if category in analysis:
                    category_data = analysis[category]
                    matched = category_data.get('matched_option', 'unclear')
                    confidence = category_data.get('confidence', 'N/A')
                    analysis_text += f"• {category.replace('_', ' ').title()}: {matched} ({confidence})\n"

            analysis_widget.update(analysis_text)

        # Update thumbnails (simplified)
        thumbnails = self.query_one("#gallery-thumbnails", Static)
        if thumbnails:
            thumb_text = f"Showing image {self.current_image_index + 1} of {len(self.results_data)}\n"
            thumb_text += "Gallery thumbnails would show here in a full implementation"
            thumbnails.update(thumb_text)

    DEFAULT_CSS = """
    ResultsDashboard {
        layout: vertical;
    }

    .dashboard-header {
        height: auto;
        background: $primary-darken-1;
        padding: 1;
        margin-bottom: 1;
    }

    .dashboard-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 0.5;
    }

    .dashboard-subtitle {
        text-align: center;
        color: $text-muted;
    }

    .summary-cards {
        height: auto;
        margin-bottom: 1;
    }

    .summary-card {
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

    .card-unit {
        color: $text-muted;
        font-size: 0.8;
    }

    .insights-section, .progress-section {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $surface;
    }

    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .insights-text {
        color: $text;
        line-height: 1.5;
    }

    .analysis-progress {
        width: 100%;
        margin: 1 0;
    }

    .metric-group {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
        background: $surface;
    }

    .metric-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .chart-row {
        margin-bottom: 0.5;
    }

    .chart-label {
        width: 15;
        color: $text;
    }

    .chart-bar {
        width: 1fr;
        margin: 0 1;
    }

    .chart-percentage {
        width: 8;
        text-align: right;
        color: $text-muted;
    }

    .chart-summary {
        margin-top: 1;
        padding-top: 1;
        border-top: solid $primary-darken-2;
    }

    .summary-label {
        color: $text-muted;
        margin-right: 1;
    }

    .summary-value {
        color: $text;
        text-style: bold;
    }

    .stats-table {
        width: 100%;
        height: 20;
    }

    .significance-indicators, .effect-sizes {
        border: solid $primary;
        padding: 1;
        margin-top: 1;
        background: $surface;
    }

    .subsection-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 0.5;
    }

    .significance-text, .effect-size-text {
        color: $text;
        line-height: 1.5;
    }

    .comparison-controls {
        margin-bottom: 1;
    }

    .compare-label {
        margin-right: 1;
        color: $text;
    }

    .experiment-selector {
        width: 1fr;
        height: 10;
    }

    .comparison-results {
        border: solid $primary;
        padding: 1;
        background: $surface;
    }

    .comparison-text {
        color: $text;
        line-height: 1.5;
    }

    .raw-data-table {
        width: 100%;
        height: 30;
    }

    .export-options {
        margin-top: 1;
        align: center;
    }

    .dashboard-actions {
        height: 3;
        margin-top: 1;
        align: center;
    }

    .results-content {
        height: 1fr;
        padding: 1;
    }
    """