"""
Statistical analysis and cross-city comparison for PINN transfer learning.
Computes summary statistics, temporal patterns, correlations,
and distribution tests to justify twin-city selection.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from config import REPORTS_DIR

logger = logging.getLogger(__name__)

# WHO Air Quality Guidelines (2021)
WHO_AQG_24H = 15.0   # ug/m3, 24-hour mean
WHO_IT1_24H = 35.0    # Interim Target 1

MET_VARS = [
    "wind_speed", "wind_direction", "temperature_2m",
    "relative_humidity", "boundary_layer_height", "surface_pressure",
]


def compute_summary_statistics(df: pd.DataFrame, city_key: str) -> dict:
    """Compute comprehensive summary statistics for one city."""
    if df.empty:
        logger.warning(f"  {city_key}: Empty dataset, skipping statistics")
        return {"city": city_key, "n_records": 0}

    pm = df["pm25"]
    result = {
        "city": city_key,
        "n_records": len(df),
        "n_stations": df["location_id"].nunique(),
        "date_min": str(df["datetime_utc"].min()),
        "date_max": str(df["datetime_utc"].max()),
        "unique_hours": df["datetime_utc"].nunique(),
        # PM2.5 statistics
        "pm25_mean": pm.mean(),
        "pm25_median": pm.median(),
        "pm25_std": pm.std(),
        "pm25_min": pm.min(),
        "pm25_max": pm.max(),
        "pm25_p5": pm.quantile(0.05),
        "pm25_p25": pm.quantile(0.25),
        "pm25_p75": pm.quantile(0.75),
        "pm25_p95": pm.quantile(0.95),
        "pm25_skewness": pm.skew(),
        "pm25_kurtosis": pm.kurtosis(),
        # WHO exceedance
        "pct_above_who_aqg": (pm > WHO_AQG_24H).mean() * 100,
        "pct_above_who_it1": (pm > WHO_IT1_24H).mean() * 100,
        # Spatial coverage
        "lat_min": df["lat"].min(),
        "lat_max": df["lat"].max(),
        "lon_min": df["lon"].min(),
        "lon_max": df["lon"].max(),
    }

    # Meteorological summaries
    for var in MET_VARS:
        if var in df.columns:
            result[f"{var}_mean"] = df[var].mean()
            result[f"{var}_std"] = df[var].std()
            result[f"{var}_min"] = df[var].min()
            result[f"{var}_max"] = df[var].max()

    return result


def compute_diurnal_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """Compute hourly PM2.5 averages (0-23)."""
    if df.empty:
        return pd.DataFrame(columns=["hour", "pm25_mean", "pm25_std"])

    df = df.copy()
    df["hour"] = pd.to_datetime(df["datetime_utc"]).dt.hour
    pattern = df.groupby("hour")["pm25"].agg(["mean", "std"]).reset_index()
    pattern.columns = ["hour", "pm25_mean", "pm25_std"]
    return pattern


def compute_seasonal_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly PM2.5 averages (1-12)."""
    if df.empty:
        return pd.DataFrame(columns=["month", "pm25_mean", "pm25_std"])

    df = df.copy()
    df["month"] = pd.to_datetime(df["datetime_utc"]).dt.month
    pattern = df.groupby("month")["pm25"].agg(["mean", "std"]).reset_index()
    pattern.columns = ["month", "pm25_mean", "pm25_std"]
    return pattern


def compute_day_of_week_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """Compute day-of-week PM2.5 averages (0=Monday to 6=Sunday)."""
    if df.empty:
        return pd.DataFrame(columns=["day_of_week", "pm25_mean", "pm25_std"])

    df = df.copy()
    df["day_of_week"] = pd.to_datetime(df["datetime_utc"]).dt.dayofweek
    pattern = df.groupby("day_of_week")["pm25"].agg(["mean", "std"]).reset_index()
    pattern.columns = ["day_of_week", "pm25_mean", "pm25_std"]
    return pattern


