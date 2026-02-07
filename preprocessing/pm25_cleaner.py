"""
Multi-stage quality control for PM2.5 measurements.
Removes outliers, spikes, and incomplete stations.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from calendar import isleap

from config import (
    PROCESSED_DIR, PM25_MIN, PM25_MAX,
    PM25_IQR_MULTIPLIER, PM25_SPIKE_THRESHOLD,
    STATION_MIN_COVERAGE, YEAR, CITIES,
)

logger = logging.getLogger(__name__)

TOTAL_HOURS = 8784 if isleap(YEAR) else 8760


def _haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points."""
    from math import radians, cos, sin, asin, sqrt
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c


def clean_pm25(raw_csv_path: Path, city_key: str) -> pd.DataFrame:
    """
    Multi-stage PM2.5 cleaning pipeline.
    Returns cleaned DataFrame.
    """
    output_path = PROCESSED_DIR / f"{city_key}_pm25_cleaned.csv"

    # Checkpointing
    if output_path.exists() and output_path.stat().st_size > 100:
        logger.info(f"  Skipping {city_key} PM2.5 cleaning (file exists)")
        return pd.read_csv(output_path, parse_dates=["datetime_utc"])

    df = pd.read_csv(raw_csv_path)
    initial_count = len(df)

    if df.empty:
        logger.warning(f"  {city_key}: Raw PM2.5 data is empty, nothing to clean")
        df = pd.DataFrame(columns=[
            "datetime_utc", "location_id", "location_name",
            "sensor_id", "lat", "lon", "pm25",
        ])
        df.to_csv(output_path, index=False)
        return df

    logger.info(f"  {city_key}: Starting cleaning with {initial_count} records")

    # Stage 1: Basic validation
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], errors="coerce", utc=True)
    before = len(df)
    df = df.dropna(subset=["datetime_utc", "pm25"])
    df = df[(df["pm25"] >= PM25_MIN) & (df["pm25"] <= PM25_MAX)]
    df = df.drop_duplicates(subset=["datetime_utc", "location_id", "sensor_id"])
    logger.info(
        f"    Stage 1 (validation): {before} -> {len(df)} "
        f"({before - len(df)} removed)"
    )

    if df.empty:
        logger.warning(f"  {city_key}: No valid records after Stage 1")
        df = _empty_df()
        df.to_csv(output_path, index=False)
        return df

    # Stage 1b: Geographic filtering (geomorphic matching)
    if city_key in CITIES and "station_radius_km" in CITIES[city_key]:
        radius_km = CITIES[city_key]["station_radius_km"]
        city_lat = CITIES[city_key]["lat"]
        city_lon = CITIES[city_key]["lon"]

        before = len(df)
        # Calculate distance for each station
        station_coords = df.groupby('location_id').agg({'lat': 'first', 'lon': 'first'})
        station_coords['distance_km'] = station_coords.apply(
            lambda row: _haversine_distance(city_lat, city_lon, row['lat'], row['lon']),
            axis=1
        )

        # Filter stations within radius
        valid_stations = station_coords[station_coords['distance_km'] <= radius_km].index
        df = df[df['location_id'].isin(valid_stations)]

        excluded_count = station_coords[station_coords['distance_km'] > radius_km].shape[0]
        logger.info(
            f"    Stage 1b (geographic filter): {before} -> {len(df)} "
            f"({before - len(df)} records removed, {excluded_count} stations beyond {radius_km}km)"
        )

    # Stage 2: Coverage filter
    if "coverage_pct" in df.columns:
        before = len(df)
        df = df[df["coverage_pct"].isna() | (df["coverage_pct"] >= 50)]
        logger.info(
            f"    Stage 2 (coverage): {before} -> {len(df)} "
            f"({before - len(df)} removed)"
        )

    # Stage 3: IQR-based outlier removal per station
    before = len(df)
    clean_dfs = []
    for lid, group in df.groupby("location_id"):
        q1 = group["pm25"].quantile(0.25)
        q3 = group["pm25"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - PM25_IQR_MULTIPLIER * iqr
        upper = q3 + PM25_IQR_MULTIPLIER * iqr
        filtered = group[(group["pm25"] >= lower) & (group["pm25"] <= upper)]
        clean_dfs.append(filtered)

    df = pd.concat(clean_dfs, ignore_index=True) if clean_dfs else _empty_df()
    logger.info(
        f"    Stage 3 (IQR outliers): {before} -> {len(df)} "
        f"({before - len(df)} removed)"
    )

    if df.empty:
        df.to_csv(output_path, index=False)
        return df

    # Stage 4: Temporal spike detection
    before = len(df)
    clean_dfs = []
    for lid, group in df.groupby("location_id"):
        group = group.sort_values("datetime_utc").reset_index(drop=True)
        pm = group["pm25"]
        diff_prev = (pm - pm.shift(1)).abs()
        diff_next = (pm - pm.shift(-1)).abs()
        is_spike = (diff_prev > PM25_SPIKE_THRESHOLD) & (
            diff_next > PM25_SPIKE_THRESHOLD
        )
        clean_dfs.append(group[~is_spike])

    df = pd.concat(clean_dfs, ignore_index=True) if clean_dfs else _empty_df()
    logger.info(
        f"    Stage 4 (spike removal): {before} -> {len(df)} "
        f"({before - len(df)} removed)"
    )

    # Stage 5: Station completeness filter
    before_stations = df["location_id"].nunique()
    station_counts = df.groupby("location_id").size()
    min_records = int(TOTAL_HOURS * STATION_MIN_COVERAGE)
    valid_stations = station_counts[station_counts >= min_records].index
    df = df[df["location_id"].isin(valid_stations)]

    after_stations = df["location_id"].nunique()
    logger.info(
        f"    Stage 5 (station coverage): {before_stations} -> {after_stations} "
        f"stations ({before_stations - after_stations} removed, "
        f"min {min_records} records required)"
    )

    # Log stations with low coverage
    for lid in valid_stations:
        count = station_counts[lid]
        coverage = count / TOTAL_HOURS * 100
        if coverage < 50:
            name = df[df["location_id"] == lid]["location_name"].iloc[0]
            logger.warning(
                f"    Low coverage station: {name} ({coverage:.1f}%)"
            )

    # Select final columns
    keep_cols = [
        "datetime_utc", "location_id", "location_name",
        "sensor_id", "lat", "lon", "pm25",
    ]
    df = df[[c for c in keep_cols if c in df.columns]]

    # Save
    df.to_csv(output_path, index=False)
    logger.info(
        f"  {city_key} cleaning complete: {initial_count} -> {len(df)} records "
        f"({len(df) / max(initial_count, 1) * 100:.1f}% retained)"
    )

    return df


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "datetime_utc", "location_id", "location_name",
        "sensor_id", "lat", "lon", "pm25",
    ])
