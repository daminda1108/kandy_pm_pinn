"""
Temporal merging of PM2.5 observations with ERA5 meteorological data.
Aligns PM2.5 measurements to the nearest hour and joins with ERA5.
"""

import logging
from pathlib import Path

import pandas as pd

from config import FINAL_DIR

logger = logging.getLogger(__name__)


def merge_pm25_era5(
    pm25_df: pd.DataFrame,
    era5_df: pd.DataFrame,
    city_key: str,
) -> pd.DataFrame:
    """
    Merge PM2.5 observations with ERA5 hourly meteorological data.
    PM2.5 timestamps are rounded to the nearest hour, then averaged
    within each hour per station, then joined with ERA5.
    """
    output_path = FINAL_DIR / f"{city_key}_pinn_dataset.csv"

    # Checkpointing
    if output_path.exists() and output_path.stat().st_size > 100:
        logger.info(f"  Skipping {city_key} merge (file exists)")
        return pd.read_csv(output_path, parse_dates=["datetime_utc"])

    if pm25_df.empty:
        logger.warning(f"  {city_key}: No PM2.5 data to merge")
        df = _empty_merged_df()
        df.to_csv(output_path, index=False)
        return df

    # Ensure datetime types
    pm25_df = pm25_df.copy()
    era5_df = era5_df.copy()

    pm25_df["datetime_utc"] = pd.to_datetime(pm25_df["datetime_utc"], utc=True)
    era5_df["datetime_utc"] = pd.to_datetime(era5_df["datetime_utc"], utc=True)

    # Step 1: Round PM2.5 timestamps to nearest hour
    pm25_df["datetime_hour"] = pm25_df["datetime_utc"].dt.round("h")

    # Step 2: Average sub-hourly observations within each hour per station
    pm25_hourly = (
        pm25_df.groupby(["location_id", "datetime_hour"])
        .agg(
            pm25=("pm25", "mean"),
            lat=("lat", "first"),
            lon=("lon", "first"),
            location_name=("location_name", "first"),
            n_obs=("pm25", "count"),
        )
        .reset_index()
    )
    pm25_hourly.rename(columns={"datetime_hour": "datetime_utc"}, inplace=True)

    logger.info(
        f"  {city_key}: {len(pm25_df)} raw -> {len(pm25_hourly)} hourly aggregated "
        f"across {pm25_hourly['location_id'].nunique()} stations"
    )

    # Step 3: Merge with ERA5 on datetime
    merged = pm25_hourly.merge(
        era5_df,
        on="datetime_utc",
        how="left",
        suffixes=("", "_era5"),
    )

    # Step 4: Check for unmatched rows
    era5_cols = [
        "u_wind_10m", "v_wind_10m", "wind_speed", "wind_direction",
        "temperature_2m", "relative_humidity", "boundary_layer_height",
        "surface_pressure",
    ]
    missing_era5 = merged[era5_cols[0]].isna().sum() if era5_cols[0] in merged.columns else 0
    if missing_era5 > 0:
        logger.warning(
            f"  {city_key}: {missing_era5} PM2.5 records could not be matched "
            f"to ERA5 ({missing_era5 / len(merged) * 100:.1f}%)"
        )
        merged = merged.dropna(subset=era5_cols[:1])

    # Step 5: Add city identifier
    merged["city"] = city_key

    # Select and order final columns
    final_cols = [
        "datetime_utc", "city", "location_id", "location_name",
        "lat", "lon", "pm25", "n_obs",
        "u_wind_10m", "v_wind_10m", "wind_speed", "wind_direction",
        "temperature_2m", "relative_humidity",
        "boundary_layer_height", "surface_pressure",
    ]
    merged = merged[[c for c in final_cols if c in merged.columns]]

    # Sort by time and station
    merged = merged.sort_values(["datetime_utc", "location_id"]).reset_index(drop=True)

    # Save
    merged.to_csv(output_path, index=False)

    # Log coverage
    era5_hours = len(era5_df)
    hours_with_pm25 = merged["datetime_utc"].nunique()
    logger.info(
        f"  {city_key} merge complete: {len(merged)} records, "
        f"{merged['location_id'].nunique()} stations, "
        f"{hours_with_pm25}/{era5_hours} ERA5 hours have PM2.5 data "
        f"({hours_with_pm25 / max(era5_hours, 1) * 100:.1f}%)"
    )

    return merged


def create_combined_dataset(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Concatenate per-city datasets into a single combined file."""
    combined_path = FINAL_DIR / "combined_pinn_dataset.csv"

    dfs = [df for df in datasets.values() if not df.empty]
    if not dfs:
        logger.warning("No data to combine")
        return pd.DataFrame()

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.sort_values(["city", "datetime_utc", "location_id"])
    combined.to_csv(combined_path, index=False)

    logger.info(
        f"Combined dataset: {len(combined)} records from "
        f"{combined['city'].nunique()} cities -> {combined_path}"
    )

    return combined


def _empty_merged_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "datetime_utc", "city", "location_id", "location_name",
        "lat", "lon", "pm25", "n_obs",
        "u_wind_10m", "v_wind_10m", "wind_speed", "wind_direction",
        "temperature_2m", "relative_humidity",
        "boundary_layer_height", "surface_pressure",
    ])