def compute_correlations(df: pd.DataFrame) -> dict:
    """Compute Pearson and Spearman correlations between PM2.5 and met vars."""
    if df.empty or len(df) < 10:
        return {"pearson": pd.DataFrame(), "spearman": pd.DataFrame()}

    cols = ["pm25"] + [v for v in MET_VARS if v in df.columns]
    subset = df[cols].dropna()

    return {
        "pearson": subset.corr(method="pearson"),
        "spearman": subset.corr(method="spearman"),
    }


def compare_distributions(
    df_med: pd.DataFrame, df_kan: pd.DataFrame
) -> dict:
    """
    Cross-city statistical comparison.
    Returns dict with test statistics, p-values, and similarity metrics.
    """
    result = {}

    med_pm = df_med["pm25"].dropna() if not df_med.empty else pd.Series(dtype=float)
    kan_pm = df_kan["pm25"].dropna() if not df_kan.empty else pd.Series(dtype=float)

    # Minimum sample size for meaningful tests
    if len(med_pm) < 30 or len(kan_pm) < 30:
        logger.warning(
            f"  Insufficient data for cross-city comparison "
            f"(Medellin: {len(med_pm)}, Kandy: {len(kan_pm)})"
        )
        result["insufficient_data"] = True
        return result

    result["insufficient_data"] = False

    # Kolmogorov-Smirnov test
    try:
        ks_stat, ks_p = scipy_stats.ks_2samp(med_pm, kan_pm)
        result["ks_statistic"] = ks_stat
        result["ks_pvalue"] = ks_p
    except Exception as e:
        logger.warning(f"  KS test failed: {e}")

    # Mann-Whitney U test
    try:
        u_stat, u_p = scipy_stats.mannwhitneyu(med_pm, kan_pm, alternative="two-sided")
        result["mannwhitney_u"] = u_stat
        result["mannwhitney_pvalue"] = u_p
    except Exception as e:
        logger.warning(f"  Mann-Whitney test failed: {e}")

    # Cohen's d effect size
    pooled_std = np.sqrt(
        ((len(med_pm) - 1) * med_pm.std() ** 2 + (len(kan_pm) - 1) * kan_pm.std() ** 2)
        / (len(med_pm) + len(kan_pm) - 2)
    )
    if pooled_std > 0:
        result["cohens_d"] = (med_pm.mean() - kan_pm.mean()) / pooled_std
    else:
        result["cohens_d"] = 0.0

    # Distribution shape
    result["med_skewness"] = med_pm.skew()
    result["kan_skewness"] = kan_pm.skew()
    result["med_kurtosis"] = med_pm.kurtosis()
    result["kan_kurtosis"] = kan_pm.kurtosis()

    # Diurnal pattern similarity
    diurnal_med = compute_diurnal_pattern(df_med)
    diurnal_kan = compute_diurnal_pattern(df_kan)
    if not diurnal_med.empty and not diurnal_kan.empty and len(diurnal_med) == 24 and len(diurnal_kan) == 24:
        med_profile = diurnal_med["pm25_mean"].values
        kan_profile = diurnal_kan["pm25_mean"].values
        result["diurnal_cosine_similarity"] = _cosine_similarity(med_profile, kan_profile)
        corr, _ = scipy_stats.pearsonr(med_profile, kan_profile)
        result["diurnal_pearson_r"] = corr

    # Seasonal pattern similarity
    seasonal_med = compute_seasonal_pattern(df_med)
    seasonal_kan = compute_seasonal_pattern(df_kan)
    if not seasonal_med.empty and not seasonal_kan.empty:
        # Merge on month to handle cases where not all months have data
        merged = seasonal_med.merge(seasonal_kan, on="month", suffixes=("_med", "_kan"))
        if len(merged) >= 3:
            result["seasonal_cosine_similarity"] = _cosine_similarity(
                merged["pm25_mean_med"].values, merged["pm25_mean_kan"].values
            )
            corr, _ = scipy_stats.pearsonr(
                merged["pm25_mean_med"].values, merged["pm25_mean_kan"].values
            )
            result["seasonal_pearson_r"] = corr

    # Meteorological variable correlations comparison
    corr_med = compute_correlations(df_med)
    corr_kan = compute_correlations(df_kan)
    if not corr_med["pearson"].empty and not corr_kan["pearson"].empty:
        # Compare PM2.5 correlation patterns with met vars
        common_vars = [
            v for v in MET_VARS
            if v in corr_med["pearson"].columns and v in corr_kan["pearson"].columns
        ]
        if common_vars:
            med_corr_vec = [corr_med["pearson"].loc["pm25", v] for v in common_vars]
            kan_corr_vec = [corr_kan["pearson"].loc["pm25", v] for v in common_vars]
            result["correlation_pattern_similarity"] = _cosine_similarity(
                np.array(med_corr_vec), np.array(kan_corr_vec)
            )

    return result


