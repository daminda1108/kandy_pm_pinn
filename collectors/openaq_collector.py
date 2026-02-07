"""
OpenAQ v3 API client for collecting PM2.5 measurements.
Handles pagination, rate limiting, and retry logic.
"""

import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from calendar import monthrange

import requests
import pandas as pd

from config import (
    RAW_DIR, OPENAQ_PAGE_LIMIT, CITIES,
    DATE_FROM, DATE_TO, YEAR,
)

logger = logging.getLogger(__name__)


class OpenAQCollector:
    def __init__(self, api_key: str, base_url: str, rate_limit: int):
        self.base_url = base_url.rstrip("/")
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Accept": "application/json",
        })
        self._request_times: list[float] = []

    def _wait_for_rate_limit(self) -> None:
        """Ensure we don't exceed the per-minute rate limit."""
        now = time.time()
        # Remove requests older than 60 seconds
        self._request_times = [t for t in self._request_times if now - t < 60]
        if len(self._request_times) >= self.rate_limit - 2:
            oldest = self._request_times[0]
            sleep_time = 60 - (now - oldest) + 1
            if sleep_time > 0:
                logger.debug(f"Rate limit approaching, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)

    def _request(self, endpoint: str, params: dict | None = None) -> dict:
        """
        Make a GET request with retry logic and rate limit tracking.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        max_retries = 3
        backoff = 2

        for attempt in range(max_retries):
            self._wait_for_rate_limit()
            try:
                resp = self.session.get(url, params=params, timeout=30)
                self._request_times.append(time.time())

                # Check rate limit headers
                remaining = resp.headers.get("x-ratelimit-remaining")
                if remaining is not None and int(remaining) < 5:
                    reset_sec = resp.headers.get("x-ratelimit-reset", "60")
                    logger.info(f"Rate limit low ({remaining} remaining), sleeping {reset_sec}s")
                    time.sleep(int(reset_sec) + 1)

                if resp.status_code == 429:
                    reset_sec = int(resp.headers.get("x-ratelimit-reset", "60"))
                    logger.warning(f"Rate limited (429). Sleeping {reset_sec}s...")
                    time.sleep(reset_sec + 1)
                    continue

                if resp.status_code >= 500:
                    logger.warning(f"Server error {resp.status_code} on attempt {attempt + 1}")
                    time.sleep(backoff ** attempt)
                    continue

                resp.raise_for_status()
                return resp.json()

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                time.sleep(backoff ** attempt)
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt + 1}")
                time.sleep(backoff ** attempt)

        raise RuntimeError(f"Failed after {max_retries} retries: {url}")

    def _paginate(self, endpoint: str, params: dict) -> list:
        """Auto-paginate through all results."""
        all_results = []
        params = dict(params)
        params["limit"] = OPENAQ_PAGE_LIMIT
        page = 1

        while True:
            params["page"] = page
            data = self._request(endpoint, params)
            results = data.get("results", [])
            all_results.extend(results)

            meta = data.get("meta", {})
            found_raw = meta.get("found", 0)
            try:
                found = int(str(found_raw).lstrip(">"))
            except (ValueError, TypeError):
                found = float("inf")

            if len(results) < OPENAQ_PAGE_LIMIT or page * OPENAQ_PAGE_LIMIT >= found:
                break

            page += 1

        return all_results

    def discover_locations(self, lat: float, lon: float, radius: int) -> list[dict]:
        """Find PM2.5 monitoring stations near the given coordinates."""
        params = {
            "coordinates": f"{lat},{lon}",
            "radius": radius,
            "limit": OPENAQ_PAGE_LIMIT,
        }

        locations = self._paginate("locations", params)

        # Filter to locations that have PM2.5 sensors
        pm25_locations = []
        for loc in locations:
            sensors = loc.get("sensors", [])
            pm25_sensors = [
                s for s in sensors
                if s.get("parameter", {}).get("name", "").lower() in ("pm25", "pm2.5")
                or s.get("parameter", {}).get("id") == 2
            ]
            if pm25_sensors:
                pm25_locations.append({
                    "location_id": loc.get("id"),
                    "name": loc.get("name", "Unknown"),
                    "lat": loc.get("coordinates", {}).get("latitude"),
                    "lon": loc.get("coordinates", {}).get("longitude"),
                    "sensors": pm25_sensors,
                })

        logger.info(f"Found {len(pm25_locations)} locations with PM2.5 sensors")
        return pm25_locations

    def get_sensor_measurements(
        self, sensor_id: int, date_from: str, date_to: str
    ) -> list[dict]:
        """Get hourly measurements for a specific sensor in a date range."""
        params = {
            "date_from": date_from,
            "date_to": date_to,
        }
        return self._paginate(f"sensors/{sensor_id}/hours", params)

    def _collect_sensor_year(self, sensor_id: int, location_info: dict) -> list[dict]:
        """Collect a full year of data for one sensor, month by month."""
        records = []

        for month in range(1, 13):
            _, last_day = monthrange(YEAR, month)
            m_from = f"{YEAR}-{month:02d}-01T00:00:00Z"
            m_to = f"{YEAR}-{month:02d}-{last_day}T23:59:59Z"

            try:
                measurements = self.get_sensor_measurements(sensor_id, m_from, m_to)
                for m in measurements:
                    period = m.get("period", {})
                    dt_from = period.get("datetimeFrom", {}).get("utc")
                    dt_to = period.get("datetimeTo", {}).get("utc")
                    records.append({
                        "datetime_utc": dt_from,
                        "datetime_to": dt_to,
                        "location_id": location_info["location_id"],
                        "location_name": location_info["name"],
                        "sensor_id": sensor_id,
                        "lat": location_info["lat"],
                        "lon": location_info["lon"],
                        "pm25": m.get("value"),
                        "coverage_pct": (
                            m.get("coverage", {}).get("observedCount", 0)
                            / max(m.get("coverage", {}).get("expectedCount", 1), 1)
                            * 100
                        ) if m.get("coverage", {}).get("expectedCount", 0) else None,
                    })

                logger.debug(
                    f"  Sensor {sensor_id} month {month:02d}: {len(measurements)} records"
                )

            except Exception as e:
                logger.warning(
                    f"  Failed to collect sensor {sensor_id} month {month:02d}: {e}"
                )

        return records

    def collect_city(self, city_key: str, city_config: dict) -> pd.DataFrame:
        """
        Full collection pipeline for one city.
        Returns DataFrame with all PM2.5 hourly measurements.
        """
        output_dir = RAW_DIR / "openaq"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{city_key}_pm25_raw.csv"

        # Checkpointing: skip if already collected
        if output_path.exists() and output_path.stat().st_size > 100:
            logger.info(f"  Skipping {city_key} PM2.5 collection (file exists)")
            return pd.read_csv(output_path)

        # Discover stations
        locations = self.discover_locations(
            city_config["lat"],
            city_config["lon"],
            city_config["openaq_search_radius"],
        )

        if not locations:
            logger.warning(
                f"  No PM2.5 stations found for {city_config['name']}. "
                f"Trying expanded search by country..."
            )
            # Fallback: search by country
            locations = self._search_by_country(city_config)

        if not locations:
            logger.warning(
                f"  No PM2.5 data available for {city_config['name']}. "
                f"Creating empty dataset."
            )
            df = pd.DataFrame(columns=[
                "datetime_utc", "datetime_to", "location_id", "location_name",
                "sensor_id", "lat", "lon", "pm25", "coverage_pct",
            ])
            df.to_csv(output_path, index=False)
            return df

        # Collect measurements from all stations
        all_records = []
        for i, loc in enumerate(locations):
            logger.info(
                f"  Station {i + 1}/{len(locations)}: {loc['name']} "
                f"({loc['lat']:.4f}, {loc['lon']:.4f})"
            )
            for sensor in loc["sensors"]:
                sid = sensor.get("id")
                if sid is None:
                    continue
                records = self._collect_sensor_year(sid, loc)
                all_records.extend(records)
                logger.info(f"    Sensor {sid}: {len(records)} hourly records")

        df = pd.DataFrame(all_records)
        if not df.empty:
            df.to_csv(output_path, index=False)
            logger.info(
                f"  {city_config['name']}: {len(df)} total records from "
                f"{df['location_id'].nunique()} stations saved to {output_path}"
            )
        else:
            df = pd.DataFrame(columns=[
                "datetime_utc", "datetime_to", "location_id", "location_name",
                "sensor_id", "lat", "lon", "pm25", "coverage_pct",
            ])
            df.to_csv(output_path, index=False)
            logger.warning(f"  {city_config['name']}: No measurements collected")

        return df

    def _search_by_country(self, city_config: dict) -> list[dict]:
        """Fallback: search for PM2.5 stations by country code."""
        try:
            params = {
                "countries": city_config["country"],
                "limit": OPENAQ_PAGE_LIMIT,
            }
            locations = self._paginate("locations", params)

            # Filter to locations near the target city (within ~50km)
            city_lat = city_config["lat"]
            city_lon = city_config["lon"]
            nearby = []

            for loc in locations:
                loc_lat = loc.get("coordinates", {}).get("latitude")
                loc_lon = loc.get("coordinates", {}).get("longitude")
                if loc_lat is None or loc_lon is None:
                    continue

                # Approximate distance in km
                dlat = abs(loc_lat - city_lat) * 111
                dlon = abs(loc_lon - city_lon) * 111 * 0.85  # cos correction
                dist = (dlat**2 + dlon**2) ** 0.5

                if dist < 50:
                    sensors = loc.get("sensors", [])
                    pm25_sensors = [
                        s for s in sensors
                        if s.get("parameter", {}).get("name", "").lower()
                        in ("pm25", "pm2.5")
                        or s.get("parameter", {}).get("id") == 2
                    ]
                    if pm25_sensors:
                        nearby.append({
                            "location_id": loc.get("id"),
                            "name": loc.get("name", "Unknown"),
                            "lat": loc_lat,
                            "lon": loc_lon,
                            "sensors": pm25_sensors,
                        })

            logger.info(f"  Country search found {len(nearby)} nearby PM2.5 stations")
            return nearby

        except Exception as e:
            logger.warning(f"  Country search failed: {e}")
            return []
