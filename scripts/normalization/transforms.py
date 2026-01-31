"""
Data Normalization and Transformation Utilities

Common transformations for cleaning and standardizing water/environmental data.
"""

import pandas as pd
import numpy as np
import re
from typing import Optional, Union


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names to snake_case.

    Converts:
    - 'Site Name' -> 'site_name'
    - 'siteID' -> 'site_id'
    - 'MEASUREMENT_VALUE' -> 'measurement_value'

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with normalized column names
    """
    def to_snake_case(name: str) -> str:
        # Handle camelCase
        name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
        # Handle spaces and special chars
        name = re.sub(r'[\s\-\.]+', '_', name)
        # Remove non-alphanumeric
        name = re.sub(r'[^a-zA-Z0-9_]', '', name)
        # Lowercase and collapse multiple underscores
        name = re.sub(r'_+', '_', name.lower())
        # Remove leading/trailing underscores
        return name.strip('_')

    df = df.copy()
    df.columns = [to_snake_case(col) for col in df.columns]
    return df


def standardize_dates(
    df: pd.DataFrame,
    date_columns: Optional[list[str]] = None,
    output_format: Optional[str] = None,
    timezone: Optional[str] = None,
) -> pd.DataFrame:
    """
    Parse and standardize date columns.

    Args:
        df: Input DataFrame
        date_columns: Columns to parse as dates (auto-detects if None)
        output_format: Output format string (keeps as datetime if None)
        timezone: Target timezone (e.g., 'UTC', 'America/Denver')

    Returns:
        DataFrame with standardized dates
    """
    df = df.copy()

    # Auto-detect date columns if not specified
    if date_columns is None:
        date_columns = []
        date_keywords = ['date', 'time', 'timestamp', 'datetime', 'dt', 'created', 'updated']
        for col in df.columns:
            col_lower = col.lower()
            if any(kw in col_lower for kw in date_keywords):
                date_columns.append(col)

    for col in date_columns:
        if col not in df.columns:
            continue

        # Parse to datetime
        df[col] = pd.to_datetime(df[col], errors='coerce')

        # Convert timezone if specified
        if timezone and df[col].dt.tz is None:
            df[col] = df[col].dt.tz_localize('UTC').dt.tz_convert(timezone)
        elif timezone:
            df[col] = df[col].dt.tz_convert(timezone)

        # Convert to string format if specified
        if output_format:
            df[col] = df[col].dt.strftime(output_format)

    return df


def standardize_coordinates(
    df: pd.DataFrame,
    lat_col: str = 'latitude',
    lon_col: str = 'longitude',
    create_geometry: bool = False,
) -> Union[pd.DataFrame, "geopandas.GeoDataFrame"]:
    """
    Standardize coordinate columns and optionally create geometry.

    Args:
        df: Input DataFrame
        lat_col: Name of latitude column
        lon_col: Name of longitude column
        create_geometry: If True, returns GeoDataFrame with Point geometry

    Returns:
        DataFrame or GeoDataFrame with standardized coordinates
    """
    df = df.copy()

    # Common variations of lat/lon column names
    lat_variations = ['lat', 'latitude', 'y', 'lat_dd', 'dec_lat_va']
    lon_variations = ['lon', 'long', 'longitude', 'x', 'lng', 'long_dd', 'dec_long_va']

    # Find actual column names
    actual_lat = None
    actual_lon = None

    for col in df.columns:
        col_lower = col.lower()
        if actual_lat is None and col_lower in lat_variations:
            actual_lat = col
        if actual_lon is None and col_lower in lon_variations:
            actual_lon = col

    if actual_lat and actual_lat != lat_col:
        df[lat_col] = df[actual_lat]
    if actual_lon and actual_lon != lon_col:
        df[lon_col] = df[actual_lon]

    # Convert to numeric
    if lat_col in df.columns:
        df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
    if lon_col in df.columns:
        df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')

    # Validate coordinate ranges
    if lat_col in df.columns:
        invalid_lat = (df[lat_col] < -90) | (df[lat_col] > 90)
        if invalid_lat.any():
            print(f"Warning: {invalid_lat.sum()} invalid latitude values set to NaN")
            df.loc[invalid_lat, lat_col] = np.nan

    if lon_col in df.columns:
        invalid_lon = (df[lon_col] < -180) | (df[lon_col] > 180)
        if invalid_lon.any():
            print(f"Warning: {invalid_lon.sum()} invalid longitude values set to NaN")
            df.loc[invalid_lon, lon_col] = np.nan

    if create_geometry:
        import geopandas as gpd
        from shapely.geometry import Point

        # Create geometry only for valid coordinates
        valid_mask = df[lat_col].notna() & df[lon_col].notna()
        geometry = [
            Point(lon, lat) if valid else None
            for lon, lat, valid in zip(df[lon_col], df[lat_col], valid_mask)
        ]

        return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    return df


# Unit conversion factors
UNIT_CONVERSIONS = {
    # Length
    ('feet', 'meters'): 0.3048,
    ('meters', 'feet'): 3.28084,
    ('inches', 'mm'): 25.4,
    ('mm', 'inches'): 0.0393701,

    # Volume flow
    ('cfs', 'm3/s'): 0.0283168,  # cubic feet/sec to cubic meters/sec
    ('m3/s', 'cfs'): 35.3147,
    ('gpm', 'l/min'): 3.78541,   # gallons/min to liters/min

    # Temperature
    ('fahrenheit', 'celsius'): lambda f: (f - 32) * 5/9,
    ('celsius', 'fahrenheit'): lambda c: c * 9/5 + 32,

    # Concentration
    ('mg/l', 'ug/l'): 1000,
    ('ug/l', 'mg/l'): 0.001,
    ('ppm', 'mg/l'): 1.0,  # For dilute aqueous solutions
}


def convert_units(
    df: pd.DataFrame,
    column: str,
    from_unit: str,
    to_unit: str,
    new_column: Optional[str] = None,
) -> pd.DataFrame:
    """
    Convert measurement units.

    Args:
        df: Input DataFrame
        column: Column to convert
        from_unit: Source unit
        to_unit: Target unit
        new_column: Name for converted column (overwrites if None)

    Returns:
        DataFrame with converted values
    """
    df = df.copy()

    key = (from_unit.lower(), to_unit.lower())
    if key not in UNIT_CONVERSIONS:
        raise ValueError(f"Unknown conversion: {from_unit} to {to_unit}")

    factor = UNIT_CONVERSIONS[key]
    output_col = new_column or column

    if callable(factor):
        df[output_col] = df[column].apply(lambda x: factor(x) if pd.notna(x) else np.nan)
    else:
        df[output_col] = df[column] * factor

    return df


def handle_missing_values(
    df: pd.DataFrame,
    strategy: str = 'drop',
    fill_value: Optional[any] = None,
    numeric_fill: str = 'median',
    columns: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Handle missing values in DataFrame.

    Args:
        df: Input DataFrame
        strategy: 'drop', 'fill', or 'interpolate'
        fill_value: Value to use for 'fill' strategy
        numeric_fill: For numeric columns: 'mean', 'median', 'zero'
        columns: Specific columns to process (all if None)

    Returns:
        DataFrame with missing values handled
    """
    df = df.copy()

    if columns:
        subset = columns
    else:
        subset = df.columns.tolist()

    if strategy == 'drop':
        df = df.dropna(subset=subset)

    elif strategy == 'fill':
        if fill_value is not None:
            df[subset] = df[subset].fillna(fill_value)
        else:
            # Fill numeric columns based on numeric_fill strategy
            numeric_cols = df[subset].select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if numeric_fill == 'mean':
                    df[col] = df[col].fillna(df[col].mean())
                elif numeric_fill == 'median':
                    df[col] = df[col].fillna(df[col].median())
                elif numeric_fill == 'zero':
                    df[col] = df[col].fillna(0)

            # Fill non-numeric with 'Unknown'
            non_numeric = df[subset].select_dtypes(exclude=[np.number]).columns
            for col in non_numeric:
                df[col] = df[col].fillna('Unknown')

    elif strategy == 'interpolate':
        numeric_cols = df[subset].select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].interpolate(method='linear')

    return df


