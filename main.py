"""
PM2.5 Data Pipeline for PINN Transfer Learning
================================================
Collects, preprocesses, and analyzes PM2.5 and meteorological data
from Medellin (Colombia) and Kandy (Sri Lanka).

Usage:
    python main.py              # Run full pipeline (skips completed stages)
    python main.py --force      # Re-run all stages from scratch
    python main.py --city medellin  # Run only for Medellin
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import (
    CITIES, RAW_DIR, PROCESSED_DIR, FINAL_DIR,
    FIGURES_DIR, REPORTS_DIR, LOG_DIR,
    OPENAQ_API_KEY, OPENAQ_BASE_URL, OPENAQ_RATE_LIMIT,
)


def setup_logging() -> None:
    """Configure logging to console and timestamped file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"pipeline_{timestamp}.log"

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(log_file), encoding="utf-8"),
    ]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("cdsapi").setLevel(logging.WARNING)


def ensure_directories() -> None:
    """Create all required directories."""
    for d in [
        RAW_DIR / "openaq", RAW_DIR / "era5",
        PROCESSED_DIR, FINAL_DIR,
        FIGURES_DIR, REPORTS_DIR, LOG_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)


def clear_outputs() -> None:
    """Remove all intermediate and output files (for --force mode)."""
    logger = logging.getLogger(__name__)
    for directory in [PROCESSED_DIR, FINAL_DIR, FIGURES_DIR, REPORTS_DIR]:
        for f in directory.glob("*"):
            if f.is_file():
                f.unlink()
                logger.info(f"  Removed: {f}")


