"""
Sample Data Generation for Offline Mode

Generates realistic synthetic data for testing and offline development.
Sample data mimics the structure and characteristics of real API responses
from USGS, EPA, Montana Mesonet, and other sources.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Any
import hashlib
import json


# Default sample data directory
SAMPLE_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "sample"


def _ensure_sample_dir():
    """Ensure the sample data directory exists."""
    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)


def generate_usgs_sites(
    n_sites: int = 50,
    state: str = "CO",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic USGS monitoring site data.

    Creates realistic site data matching USGS Water Services format.

    Args:
        n_sites: Number of sites to generate
        state: State code for site names
        seed: Random seed for reproducibility

    Returns:
        DataFrame with USGS-style site information
    """
    np.random.seed(seed)

    # State-specific coordinate ranges
    state_bounds = {
        "CO": {"lat": (37.0, 41.0), "lon": (-109.0, -102.0)},
        "AZ": {"lat": (31.3, 37.0), "lon": (-114.8, -109.0)},
        "UT": {"lat": (37.0, 42.0), "lon": (-114.0, -109.0)},
        "NV": {"lat": (35.0, 42.0), "lon": (-120.0, -114.0)},
        "MT": {"lat": (44.4, 49.0), "lon": (-116.0, -104.0)},
    }

    bounds = state_bounds.get(state, {"lat": (35.0, 45.0), "lon": (-115.0, -105.0)})

    # Water body name components
    water_names = [
        "Big", "Little", "North", "South", "East", "West", "Clear", "Muddy",
        "Blue", "Black", "Red", "Green", "White", "Sandy", "Rocky", "Bear",
        "Deer", "Eagle", "Elk", "Beaver", "Cottonwood", "Willow", "Pine",
    ]
    water_types = ["Creek", "River", "Brook", "Run", "Fork", "Branch", "Wash", "Gulch"]
    locations = ["at Bridge", "near Town", "below Dam", "at Gage", "at Highway",
                 "above Confluence", "below Reservoir", "at State Line"]

    sites = []
    for i in range(n_sites):
        site_no = f"{np.random.randint(1, 99):02d}{np.random.randint(100000, 999999)}"

        name_parts = [
            np.random.choice(water_names),
            np.random.choice(water_types),
            np.random.choice(locations),
        ]
        site_name = " ".join(name_parts) + f", {state}"

        sites.append({
            "agency_cd": "USGS",
            "site_no": site_no,
            "station_nm": site_name.upper(),
            "site_tp_cd": np.random.choice(["ST", "GW", "SP", "AT"], p=[0.6, 0.25, 0.1, 0.05]),
            "dec_lat_va": np.random.uniform(*bounds["lat"]),
            "dec_long_va": np.random.uniform(*bounds["lon"]),
            "coord_datum_cd": "NAD83",
            "alt_va": np.random.uniform(1000, 10000),
            "alt_datum_cd": "NAVD88",
            "huc_cd": f"14{np.random.randint(10000, 99999):05d}",
            "state_cd": state,
            "county_cd": f"{np.random.randint(1, 125):03d}",
        })

    return pd.DataFrame(sites)