def normalize_water_data(
    df: pd.DataFrame,
    source: str = 'generic',
) -> pd.DataFrame:
    """
    Apply standard normalizations for water data from various sources.

    This is a convenience function that applies common transformations
    appropriate for water quality and quantity data.

    Args:
        df: Input DataFrame
        source: Data source ('usgs', 'epa', 'noaa', 'generic')

    Returns:
        Normalized DataFrame
    """
    df = df.copy()

    # Normalize column names
    df = normalize_column_names(df)

    # Standardize dates
    df = standardize_dates(df)

    # Standardize coordinates
    df = standardize_coordinates(df)

    # Source-specific normalizations
    if source == 'usgs':
        # USGS uses specific column names
        rename_map = {
            'site_no': 'site_id',
            'station_nm': 'site_name',
            'dec_lat_va': 'latitude',
            'dec_long_va': 'longitude',
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    elif source == 'epa':
        # EPA WQP normalizations
        rename_map = {
            'monitoringlocationidentifier': 'site_id',
            'monitoringlocationname': 'site_name',
            'activitystartdate': 'measurement_date',
            'resultmeasurevalue': 'value',
            'resultmeasure_measureunitcode': 'unit',
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    elif source == 'noaa':
        # NOAA normalizations
        if 'date' in df.columns:
            df = df.rename(columns={'date': 'measurement_date'})

    # Handle missing values (conservative approach)
    df = handle_missing_values(df, strategy='fill', numeric_fill='median')

    return df


# Example usage
if __name__ == "__main__":
    # Sample data with various issues
    data = {
        'Site Name': ['Station A', 'Station B', 'Station C'],
        'measurementDate': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'LAT': [39.7392, 40.0150, None],
        'LONG': [-104.9903, -105.2705, -106.0],
        'Water Temp (F)': [50.0, 55.0, 48.0],
        'Discharge_CFS': [100.0, None, 150.0],
    }
    df = pd.DataFrame(data)

    print("Original:")
    print(df)
    print()

    # Normalize
    df = normalize_column_names(df)
    print("After normalize_column_names:")
    print(df.columns.tolist())

    df = standardize_dates(df)
    df = standardize_coordinates(df)
    df = convert_units(df, 'water_temp_f', 'fahrenheit', 'celsius', 'water_temp_c')
    df = convert_units(df, 'discharge_cfs', 'cfs', 'm3/s', 'discharge_m3s')
    df = handle_missing_values(df, strategy='fill')

    print("\nFinal:")
    print(df)
