"""
Interactive helper to configure the CDS API for ERA5 data downloads.
Run this script if you haven't set up your Copernicus CDS credentials.
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_cdsapirc_path() -> Path:
    return Path.home() / ".cdsapirc"


def _check_existing_config() -> bool:
    rc_path = _get_cdsapirc_path()
    if not rc_path.exists():
        return False

    content = rc_path.read_text().strip()
    has_url = "url:" in content
    has_key = "key:" in content
    if has_url and has_key:
        logger.info(f"Found existing CDS API config at {rc_path}")
        return True
    return False


def _write_config(api_key: str) -> None:
    rc_path = _get_cdsapirc_path()
    content = f"url: https://cds.climate.copernicus.eu/api\nkey: {api_key}\n"
    rc_path.write_text(content)
    logger.info(f"CDS API config written to {rc_path}")


def _verify_config() -> bool:
    try:
        import cdsapi
        client = cdsapi.Client(quiet=True)
        logger.info("CDS API client initialized successfully")
        return True
    except Exception as e:
        error_msg = str(e)
        if "licence" in error_msg.lower() or "license" in error_msg.lower():
            logger.warning(
                "CDS API credentials valid, but you need to accept the ERA5 Terms of Use.\n"
                "Visit: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels\n"
                "Click 'Download' and accept the license agreement."
            )
            return True
        logger.error(f"CDS API verification failed: {e}")
        return False


def setup_cds_api() -> bool:
    """
    Check and configure CDS API credentials.
    Returns True if the API is ready to use.
    """
    if _check_existing_config():
        return _verify_config()

    print("\n" + "=" * 60)
    print("CDS API Setup Required")
    print("=" * 60)
    print("\nTo download ERA5 meteorological data, you need a Copernicus CDS API key.")
    print("\nSteps:")
    print("  1. Go to https://cds.climate.copernicus.eu/profile")
    print("  2. Log in with your account")
    print("  3. Scroll to 'Personal Access Token' section")
    print("  4. Copy your Personal Access Token")
    print()

    api_key = input("Paste your Personal Access Token here: ").strip()

    if not api_key:
        logger.error("No API key provided. CDS setup aborted.")
        return False

    _write_config(api_key)

    print("\nIMPORTANT: You must also accept the ERA5 Terms of Use:")
    print("  Visit: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels")
    print("  Click 'Download' tab and accept the license agreement.")
    input("\nPress Enter once you've accepted the terms (or if already done)...")

    return _verify_config()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = setup_cds_api()
    if success:
        print("\nCDS API is ready!")
    else:
        print("\nCDS API setup failed. Please check your credentials.")
