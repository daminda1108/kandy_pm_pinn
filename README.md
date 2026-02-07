# PINN PM2.5 Transfer Learning: Medellin → Kandy

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Data Pipeline](https://img.shields.io/badge/pipeline-production-green.svg)]()
[![PINN Development](https://img.shields.io/badge/PINN-in--progress-orange.svg)]()

**Physics-Informed Neural Network (PINN) for PM2.5 prediction using transfer learning between Medellin, Colombia and Kandy, Sri Lanka.**

---

## 🎯 Project Overview

This repository contains:
1. **Data Pipeline** - Complete data collection, quality control, and validation pipeline
2. **PINN Implementation** - Physics-Informed Neural Network for PM2.5 prediction with transfer learning

The project uses **transfer learning** to leverage knowledge from a data-rich city (Medellin, Colombia) to improve predictions in a data-scarce city (Kandy, Sri Lanka).

### Key Features

- ✅ **89,195 quality-controlled records** from 24 monitoring stations
- ✅ **Perfect temporal alignment** (Oct 2018 - Sep 2019, 365 days)
- ✅ **0.908 correlation similarity** between meteorology-PM2.5 relationships (statistically validates transfer learning)
- ✅ **Automated 5-phase data pipeline** from collection to PINN-ready datasets
- ✅ **Zero missing values** across all features
- ✅ **Comprehensive statistical validation** (KS test, Mann-Whitney U, Cohen's d, pattern similarity)
- 🚧 **PINN model implementation** (in progress)

---

## 📊 Dataset Summary

| City | Records | Stations | Period | PM2.5 Mean | Coverage |
|------|---------|----------|--------|------------|----------|
| **Medellin** | 86,275 | 23 | Oct 2018 - Sep 2019 | 21.06 ± 12.02 µg/m³ | 97.1% |
| **Kandy** | 2,920 | 1 | Oct 2018 - Sep 2019 | 35.96 ± 20.43 µg/m³ | 100.0% |
| **Combined** | 89,195 | 24 | Oct 2018 - Sep 2019 | - | - |

**Features:** pm25, wind_speed, wind_direction, temperature_2m, relative_humidity, boundary_layer_height, surface_pressure

---

## 📁 Repository Structure

```
kandy_pm_pinn/
├── main.py                          # Data pipeline orchestrator
├── config_template.py               # Configuration template (API keys)
├── setup_cds.py                     # CDS API setup utility
├── requirements.txt                 # Python dependencies
│
├── collectors/                      # Data collection modules
│   ├── openaq_collector.py         # OpenAQ v3 API (PM2.5)
│   └── era5_collector.py            # CDS API (ERA5 meteorology, CAMS)
│
├── preprocessing/                   # Data preprocessing
│   ├── pm25_cleaner.py             # 5-stage QC + geographic filtering
│   ├── era5_processor.py           # ERA5 NetCDF processing
│   └── merger.py                   # Temporal merging
│
├── analysis/                        # Statistical analysis
│   ├── statistics.py               # Distribution tests, pattern similarity
│   └── visualizations.py           # 9 publication-quality figures
│
├── converters/                      # Data format converters
│   ├── siata_to_csv.py             # SIATA JSON → CSV
│   └── combine_pm25_sources.py     # Multi-source PM2.5 merging
│
├── src/                            # PINN model implementation (in progress)
│   ├── models.py                   # PINN architecture
│   ├── physics.py                  # Physics-informed loss functions
│   └── data.py                     # Data loaders and utilities
│
├── notebooks/                       # Jupyter notebooks
│   ├── colab_setup.ipynb           # Google Colab environment setup
│   └── 00_environment_test.ipynb   # Environment verification
│
├── docs/                           # Documentation
│   ├── TECHNICAL_REPORT.md         # Comprehensive technical documentation
│   ├── FINAL_VALIDATION_SUMMARY.md # Statistical validation results
│   ├── KANDY_EXTENSION_COMPLETION_SUMMARY.md
│   └── REBUILD_COMPLETION_SUMMARY.md
│
└── outputs/                        # Generated outputs
    └── figures/                    # Sample visualizations (9 PNGs)
```

---

## 🏗️ Data Pipeline Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Phase 0: CDS API Configuration                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Data Collection                               │
│  • OpenAQ v3 API (PM2.5)                                │
│  • CDS API (ERA5 meteorology, CAMS PM2.5)              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 2: Preprocessing                                 │
│  • 5-stage QC (validation, geographic, IQR, spike)     │
│  • Geographic filtering (10km Medellin, 5km Kandy)     │
│  • CAMS bias correction (0.6327 factor)                │
│  • Temporal merging (PM2.5 + ERA5)                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 3: Statistical Analysis                          │
│  • Distribution tests (KS, Mann-Whitney)                │
│  • Pattern similarity (seasonal, diurnal, correlation)  │
│  • Transfer learning validation                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 4: Visualization (9 figures)                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 5: PINN-Ready Dataset                            │
│  Output: combined_pinn_dataset.csv (89,195 records)    │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- CDS API account (for ERA5/CAMS data): https://cds.climate.copernicus.eu/user/register
- OpenAQ API key (optional, for re-running data collection): https://openaq.org/

### Installation

```bash
# Clone the repository
git clone https://github.com/daminda1108/kandy_pm_pinn.git
cd kandy_pm_pinn

# Install dependencies
pip install -r requirements.txt

# Configure CDS API (create ~/.cdsapirc)
python setup_cds.py
```

### Running the Data Pipeline

```bash
# Full pipeline (both cities)
python main.py

# Single city
python main.py --city medellin
python main.py --city kandy

# Force reprocess (delete checkpoints)
python main.py --force
```

### Expected Outputs

```
data/final/
├── medellin_pinn_dataset.csv       # 86,275 records
├── kandy_pinn_dataset.csv          # 2,920 records
└── combined_pinn_dataset.csv       # 89,195 records (PINN-ready)

outputs/
├── figures/
│   ├── pm25_timeseries.png
│   ├── pm25_distributions.png
│   ├── seasonal_patterns.png
│   ├── diurnal_patterns.png
│   ├── correlation_heatmaps.png
│   ├── meteorological_comparison.png
│   ├── wind_pm25_scatter.png
│   ├── data_coverage.png
│   └── station_locations.png
└── reports/
    └── statistical_comparison.txt
```

---

## 🧠 PINN Development (In Progress)

### Model Architecture

**Shared Encoder** (Pre-train on Medellin):
```python
Input: [wind_speed, temperature, RH, BLH, pressure, hour, month]
  ↓
Dense(64) → ReLU
  ↓
Dense(32) → ReLU
  ↓
Latent Physics (16 dimensions)
```

**City-Specific Decoders**:
```python
Medellin Decoder:
  Latent(16) → Dense(16) → PM2.5 (baseline ~21 µg/m³)

Kandy Decoder:
  Latent(16) → Dense(16) → PM2.5 (baseline ~36 µg/m³)
```

### Physics-Informed Loss

```python
Total Loss = MSE Loss + λ_physics × Physics Loss

Physics Loss = PDE Residuals:
  ∂C/∂t + u·∇C = ∇·(K∇C) + S - R

Where:
  - C: PM2.5 concentration
  - u: Wind velocity (u10, v10)
  - K: Diffusivity (function of BLH)
  - S: Source emissions (learned)
  - R: Removal (deposition)
```

### Training Strategy

1. **Pre-train on Medellin** (86K records, 80/20 split)
2. **Transfer to Kandy** (2.3K records, fine-tune decoder)
3. **Domain adaptation** for +14.9 µg/m³ baseline shift
4. **Evaluate** transfer learning gain vs from-scratch

---

## 📈 Transfer Learning Validation

### Statistical Tests
- **Kolmogorov-Smirnov:** stat=0.3424, p=3.82e-296 (distributions differ)
- **Mann-Whitney U:** U=65.9M, p≈0 (Kandy median > Medellin)
- **Cohen's d:** -1.20 (large effect size, domain adaptation needed)

### Pattern Similarity ✅
- **Meteorology-PM2.5 correlation:** 0.9075 (excellent - **validates transfer learning**)
- **Seasonal alignment:** 0.9726 (near-perfect)
- **Seasonal Pearson r:** 0.5591 (moderate)

**Conclusion:** Transfer learning is statistically **JUSTIFIED** based on excellent meteorology-PM2.5 relationship similarity (>0.90).

---

## 📚 Documentation

- **[TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md)** - Comprehensive 60-page technical documentation
- **[FINAL_VALIDATION_SUMMARY.md](docs/FINAL_VALIDATION_SUMMARY.md)** - Statistical validation results
- **[KANDY_EXTENSION_COMPLETION_SUMMARY.md](docs/KANDY_EXTENSION_COMPLETION_SUMMARY.md)** - Kandy dataset extension details
- **[REBUILD_COMPLETION_SUMMARY.md](docs/REBUILD_COMPLETION_SUMMARY.md)** - Medellin full-year rebuild details

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## 📄 License

- **Code:** MIT License (see [LICENSE](LICENSE))
- **Documentation:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Data:** See individual data source licenses (SIATA, OpenAQ, ERA5, CAMS)

---

## 🙏 Acknowledgments

**Data Sources:**
- **SIATA** - Sistema de Alerta Temprana de Medellín (Medellin air quality data)
- **OpenAQ** - Open Air Quality platform (global PM2.5 data)
- **ERA5** - ECMWF Reanalysis v5 (meteorological data)
- **CAMS** - Copernicus Atmosphere Monitoring Service (Kandy PM2.5 estimates)

**Key References:**
- Priyankara et al. (2021) - CAMS bias correction factors for Sri Lanka
- Raissi et al. (2019) - Physics-Informed Neural Networks

---

## 📧 Contact

**Author:** Daminda Herath
**GitHub:** [@daminda1108](https://github.com/daminda1108)
**Repository:** [kandy_pm_pinn](https://github.com/daminda1108/kandy_pm_pinn)

---

**Last Updated:** 2026-02-07
**Status:** Data Pipeline ✅ Complete | PINN Development 🚧 In Progress
