"""
Convert SIATA JSON format to OpenAQ-compatible CSV format.
"""

import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def convert_siata_json_to_csv(json_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Convert SIATA JSON data to OpenAQ-compatible CSV format.

    Expected JSON structure:
    [
      {
        "codigoSerial": 3,
        "latitud": 6.379,
        "longitud": -75.567,  # if available
        "datos": [
          {
            "variableConsulta": "pm25",
            "fecha": "2019-01-01 00:00:00",
            "calidad": "1.0",
            "valor": 15.0
          },
          ...
        ]
      },
      ...
    ]

    Output columns: datetime_utc, location_id, location_name, sensor_id, lat, lon, pm25, coverage_pct
    """
    logger.info(f"Converting SIATA JSON: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    records = []
    for station in data:
        station_id = station['codigoSerial']
        lat = station.get('latitud', None)
        lon = station.get('longitud', None)  # May not exist in JSON

        for measurement in station['datos']:
            # Convert datetime format
            timestamp = pd.to_datetime(measurement['fecha'])
            timestamp_utc = timestamp.tz_localize('UTC') if timestamp.tzinfo is None else timestamp

            records.append({
                'datetime_utc': timestamp_utc.isoformat(),
                'location_id': station_id,
                'location_name': f"SIATA-{station_id}",
                'sensor_id': station_id,
                'lat': lat,
                'lon': lon,
                'pm25': float(measurement['valor']),
                'coverage_pct': 100.0 if float(measurement.get('calidad', 1.0)) == 1.0 else 75.0
            })

    df = pd.DataFrame(records)

    # Sort by datetime and location
    df = df.sort_values(['datetime_utc', 'location_id']).reset_index(drop=True)

    logger.info(f"  Converted {len(df):,} records from {len(data)} stations")
    logger.info(f"  Date range: {df['datetime_utc'].min()} to {df['datetime_utc'].max()}")

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"  Saved to: {output_path}")

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Paths
    json_path = Path("data/raw/Datos_SIATA_Aire_pm25.json")
    output_path = Path("data/raw/openaq/medellin_siata_pm25_raw.csv")

    # Convert
    convert_siata_json_to_csv(json_path, output_path)
