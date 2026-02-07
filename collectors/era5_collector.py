"""
ERA5 reanalysis data collector using the CDS API.
Downloads hourly single-level meteorological variables.
"""

import logging
from pathlib import Path

from config import (
    RAW_DIR, ERA5_DATASET, ERA5_VARIABLES,
    CITIES, YEAR, MONTHS, DAYS, HOURS,
)

logger = logging.getLogger(__name__)

# Minimum file size in bytes to consider a download complete
# Small for single-grid-point (3x3km) areas (~800 KB for a year)
MIN_FILE_SIZE = 500 * 1024


class ERA5Collector:
    def __init__(self):
        try:
            import cdsapi
            self.client = cdsapi.Client(quiet=True)
            logger.info("CDS API client initialized")
        except Exception as e:
            logger.error(
                f"Failed to initialize CDS API client: {e}\n"
                "Run setup_cds.py to configure your credentials."
            )
            raise

    def download_city(self, city_key: str, city_config: dict) -> Path:
        """
        Download ERA5 single-level data for a city's bounding box.
        Returns the path to the downloaded NetCDF file.
        """
        output_dir = RAW_DIR / "era5"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{city_key}_era5_{YEAR}.nc"

        # Checkpointing: skip if already downloaded
        if output_path.exists() and output_path.stat().st_size > MIN_FILE_SIZE:
            logger.info(
                f"  Skipping {city_key} ERA5 download "
                f"(file exists: {output_path.stat().st_size / 1e6:.1f} MB)"
            )
            return output_path

        area = city_config["era5_area"]
        logger.info(
            f"  Requesting ERA5 data for {city_config['name']} "
            f"(area: N={area[0]}, W={area[1]}, S={area[2]}, E={area[3]})"
        )
        logger.info(
            "  This request is queued on the CDS server. "
            "It may take a while to process..."
        )

        try:
            self.client.retrieve(
                ERA5_DATASET,
                {
                    "product_type": ["reanalysis"],
                    "variable": ERA5_VARIABLES,
                    "year": [str(YEAR)],
                    "month": MONTHS,
                    "day": DAYS,
                    "time": HOURS,
                    "data_format": "netcdf",
                    "download_format": "unarchived",
                    "area": area,
                },
                str(output_path),
            )
            logger.info(
                f"  ERA5 download complete: {output_path} "
                f"({output_path.stat().st_size / 1e6:.1f} MB)"
            )
            return output_path

        except Exception as e:
            logger.warning(
                f"  Full-year request failed: {e}\n"
                "  Falling back to monthly downloads..."
            )
            return self._download_monthly_fallback(city_key, city_config, output_dir)

    def _download_monthly_fallback(
        self, city_key: str, city_config: dict, output_dir: Path
    ) -> Path:
        """Download ERA5 data month by month and merge."""
        import xarray as xr

        area = city_config["era5_area"]
        monthly_files = []

        for month in MONTHS:
            month_path = output_dir / f"{city_key}_era5_{YEAR}_{month}.nc"

            if month_path.exists() and month_path.stat().st_size > 100_000:
                logger.info(f"    Month {month} already downloaded, skipping")
                monthly_files.append(month_path)
                continue

            try:
                logger.info(f"    Downloading month {month}...")
                self.client.retrieve(
                    ERA5_DATASET,
                    {
                        "product_type": ["reanalysis"],
                        "variable": ERA5_VARIABLES,
                        "year": [str(YEAR)],
                        "month": [month],
                        "day": DAYS,
                        "time": HOURS,
                        "data_format": "netcdf",
                        "download_format": "unarchived",
                        "area": area,
                    },
                    str(month_path),
                )
                monthly_files.append(month_path)
                logger.info(f"    Month {month} done")

            except Exception as e:
                logger.error(f"    Month {month} failed: {e}")

        if not monthly_files:
            raise RuntimeError(f"No ERA5 data downloaded for {city_key}")

        # Merge monthly files (sequential open to avoid dask dependency)
        merged_path = output_dir / f"{city_key}_era5_{YEAR}.nc"
        logger.info(f"  Merging {len(monthly_files)} monthly files...")
        datasets = [xr.open_dataset(str(f)) for f in monthly_files]
        ds = xr.concat(datasets, dim="valid_time")
        for d in datasets:
            d.close()
        ds.to_netcdf(str(merged_path))
        ds.close()
        logger.info(f"  Merged ERA5 saved: {merged_path}")

        return merged_path

    def collect_all(self, cities: dict | None = None) -> dict[str, Path]:
        """Download ERA5 data for specified cities (defaults to all)."""
        if cities is None:
            cities = CITIES
        results = {}
        for city_key, city_cfg in cities.items():
            logger.info(f"Collecting ERA5 for {city_cfg['name']}...")
            results[city_key] = self.download_city(city_key, city_cfg)
        return results
