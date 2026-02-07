# Changelog

All notable changes to the PINN PM2.5 Transfer Learning project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-02-07

### Added - Data Pipeline Complete

#### Core Pipeline
- **5-phase automated pipeline** from data collection to PINN-ready dataset
- **Phase 0:** CDS API configuration and validation
- **Phase 1:** PM2.5 (OpenAQ, SIATA, CAMS) and meteorology (ERA5) collection
- **Phase 2:** 5-stage quality control and preprocessing
- **Phase 3:** Statistical validation and transfer learning justification
- **Phase 4:** 9 publication-quality visualization figures
- **Phase 5:** Final dataset generation (89,195 records)

#### Data Collection
- OpenAQ v3 API client with pagination and rate limiting
- CDS API client for ERA5 meteorology (month-by-month fallback)
- SIATA JSON to CSV converter for Medellin historical data
- CAMS PM2.5 bias correction for Kandy (0.6327 factor based on Priyankara et al. 2021)

#### Quality Control
- **Stage 1:** Physical range validation (0-500 µg/m³)
- **Stage 1b:** Geographic filtering (10km Medellin, 5km Kandy)
- **Stage 2:** Temporal coverage filtering (minimum 10%)
- **Stage 3:** IQR outlier removal (3×IQR threshold)
- **Stage 4:** Spike detection (100 µg/m³/hour threshold)
- **Stage 5:** Station-level coverage check

#### Preprocessing
- NetCDF to CSV conversion with unit standardization
- Derived variable calculation:
  - Wind speed/direction from u10/v10 components
  - Relative humidity from temperature and dewpoint (Magnus formula)
- Temporal merging of PM2.5 and ERA5 on datetime_utc

#### Statistical Validation
- Kolmogorov-Smirnov test for distribution comparison
- Mann-Whitney U test for median differences
- Cohen's d effect size calculation
- Seasonal pattern correlation (cosine similarity, Pearson r)
- Diurnal pattern analysis
- **Meteorology-PM2.5 correlation similarity: 0.9075** (transfer learning justified)

#### Visualizations
1. PM2.5 time series (full year, both cities)
2. Distribution histograms with WHO guidelines
3. Diurnal patterns (hour-of-day means)
4. Seasonal patterns (monthly aggregates)
5. Correlation heatmaps (meteorology-PM2.5)
6. Wind speed vs PM2.5 scatter plots
7. Meteorological variable comparisons (violin plots)
8. Data coverage heatmaps
9. Station location maps

#### Documentation
- **TECHNICAL_REPORT.md:** 60-page comprehensive technical documentation
- **README.md:** GitHub repository documentation with quick start guide
- **KANDY_EXTENSION_COMPLETION_SUMMARY.md:** Temporal alignment process
- **REBUILD_COMPLETION_SUMMARY.md:** Medellin full-year extension
- **FINAL_VALIDATION_SUMMARY.md:** Statistical validation results
- **CHANGELOG.md:** Version history (this file)

### Dataset Statistics

#### Medellin (Oct 2018 - Sep 2019)
- **Records:** 86,275 (hourly)
- **Stations:** 23 (within 10km geomorphic core)
- **Coverage:** 97.1%
- **PM2.5:** 21.06 ± 12.02 µg/m³
- **Sources:** SIATA + OpenAQ

#### Kandy (Oct 2018 - Sep 2019)
- **Records:** 2,920 (3-hourly)
- **Stations:** 1 (CAMS grid point, bias-corrected)
- **Coverage:** 100.0%
- **PM2.5:** 35.96 ± 20.43 µg/m³
- **Source:** CAMS EAC4

#### Combined
- **Total records:** 89,195
- **Temporal alignment:** PERFECT (365 days overlap)
- **Missing values:** 0
- **Features:** 11 (pm25, wind_speed, wind_direction, temperature_2m, relative_humidity, boundary_layer_height, surface_pressure, datetime_utc, city, lat, lon)

### Transfer Learning Validation

