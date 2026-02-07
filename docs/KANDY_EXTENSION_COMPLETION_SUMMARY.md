# Kandy Temporal Extension - Completion Summary

**Date:** 2026-02-07
**Status:** ✅ COMPLETE - Both cities temporally aligned (Oct 2018 - Sep 2019)

---

## Mission Accomplished

Successfully extended Kandy dataset from Jan-Dec 2019 to **Oct 2018 - Sep 2019**, achieving **perfect temporal alignment** with Medellin for robust PINN transfer learning.

---

## What Was Done

### 1. CAMS Data Processing (Oct-Dec 2018)
**Source file:** `a1919f92534a5b3c8f7f5f9dcf46e07d/data_sfc.nc`

**Processing steps:**
1. Extracted PM2.5 from CAMS NetCDF at Kandy location (7.00°N, 80.75°E)
2. Converted units: kg/m³ → µg/m³ (×1e9)
3. Applied bias correction:
   - CAMS uncorrected mean: 54.50 µg/m³
   - Correction factor: 0.6327
   - Corrected mean: 34.48 µg/m³ (matches Priyankara et al. 2021 ground truth)
4. Added metadata columns to match pipeline format
5. Created 736 records (Oct-Dec 2018, 3-hourly)

**Output:** `data/raw/openaq/kandy_pm25_2018_oct_dec.csv`

### 2. Dataset Combination
**Combined sources:**
- Oct-Dec 2018: 736 records (CAMS bias-corrected)
- Jan-Dec 2019: 2,920 records (existing CAMS data)
- **Total raw:** 3,656 records

**Filtered to Oct 2018 - Sep 2019:**
- **Final count:** 2,920 records (100% temporal coverage)
- **Date range:** 2018-10-01 to 2019-09-30
- **PM2.5 mean:** 35.96 ± 20.43 µg/m³

**Output:** `data/raw/openaq/kandy_pm25_oct2018_sep2019.csv`

### 3. ERA5 Combination
**Combined meteorology:**
- Oct-Dec 2018: 2,208 hourly timesteps (already downloaded)
- Jan-Dec 2019: 8,760 hourly timesteps
- **Filtered:** 8,760 timesteps (Oct 2018 - Sep 2019)

**Output:** `data/raw/era5/kandy_era5_oct2018_sep2019.nc`

### 4. Pipeline Reprocessing
**Actions:**
1. Backed up old files:
   - `kandy_pm25_raw_2019_backup.csv`
   - `kandy_era5_2019_backup.nc`

2. Replaced raw files with new full-year datasets
3. Deleted old processed files
4. Reran pipeline: `python main.py --city kandy`
5. Reran full pipeline: `python main.py`

---

## Final Dataset Statistics

### Combined Dataset (Both Cities)
```
Total records:     89,195
Cities:            2
Stations:          24 (23 Medellin + 1 Kandy)
Temporal overlap:  365 days (Oct 2018 - Sep 2019)
Alignment:         PERFECT ✅
```

### Medellin (Oct 2018 - Sep 2019)
```
Records:           86,275 (hourly)
Stations:          23 (within 10km geomorphic core)
Date range:        2018-10-01 00:00 to 2019-09-30 23:00 UTC
Temporal coverage: 97.1%

PM2.5 Statistics:
  Mean:            21.06 ± 12.02 µg/m³
  Median:          19.00 µg/m³
  Range:           [0.0, 96.0] µg/m³
  > WHO AQG (15):  64.5%
  > WHO IT-1 (35): 12.3%

Meteorology:
  Wind speed:      0.83 ± 0.38 m/s
  Temperature:     19.29 ± 3.72 °C
  Rel. humidity:   80.12 ± 16.96%
  BLH:             370.01 ± 524.85 m
  Surface press.:  816.57 ± 1.44 hPa
```

### Kandy (Oct 2018 - Sep 2019) ✅ NEW
```
Records:           2,920 (3-hourly)
Stations:          1 (CAMS grid point, bias-corrected)
Date range:        2018-10-01 00:00 to 2019-09-30 21:00 UTC
Temporal coverage: 100.0%

PM2.5 Statistics:
  Mean:            35.96 ± 20.43 µg/m³  (was 32.96 before extension)
  Median:          29.68 µg/m³
  Range:           [1.4, 115.1] µg/m³
  > WHO AQG (15):  90.9%
  > WHO IT-1 (35): 40.3%

Meteorology:
  Wind speed:      1.83 ± 1.08 m/s
  Temperature:     23.85 ± 2.66 °C
  Rel. humidity:   82.72 ± 12.31%
  BLH:             449.70 ± 367.45 m
  Surface press.:  939.62 ± 1.82 hPa
```

---

## Transfer Learning Validation (Updated)

### Statistical Tests
| Test | Result | Interpretation |
|------|--------|----------------|
| **Kolmogorov-Smirnov** | stat=0.3424, p=3.82e-296 | Distributions differ significantly |
| **Mann-Whitney U** | U=65.9M, p≈0 | Kandy median > Medellin |
| **Cohen's d** | -1.20 | Large effect size (requires adaptation) |