def validate_final_dataset(csv_path: Path) -> bool:
    """Validate a final dataset for PINN readiness."""
    logger = logging.getLogger(__name__)
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            logger.warning(f"  Validation: {csv_path.name} is empty")
            return False

        required_cols = [
            "datetime_utc", "pm25", "wind_speed",
            "temperature_2m", "relative_humidity",
            "boundary_layer_height", "surface_pressure",
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            logger.error(f"  Validation FAILED: Missing columns: {missing}")
            return False

        # Check for NaN in critical columns
        for col in required_cols:
            nan_count = df[col].isna().sum()
            if nan_count > 0:
                logger.warning(f"  {csv_path.name}: {col} has {nan_count} NaN values")

        # Check PM2.5 range
        if (df["pm25"] <= 0).any():
            bad = (df["pm25"] <= 0).sum()
            logger.warning(f"  {csv_path.name}: {bad} non-positive PM2.5 values")

        logger.info(
            f"  Validation PASSED: {csv_path.name} — "
            f"{len(df):,} records, "
            f"{df['city'].nunique() if 'city' in df.columns else '?'} city(ies), "
            f"{df['location_id'].nunique() if 'location_id' in df.columns else '?'} stations"
        )
        return True

    except Exception as e:
        logger.error(f"  Validation FAILED: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="PM2.5 PINN Data Pipeline")
    parser.add_argument(
        "--force", action="store_true",
        help="Re-run all stages, ignoring existing outputs",
    )
    parser.add_argument(
        "--city", type=str, default=None,
        help="Run pipeline for a single city (e.g., medellin or kandy)",
    )
    args = parser.parse_args()

    setup_logging()
    ensure_directories()
    logger = logging.getLogger(__name__)

    # Determine which cities to process
    if args.city:
        if args.city not in CITIES:
            logger.error(f"Unknown city '{args.city}'. Available: {list(CITIES.keys())}")
            sys.exit(1)
        run_cities = {args.city: CITIES[args.city]}
        logger.info(f"Single-city mode: {args.city}")
    else:
        run_cities = CITIES

    logger.info("=" * 60)
    logger.info("PM2.5 Data Pipeline for PINN Transfer Learning")
    logger.info(f"Started at {datetime.now()}")
    logger.info(f"Cities: {', '.join(run_cities.keys())}")
    logger.info("=" * 60)

    if args.force:
        logger.info("Force mode: clearing previous outputs...")
        clear_outputs()

    # ================================================================
    # Phase 0: CDS API Setup
    # ================================================================
    logger.info("")
    logger.info("Phase 0: Checking CDS API configuration...")
    from setup_cds import setup_cds_api

    if not setup_cds_api():
        logger.error(
            "CDS API setup failed. Please run 'python setup_cds.py' "
            "to configure your credentials, then re-run this pipeline."
        )
        sys.exit(1)
    logger.info("Phase 0: CDS API ready.")

    # ================================================================
    # Phase 1: Data Collection
    # ================================================================
    logger.info("")
    logger.info("Phase 1: Collecting data...")

    # 1a: OpenAQ PM2.5
    from collectors.openaq_collector import OpenAQCollector

    openaq = OpenAQCollector(OPENAQ_API_KEY, OPENAQ_BASE_URL, OPENAQ_RATE_LIMIT)
    pm25_raw = {}
    for city_key, city_cfg in run_cities.items():
        logger.info(f"  Collecting PM2.5 for {city_cfg['name']}...")
        try:
            pm25_raw[city_key] = openaq.collect_city(city_key, city_cfg)
            logger.info(f"  -> {len(pm25_raw[city_key]):,} measurements collected")
        except Exception as e:
            logger.error(f"  PM2.5 collection failed for {city_cfg['name']}: {e}")
            pm25_raw[city_key] = pd.DataFrame()

    # 1b: ERA5 meteorological
    from collectors.era5_collector import ERA5Collector

    try:
        era5_collector = ERA5Collector()
        era5_files = era5_collector.collect_all(run_cities)
    except Exception as e:
        logger.error(f"  ERA5 collection failed: {e}")
        logger.error("  Pipeline cannot continue without meteorological data.")
        sys.exit(1)

    logger.info("Phase 1: Data collection complete.")

    # ================================================================
    # Phase 2: Preprocessing
    # ================================================================
    logger.info("")
    logger.info("Phase 2: Preprocessing...")

    from preprocessing.pm25_cleaner import clean_pm25
    from preprocessing.era5_processor import process_era5
    from preprocessing.merger import merge_pm25_era5, create_combined_dataset

    pm25_clean = {}
    era5_processed = {}
    merged = {}

    for city_key in run_cities:
        logger.info(f"  Processing {run_cities[city_key]['name']}...")

        # 2a: Clean PM2.5
        # Check for combined dataset first (e.g., SIATA + OpenAQ), fall back to OpenAQ only
        combined_path = RAW_DIR / "openaq" / f"{city_key}_combined_pm25_raw.csv"
        raw_path = RAW_DIR / "openaq" / f"{city_key}_pm25_raw.csv"

        if combined_path.exists():
            logger.info(f"    Using combined PM2.5 data: {combined_path.name}")
            pm25_clean[city_key] = clean_pm25(combined_path, city_key)
        elif raw_path.exists():
            pm25_clean[city_key] = clean_pm25(raw_path, city_key)
        else:
            logger.warning(f"  No raw PM2.5 file for {city_key}")
            pm25_clean[city_key] = pd.DataFrame()

        # 2b: Process ERA5
        if city_key in era5_files:
            era5_processed[city_key] = process_era5(era5_files[city_key], city_key)
        else:
            logger.warning(f"  No ERA5 file for {city_key}")
            era5_processed[city_key] = pd.DataFrame()

        # 2c: Merge
        if not pm25_clean[city_key].empty and not era5_processed[city_key].empty:
            merged[city_key] = merge_pm25_era5(
                pm25_clean[city_key], era5_processed[city_key], city_key
            )
        else:
            logger.warning(f"  Cannot merge {city_key}: missing PM2.5 or ERA5 data")
            merged[city_key] = pd.DataFrame()

    # Combined dataset
    create_combined_dataset(merged)

    logger.info("Phase 2: Preprocessing complete.")

    # ================================================================
    # Phase 3: Statistical Analysis
    # ================================================================
    logger.info("")
    logger.info("Phase 3: Statistical analysis...")

    from analysis.statistics import (
        compute_summary_statistics,
        compare_distributions,
        generate_report,
    )

    stats = {}
    for city_key in run_cities:
        stats[city_key] = compute_summary_statistics(merged[city_key], city_key)

    comparison = compare_distributions(
        merged.get("medellin", pd.DataFrame()),
        merged.get("kandy", pd.DataFrame()),
    )
    report = generate_report(
        stats.get("medellin", {}),
        stats.get("kandy", {}),
        comparison,
    )

    # Print report summary to console
    logger.info("\n" + report)

    logger.info("Phase 3: Statistical analysis complete.")

    # ================================================================
    # Phase 4: Visualizations
    # ================================================================
    logger.info("")
    logger.info("Phase 4: Generating visualizations...")

    from analysis.visualizations import generate_all_plots

    generate_all_plots(
        merged.get("medellin", pd.DataFrame()),
        merged.get("kandy", pd.DataFrame()),
    )

    logger.info("Phase 4: Visualizations complete.")

    # ================================================================
    # Phase 5: Final Validation
    # ================================================================
    logger.info("")
    logger.info("Phase 5: Final validation...")

    for city_key in run_cities:
        dataset_path = FINAL_DIR / f"{city_key}_pinn_dataset.csv"
        if dataset_path.exists():
            validate_final_dataset(dataset_path)

    combined_path = FINAL_DIR / "combined_pinn_dataset.csv"
    if combined_path.exists():
        validate_final_dataset(combined_path)

    # ================================================================
    # Summary
    # ================================================================
    logger.info("")
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
    logger.info(f"  Final datasets:    {FINAL_DIR}")
    logger.info(f"  Visualizations:    {FIGURES_DIR}")
    logger.info(f"  Reports:           {REPORTS_DIR}")
    logger.info(f"  Logs:              {LOG_DIR}")

    # Print dataset sizes
    for f in sorted(FINAL_DIR.glob("*.csv")):
        df = pd.read_csv(f)
        logger.info(f"  {f.name}: {len(df):,} records")

    logger.info(f"Finished at {datetime.now()}")


if __name__ == "__main__":
    main()
