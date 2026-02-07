"""
ERA5 NetCDF processing: unit conversions, derived variables, spatial averaging.
"""

import logging
from pathlib import Path

from calendar import isleap

import numpy as np
import pandas as pd
import xarray as xr

from config import PROCESSED_DIR, YEAR

logger = logging.getLogger(__name__)


def process_era5(nc_path: Path, city_key: str) -> pd.DataFrame:
    """
    Process raw ERA5 NetCDF into a clean hourly CSV.
    Computes derived variables (wind speed, direction, relative humidity).
    Returns DataFrame with one row per hour.
    """
    output_path = PROCESSED_DIR / f"{city_key}_era5_processed.csv"

    # Checkpointing
    if output_path.exists() and output_path.stat().st_size > 1000:
        logger.info(f"  Skipping {city_key} ERA5 processing (file exists)")
        return pd.read_csv(output_path, parse_dates=["datetime_utc"])

    logger.info(f"  Processing ERA5: {nc_path}")
    ds = xr.open_dataset(str(nc_path))

    # Detect time dimension name (new CDS API uses 'valid_time', old uses 'time')
    time_dim = "valid_time" if "valid_time" in ds.dims else "time"

    # Log dataset info
    logger.info(f"    Variables: {list(ds.data_vars)}")
    logger.info(f"    Time range: {ds[time_dim].values[0]} to {ds[time_dim].values[-1]}")
    if "latitude" in ds.dims:
        logger.info(
            f"    Grid: {ds.dims.get('latitude', '?')} lat x "
            f"{ds.dims.get('longitude', '?')} lon points"
        )

    # Spatial average across all grid points
    spatial_dims = [d for d in ds.dims if d in ("latitude", "longitude")]
    if spatial_dims:
        ds_avg = ds.mean(dim=spatial_dims)
    else:
        ds_avg = ds

    # Extract variables and convert units
    time = pd.DatetimeIndex(ds_avg[time_dim].values).tz_localize("UTC")

    # U and V wind components (m/s) - already in correct units
    u_wind = ds_avg["u10"].values.astype(float)
    v_wind = ds_avg["v10"].values.astype(float)

    # Temperature: Kelvin -> Celsius
    temp_k = ds_avg["t2m"].values.astype(float)
    temp_c = temp_k - 273.15

    # Dewpoint temperature: Kelvin -> Celsius
    dewpoint_k = ds_avg["d2m"].values.astype(float)
    dewpoint_c = dewpoint_k - 273.15

    # Boundary layer height (m) - already in correct units
    blh = ds_avg["blh"].values.astype(float)

    # Surface pressure: Pa -> hPa
    sp_pa = ds_avg["sp"].values.astype(float)
    sp_hpa = sp_pa / 100.0

    # Derived: wind speed and direction
    wind_speed = np.sqrt(u_wind**2 + v_wind**2)
    wind_direction = (270 - np.degrees(np.arctan2(v_wind, u_wind))) % 360

    # Derived: relative humidity (Magnus formula)
    rh = _compute_relative_humidity(temp_c, dewpoint_c)

    ds.close()

    # Build DataFrame
    df = pd.DataFrame({
        "datetime_utc": time,
        "u_wind_10m": u_wind,
        "v_wind_10m": v_wind,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
        "temperature_2m": temp_c,
        "dewpoint_2m": dewpoint_c,
        "relative_humidity": rh,
        "boundary_layer_height": blh,
        "surface_pressure": sp_hpa,
    })

    # Verify completeness
    expected_hours = 8784 if isleap(YEAR) else 8760
    if len(df) != expected_hours:
        logger.warning(
            f"    Expected {expected_hours} hours, got {len(df)} "
            f"({expected_hours - len(df)} missing)"
        )

    # Sanity checks
    _sanity_check(df, city_key)

    # Save
    df.to_csv(output_path, index=False)
    logger.info(f"  ERA5 processing complete: {len(df)} hourly records -> {output_path}")

    return df


def _compute_relative_humidity(temp_c: np.ndarray, dewpoint_c: np.ndarray) -> np.ndarray:
    """
    Compute relative humidity from temperature and dewpoint
    using the August-Roche-Magnus approximation.
    """
    a = 17.67
    b = 243.5

    es_t = 6.112 * np.exp(a * temp_c / (temp_c + b))
    es_td = 6.112 * np.exp(a * dewpoint_c / (dewpoint_c + b))

    rh = 100.0 * es_td / es_t
    return np.clip(rh, 0, 100)


def _sanity_check(df: pd.DataFrame, city_key: str) -> None:
    """Log warnings for physically implausible values."""
    checks = {
        "temperature_2m": (-30, 50, "°C"),
        "relative_humidity": (0, 100, "%"),
        "surface_pressure": (800, 1100, "hPa"),
        "boundary_layer_height": (0, 5000, "m"),
        "wind_speed": (0, 50, "m/s"),
    }

    for col, (vmin, vmax, unit) in checks.items():
        if col not in df.columns:
            continue
        below = (df[col] < vmin).sum()
        above = (df[col] > vmax).sum()
        if below > 0 or above > 0:
            logger.warning(
                f"    {city_key} {col}: {below} values below {vmin}{unit}, "
                f"{above} values above {vmax}{unit}"
            )
        else:
            logger.debug(
                f"    {city_key} {col}: range [{df[col].min():.1f}, "
                f"{df[col].max():.1f}] {unit} OK"
            )
