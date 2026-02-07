"""
Combine multiple PM2.5 data sources (SIATA + OpenAQ) for Medellin.
"""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def combine_pm25_sources(
    siata_path: Path,
    openaq_path: Path,
    output_path: Path,
    prefer_source: str = "siata"
) -> pd.DataFrame:
    """
    Combine SIATA and OpenAQ PM2.5 data, removing duplicates.

    Args:
        siata_path: Path to SIATA CSV
        openaq_path: Path to OpenAQ CSV
        output_path: Path to save combined CSV
        prefer_source: Which source to prefer for overlapping data ('siata' or 'openaq')

    Returns:
        Combined DataFrame
    """
    logger.info("Combining PM2.5 data sources...")

    # Load both datasets
    df_siata = pd.read_csv(siata_path)
    df_openaq = pd.read_csv(openaq_path)

    logger.info(f"  SIATA: {len(df_siata):,} records from {df_siata['location_id'].nunique()} stations")
    logger.info(f"  OpenAQ: {len(df_openaq):,} records from {df_openaq['location_id'].nunique()} stations")

    # Add source column
    df_siata['source'] = 'SIATA'
    df_openaq['source'] = 'OpenAQ'

    # Parse datetime
    df_siata['datetime_utc'] = pd.to_datetime(df_siata['datetime_utc'])
    df_openaq['datetime_utc'] = pd.to_datetime(df_openaq['datetime_utc'])

    # Find overlapping date range
    siata_start = df_siata['datetime_utc'].min()
    siata_end = df_siata['datetime_utc'].max()
    openaq_start = df_openaq['datetime_utc'].min()
    openaq_end = df_openaq['datetime_utc'].max()

    logger.info(f"  SIATA date range: {siata_start} to {siata_end}")
    logger.info(f"  OpenAQ date range: {openaq_start} to {openaq_end}")

    overlap_start = max(siata_start, openaq_start)
    overlap_end = min(siata_end, openaq_end)

    if overlap_start <= overlap_end:
        logger.info(f"  Overlap period: {overlap_start} to {overlap_end}")

        # For overlap period, prefer one source
        if prefer_source == "siata":
            # Use SIATA for overlap period, OpenAQ for the rest
            df_combined = pd.concat([
                df_siata,  # All SIATA data
                df_openaq[df_openaq['datetime_utc'] > siata_end]  # OpenAQ after SIATA ends
            ], ignore_index=True)
            logger.info(f"  Strategy: Using SIATA for overlap, OpenAQ for Sept-Dec 2019")
        else:
            # Use OpenAQ for overlap period, SIATA for the rest
            df_combined = pd.concat([
                df_openaq,  # All OpenAQ data
                df_siata[df_siata['datetime_utc'] < openaq_start]  # SIATA before OpenAQ starts
            ], ignore_index=True)
            logger.info(f"  Strategy: Using OpenAQ for overlap, SIATA for Aug-Dec 2018")
    else:
        # No overlap - just concatenate
        df_combined = pd.concat([df_siata, df_openaq], ignore_index=True)
        logger.info("  No overlap - concatenating all data")

    # Sort by datetime
    df_combined = df_combined.sort_values(['datetime_utc', 'location_id']).reset_index(drop=True)

    logger.info(f"  Combined: {len(df_combined):,} total records")
    logger.info(f"  Date range: {df_combined['datetime_utc'].min()} to {df_combined['datetime_utc'].max()}")
    logger.info(f"  Total stations: {df_combined['location_id'].nunique()}")

    # Save
    df_combined.to_csv(output_path, index=False)
    logger.info(f"  Saved to: {output_path}")

    return df_combined


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    siata_path = Path("data/raw/openaq/medellin_siata_pm25_raw.csv")
    openaq_path = Path("data/raw/openaq/medellin_pm25_raw.csv")
    output_path = Path("data/raw/openaq/medellin_combined_pm25_raw.csv")

    combine_pm25_sources(siata_path, openaq_path, output_path, prefer_source="siata")
