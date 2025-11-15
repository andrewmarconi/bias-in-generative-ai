"""
Statistical analysis and bias quantification.

Implements Phase 5 of the research framework: Statistical Analysis and Bias Quantification.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import chi2_contingency, bootstrap
import statsmodels.stats.proportion as smp
from tqdm import tqdm

logger = logging.getLogger(__name__)


class BiasMetrics:
    """
    Calculate statistical metrics for bias detection.

    Implements chi-square tests, effect sizes, and confidence intervals
    as specified in the research framework (Phase 5).
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize bias metrics calculator.

        Args:
            config: Experiment configuration dictionary
        """
        self.config = config
        self.stats_config = config['statistics']
        self.confidence_level = self.stats_config.get('confidence_level', 0.95)
        self.alpha = self.stats_config.get('significance_level', 0.05)

    def calculate_distribution(
        self,
        analysis_results: List[Dict[str, Any]],
        category: str
    ) -> pd.DataFrame:
        """
        Calculate frequency distribution for a bias category.

        Args:
            analysis_results: List of VQA analysis results
            category: Bias category (e.g., 'gender', 'race_ethnicity')

        Returns:
            DataFrame with counts and proportions
        """
        # Extract classifications for this category
        classifications = []
        for result in analysis_results:
            if 'analysis' in result:
                matched = result['analysis'].get(category, {}).get('matched_option', 'unclear')
                classifications.append(matched)

        # Create frequency table
        counts = pd.Series(classifications).value_counts()
        total = len(classifications)
        proportions = counts / total

        # Calculate confidence intervals for proportions
        ci_lower = []
        ci_upper = []

        for count in counts:
            ci = smp.proportion_confint(
                count,
                total,
                alpha=1 - self.confidence_level,
                method='wilson'
            )
            ci_lower.append(ci[0])
            ci_upper.append(ci[1])

        df = pd.DataFrame({
            'count': counts,
            'proportion': proportions,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        })

        return df

    def chi_square_test(
        self,
        observed_counts: pd.Series,
        baseline: str = 'uniform'
    ) -> Dict[str, Any]:
        """
        Perform chi-square goodness of fit test.

        Tests whether observed distribution differs significantly from baseline.

        Args:
            observed_counts: Observed frequency counts
            baseline: 'uniform' for equal distribution, or array of expected proportions

        Returns:
            Dictionary with test statistics
        """
        total = observed_counts.sum()
        num_categories = len(observed_counts)

        # Determine expected frequencies
        if baseline == 'uniform':
            expected = np.ones(num_categories) * (total / num_categories)
        else:
            # Could extend to use population statistics
            expected = np.ones(num_categories) * (total / num_categories)

        # Perform chi-square test
        chi2_stat, p_value = stats.chisquare(observed_counts, expected)

        # Calculate effect size (Cramer's V)
        cramers_v = np.sqrt(chi2_stat / total)

        # Interpret effect size
        effect_size_interpretation = self._interpret_cramers_v(cramers_v)

        result = {
            'chi_square_statistic': float(chi2_stat),
            'p_value': float(p_value),
            'degrees_of_freedom': num_categories - 1,
            'cramers_v': float(cramers_v),
            'effect_size': effect_size_interpretation,
            'significant': bool(p_value < self.alpha),
            'baseline': baseline
        }

        return result

    def _interpret_cramers_v(self, v: float) -> str:
        """
        Interpret Cramer's V effect size.

        Args:
            v: Cramer's V value

        Returns:
            Effect size interpretation
        """
        thresholds = self.stats_config.get('effect_size_thresholds', {
            'small': 0.1,
            'medium': 0.3,
            'large': 0.5
        })

        if v < thresholds['small']:
            return 'negligible'
        elif v < thresholds['medium']:
            return 'small'
        elif v < thresholds['large']:
            return 'medium'
        else:
            return 'large'

    def compare_distributions(
        self,
        dist1: pd.Series,
        dist2: pd.Series,
        labels: Tuple[str, str] = ('Model 1', 'Model 2')
    ) -> Dict[str, Any]:
        """
        Compare two distributions using chi-square test of independence.

        Args:
            dist1: First distribution (frequency counts)
            dist2: Second distribution (frequency counts)
            labels: Labels for the two distributions

        Returns:
            Dictionary with test statistics
        """
        # Create contingency table
        # Ensure same categories
        all_categories = sorted(set(dist1.index) | set(dist2.index))
        counts1 = [dist1.get(cat, 0) for cat in all_categories]
        counts2 = [dist2.get(cat, 0) for cat in all_categories]

        contingency_table = np.array([counts1, counts2])

        # Perform chi-square test of independence
        chi2_stat, p_value, dof, expected = chi2_contingency(contingency_table)

        # Calculate Cramer's V
        n = contingency_table.sum()
        min_dim = min(contingency_table.shape) - 1
        cramers_v = np.sqrt(chi2_stat / (n * min_dim))

        effect_size = self._interpret_cramers_v(cramers_v)

        result = {
            'chi_square_statistic': float(chi2_stat),
            'p_value': float(p_value),
            'degrees_of_freedom': int(dof),
            'cramers_v': float(cramers_v),
            'effect_size': effect_size,
            'significant': bool(p_value < self.alpha),
            'labels': labels,
            'contingency_table': contingency_table.tolist()
        }

        return result

    def bootstrap_confidence_interval(
        self,
        data: np.ndarray,
        statistic_func: callable = np.mean,
        n_iterations: Optional[int] = None
    ) -> Tuple[float, float]:
        """
        Calculate bootstrap confidence interval for a statistic.

        Args:
            data: Input data
            statistic_func: Function to calculate statistic (default: mean)
            n_iterations: Number of bootstrap iterations

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if n_iterations is None:
            n_iterations = self.stats_config.get('bootstrap_iterations', 1000)

        # Perform bootstrap
        rng = np.random.default_rng(self.config['experiment'].get('random_seed', 42))

        res = bootstrap(
            (data,),
            statistic_func,
            n_resamples=n_iterations,
            confidence_level=self.confidence_level,
            random_state=rng
        )

        return res.confidence_interval.low, res.confidence_interval.high

    def calculate_demographic_parity(
        self,
        distribution: pd.Series
    ) -> Dict[str, Any]:
        """
        Calculate demographic parity metric.

        Measures deviation from uniform distribution.

        Args:
            distribution: Frequency distribution (proportions)

        Returns:
            Dictionary with parity metrics
        """
        num_categories = len(distribution)
        uniform_proportion = 1.0 / num_categories

        # Calculate max deviation from uniform
        max_deviation = float((distribution - uniform_proportion).abs().max())

        # Calculate total variation distance
        tvd = float((distribution - uniform_proportion).abs().sum() / 2)

        # Demographic parity satisfied if all proportions are close to uniform
        parity_threshold = 0.1  # 10% deviation threshold
        parity_satisfied = bool(max_deviation <= parity_threshold)

        result = {
            'max_deviation': max_deviation,
            'total_variation_distance': tvd,
            'parity_satisfied': parity_satisfied,
            'threshold': parity_threshold,
            'expected_proportion': uniform_proportion
        }

        return result

    def analyze_prompt_category(
        self,
        analysis_results: List[Dict[str, Any]],
        bias_category: str,
        prompt_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis for a bias category.

        Args:
            analysis_results: List of VQA analysis results
            bias_category: Bias category to analyze (e.g., 'gender')
            prompt_category: Optional prompt category to filter by

        Returns:
            Dictionary with comprehensive statistics
        """
        # Filter by prompt category if specified
        if prompt_category:
            filtered_results = [
                r for r in analysis_results
                if r.get('prompt_id', '').startswith(prompt_category)
            ]
        else:
            filtered_results = analysis_results

        # Calculate distribution
        distribution_df = self.calculate_distribution(filtered_results, bias_category)

        # Chi-square test
        chi_square_result = self.chi_square_test(distribution_df['count'])

        # Demographic parity
        parity_result = self.calculate_demographic_parity(distribution_df['proportion'])

        # Compile comprehensive result
        result = {
            'bias_category': bias_category,
            'prompt_category': prompt_category or 'all',
            'sample_size': len(filtered_results),
            'distribution': distribution_df.to_dict(),
            'chi_square_test': chi_square_result,
            'demographic_parity': parity_result
        }

        return result

    def generate_summary_report(
        self,
        analysis_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive statistical summary.

        Args:
            analysis_results: List of VQA analysis results

        Returns:
            Dictionary with summary statistics for all bias categories
        """
        bias_categories = self.config['bias_categories']

        summary = {
            'experiment': self.config['experiment']['name'],
            'total_images_analyzed': len(analysis_results),
            'bias_analyses': {}
        }

        for category in tqdm(bias_categories, desc="Analyzing bias categories", unit="category"):
            category_analysis = self.analyze_prompt_category(
                analysis_results,
                category
            )
            summary['bias_analyses'][category] = category_analysis

        return summary
