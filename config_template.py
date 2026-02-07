"""
Configuration Template for PINN PM2.5 Transfer Learning Pipeline

INSTRUCTIONS:
1. Copy this file to config.py
2. Add your OpenAQ API key below
3. Do NOT commit config.py to Git (it's in .gitignore)
"""

# =============================================================================
# API KEYS (REQUIRED)
# =============================================================================

# OpenAQ API Key (get from: https://openaq.org/developers)
OPENAQ_API_KEY = "YOUR_OPENAQ_API_KEY_HERE"  # Replace with your actual key

# CDS API Configuration
# Register at: https://cds.climate.copernicus.eu/user/register
# Then run: python setup_cds.py to configure ~/.cdsapirc

# =============================================================================
# CITY DEFINITIONS
# =============================================================================

CITIES = {
    "medellin": {
        "lat": 6.2476,
        "lon": -75.5658,
        "era5_area": [6.34, -75.66, 6.15, -75.47],  # [N, W, S, E]
        "station_radius_km": 10.0,  # Geographic filter radius
        "timezone": "America/Bogota",
        "temporal_resolution": "1H"  # Hourly
    },
    "kandy": {
        "lat": 7.2906,
        "lon": 80.6337,
        "era5_area": [7.38, 80.54, 7.20, 80.72],  # [N, W, S, E]
        "station_radius_km": 5.0,  # Geographic filter radius
        "timezone": "Asia/Colombo",
        "temporal_resolution": "3H"  # 3-hourly
    }
}

# =============================================================================
# DATA QUALITY CONTROL PARAMETERS
# =============================================================================

# PM2.5 valid range (µg/m³)
PM25_MIN = 0.0
PM25_MAX = 500.0

# Outlier detection
PM25_IQR_MULTIPLIER = 3.0  # Conservative threshold (retains 99.7% of normal dist)

# Spike detection threshold (µg/m³/hour)
PM25_SPIKE_THRESHOLD = 100.0

# Minimum station coverage (fraction of total hours)
STATION_MIN_COVERAGE = 0.10  # 10%

# =============================================================================
# WHO AIR QUALITY GUIDELINES (µg/m³)
# =============================================================================

WHO_AQG = 15.0   # Annual mean guideline
WHO_IT1 = 35.0   # Interim Target 1
WHO_IT2 = 25.0   # Interim Target 2
WHO_IT3 = 15.0   # Interim Target 3

# =============================================================================
# ERA5 VARIABLES
# =============================================================================

ERA5_VARIABLES = [
    '10m_u_component_of_wind',
    '10m_v_component_of_wind',
    '2m_temperature',
    '2m_dewpoint_temperature',
    'boundary_layer_height',
    'surface_pressure'
]

# =============================================================================
# PATHS
# =============================================================================

from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

# Data subdirectories
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FINAL_DIR = DATA_DIR / "final"

# Raw data sources
OPENAQ_DIR = RAW_DIR / "openaq"
ERA5_DIR = RAW_DIR / "era5"
CAMS_DIR = RAW_DIR / "cams"

# Output subdirectories
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORTS_DIR = OUTPUT_DIR / "reports"
LOGS_DIR = OUTPUT_DIR / "logs"

# Create directories if they don't exist
for directory in [OPENAQ_DIR, ERA5_DIR, CAMS_DIR, PROCESSED_DIR, FINAL_DIR,
                   FIGURES_DIR, REPORTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

import logging

LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# =============================================================================
# OPENAQ API CONFIGURATION
# =============================================================================

OPENAQ_BASE_URL = "https://api.openaq.org/v3"
OPENAQ_RATE_LIMIT = 60  # Requests per minute
OPENAQ_PAGE_SIZE = 1000  # Results per page

# =============================================================================
# TEMPORAL COVERAGE
# =============================================================================

# Target period for both cities
START_DATE = "2018-10-01"
END_DATE = "2019-09-30"

# =============================================================================
# VISUALIZATION SETTINGS
# =============================================================================

# Figure size (inches)
FIGURE_SIZE = (12, 6)
FIGURE_DPI = 300

# Color palette
CITY_COLORS = {
    "medellin": "#1f77b4",  # Blue
    "kandy": "#ff7f0e"       # Orange
}

# Plot style
PLOT_STYLE = "seaborn-v0_8-darkgrid"
