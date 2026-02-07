"""
Visualization module for PM2.5 data analysis.
Generates publication-quality PNG charts comparing Medellin and Kandy.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

from config import FIGURES_DIR, YEAR

logger = logging.getLogger(__name__)

# Styling
sns.set_theme(style="whitegrid", font_scale=1.1)
COLORS = {"medellin": "#E74C3C", "kandy": "#3498DB"}
CITY_LABELS = {"medellin": "Medellín", "kandy": "Kandy"}
DPI = 200


def _save_fig(fig: plt.Figure, name: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(str(path), dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info(f"    Saved: {path}")


def _has_data(*dfs: pd.DataFrame) -> bool:
    return all(not df.empty for df in dfs)


def plot_pm25_timeseries(df_med: pd.DataFrame, df_kan: pd.DataFrame) -> None:
    """Daily average PM2.5 time series for each city."""
    try:
        fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

        for ax, (key, df) in zip(axes, [("medellin", df_med), ("kandy", df_kan)]):
            if df.empty:
                ax.text(0.5, 0.5, f"No data for {CITY_LABELS[key]}",
                        ha="center", va="center", transform=ax.transAxes)
                ax.set_ylabel("PM2.5 (μg/m³)")
                continue

            df = df.copy()
            df["date"] = pd.to_datetime(df["datetime_utc"]).dt.date
            daily = df.groupby("date")["pm25"].agg(["mean", "std"]).reset_index()
            daily["date"] = pd.to_datetime(daily["date"])

            ax.plot(daily["date"], daily["mean"], color=COLORS[key], linewidth=0.8)
            ax.fill_between(
                daily["date"],
                daily["mean"] - daily["std"],
                daily["mean"] + daily["std"],
                alpha=0.2, color=COLORS[key],
            )
            ax.axhline(15, color="green", linestyle="--", alpha=0.7, label="WHO AQG (15)")
            ax.axhline(35, color="orange", linestyle="--", alpha=0.7, label="WHO IT-1 (35)")
            ax.set_ylabel("PM2.5 (μg/m³)")
            ax.set_title(f"{CITY_LABELS[key]} - Daily Average PM2.5")
            ax.legend(loc="upper right", fontsize=9)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
            ax.xaxis.set_major_locator(mdates.MonthLocator())

        axes[-1].set_xlabel(str(YEAR))
        fig.suptitle("PM2.5 Time Series Comparison", fontsize=14, fontweight="bold")
        plt.tight_layout()
        _save_fig(fig, "pm25_timeseries")
    except Exception as e:
        logger.error(f"  Failed to plot timeseries: {e}")


def plot_pm25_distributions(df_med: pd.DataFrame, df_kan: pd.DataFrame) -> None:
    """Overlapping histograms and KDE for PM2.5 distributions."""
    try:
        fig, ax = plt.subplots(figsize=(10, 6))

        for key, df in [("medellin", df_med), ("kandy", df_kan)]:
            if df.empty:
                continue
            pm = df["pm25"].dropna()
            ax.hist(pm, bins=60, alpha=0.4, color=COLORS[key],
                    label=f"{CITY_LABELS[key]} (n={len(pm):,})", density=True)
            pm.plot.kde(ax=ax, color=COLORS[key], linewidth=2)

        ax.axvline(15, color="green", linestyle="--", alpha=0.7, label="WHO AQG")
        ax.axvline(35, color="orange", linestyle="--", alpha=0.7, label="WHO IT-1")
        ax.set_xlabel("PM2.5 (μg/m³)")
        ax.set_ylabel("Density")
        ax.set_title("PM2.5 Distribution Comparison")
        ax.legend()
        ax.set_xlim(left=0)
        plt.tight_layout()
        _save_fig(fig, "pm25_distributions")
    except Exception as e:
        logger.error(f"  Failed to plot distributions: {e}")


def plot_diurnal_patterns(df_med: pd.DataFrame, df_kan: pd.DataFrame) -> None:
    """Hourly PM2.5 patterns with shaded std range."""
    try:
        fig, ax = plt.subplots(figsize=(10, 6))

        for key, df in [("medellin", df_med), ("kandy", df_kan)]:
            if df.empty:
                continue
            df = df.copy()
            df["hour"] = pd.to_datetime(df["datetime_utc"]).dt.hour
            hourly = df.groupby("hour")["pm25"].agg(["mean", "std"]).reset_index()

            ax.plot(hourly["hour"], hourly["mean"], color=COLORS[key],
                    linewidth=2, marker="o", markersize=4, label=CITY_LABELS[key])
            ax.fill_between(
                hourly["hour"],
                hourly["mean"] - hourly["std"],
                hourly["mean"] + hourly["std"],
                alpha=0.15, color=COLORS[key],
            )

        ax.set_xlabel("Hour of Day (UTC)")
        ax.set_ylabel("PM2.5 (μg/m³)")
        ax.set_title("Diurnal PM2.5 Pattern")
        ax.set_xticks(range(0, 24, 2))
        ax.legend()
        plt.tight_layout()
        _save_fig(fig, "diurnal_patterns")
    except Exception as e:
        logger.error(f"  Failed to plot diurnal patterns: {e}")


def plot_seasonal_patterns(df_med: pd.DataFrame, df_kan: pd.DataFrame) -> None:
    """Monthly average PM2.5 bar chart."""
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        x = np.arange(12)
        width = 0.35

        for i, (key, df) in enumerate([("medellin", df_med), ("kandy", df_kan)]):
            if df.empty:
                continue
            df = df.copy()
            df["month"] = pd.to_datetime(df["datetime_utc"]).dt.month
            monthly = df.groupby("month")["pm25"].agg(["mean", "std"])

            means = [monthly.loc[m, "mean"] if m in monthly.index else 0 for m in range(1, 13)]
            stds = [monthly.loc[m, "std"] if m in monthly.index else 0 for m in range(1, 13)]

            offset = -width / 2 + i * width
            ax.bar(x + offset, means, width, yerr=stds, capsize=3,
                   color=COLORS[key], alpha=0.8, label=CITY_LABELS[key])

        ax.set_xticks(x)
        ax.set_xticklabels(month_names)
        ax.set_xlabel("Month")
        ax.set_ylabel("PM2.5 (μg/m³)")
        ax.set_title(f"Seasonal PM2.5 Pattern ({YEAR})")
        ax.legend()
        plt.tight_layout()
        _save_fig(fig, "seasonal_patterns")
    except Exception as e:
        logger.error(f"  Failed to plot seasonal patterns: {e}")


def plot_correlation_heatmaps(df_med: pd.DataFrame, df_kan: pd.DataFrame) -> None:
    """Correlation heatmaps for PM2.5 vs meteorological variables."""
    try:
        met_cols = [
            "pm25", "wind_speed", "wind_direction", "temperature_2m",
            "relative_humidity", "boundary_layer_height", "surface_pressure",
        ]

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        for ax, (key, df) in zip(axes, [("medellin", df_med), ("kandy", df_kan)]):
            if df.empty:
                ax.text(0.5, 0.5, f"No data for {CITY_LABELS[key]}",
                        ha="center", va="center", transform=ax.transAxes)
                ax.set_title(CITY_LABELS[key])
                continue

            available = [c for c in met_cols if c in df.columns]
            corr = df[available].corr()

            short_labels = {
                "pm25": "PM2.5", "wind_speed": "Wind Spd",
                "wind_direction": "Wind Dir", "temperature_2m": "Temp",
                "relative_humidity": "RH", "boundary_layer_height": "BLH",
                "surface_pressure": "Pressure",
            }
            labels = [short_labels.get(c, c) for c in available]

            sns.heatmap(
                corr, annot=True, fmt=".2f", cmap="RdBu_r",
                vmin=-1, vmax=1, ax=ax,
                xticklabels=labels, yticklabels=labels,
                square=True, linewidths=0.5,
            )
            ax.set_title(f"{CITY_LABELS[key]} - Pearson Correlations")

        fig.suptitle("PM2.5 - Meteorology Correlations", fontsize=14, fontweight="bold")
        plt.tight_layout()
        _save_fig(fig, "correlation_heatmaps")
    except Exception as e:
        logger.error(f"  Failed to plot correlation heatmaps: {e}")


def plot_wind_pm25_scatter(df_med: pd.DataFrame, df_kan: pd.DataFrame) -> None:
    """Wind direction vs speed colored by PM2.5."""
    try:
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        for ax, (key, df) in zip(axes, [("medellin", df_med), ("kandy", df_kan)]):
            if df.empty or "wind_speed" not in df.columns:
                ax.text(0.5, 0.5, f"No data for {CITY_LABELS[key]}",
                        ha="center", va="center", transform=ax.transAxes)
                ax.set_title(CITY_LABELS[key])
                continue

            sample = df.sample(min(5000, len(df)), random_state=42)
            sc = ax.scatter(
                sample["wind_direction"], sample["wind_speed"],
                c=sample["pm25"], cmap="RdYlGn_r", s=8, alpha=0.4,
                vmin=0, vmax=df["pm25"].quantile(0.95),
            )
            plt.colorbar(sc, ax=ax, label="PM2.5 (μg/m³)")
            ax.set_xlabel("Wind Direction (°)")
            ax.set_ylabel("Wind Speed (m/s)")
            ax.set_title(CITY_LABELS[key])
            ax.set_xlim(0, 360)

        fig.suptitle("Wind Conditions and PM2.5", fontsize=14, fontweight="bold")
        plt.tight_layout()
        _save_fig(fig, "wind_pm25_scatter")
    except Exception as e:
        logger.error(f"  Failed to plot wind-PM2.5 scatter: {e}")


def plot_met_comparison(df_med: pd.DataFrame, df_kan: pd.DataFrame) -> None:
    """Violin plots comparing meteorological variables between cities."""
    try:
        met_vars = [
            ("temperature_2m", "Temperature (°C)"),
            ("relative_humidity", "Relative Humidity (%)"),
            ("boundary_layer_height", "BLH (m)"),
            ("surface_pressure", "Pressure (hPa)"),
            ("wind_speed", "Wind Speed (m/s)"),
        ]

        fig, axes = plt.subplots(1, len(met_vars), figsize=(18, 5))

        for ax, (var, label) in zip(axes, met_vars):
            plot_data = []
            for key, df in [("medellin", df_med), ("kandy", df_kan)]:
                if df.empty or var not in df.columns:
                    continue
                sample = df[[var]].dropna().sample(min(5000, len(df)), random_state=42)
                sample["City"] = CITY_LABELS[key]
                sample.rename(columns={var: "value"}, inplace=True)
                plot_data.append(sample)

            if plot_data:
                combined = pd.concat(plot_data, ignore_index=True)
                palette = [COLORS[k] for k in ["medellin", "kandy"]
                           if CITY_LABELS[k] in combined["City"].unique()]
                sns.violinplot(
                    data=combined, x="City", y="value",
                    palette=palette, ax=ax, inner="quartile",
                )
            ax.set_ylabel(label)
            ax.set_xlabel("")
            ax.set_title(label.split("(")[0].strip())

        fig.suptitle("Meteorological Variable Comparison", fontsize=14, fontweight="bold")
        plt.tight_layout()
        _save_fig(fig, "meteorological_comparison")
    except Exception as e:
        logger.error(f"  Failed to plot met comparison: {e}")


def plot_data_coverage(df_med: pd.DataFrame, df_kan: pd.DataFrame) -> None:
    """Heatmap showing daily data availability per station."""
    try:
        fig, axes = plt.subplots(2, 1, figsize=(16, 8))

        for ax, (key, df) in zip(axes, [("medellin", df_med), ("kandy", df_kan)]):
            if df.empty:
                ax.text(0.5, 0.5, f"No data for {CITY_LABELS[key]}",
                        ha="center", va="center", transform=ax.transAxes)
                ax.set_title(f"{CITY_LABELS[key]} - Data Coverage")
                continue

            df = df.copy()
            df["date"] = pd.to_datetime(df["datetime_utc"]).dt.date
            coverage = df.groupby(["location_name", "date"]).size().unstack(fill_value=0)

            # Limit station labels if too many
            if len(coverage) > 15:
                # Keep top 15 stations by total records
                top = coverage.sum(axis=1).nlargest(15).index
                coverage = coverage.loc[top]

            sns.heatmap(
                coverage, ax=ax, cmap="YlOrRd", cbar_kws={"label": "Hours/day"},
                xticklabels=30,
            )
            ax.set_title(f"{CITY_LABELS[key]} - Data Coverage")
            ax.set_ylabel("Station")
            ax.set_xlabel("Date")

        plt.tight_layout()
        _save_fig(fig, "data_coverage")
    except Exception as e:
        logger.error(f"  Failed to plot data coverage: {e}")


def plot_station_map(df_med: pd.DataFrame, df_kan: pd.DataFrame) -> None:
    """Scatter plot of station locations sized by data completeness."""
    try:
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        for ax, (key, df) in zip(axes, [("medellin", df_med), ("kandy", df_kan)]):
            if df.empty:
                ax.text(0.5, 0.5, f"No data for {CITY_LABELS[key]}",
                        ha="center", va="center", transform=ax.transAxes)
                ax.set_title(f"{CITY_LABELS[key]} - Station Locations")
                continue

            stations = df.groupby(["location_id", "location_name", "lat", "lon"]).agg(
                n_records=("pm25", "count"),
                pm25_mean=("pm25", "mean"),
            ).reset_index()

            sc = ax.scatter(
                stations["lon"], stations["lat"],
                s=stations["n_records"] / stations["n_records"].max() * 200 + 20,
                c=stations["pm25_mean"], cmap="RdYlGn_r",
                edgecolors="black", linewidths=0.5, alpha=0.8,
            )
            plt.colorbar(sc, ax=ax, label="Mean PM2.5 (μg/m³)")

            for _, row in stations.iterrows():
                ax.annotate(
                    row["location_name"][:15],
                    (row["lon"], row["lat"]),
                    fontsize=7, ha="left", va="bottom",
                    xytext=(3, 3), textcoords="offset points",
                )

            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
            ax.set_title(f"{CITY_LABELS[key]} - Monitoring Stations")

        fig.suptitle("Station Locations and Mean PM2.5", fontsize=14, fontweight="bold")
        plt.tight_layout()
        _save_fig(fig, "station_locations")
    except Exception as e:
        logger.error(f"  Failed to plot station map: {e}")


def generate_all_plots(df_med: pd.DataFrame, df_kan: pd.DataFrame) -> None:
    """Generate all visualization plots."""
    logger.info("  Generating plots...")

    plot_pm25_timeseries(df_med, df_kan)
    plot_pm25_distributions(df_med, df_kan)
    plot_diurnal_patterns(df_med, df_kan)
    plot_seasonal_patterns(df_med, df_kan)
    plot_correlation_heatmaps(df_med, df_kan)
    plot_wind_pm25_scatter(df_med, df_kan)
    plot_met_comparison(df_med, df_kan)
    plot_data_coverage(df_med, df_kan)
    plot_station_map(df_med, df_kan)

    logger.info(f"  All plots saved to {FIGURES_DIR}")
