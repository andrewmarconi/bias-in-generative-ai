"""
Visualization module for bias detection results.

Implements Phase 10 of the research framework: Reporting and Visualization.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Set style
sns.set_style("whitegrid")
sns.set_palette("husl")


class BiasVisualizer:
    """
    Create visualizations for bias detection results.

    Implements visualization best practices from Phase 10.
    """

    def __init__(self, output_dir: str = "data/results/visualizations"):
        """
        Initialize visualizer.

        Args:
            output_dir: Directory to save visualizations
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_distribution(
        self,
        distribution_df: pd.DataFrame,
        category: str,
        title: Optional[str] = None
    ) -> str:
        """
        Plot demographic distribution with confidence intervals.

        Args:
            distribution_df: DataFrame with counts, proportions, and CIs
            category: Bias category name
            title: Optional custom title

        Returns:
            Path to saved figure
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        # Sort by proportion
        df_sorted = distribution_df.sort_values('proportion', ascending=False)

        # Create bar plot with error bars
        x = range(len(df_sorted))
        proportions = df_sorted['proportion']
        errors = np.array([
            proportions - df_sorted['ci_lower'],
            df_sorted['ci_upper'] - proportions
        ])

        ax.bar(x, proportions, capsize=5, alpha=0.7, edgecolor='black')
        ax.errorbar(
            x, proportions, yerr=errors,
            fmt='none', ecolor='black', capsize=5, linewidth=2
        )

        # Labels and formatting
        ax.set_xticks(x)
        ax.set_xticklabels(df_sorted.index, rotation=45, ha='right')
        ax.set_ylabel('Proportion', fontsize=12)
        ax.set_xlabel(category.replace('_', ' ').title(), fontsize=12)

        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        else:
            ax.set_title(
                f'{category.replace("_", " ").title()} Distribution',
                fontsize=14,
                fontweight='bold'
            )

        # Add count annotations
        for i, (idx, row) in enumerate(df_sorted.iterrows()):
            ax.text(
                i, row['proportion'] + 0.02,
                f"n={row['count']}",
                ha='center',
                va='bottom',
                fontsize=9
            )

        # Add uniform baseline
        uniform = 1.0 / len(df_sorted)
        ax.axhline(uniform, color='red', linestyle='--', label='Uniform distribution', alpha=0.7)
        ax.legend()

        plt.tight_layout()

        # Save
        filename = f"{category}_distribution.png"
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved distribution plot: {filepath}")
        return str(filepath)

    def plot_all_distributions(
        self,
        statistical_summary: Dict[str, Any]
    ) -> List[str]:
        """
        Create distribution plots for all bias categories.

        Args:
            statistical_summary: Statistical summary dictionary

        Returns:
            List of paths to saved figures
        """
        filepaths = []

        for category, analysis in statistical_summary['bias_analyses'].items():
            # Convert distribution dict to DataFrame
            dist_dict = analysis['distribution']
            df = pd.DataFrame({
                'count': dist_dict['count'],
                'proportion': dist_dict['proportion'],
                'ci_lower': dist_dict['ci_lower'],
                'ci_upper': dist_dict['ci_upper']
            })

            filepath = self.plot_distribution(df, category)
            filepaths.append(filepath)

        return filepaths

    def plot_effect_sizes(
        self,
        statistical_summary: Dict[str, Any]
    ) -> str:
        """
        Plot effect sizes (Cramer's V) across bias categories.

        Args:
            statistical_summary: Statistical summary dictionary

        Returns:
            Path to saved figure
        """
        categories = []
        cramers_v_values = []
        p_values = []
        effect_sizes = []

        for category, analysis in statistical_summary['bias_analyses'].items():
            chi_square = analysis['chi_square_test']
            categories.append(category.replace('_', ' ').title())
            cramers_v_values.append(chi_square['cramers_v'])
            p_values.append(chi_square['p_value'])
            effect_sizes.append(chi_square['effect_size'])

        fig, ax = plt.subplots(figsize=(10, 6))

        # Create bar plot
        bars = ax.barh(categories, cramers_v_values, alpha=0.7, edgecolor='black')

        # Color bars by significance
        colors = ['green' if p < 0.05 else 'gray' for p in p_values]
        for bar, color in zip(bars, colors):
            bar.set_color(color)

        # Add effect size thresholds
        ax.axvline(0.1, color='orange', linestyle='--', alpha=0.5, label='Small effect')
        ax.axvline(0.3, color='red', linestyle='--', alpha=0.5, label='Medium effect')
        ax.axvline(0.5, color='darkred', linestyle='--', alpha=0.5, label='Large effect')

        ax.set_xlabel("Cramer's V (Effect Size)", fontsize=12)
        ax.set_title("Effect Sizes Across Bias Categories", fontsize=14, fontweight='bold')
        ax.legend()

        # Add value labels
        for i, (v, es) in enumerate(zip(cramers_v_values, effect_sizes)):
            ax.text(v + 0.01, i, f'{v:.3f} ({es})', va='center', fontsize=9)

        plt.tight_layout()

        # Save
        filepath = self.output_dir / "effect_sizes.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved effect sizes plot: {filepath}")
        return str(filepath)

    def create_summary_figure(
        self,
        statistical_summary: Dict[str, Any]
    ) -> str:
        """
        Create a comprehensive summary figure with multiple subplots.

        Args:
            statistical_summary: Statistical summary dictionary

        Returns:
            Path to saved figure
        """
        num_categories = len(statistical_summary['bias_analyses'])
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(
            f"Bias Detection Summary: {statistical_summary['experiment']}",
            fontsize=16,
            fontweight='bold'
        )

        # Plot 1: Effect sizes
        ax = axes[0, 0]
        categories = []
        cramers_v = []

        for cat, analysis in statistical_summary['bias_analyses'].items():
            categories.append(cat.replace('_', '\n'))
            cramers_v.append(analysis['chi_square_test']['cramers_v'])

        ax.bar(categories, cramers_v, alpha=0.7, edgecolor='black')
        ax.set_ylabel("Cramer's V")
        ax.set_title("Effect Sizes by Category")
        ax.axhline(0.3, color='red', linestyle='--', alpha=0.5, label='Medium effect')
        ax.legend()

        # Plot 2: P-values (log scale)
        ax = axes[0, 1]
        p_values = [analysis['chi_square_test']['p_value']
                   for analysis in statistical_summary['bias_analyses'].values()]

        ax.bar(categories, p_values, alpha=0.7, edgecolor='black')
        ax.set_ylabel("p-value")
        ax.set_title("Statistical Significance")
        ax.axhline(0.05, color='red', linestyle='--', alpha=0.5, label='α = 0.05')
        ax.set_yscale('log')
        ax.legend()

        # Plot 3: Max deviations from uniform
        ax = axes[1, 0]
        deviations = [analysis['demographic_parity']['max_deviation']
                     for analysis in statistical_summary['bias_analyses'].values()]

        ax.bar(categories, deviations, alpha=0.7, edgecolor='black')
        ax.set_ylabel("Max Deviation from Uniform")
        ax.set_title("Demographic Parity Violations")
        ax.axhline(0.1, color='red', linestyle='--', alpha=0.5, label='Threshold')
        ax.legend()

        # Plot 4: Sample sizes
        ax = axes[1, 1]
        sample_sizes = [analysis['sample_size']
                       for analysis in statistical_summary['bias_analyses'].values()]

        ax.bar(categories, sample_sizes, alpha=0.7, edgecolor='black')
        ax.set_ylabel("Sample Size")
        ax.set_title("Images Analyzed per Category")

        plt.tight_layout()

        # Save
        filepath = self.output_dir / "summary_figure.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Saved summary figure: {filepath}")
        return str(filepath)

    def generate_all_visualizations(
        self,
        statistical_summary: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Generate all visualizations.

        Args:
            statistical_summary: Statistical summary dictionary

        Returns:
            Dictionary mapping visualization types to file paths
        """
        logger.info("Generating visualizations...")

        visualizations = {
            'distributions': self.plot_all_distributions(statistical_summary),
            'effect_sizes': [self.plot_effect_sizes(statistical_summary)],
            'summary': [self.create_summary_figure(statistical_summary)]
        }

        logger.info(f"All visualizations saved to {self.output_dir}")

        return visualizations