- **Meteorology-PM2.5 correlation similarity:** 0.9075 ✅ (excellent, >0.80 threshold)
- **Seasonal cosine similarity:** 0.9726 ✅ (near-perfect)
- **Cohen's d:** -1.20 (requires domain adaptation for +14.9 µg/m³ shift)
- **Conclusion:** Transfer learning statistically justified

---

## [0.9.0] - 2026-02-07 - Kandy Temporal Extension

### Added
- CAMS PM2.5 data processing for Kandy Oct-Dec 2018
- Temporal extension of Kandy dataset to Oct 2018 - Sep 2019
- CAMS bias correction based on Priyankara et al. (2021)
- `process_kandy_cams_data.py` script

### Changed
- Extended Kandy coverage from Jan-Dec 2019 to Oct 2018 - Sep 2019
- Improved transfer learning validation (0.879 → 0.908 correlation similarity)
- Updated all statistical reports with aligned-period data

---

## [0.8.0] - 2026-02-07 - Medellin Full-Year Rebuild

### Added
- SIATA historical data integration (Aug 2018 - Aug 2019)
- `rebuild_full_year_dataset.py` script
- `combine_pm25_sources.py` converter (SIATA + OpenAQ merge)
- ERA5 Oct-Dec 2018 download for Medellin

### Changed
- Extended Medellin from Jan-Oct 2019 to Oct 2018 - Sep 2019
- Increased record count from 63,002 to 86,275 (+37%)
- Achieved full seasonal cycle coverage (365 days)

---

## [0.7.0] - 2026-02-06 - Geographic Filtering Implementation

### Added
- Stage 1b geographic filtering in QC pipeline
- Haversine distance calculation
- City-specific radius thresholds (10km Medellin, 5km Kandy)

### Fixed
- Geographic filtering was configured but not implemented in `pm25_cleaner.py`

### Changed
- Excluded 10 distant Medellin stations (47% of raw data)
- Ensured geomorphic consistency for transfer learning

---

## [0.6.0] - 2026-02-05 - Statistical Analysis & Visualization

### Added
- Cross-city statistical comparison (KS test, Mann-Whitney U, Cohen's d)
- Pattern similarity metrics (seasonal, diurnal, correlation structure)
- 9 publication-quality visualization figures
- `analysis/statistics.py` module
- `analysis/visualizations.py` module

---

## [0.5.0] - 2026-02-04 - Preprocessing Pipeline

### Added
- 5-stage PM2.5 quality control
- ERA5 NetCDF processing and unit conversion
- Temporal merging (PM2.5 + ERA5)
- `preprocessing/pm25_cleaner.py` module
- `preprocessing/era5_processor.py` module
- `preprocessing/merger.py` module

---

## [0.4.0] - 2026-02-03 - ERA5 Data Collection

### Added
- CDS API client for ERA5 reanalysis
- Monthly fallback download strategy
- NetCDF file handling
- `collectors/era5_collector.py` module
- `setup_cds.py` configuration script

---

## [0.3.0] - 2026-02-02 - OpenAQ Integration

### Added
- OpenAQ v3 API client
- Pagination and rate limiting
- `collectors/openaq_collector.py` module

---

## [0.2.0] - 2026-02-01 - SIATA Data Processing

### Added
- SIATA JSON to CSV converter
- `converters/siata_to_csv.py` module

---

## [0.1.0] - 2026-01-31 - Initial Setup

### Added
- Project structure and repository setup
- `main.py` pipeline orchestrator
- `config.py` configuration file
- Basic logging infrastructure

---

## Future Releases (Planned)

### [2.0.0] - PINN Model Implementation (Planned)
- Physics-informed neural network architecture
- Transfer learning from Medellin to Kandy
- Training and evaluation scripts
- Model checkpointing and saving
- Hyperparameter optimization

### [1.1.0] - Extended Validation (Planned)
- Multi-year dataset extension (2018-2023)
- Additional valley cities (Kathmandu, Quito)
- Ground-truth Kandy validation data

---

**Note:** Version numbers follow Semantic Versioning (MAJOR.MINOR.PATCH)
- MAJOR: Incompatible API changes
- MINOR: New features (backward-compatible)
- PATCH: Bug fixes (backward-compatible)
