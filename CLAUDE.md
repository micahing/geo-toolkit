# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Scientific Data Engineering Environment - a Python framework for retrieving, processing, storing, and visualizing water and environmental data from multiple APIs. Uses Jupyter notebooks as the primary interface.

## Development Commands

```bash
# Environment setup
conda env create -f environment.yml
conda activate data-eng

# Alternative with mamba (faster)
mamba env create -f environment.yml

# Update dependencies after editing environment.yml
conda env update -f environment.yml --prune

# Code formatting
black scripts/

# Linting
ruff check scripts/
ruff check --fix scripts/

# Start development
jupyter lab
# Then open notebooks/getting_started.ipynb
```

## Architecture

### Data Flow

```
API Clients → Raw DataFrames → Normalization → Parquet Storage → Visualization
```

### Package Structure (`scripts/`)

Four layered modules in `scripts/`:

1. **data_retrieval/** - API clients (USGS, EPA, NOAA, Montana sources, generic REST)
   - All clients inherit common patterns from `RESTClient` base class
   - Return Pandas DataFrames with built-in rate limiting

2. **normalization/** - Data transformation utilities
   - `normalize_water_data()` - main entry point for standard cleaning
   - `standardize_coordinates()` - can create GeoPandas geometry column

3. **data_storage/** - Parquet utilities
   - `save_parquet()`/`load_parquet()` - type-preserving storage
   - `save_geoparquet()`/`load_geoparquet()` - spatial data with GeoParquet

4. **visualization/** - Three sub-modules
   - `plots.py` - matplotlib/seaborn (time series, histogram, scatter, box, heatmap)
   - `maps.py` - folium/geopandas (point maps, choropleths, heatmaps)
   - `tables.py` - pandas styled tables and summaries

### Data Directories

- `data/raw/` - Raw API responses
- `data/processed/` - Normalized data
- `data/outputs/` - Generated visualizations

### Configuration

API keys go in `config/api_config.yml` (copy from `config/api_config.example.yml`). Alternatively use environment variables (e.g., `NOAA_API_TOKEN`).

## Adding New Functionality

1. Add code to appropriate `scripts/[module]/` subdirectory
2. Export in `scripts/[module]/__init__.py`
3. Add usage example to relevant `notebooks/examples/` notebook
4. Update `environment.yml` if new dependencies needed
