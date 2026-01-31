"""
Shared test fixtures for the data engineering test suite.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def sample_water_data():
    """Basic water quality DataFrame for general testing."""
    np.random.seed(42)
    n_records = 50

    return pd.DataFrame({
        'site_id': [f'SITE_{i:03d}' for i in range(n_records)],
        'site_name': [f'Test Station {i}' for i in range(n_records)],
        'measurement_date': pd.date_range('2024-01-01', periods=n_records, freq='D'),
        'latitude': np.random.uniform(35, 42, n_records),
        'longitude': np.random.uniform(-115, -105, n_records),
        'ph': np.random.uniform(6.5, 8.5, n_records),
        'temperature_c': np.random.uniform(5, 25, n_records),
        'dissolved_oxygen': np.random.uniform(6, 12, n_records),
        'turbidity': np.random.exponential(5, n_records),
        'category': np.random.choice(['High', 'Medium', 'Low'], n_records),
    })


@pytest.fixture
def sample_geodataframe(sample_water_data):
    """GeoDataFrame with point geometry."""
    import geopandas as gpd
    from shapely.geometry import Point

    geometry = [
        Point(lon, lat)
        for lon, lat in zip(sample_water_data['longitude'], sample_water_data['latitude'])
    ]

    return gpd.GeoDataFrame(
        sample_water_data,
        geometry=geometry,
        crs="EPSG:4326"
    )


@pytest.fixture
def sample_timeseries_data():
    """Time series data for visualization testing."""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')

    return pd.DataFrame({
        'date': dates,
        'value': np.cumsum(np.random.randn(100)) + 50,
        'value2': np.cumsum(np.random.randn(100)) + 30,
        'category': np.random.choice(['A', 'B', 'C'], 100),
    })


@pytest.fixture
def usgs_style_dataframe():
    """DataFrame in USGS format for normalization testing."""
    return pd.DataFrame({
        'Site Name': ['Station A', 'Station B', 'Station C'],
        'site_no': ['01234567', '01234568', '01234569'],
        'station_nm': ['Big River at Bridge', 'Small Creek nr Town', 'Lake Outlet'],
        'dec_lat_va': [39.7392, 40.0150, 38.8339],
        'dec_long_va': [-104.9903, -105.2705, -104.8214],
        'measurementDate': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'Water Temp (F)': [50.0, 55.0, 48.0],
        'Discharge_CFS': [100.0, None, 150.0],
    })


@pytest.fixture
def epa_style_dataframe():
    """DataFrame in EPA WQP format for normalization testing."""
    return pd.DataFrame({
        'MonitoringLocationIdentifier': ['EPA-001', 'EPA-002', 'EPA-003'],
        'MonitoringLocationName': ['Site Alpha', 'Site Beta', 'Site Gamma'],
        'ActivityStartDate': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'ResultMeasureValue': [7.2, 7.5, 6.9],
        'ResultMeasure/MeasureUnitCode': ['mg/L', 'mg/L', 'mg/L'],
        'LatitudeMeasure': [39.5, 40.1, 38.9],
        'LongitudeMeasure': [-105.0, -105.5, -104.5],
    })


@pytest.fixture
def temp_data_dir():
    """Temporary directory for I/O tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_usgs_json_response():
    """Mock USGS JSON API response for time series data."""
    return {
        "value": {
            "timeSeries": [
                {
                    "sourceInfo": {
                        "siteName": "Test River at Test Bridge",
                        "siteCode": [{"value": "09380000"}],
                        "geoLocation": {
                            "geogLocation": {
                                "latitude": 36.8619,
                                "longitude": -111.5879
                            }
                        }
                    },
                    "variable": {
                        "variableName": "Streamflow, ft³/s",
                        "variableCode": [{"value": "00060"}],
                        "unit": {"unitCode": "ft3/s"}
                    },
                    "values": [
                        {
                            "value": [
                                {"dateTime": "2024-01-01T00:00:00.000-07:00", "value": "500", "qualifiers": ["A"]},
                                {"dateTime": "2024-01-02T00:00:00.000-07:00", "value": "520", "qualifiers": ["A"]},
                                {"dateTime": "2024-01-03T00:00:00.000-07:00", "value": "510", "qualifiers": ["A"]},
                            ]
                        }
                    ]
                }
            ]
        }
    }