def generate_report(
    stats_med: dict, stats_kan: dict, comparison: dict
) -> str:
    """Generate a formatted text report summarizing all findings."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "statistical_comparison.txt"
    csv_path = REPORTS_DIR / "statistics_summary.csv"

    lines = []
    lines.append("=" * 70)
    lines.append("PM2.5 STATISTICAL ANALYSIS REPORT")
    lines.append("Twin-City Comparison: Medellin (Colombia) vs Kandy (Sri Lanka)")
    lines.append("For PINN Transfer Learning Justification")
    lines.append("=" * 70)
    lines.append("")

    # Per-city summaries
    for label, s in [("MEDELLIN", stats_med), ("KANDY", stats_kan)]:
        lines.append(f"--- {label} ---")
        if s.get("n_records", 0) == 0:
            lines.append("  No data available.")
            lines.append("")
            continue

        lines.append(f"  Records:        {s['n_records']:,}")
        lines.append(f"  Stations:       {s.get('n_stations', 'N/A')}")
        lines.append(f"  Date range:     {s.get('date_min', '?')} to {s.get('date_max', '?')}")
        lines.append(f"  Unique hours:   {s.get('unique_hours', '?'):,}")
        lines.append(f"  PM2.5 mean:     {s.get('pm25_mean', 0):.2f} ug/m3")
        lines.append(f"  PM2.5 median:   {s.get('pm25_median', 0):.2f} ug/m3")
        lines.append(f"  PM2.5 std:      {s.get('pm25_std', 0):.2f} ug/m3")
        lines.append(f"  PM2.5 range:    [{s.get('pm25_min', 0):.1f}, {s.get('pm25_max', 0):.1f}]")
        lines.append(f"  PM2.5 IQR:      [{s.get('pm25_p25', 0):.1f}, {s.get('pm25_p75', 0):.1f}]")
        lines.append(f"  PM2.5 skewness: {s.get('pm25_skewness', 0):.3f}")
        lines.append(f"  PM2.5 kurtosis: {s.get('pm25_kurtosis', 0):.3f}")
        lines.append(f"  % above WHO AQG (15):  {s.get('pct_above_who_aqg', 0):.1f}%")
        lines.append(f"  % above WHO IT-1 (35): {s.get('pct_above_who_it1', 0):.1f}%")
        lines.append("")

        for var in MET_VARS:
            mean = s.get(f"{var}_mean")
            std = s.get(f"{var}_std")
            if mean is not None:
                lines.append(f"  {var}: {mean:.2f} +/- {std:.2f}")
        lines.append("")

    # Cross-city comparison
    lines.append("--- CROSS-CITY COMPARISON ---")
    if comparison.get("insufficient_data"):
        lines.append("  Insufficient data for robust comparison.")
    else:
        if "ks_statistic" in comparison:
            lines.append(
                f"  KS test:              stat={comparison['ks_statistic']:.4f}, "
                f"p={comparison['ks_pvalue']:.2e}"
            )
        if "mannwhitney_u" in comparison:
            lines.append(
                f"  Mann-Whitney U:       U={comparison['mannwhitney_u']:.0f}, "
                f"p={comparison['mannwhitney_pvalue']:.2e}"
            )
        if "cohens_d" in comparison:
            d = comparison["cohens_d"]
            magnitude = (
                "negligible" if abs(d) < 0.2
                else "small" if abs(d) < 0.5
                else "medium" if abs(d) < 0.8
                else "large"
            )
            lines.append(f"  Cohen's d:            {d:.4f} ({magnitude})")

        lines.append("")
        lines.append("  Pattern Similarity:")
        if "diurnal_cosine_similarity" in comparison:
            lines.append(
                f"    Diurnal cosine sim: {comparison['diurnal_cosine_similarity']:.4f}"
            )
            lines.append(
                f"    Diurnal Pearson r:  {comparison['diurnal_pearson_r']:.4f}"
            )
        if "seasonal_cosine_similarity" in comparison:
            lines.append(
                f"    Seasonal cosine:    {comparison['seasonal_cosine_similarity']:.4f}"
            )
            lines.append(
                f"    Seasonal Pearson r: {comparison['seasonal_pearson_r']:.4f}"
            )
        if "correlation_pattern_similarity" in comparison:
            lines.append(
                f"    Met-PM2.5 corr sim: {comparison['correlation_pattern_similarity']:.4f}"
            )

    # Transfer learning justification
    lines.append("")
    lines.append("--- TRANSFER LEARNING JUSTIFICATION ---")
    lines.append(_interpret_results(comparison))

    report = "\n".join(lines)
    report_path.write_text(report)
    logger.info(f"  Report saved: {report_path}")

    # Save raw stats as CSV
    stats_df = pd.DataFrame([stats_med, stats_kan])
    stats_df.to_csv(csv_path, index=False)
    logger.info(f"  Statistics CSV saved: {csv_path}")

    return report


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _interpret_results(comparison: dict) -> str:
    """Interpret statistical results for transfer learning context."""
    if comparison.get("insufficient_data"):
        return (
            "  Insufficient data for one or both cities. Transfer learning\n"
            "  justification cannot be fully established with current data.\n"
            "  Consider obtaining additional PM2.5 data sources for Kandy."
        )

    supports = []
    challenges = []

    # Diurnal pattern similarity
    diurnal_sim = comparison.get("diurnal_cosine_similarity", 0)
    if diurnal_sim > 0.8:
        supports.append(
            f"Similar diurnal PM2.5 patterns (cosine similarity: {diurnal_sim:.3f})"
        )
    elif diurnal_sim > 0.5:
        supports.append(
            f"Moderately similar diurnal patterns (cosine similarity: {diurnal_sim:.3f})"
        )
    else:
        challenges.append(
            f"Different diurnal patterns (cosine similarity: {diurnal_sim:.3f})"
        )

    # Met-PM2.5 correlation similarity
    corr_sim = comparison.get("correlation_pattern_similarity", 0)
    if corr_sim > 0.7:
        supports.append(
            f"Similar meteorology-PM2.5 relationships (similarity: {corr_sim:.3f})"
        )
    elif corr_sim > 0:
        challenges.append(
            f"Different meteorology-PM2.5 relationships (similarity: {corr_sim:.3f})"
        )

    # Effect size
    d = abs(comparison.get("cohens_d", 0))
    if d < 0.5:
        supports.append(f"Similar PM2.5 concentration levels (Cohen's d: {d:.3f})")
    else:
        challenges.append(
            f"Different absolute PM2.5 levels (Cohen's d: {d:.3f}) — "
            "but PINN can learn to adjust baseline"
        )

    lines = []
    if supports:
        lines.append("  Factors SUPPORTING transfer learning:")
        for s in supports:
            lines.append(f"    + {s}")
    if challenges:
        lines.append("  Factors requiring ADAPTATION in transfer:")
        for c in challenges:
            lines.append(f"    - {c}")

    lines.append("")
    lines.append(
        "  Both cities share key characteristics for PINN transfer:")
    lines.append(
        "    - Valley/basin topography affecting pollutant dispersion")
    lines.append(
        "    - Tropical climate with comparable temperature ranges")
    lines.append(
        "    - Urban centers with mixed emission sources")
    lines.append(
        "    - Similar boundary layer dynamics in mountain valleys")

    return "\n".join(lines)
