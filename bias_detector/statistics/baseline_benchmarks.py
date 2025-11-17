from __future__ import annotations
import math
from typing import Dict, Optional

try:
    import yaml
except Exception:
    yaml = None  # type: ignore

import os
from pathlib import Path


def load_baseline_config(path: str = "config/baseline.yaml") -> Optional[Dict[str, Dict[str, float]]]:
    """Load baseline distributions from a YAML file.

    Returns a dict of categories -> {category_value: proportion} or None if file not found.
    """
    p = Path(path)
    if not p.exists():
        return None
    if yaml is None:
        raise RuntimeError("PyYAML is required to load baseline.yaml but is not available.")
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # expected shape: {baselines: {gender: {female: 0.5, male: 0.5}, ...}}
    if not isinstance(data, dict):
        return None
    baselines = data.get("baselines") or data
    if not isinstance(baselines, dict):
        return None
    # Normalize: ensure inner dicts map to float values
    normalized: Dict[str, Dict[str, float]] = {}
    for cat, values in baselines.items():
        if isinstance(values, dict):
            inner: Dict[str, float] = {}
            for k, v in values.items():
                try:
                    inner[str(k)] = float(v)
                except Exception:
                    continue
            normalized[cat] = inner
    return normalized


def _sum(d: Dict[str, float]) -> float:
    return sum(d.values())


def chi_square_against_baseline(observed: Dict[str, int], baseline_cat: Dict[str, float]) -> Optional[Dict[str, float]]:
    """Compute a chi-square statistic comparing observed counts to baseline proportions for a single category.

    observed: mapping from category label to observed count (must cover same keys as baseline_cat if you want full test)
    baseline_cat: mapping from category label to baseline proportion (sums to ~1.0)

    Returns dict with chi_square and total, or None if total == 0 or mismatch.
    """
    if not observed:
        return None
    total = sum(observed.values())
    if total == 0:
        return None
    # If observed keys don't align perfectly with baseline, aggregate by intersection and handle missing as 0
    chi2 = 0.0
    for label, count in observed.items():
        # Determine expected proportion for this label if present in baseline
        p = baseline_cat.get(label)
        if p is None:
            # If label not in baseline, skip in this simple benchmark
            continue
        expected = p * total
        if expected <= 0:
            continue
        chi2 += (count - expected) ** 2 / expected
    return {"chi_square": chi2, "total": total}
