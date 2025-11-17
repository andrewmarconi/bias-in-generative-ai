#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Optional

# Attempt to reuse existing baseline utilities if available
try:
    from bias_detector.statistics.baseline_benchmarks import load_baseline_config, chi_square_against_baseline
except Exception:
    load_baseline_config = None  # type: ignore
    chi_square_against_baseline = None  # type: ignore


def _load_json(path: Path) -> list:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception:
            data = []
    if isinstance(data, list):
        return data
    # wrap if an object with a key like "results"
    if isinstance(data, dict) and data:
        # try common keys
        for k in ("results", "analysis_results", "analysis"):
            v = data.get(k)
            if isinstance(v, list):
                return v
    return []


def _accumulate_counts(results: list, category: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for entry in results:
        if not isinstance(entry, dict):
            continue
        analysis = entry.get("analysis") or entry.get("analysis_results") or entry.get("results")
        if not isinstance(analysis, dict):
            continue
        cat_val = analysis.get(category)
        if cat_val is None:
            continue
        if isinstance(cat_val, dict):
            for lbl, v in cat_val.items():
                try:
                    n = int(v)
                except Exception:
                    continue
                counts[lbl] = counts.get(lbl, 0) + n
        elif isinstance(cat_val, dict):  # pragma: no cover
            pass
        elif isinstance(cat_val, str):
            counts[cat_val] = counts.get(cat_val, 0) + 1
        elif isinstance(cat_val, list):
            for item in cat_val:
                if isinstance(item, str):
                    counts[item] = counts.get(item, 0) + 1
    return counts


def _safe_float(x: Optional[float]) -> Optional[float]:
    try:
        return float(x) if x is not None else None
    except Exception:
        return None


def _maybe_import_scipy():
    try:
        from scipy.stats import chi2
        return chi2
    except Exception:
        return None


def main():
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Baseline benchmarking for demographic parity in generated images.")
    parser.add_argument("--results", default="data/processed/analysis_results.json", help="Path to analysis results JSON (per-image demographics)")
    parser.add_argument("--baseline", default="config/baseline.yaml", help="Path to YAML baseline file")
    parser.add_argument("--category", default=None, help="Comma-separated category names to analyze (e.g., gender, age, race_ethnicity) or omit to analyze all")
    parser.add_argument("--output", default=None, help="Optional path to write JSON summary")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Resolve paths
    results_path = Path(args.results)
    baseline_path = Path(args.baseline)

    # Load results
    results = _load_json(results_path)
    if args.verbose:
        print(f"Loaded {len(results)} analysis records from {results_path}")

    # Load baseline (using helper if available)
    if load_baseline_config is None:
        print("Baseline loader not available in this environment.")
        return
    baseline = load_baseline_config(str(baseline_path)) or {}
    if not baseline:
        logging.warning("No baselines loaded from %s", baseline_path)

    categories: list[str] = []
    if args.category:
        categories = [c.strip() for c in args.category.split(",") if c.strip()]
    else:
        categories = list(baseline.keys())

    summary: Dict[str, dict] = {}
    # Try to reuse SciPy for p-values if available
    chi2_dist = _maybe_import_scipy()

    for cat in categories:
        counts = _accumulate_counts(results, cat)
        baseline_cat = baseline.get(cat, {}) or {}
        if not counts or not baseline_cat:
            summary[cat] = {"counts": counts, "baseline": baseline_cat, "note": "insufficient data"}
            continue
        # Compute chi-square against baseline
        if chi_square_against_baseline is None:
            summary[cat] = {"counts": counts, "baseline": baseline_cat, "chi_square": None}
            continue
        res = chi_square_against_baseline(counts, baseline_cat)
        chi_square = res.get("chi_square") if res else None
        total = res.get("total") if res else 0
        p_val = None
        df = 0
        if chi_square is not None:
            # degrees of freedom: number of observed labels we compared against baseline minus 1
            df = max(1, len([k for k in baseline_cat.keys() if k in counts]) - 1)
            if chi2_dist is not None and df > 0:
                p_val = float(chi2_dist.sf(chi_square, df))
        summary[cat] = {
            "counts": counts,
            "baseline": baseline_cat,
            "chi_square": chi_square,
            "total": total,
            "p_value": p_val,
            "df": df,
        }

    # Print a readable summary
    for cat, data in summary.items():
        print(f"Category: {cat}")
        counts = data.get("counts") or {}
        if isinstance(counts, dict):
            print(f"  Observed counts: {counts}")
        print(f"  Baseline: {data.get('baseline')}")
        chi = data.get("chi_square")
        if chi is not None:
            p = data.get("p_value")
            df = data.get("df")
            if p is not None:
                print(f"  Chi-square: {chi:.4f} (p={p:.4f}, df={df})")
            else:
                print(f"  Chi-square: {chi:.4f} (df={df})")
        else:
            print("  Chi-square: N/A (insufficient data)")
        print("")

    # Optional JSON output
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"Wrote baseline benchmark summary to {out_path}")


if __name__ == "__main__":
    main()