### Pattern Similarity ⬆️ IMPROVED
| Metric | Score | Change | Quality |
|--------|-------|--------|---------|
| **Meteorology-PM2.5 correlation** | **0.9075** | +0.0288 | **Excellent** ✅ |
| **Seasonal cosine similarity** | **0.9726** | +0.0098 | **Excellent** ✅ |
| **Seasonal Pearson r** | 0.5591 | +0.0003 | Moderate |

### Transfer Learning Justification ✅ STRENGTHENED

**SUPPORTING factors:**
- ✅ **Excellent meteorology-PM2.5 relationship similarity (0.908)**
  - *Improved from 0.879 after temporal alignment*
- ✅ **Near-perfect seasonal pattern alignment (0.973)**
- ✅ Valley/basin topography affecting dispersion
- ✅ Tropical climate with comparable temperature ranges
- ✅ Similar boundary layer dynamics

**REQUIRES ADAPTATION:**
- ⚠️ Different absolute PM2.5 levels (+14.9 µg/m³ shift)
  - Cohen's d = -1.20 → PINN needs domain adaptation layer
- ⚠️ Different diurnal patterns
  - Temporal attention mechanism needed for 3-hourly vs hourly mismatch

**CONCLUSION:** Transfer learning is **statistically justified** and **strengthened** by perfect temporal alignment. Adaptation strategies are well-defined.

---

## PINN Readiness Checklist ✅

- [x] **Temporal alignment:** PERFECT (365 days overlap)
- [x] **All features present:** pm25, wind_speed, wind_direction, temperature_2m, relative_humidity, boundary_layer_height, surface_pressure
- [x] **Zero missing values:** All columns complete
- [x] **Data quality:** QC pipeline applied (5-stage cleaning + geographic filtering)
- [x] **Transfer learning justified:** 0.908 meteorology-PM2.5 similarity
- [x] **Files validated:** 89,195 records in combined dataset

**Status:** READY FOR PINN DEVELOPMENT 🚀

---

## Files Created/Updated

### New Files
```
data/raw/openaq/
  └── kandy_pm25_2018_oct_dec.csv          # 736 records (Oct-Dec 2018)
  └── kandy_pm25_oct2018_sep2019.csv       # 2,920 records (full year)

data/raw/era5/
  └── kandy_era5_oct2018_sep2019.nc        # 8,760 timesteps (full year)

data/raw/cams/
  └── kandy_cams_pm25_2018_oct_dec.nc      # Original NetCDF (reference)

Scripts:
  └── process_kandy_cams_data.py           # CAMS processing script
```

### Updated Files
```
data/raw/openaq/
  └── kandy_pm25_raw.csv                   # NOW: Oct 2018 - Sep 2019

data/raw/era5/
  └── kandy_era5_2019.nc                   # NOW: Oct 2018 - Sep 2019

data/processed/
  └── kandy_pm25_cleaned.csv               # UPDATED: 2,920 records
  └── kandy_era5_processed.csv             # UPDATED: 8,760 timesteps

data/final/
  └── kandy_pinn_dataset.csv               # UPDATED: 2,920 records
  └── combined_pinn_dataset.csv            # UPDATED: 89,195 records

outputs/reports/
  └── statistical_comparison.txt           # UPDATED: With aligned-period stats
  └── statistics_summary.csv               # UPDATED

outputs/figures/
  └── *.png (9 figures)                    # UPDATED: All visualizations regenerated
```

### Backup Files
```
data/raw/openaq/
  └── kandy_pm25_raw_2019_backup.csv       # Original 2019-only data

data/raw/era5/
  └── kandy_era5_2019_backup.nc            # Original 2019-only ERA5
```

---

## Commands Used

```bash
# 1. Process CAMS data
python process_kandy_cams_data.py

# 2. Backup old files
cp data/raw/openaq/kandy_pm25_raw.csv data/raw/openaq/kandy_pm25_raw_2019_backup.csv
cp data/raw/era5/kandy_era5_2019.nc data/raw/era5/kandy_era5_2019_backup.nc

# 3. Replace with new files
cp data/raw/openaq/kandy_pm25_oct2018_sep2019.csv data/raw/openaq/kandy_pm25_raw.csv
cp data/raw/era5/kandy_era5_oct2018_sep2019.nc data/raw/era5/kandy_era5_2019.nc

# 4. Delete old processed files
rm data/processed/kandy_*.csv
rm data/final/kandy_*.csv
rm data/final/combined_*.csv

# 5. Rerun pipeline
python main.py --city kandy  # Single-city processing
python main.py               # Full cross-city analysis
```

---

## Next Steps: PINN Development

### 1. Feature Engineering

**Meteorological Features:**
- `wind_speed`, `wind_direction` (advection)
- `temperature_2m`, `relative_humidity` (chemistry)
- `boundary_layer_height` (vertical mixing)
- `surface_pressure` (atmospheric stability)