def generate_groundwater_levels(
    n_records: int = 500,
    n_sites: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic groundwater level measurements.

    Creates time series data with realistic seasonal patterns and trends.

    Args:
        n_records: Total number of measurements
        n_sites: Number of unique sites
        start_date: Start of measurement period
        end_date: End of measurement period
        seed: Random seed for reproducibility

    Returns:
        DataFrame with groundwater level data
    """
    np.random.seed(seed)

    if start_date is None:
        start_date = datetime.now() - timedelta(days=365)
    if end_date is None:
        end_date = datetime.now()

    # Generate site IDs
    site_ids = [f"GW{np.random.randint(100000, 999999)}" for _ in range(n_sites)]

    records = []
    for _ in range(n_records):
        site_id = np.random.choice(site_ids)

        # Random date in range
        days_range = (end_date - start_date).days
        measurement_date = start_date + timedelta(days=np.random.randint(0, days_range))

        # Base depth with site-specific offset
        site_idx = site_ids.index(site_id)
        base_depth = 50 + site_idx * 10  # Different base depths per site

        # Add seasonal variation (deeper in summer, shallower in winter)
        day_of_year = measurement_date.timetuple().tm_yday
        seasonal = 5 * np.sin(2 * np.pi * day_of_year / 365)

        # Add some noise and long-term trend
        noise = np.random.normal(0, 2)
        trend = 0.01 * (measurement_date - start_date).days  # Slight decline

        depth = base_depth + seasonal + noise + trend

        records.append({
            "site_code": site_id,
            "site_name": f"Well {site_id}",
            "latitude": np.random.uniform(35, 42),
            "longitude": np.random.uniform(-115, -105),
            "datetime": measurement_date,
            "value": round(max(0, depth), 2),  # Depth can't be negative
            "unit": "ft",
            "parameter_name": "Depth to water level, feet below land surface",
            "parameter_code": "72019",
        })

    return pd.DataFrame(records)


def generate_water_quality_data(
    n_records: int = 200,
    n_sites: int = 15,
    parameters: Optional[list[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic water quality measurements.

    Creates data matching EPA Water Quality Portal format with
    realistic parameter distributions.

    Args:
        n_records: Total number of measurements
        n_sites: Number of unique monitoring locations
        parameters: List of parameters to include
        start_date: Start of measurement period
        end_date: End of measurement period
        seed: Random seed for reproducibility

    Returns:
        DataFrame with water quality data
    """
    np.random.seed(seed)

    if start_date is None:
        start_date = datetime.now() - timedelta(days=365)
    if end_date is None:
        end_date = datetime.now()

    if parameters is None:
        parameters = ["pH", "Temperature, water", "Dissolved oxygen (DO)",
                      "Specific conductance", "Turbidity"]

    # Parameter distributions (mean, std, unit)
    param_dists = {
        "pH": (7.5, 0.5, "None"),
        "Temperature, water": (15, 8, "deg C"),
        "Dissolved oxygen (DO)": (9, 2, "mg/L"),
        "Specific conductance": (500, 200, "uS/cm"),
        "Turbidity": (10, 15, "NTU"),
        "Nitrate": (2, 1.5, "mg/L"),
        "Phosphorus": (0.1, 0.08, "mg/L"),
        "Arsenic": (5, 3, "ug/L"),
    }

    # Generate site IDs
    site_ids = [f"WQP-{np.random.randint(10000, 99999)}" for _ in range(n_sites)]
    site_names = [f"Monitoring Site {i+1}" for i in range(n_sites)]
    site_coords = [(np.random.uniform(35, 42), np.random.uniform(-115, -105))
                   for _ in range(n_sites)]

    records = []
    for _ in range(n_records):
        site_idx = np.random.randint(0, n_sites)
        site_id = site_ids[site_idx]
        site_name = site_names[site_idx]
        lat, lon = site_coords[site_idx]

        param = np.random.choice(parameters)
        mean, std, unit = param_dists.get(param, (10, 5, "units"))

        # Random date in range
        days_range = (end_date - start_date).days
        measurement_date = start_date + timedelta(days=np.random.randint(0, days_range))

        value = max(0, np.random.normal(mean, std))
        if param == "pH":
            value = np.clip(value, 0, 14)

        records.append({
            "MonitoringLocationIdentifier": site_id,
            "MonitoringLocationName": site_name,
            "MonitoringLocationTypeName": np.random.choice(["River/Stream", "Lake", "Well"]),
            "LatitudeMeasure": lat,
            "LongitudeMeasure": lon,
            "ActivityStartDate": measurement_date.strftime("%Y-%m-%d"),
            "CharacteristicName": param,
            "ResultMeasureValue": round(value, 3),
            "ResultMeasure/MeasureUnitCode": unit,
            "ResultStatusIdentifier": "Final",
        })

    return pd.DataFrame(records)


def generate_mesonet_stations(
    n_stations: int = 30,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic Montana Mesonet station data.

    Creates station metadata matching Montana Mesonet API format.

    Args:
        n_stations: Number of stations to generate
        seed: Random seed for reproducibility

    Returns:
        DataFrame with Mesonet station information
    """
    np.random.seed(seed)

    # Montana county names
    counties = [
        "Gallatin", "Yellowstone", "Missoula", "Cascade", "Lewis and Clark",
        "Flathead", "Ravalli", "Silver Bow", "Lake", "Lincoln",
        "Park", "Carbon", "Stillwater", "Big Horn", "Rosebud",
    ]

    # Station name prefixes
    prefixes = ["ace", "agr", "hyd", "met"]

    stations = []
    for i in range(n_stations):
        county = np.random.choice(counties)
        station_id = f"{np.random.choice(prefixes)}{county[:4].lower()}{i:02d}"

        stations.append({
            "station": station_id,
            "name": f"{county} Station {i+1}",
            "county": county,
            "latitude": np.random.uniform(44.5, 49.0),
            "longitude": np.random.uniform(-116.0, -104.0),
            "elevation": np.random.uniform(800, 2500),
            "network": np.random.choice(["agrinet", "hydromet"], p=[0.7, 0.3]),
            "active": np.random.choice([True, False], p=[0.9, 0.1]),
            "date_installed": (datetime.now() - timedelta(days=np.random.randint(365, 3650))).strftime("%Y-%m-%d"),
        })

    return pd.DataFrame(stations)


def generate_mesonet_observations(
    stations: pd.DataFrame,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    frequency: str = "hourly",
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic Mesonet weather observations.

    Creates time series with realistic diurnal and seasonal patterns.

    Args:
        stations: DataFrame of stations (from generate_mesonet_stations)
        start_date: Start of observation period
        end_date: End of observation period
        frequency: 'hourly' or 'daily'
        seed: Random seed for reproducibility

    Returns:
        DataFrame with weather observations
    """
    np.random.seed(seed)

    if start_date is None:
        start_date = datetime.now() - timedelta(days=7)
    if end_date is None:
        end_date = datetime.now()

    active_stations = stations[stations['active'] == True]['station'].tolist()

    records = []

    if frequency == "hourly":
        dates = pd.date_range(start_date, end_date, freq='H')
    else:
        dates = pd.date_range(start_date, end_date, freq='D')

    for station in active_stations:
        station_data = stations[stations['station'] == station].iloc[0]
        elevation = station_data['elevation']

        # Base temperature varies with elevation
        base_temp = 15 - (elevation - 1000) * 0.006  # ~6°C per 1000m

        for dt in dates:
            # Seasonal variation
            day_of_year = dt.timetuple().tm_yday
            seasonal = 15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)

            # Diurnal variation (for hourly data)
            if frequency == "hourly":
                hour = dt.hour
                diurnal = 8 * np.sin(2 * np.pi * (hour - 6) / 24)
            else:
                diurnal = 0

            # Add noise
            noise = np.random.normal(0, 2)

            temp = base_temp + seasonal + diurnal + noise

            record = {
                "station": station,
                "datetime" if frequency == "hourly" else "date": dt,
                "air_temp": round(temp, 1),
                "relative_humidity": round(np.clip(np.random.normal(60, 20), 10, 100), 1),
                "wind_speed": round(max(0, np.random.exponential(3)), 1),
                "wind_direction": np.random.randint(0, 360),
                "ppt": round(max(0, np.random.exponential(0.1)), 2),
                "solar_radiation": round(max(0, 500 * max(0, np.sin(2 * np.pi * (dt.hour - 6) / 24)) + np.random.normal(0, 50)), 1) if frequency == "hourly" else None,
            }

            if frequency == "daily":
                record["air_temp_max"] = round(temp + np.random.uniform(5, 10), 1)
                record["air_temp_min"] = round(temp - np.random.uniform(5, 10), 1)
                del record["solar_radiation"]

            records.append(record)

    return pd.DataFrame(records)


def get_or_generate(
    name: str,
    generator_func: Callable[..., pd.DataFrame],
    force_regenerate: bool = False,
    **kwargs: Any,
) -> pd.DataFrame:
    """
    Get cached sample data or generate if not exists.

    Caches generated data to parquet files for faster subsequent loads.

    Args:
        name: Name for the cached dataset
        generator_func: Function to generate the data
        force_regenerate: If True, regenerate even if cached version exists
        **kwargs: Arguments to pass to generator function

    Returns:
        DataFrame with sample data

    Example:
        >>> sites = get_or_generate('usgs_sites', generate_usgs_sites, n_sites=100)
    """
    _ensure_sample_dir()

    # Create a hash of the kwargs for cache invalidation
    kwargs_hash = hashlib.md5(json.dumps(kwargs, sort_keys=True, default=str).encode()).hexdigest()[:8]
    cache_path = SAMPLE_DATA_DIR / f"{name}_{kwargs_hash}.parquet"

    if cache_path.exists() and not force_regenerate:
        return pd.read_parquet(cache_path)

    # Generate and cache
    df = generator_func(**kwargs)
    df.to_parquet(cache_path, index=False)

    return df


def clear_sample_cache():
    """Clear all cached sample data files."""
    _ensure_sample_dir()
    for f in SAMPLE_DATA_DIR.glob("*.parquet"):
        f.unlink()
    print(f"Cleared sample data cache at {SAMPLE_DATA_DIR}")


# Convenience function to generate a complete sample dataset
def generate_sample_dataset(
    seed: int = 42,
) -> dict[str, pd.DataFrame]:
    """
    Generate a complete set of sample data for all data sources.

    Returns:
        Dict with DataFrames for each data type
    """
    np.random.seed(seed)

    usgs_sites = generate_usgs_sites(n_sites=50, state="CO", seed=seed)
    groundwater = generate_groundwater_levels(n_records=500, seed=seed)
    water_quality = generate_water_quality_data(n_records=300, seed=seed)
    mesonet_stations = generate_mesonet_stations(n_stations=30, seed=seed)
    mesonet_obs = generate_mesonet_observations(
        mesonet_stations,
        start_date=datetime.now() - timedelta(days=7),
        frequency="daily",
        seed=seed
    )

    return {
        "usgs_sites": usgs_sites,
        "groundwater_levels": groundwater,
        "water_quality": water_quality,
        "mesonet_stations": mesonet_stations,
        "mesonet_observations": mesonet_obs,
    }


# Example usage
if __name__ == "__main__":
    print("=== Sample Data Generation ===\n")

    # Generate USGS sites
    sites = generate_usgs_sites(n_sites=10, state="CO")
    print(f"Generated {len(sites)} USGS sites:")
    print(sites[['site_no', 'station_nm', 'site_tp_cd']].head())

    print("\n" + "="*50 + "\n")

    # Generate groundwater levels
    gw = generate_groundwater_levels(n_records=100)
    print(f"Generated {len(gw)} groundwater measurements:")
    print(gw[['site_code', 'datetime', 'value']].head())

    print("\n" + "="*50 + "\n")

    # Generate water quality data
    wq = generate_water_quality_data(n_records=50)
    print(f"Generated {len(wq)} water quality measurements:")
    print(wq[['MonitoringLocationIdentifier', 'CharacteristicName', 'ResultMeasureValue']].head())

    print("\n" + "="*50 + "\n")

    # Generate Mesonet data
    stations = generate_mesonet_stations(n_stations=5)
    print(f"Generated {len(stations)} Mesonet stations:")
    print(stations[['station', 'name', 'county']].head())

    obs = generate_mesonet_observations(stations, frequency="daily")
    print(f"\nGenerated {len(obs)} daily observations")

    print("\n" + "="*50 + "\n")

    # Test caching
    cached = get_or_generate('test_sites', generate_usgs_sites, n_sites=5)
    print(f"Cached dataset: {len(cached)} rows")
