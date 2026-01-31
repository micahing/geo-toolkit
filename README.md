# Scientific Data Engineering Environment

A self-contained Python environment for scientific data engineering, focused on water and environmental data analysis. Designed for retrieving data from web APIs, storing and transforming data, and creating visualizations including geospatial maps.

## Quick Start

### Prerequisites

- **conda** or **mamba** (recommended: [Miniforge](https://github.com/conda-forge/miniforge))
- macOS or Linux

### Setup

1. **Clone or download this directory**

2. **Create the conda environment:**
   ```bash
   cd claude-dev
   conda env create -f environment.yml
   ```

   Or with mamba (faster):
   ```bash
   mamba env create -f environment.yml
   ```

3. **Activate the environment:**
   ```bash
   conda activate data-eng
   ```

4. **Configure API keys (optional):**
   ```bash
   cp config/api_config.example.yml config/api_config.yml
   # Edit config/api_config.yml with your API keys
   ```

5. **Start Jupyter:**
   ```bash
   jupyter lab
   ```

6. **Open `notebooks/getting_started.ipynb`** to begin.

## Directory Structure

```
.
├── environment.yml          # Conda environment definition
├── README.md               # This file
├── config/
│   └── api_config.example.yml  # API configuration template
├── data/
│   ├── raw/                # Raw data from APIs
│   ├── processed/          # Normalized/transformed data
│   └── outputs/            # Generated visualizations
├── notebooks/
│   ├── getting_started.ipynb   # Start here!
│   └── examples/
│       ├── data_retrieval_demo.ipynb
│       ├── visualization_demo.ipynb
│       └── geospatial_demo.ipynb
└── scripts/
    ├── data_retrieval/     # API clients (USGS, EPA, NOAA, generic)
    ├── data_storage/       # Parquet utilities
    ├── normalization/      # Data cleaning and transformation
    └── visualization/      # Plots, tables, and maps
```

## Features

### Data Retrieval

Built-in clients for environmental data APIs:

- **USGS Water Services** - Groundwater levels, stream discharge, water quality
- **EPA Water Quality Portal** - Water quality measurements from multiple agencies
- **NOAA Climate Data** - Weather and climate data (requires free API token)
- **Generic REST Client** - Template for any REST API

```python
from scripts.data_retrieval import USGSWaterServices

usgs = USGSWaterServices()
sites = usgs.get_colorado_basin_sites(basin="upper")
levels = usgs.get_groundwater_levels(state_code="CO")
```

### Data Storage

Parquet format for efficient, type-preserving storage:

```python
from scripts.data_storage import save_parquet, load_parquet, save_geoparquet

# Save DataFrame
save_parquet(df, "my_data")

# Load it back (types preserved!)
df = load_parquet("my_data")

# GeoParquet for spatial data
save_geoparquet(gdf, "sites_with_geometry")
```

### Data Normalization

Common transformations for environmental data:

```python
from scripts.normalization import normalize_water_data, convert_units

# Apply standard normalizations
df = normalize_water_data(raw_df, source='usgs')

# Unit conversions
df = convert_units(df, 'temp_f', 'fahrenheit', 'celsius', 'temp_c')
```

### Visualization

Plots, tables, and interactive maps:

```python
from scripts.visualization import time_series_plot, point_map, summary_table

# Time series with rolling average
time_series_plot(df, 'date', 'value', rolling_window=7)

# Interactive map
point_map(df, color_col='site_type', popup_cols=['site_id', 'value'])

# Summary statistics
summary_table(df, group_by='basin')
```

## Environment Management

### Update dependencies

Edit `environment.yml`, then:

```bash
conda env update -f environment.yml --prune
```

### Export current environment

To capture exact versions:

```bash
conda env export > environment-lock.yml
```

### Remove environment

```bash
conda deactivate
conda env remove -n data-eng
```

### Add a new package

```bash
conda activate data-eng
conda install -c conda-forge package_name
# Then add to environment.yml for reproducibility
```

## API Keys

Some data sources require API keys:

| Source | Key Required | How to Get |
|--------|--------------|------------|
| USGS Water Services | No | - |
| EPA Water Quality Portal | No | - |
| NOAA Climate Data | Yes | https://www.ncdc.noaa.gov/cdo-web/token |
| Mapbox (optional) | Yes | https://account.mapbox.com/ |

Store keys in `config/api_config.yml` (not tracked by git) or as environment variables:

```bash
export NOAA_API_TOKEN="your_token_here"
```

## Common Workflows

### 1. Retrieve and store groundwater data

```python
from scripts.data_retrieval import USGSWaterServices
from scripts.data_storage import save_parquet
from scripts.normalization import normalize_water_data

# Fetch data
usgs = USGSWaterServices()
raw_data = usgs.get_groundwater_levels(state_code="CO")

# Normalize
clean_data = normalize_water_data(raw_data, source='usgs')

# Store
save_parquet(clean_data, "colorado_groundwater")
```

### 2. Create a map of monitoring sites

```python
from scripts.data_storage import load_parquet
from scripts.normalization import standardize_coordinates
from scripts.visualization import point_map

# Load data
df = load_parquet("colorado_groundwater")

# Add geometry
gdf = standardize_coordinates(df, create_geometry=True)

# Create interactive map
m = point_map(gdf, color_col='site_type', save_path='data/outputs/sites.html')
```

### 3. Analyze time series

```python
from scripts.visualization import time_series_plot, histogram, summary_table

# Plot with trend
time_series_plot(df, 'date', 'value', rolling_window=30, show_trend=True)

# Distribution
histogram(df, 'value', show_stats=True)

# Summary by group
summary_table(df, columns=['value'], group_by='site')
```

## Troubleshooting

### GDAL installation issues

This environment uses conda specifically because it handles GDAL well. If you see GDAL errors:

```bash
conda activate data-eng
conda install -c conda-forge gdal --force-reinstall
```

### Jupyter kernel not found

Register the environment as a Jupyter kernel:

```bash
conda activate data-eng
python -m ipykernel install --user --name data-eng --display-name "Data Engineering"
```

### Slow conda environment creation

Use mamba instead:

```bash
conda install -n base -c conda-forge mamba
mamba env create -f environment.yml
```

## Contributing

When adding new functionality:

1. Add scripts to the appropriate `scripts/` subdirectory
2. Update the `__init__.py` exports
3. Add an example to the relevant demo notebook
4. Update `environment.yml` if new dependencies are needed

## License

This environment template is provided as-is for educational and research purposes.