@pytest.fixture
def mock_usgs_rdb_response():
    """Mock USGS RDB (tab-delimited) response for site data."""
    return """#
# US Geological Survey
# retrieved: 2024-01-15
#
agency_cd	site_no	station_nm	dec_lat_va	dec_long_va	alt_va	huc_cd	site_tp_cd
5s	15s	50s	16s	16s	8s	16s	7s
USGS	09380000	COLORADO RIVER AT LEES FERRY, AZ	36.8619444	-111.5879167	3107.06	14070006	ST
USGS	09402500	COLORADO RIVER NEAR GRAND CANYON, AZ	36.1069444	-112.0955556	2425.1	15010001	ST
USGS	09421500	COLORADO RIVER BELOW HOOVER DAM, AZ-NV	36.0116667	-114.7394444	505.22	15010015	ST"""


@pytest.fixture
def mock_epa_csv_response():
    """Mock EPA WQP CSV response."""
    return """OrganizationIdentifier,OrganizationFormalName,MonitoringLocationIdentifier,MonitoringLocationName,MonitoringLocationTypeName,HUCEightDigitCode,LatitudeMeasure,LongitudeMeasure
EPA-CO,Colorado EPA,CO-001,Bear Creek at Highway 74,River/Stream,14010001,39.6456,-105.2369
EPA-CO,Colorado EPA,CO-002,Clear Creek at Golden,River/Stream,14010001,39.7561,-105.2211
EPA-CO,Colorado EPA,CO-003,South Platte at Denver,River/Stream,10190002,39.7553,-104.9872"""


@pytest.fixture
def mock_mesonet_stations_response():
    """Mock Montana Mesonet stations API response."""
    return [
        {
            "station": "aceabsar",
            "name": "Absarokee",
            "county": "Stillwater",
            "latitude": 45.5428,
            "longitude": -109.4128,
            "elevation": 1213,
            "network": "agrinet",
            "active": True,
        },
        {
            "station": "aceamste",
            "name": "Amsterdam",
            "county": "Gallatin",
            "latitude": 45.7489,
            "longitude": -111.3892,
            "elevation": 1472,
            "network": "agrinet",
            "active": True,
        },
    ]


@pytest.fixture
def mock_mesonet_observations_response():
    """Mock Montana Mesonet observations API response."""
    return [
        {
            "station": "aceabsar",
            "datetime": "2024-01-01T12:00:00Z",
            "air_temp": 5.2,
            "relative_humidity": 65.0,
            "wind_speed": 3.5,
            "ppt": 0.0,
        },
        {
            "station": "aceabsar",
            "datetime": "2024-01-01T13:00:00Z",
            "air_temp": 6.1,
            "relative_humidity": 62.0,
            "wind_speed": 4.2,
            "ppt": 0.0,
        },
    ]


@pytest.fixture
def sample_polygon_geodataframe():
    """GeoDataFrame with polygon geometry for choropleth testing."""
    import geopandas as gpd
    from shapely.geometry import box

    # Create a grid of polygons
    polygons = []
    values = []
    names = []

    for i in range(3):
        for j in range(3):
            x_min = -115 + i * 3
            y_min = 35 + j * 2
            polygons.append(box(x_min, y_min, x_min + 3, y_min + 2))
            values.append(np.random.uniform(10, 100))
            names.append(f'Region_{i}_{j}')

    gdf = gpd.GeoDataFrame({
        'name': names,
        'value': values,
        'geometry': polygons,
    }, crs="EPSG:4326")
    # Set index name for choropleth compatibility
    gdf.index.name = 'id'
    return gdf


@pytest.fixture
def dataframe_with_missing_values():
    """DataFrame with various missing value patterns."""
    return pd.DataFrame({
        'id': [1, 2, 3, 4, 5],
        'numeric_col': [1.0, None, 3.0, None, 5.0],
        'string_col': ['a', None, 'c', 'd', None],
        'date_col': ['2024-01-01', '2024-01-02', None, '2024-01-04', '2024-01-05'],
    })


@pytest.fixture
def column_name_variations_df():
    """DataFrame with various column naming conventions."""
    return pd.DataFrame({
        'Site Name': [1],
        'siteID': [2],
        'MEASUREMENT_VALUE': [3],
        'camelCaseColumn': [4],
        'snake_case_column': [5],
        'Column With  Multiple   Spaces': [6],
        'column.with.dots': [7],
        'column-with-dashes': [8],
    })