**Temporal Features:**
- `hour` (0-23) for diurnal patterns
- `day_of_week` (0-6) for weekly cycles
- `month` (1-12) for seasonal patterns
- `day_of_year` (1-365) for continuous seasonality

**Spatial Features:**
- City encoding (one-hot or embedding)
- Elevation, lat/lon (geomorphology)

### 2. PINN Architecture

**Physics-Informed Components:**
```
1. Advection-Diffusion PDE:
   ∂C/∂t + u·∇C = ∇·(K∇C) + S - R

   Where:
   - C: PM2.5 concentration
   - u: wind velocity (u10, v10)
   - K: diffusion coefficient (f(BLH, stability))
   - S: source term (urban emissions)
   - R: removal term (deposition, chemistry)

2. Boundary Layer Constraint:
   - Vertical mixing limited by BLH
   - Temperature inversion effects

3. Valley Geometry:
   - Topographic channeling of flow
   - Stagnation under stable conditions
```

**Transfer Learning Components:**
```
1. Shared Encoder (Medellin pre-training):
   - Meteorology → Latent physics representation
   - Learns universal PM2.5-meteorology relationships

2. City-Specific Decoders:
   - Medellin decoder: Baseline ~21 µg/m³
   - Kandy decoder: Baseline ~36 µg/m³
   - Domain adaptation layer handles +15 µg/m³ shift

3. Temporal Attention:
   - Handles 3-hourly (Kandy) vs hourly (Medellin)
   - Learns to upscale/downscale temporal resolution
```

### 3. Training Strategy

**Phase 1: Pre-training on Medellin**
```
Data split:    80/20 (69,020 train / 17,255 val)
Epochs:        100-200
Loss:          MSE + Physics loss (PDE residuals)
Optimizer:     Adam (lr=1e-3, decay)
Early stop:    Validation loss plateau
```

**Phase 2: Transfer to Kandy**
```
Freeze:        Shared encoder (optional, test both)
Fine-tune:     Kandy decoder + domain adaptation
Data split:    80/20 (2,336 train / 584 val)
Epochs:        50-100
Loss:          MSE + Physics loss + Domain consistency
```

**Phase 3: Evaluation**
```
Metrics:
  - RMSE, MAE, R² on holdout sets
  - Physics loss (PDE residual magnitude)
  - Peak detection (diurnal cycle accuracy)
  - Seasonal pattern fidelity

Baselines:
  - Train Kandy from scratch (no transfer)
  - Train Kandy with frozen Medellin encoder
  - Train Kandy with unfrozen encoder

Ablation:
  - With/without physics loss
  - With/without domain adaptation
  - With/without temporal attention
```

### 4. Expected Outcomes

**Transfer Learning Benefits:**
- Reduced Kandy training data requirement (2.3K vs theoretical 20K+)
- Improved generalization on small Kandy dataset
- Faster convergence (~50 epochs vs ~200 from scratch)
- Better physics consistency (learned from larger Medellin dataset)

**Adaptation Challenges:**
- Baseline shift: +14.9 µg/m³ (Kandy > Medellin)
- Diurnal pattern differences (urban emissions timing)
- Temporal resolution mismatch (3-hourly vs hourly)

**Success Criteria:**
- Kandy RMSE < 15 µg/m³ (baseline: ~20 µg/m³ from naive model)
- Transfer learning improves RMSE by >20% vs from-scratch
- Physics loss < 0.1 (PDE residuals small)
- Diurnal peaks captured with <1 hour timing error

---

## Key Lessons Learned

1. **CAMS bias correction is critical** - Raw CAMS overestimated by 58% (54.5 → 34.5 µg/m³)
2. **Temporal alignment matters** - Met-PM2.5 correlation improved from 0.879 → 0.908
3. **Timezone handling** - Required `.tz_localize('UTC')` for consistent merging
4. **Windows encoding** - Remove Unicode characters (→, ✅, °) for cp1252 compatibility
5. **NetCDF flexibility** - CAMS file contained both PM2.5 and meteorology (unexpected but useful)

---

## Project Completion Status

| Component | Status | Records/Files |
|-----------|--------|---------------|
| Medellin data | ✅ COMPLETE | 86,275 records |
| Kandy data | ✅ COMPLETE | 2,920 records |
| Temporal alignment | ✅ PERFECT | 365 days overlap |
| Data QC | ✅ APPLIED | 5-stage cleaning |
| Geographic filtering | ✅ APPLIED | 10km/5km radius |
| Statistical validation | ✅ COMPLETE | Transfer learning justified |
| Visualizations | ✅ UPDATED | 9 figures |
| Documentation | ✅ UPDATED | All markdown files |
| **PINN readiness** | ✅ **READY** | **89,195 records** |

---

**Last Updated:** 2026-02-07 12:00 PM
**Pipeline Version:** v1.0
**Ready for:** PINN Model Development 🚀
