"""
Unit tests for Parquet storage utilities.

Tests save/load roundtrips, type preservation, and compression options.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

from scripts.data_storage.parquet_utils import (
    save_parquet,
    load_parquet,
    save_geoparquet,
    load_geoparquet,
    list_datasets,
    parquet_info,
)


class TestSaveLoadParquet:
    """Tests for save_parquet and load_parquet functions."""

    @pytest.mark.unit
    def test_basic_roundtrip(self, sample_water_data, temp_data_dir):
        """Basic save and load preserves data."""
        path = save_parquet(sample_water_data, 'test_data', data_dir=temp_data_dir)
        loaded = load_parquet('test_data', data_dir=temp_data_dir)

        assert len(loaded) == len(sample_water_data)
        assert list(loaded.columns) == list(sample_water_data.columns)

    @pytest.mark.unit
    def test_preserves_numeric_types(self, temp_data_dir):
        """Numeric types are preserved."""
        df = pd.DataFrame({
            'int_col': pd.array([1, 2, 3], dtype='int64'),
            'float_col': pd.array([1.1, 2.2, 3.3], dtype='float64'),
        })
        save_parquet(df, 'numeric_test', data_dir=temp_data_dir)
        loaded = load_parquet('numeric_test', data_dir=temp_data_dir)

        assert loaded['int_col'].dtype == np.int64
        assert loaded['float_col'].dtype == np.float64

    @pytest.mark.unit
    def test_preserves_datetime_types(self, temp_data_dir):
        """Datetime types are preserved."""
        df = pd.DataFrame({
            'date_col': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
        })
        save_parquet(df, 'datetime_test', data_dir=temp_data_dir)
        loaded = load_parquet('datetime_test', data_dir=temp_data_dir)

        assert pd.api.types.is_datetime64_any_dtype(loaded['date_col'])

    @pytest.mark.unit
    def test_preserves_string_types(self, temp_data_dir):
        """String types are preserved."""
        df = pd.DataFrame({
            'str_col': ['a', 'b', 'c'],
        })
        save_parquet(df, 'string_test', data_dir=temp_data_dir)
        loaded = load_parquet('string_test', data_dir=temp_data_dir)

        # Parquet may return object, string, or str dtype depending on version
        dtype_str = str(loaded['str_col'].dtype).lower()
        assert dtype_str in ('object', 'string', 'str', 'string[python]') or 'string' in dtype_str

    @pytest.mark.unit
    def test_preserves_categorical_types(self, temp_data_dir):
        """Categorical types are preserved."""
        df = pd.DataFrame({
            'cat_col': pd.Categorical(['a', 'b', 'a', 'c']),
        })
        save_parquet(df, 'categorical_test', data_dir=temp_data_dir)
        loaded = load_parquet('categorical_test', data_dir=temp_data_dir)

        # Parquet preserves categorical
        assert loaded['cat_col'].dtype.name == 'category'

    @pytest.mark.unit
    def test_handles_null_values(self, temp_data_dir):
        """Null values are preserved."""
        df = pd.DataFrame({
            'col_with_nulls': [1.0, None, 3.0, None, 5.0],
        })
        save_parquet(df, 'nulls_test', data_dir=temp_data_dir)
        loaded = load_parquet('nulls_test', data_dir=temp_data_dir)

        assert pd.isna(loaded['col_with_nulls'].iloc[1])
        assert pd.isna(loaded['col_with_nulls'].iloc[3])

    @pytest.mark.unit
    def test_compression_snappy(self, sample_water_data, temp_data_dir):
        """Snappy compression works."""
        path = save_parquet(sample_water_data, 'snappy_test', data_dir=temp_data_dir, compression='snappy')
        assert path.exists()
        loaded = load_parquet('snappy_test', data_dir=temp_data_dir)
        assert len(loaded) == len(sample_water_data)

    @pytest.mark.unit
    def test_compression_gzip(self, sample_water_data, temp_data_dir):
        """Gzip compression works."""
        path = save_parquet(sample_water_data, 'gzip_test', data_dir=temp_data_dir, compression='gzip')
        assert path.exists()
        loaded = load_parquet('gzip_test', data_dir=temp_data_dir)
        assert len(loaded) == len(sample_water_data)

    @pytest.mark.unit
    def test_timestamp_in_filename(self, sample_water_data, temp_data_dir):
        """Timestamp can be added to filename."""
        path = save_parquet(sample_water_data, 'ts_test', data_dir=temp_data_dir, add_timestamp=True)
        # Filename should contain underscore followed by timestamp pattern
        assert 'ts_test_' in path.name
        assert path.exists()

    @pytest.mark.unit
    def test_load_specific_columns(self, sample_water_data, temp_data_dir):
        """Load only specific columns."""
        save_parquet(sample_water_data, 'columns_test', data_dir=temp_data_dir)
        loaded = load_parquet('columns_test', data_dir=temp_data_dir, columns=['site_id', 'ph'])

        assert 'site_id' in loaded.columns
        assert 'ph' in loaded.columns
        assert 'temperature_c' not in loaded.columns

    @pytest.mark.unit
    def test_load_with_extension(self, sample_water_data, temp_data_dir):
        """Load works with or without .parquet extension."""
        save_parquet(sample_water_data, 'ext_test', data_dir=temp_data_dir)

        loaded1 = load_parquet('ext_test', data_dir=temp_data_dir)
        loaded2 = load_parquet('ext_test.parquet', data_dir=temp_data_dir)

        assert len(loaded1) == len(loaded2)

    @pytest.mark.unit
    def test_partitioned_save(self, temp_data_dir):
        """Partitioned save creates directory structure."""
        df = pd.DataFrame({
            'value': [1, 2, 3, 4],
            'year': [2023, 2023, 2024, 2024],
            'state': ['CO', 'AZ', 'CO', 'AZ'],
        })
        path = save_parquet(df, 'partitioned_test', data_dir=temp_data_dir, partition_cols=['year'])

        # Should create a directory
        assert path.is_dir()
        # With year partitions
        assert (path / 'year=2023').exists() or list(path.glob('**/year=2023'))

    @pytest.mark.unit
    def test_creates_parent_directories(self, temp_data_dir):
        """Creates parent directories if they don't exist."""
        nested_dir = temp_data_dir / 'nested' / 'deep' / 'path'
        df = pd.DataFrame({'value': [1, 2, 3]})
        path = save_parquet(df, 'nested_test', data_dir=nested_dir)
        assert path.exists()


class TestGeoParquet:
    """Tests for GeoParquet save/load functions."""

    @pytest.mark.unit
    def test_geoparquet_roundtrip(self, sample_geodataframe, temp_data_dir):
        """GeoDataFrame save and load preserves geometry."""
        path = save_geoparquet(sample_geodataframe, 'geo_test', data_dir=temp_data_dir)
        loaded = load_geoparquet('geo_test', data_dir=temp_data_dir)

        import geopandas as gpd
        assert isinstance(loaded, gpd.GeoDataFrame)
        assert loaded.geometry is not None
        assert len(loaded) == len(sample_geodataframe)

    @pytest.mark.unit
    def test_preserves_crs(self, sample_geodataframe, temp_data_dir):
        """CRS is preserved in GeoParquet."""
        save_geoparquet(sample_geodataframe, 'crs_test', data_dir=temp_data_dir)
        loaded = load_geoparquet('crs_test', data_dir=temp_data_dir)

        assert loaded.crs is not None
        assert loaded.crs.to_epsg() == 4326

    @pytest.mark.unit
    def test_preserves_geometry_type(self, sample_geodataframe, temp_data_dir):
        """Geometry type is preserved."""
        save_geoparquet(sample_geodataframe, 'geom_type_test', data_dir=temp_data_dir)
        loaded = load_geoparquet('geom_type_test', data_dir=temp_data_dir)

        # Should all be points
        assert all(loaded.geometry.geom_type == 'Point')

    @pytest.mark.unit
    def test_preserves_attributes(self, sample_geodataframe, temp_data_dir):
        """Non-geometry attributes are preserved."""
        save_geoparquet(sample_geodataframe, 'attrs_test', data_dir=temp_data_dir)
        loaded = load_geoparquet('attrs_test', data_dir=temp_data_dir)

        assert 'site_id' in loaded.columns
        assert 'ph' in loaded.columns


class TestListDatasets:
    """Tests for list_datasets function."""

    @pytest.mark.unit
    def test_lists_parquet_files(self, sample_water_data, temp_data_dir):
        """Lists all Parquet files in directory."""
        save_parquet(sample_water_data, 'dataset1', data_dir=temp_data_dir)
        save_parquet(sample_water_data, 'dataset2', data_dir=temp_data_dir)

        datasets = list_datasets(data_dir=temp_data_dir)
        names = [d['name'] for d in datasets]

        assert 'dataset1' in names
        assert 'dataset2' in names

    @pytest.mark.unit
    def test_includes_size_info(self, sample_water_data, temp_data_dir):
        """Dataset info includes size."""
        save_parquet(sample_water_data, 'size_test', data_dir=temp_data_dir)
        datasets = list_datasets(data_dir=temp_data_dir)

        assert len(datasets) > 0
        assert 'size_mb' in datasets[0]
        assert datasets[0]['size_mb'] > 0

    @pytest.mark.unit
    def test_includes_modified_time(self, sample_water_data, temp_data_dir):
        """Dataset info includes modification time."""
        save_parquet(sample_water_data, 'time_test', data_dir=temp_data_dir)
        datasets = list_datasets(data_dir=temp_data_dir)

        assert len(datasets) > 0
        assert 'modified' in datasets[0]
        assert isinstance(datasets[0]['modified'], datetime)


class TestParquetInfo:
    """Tests for parquet_info function."""

    @pytest.mark.unit
    def test_returns_row_count(self, sample_water_data, temp_data_dir):
        """Returns correct row count."""
        save_parquet(sample_water_data, 'info_test', data_dir=temp_data_dir)
        info = parquet_info('info_test', data_dir=temp_data_dir)

        assert info['num_rows'] == len(sample_water_data)

    @pytest.mark.unit
    def test_returns_column_count(self, sample_water_data, temp_data_dir):
        """Returns correct column count."""
        save_parquet(sample_water_data, 'cols_test', data_dir=temp_data_dir)
        info = parquet_info('cols_test', data_dir=temp_data_dir)

        assert info['num_columns'] == len(sample_water_data.columns)

    @pytest.mark.unit
    def test_returns_schema(self, temp_data_dir):
        """Returns schema information."""
        df = pd.DataFrame({
            'int_col': [1, 2, 3],
            'str_col': ['a', 'b', 'c'],
        })
        save_parquet(df, 'schema_test', data_dir=temp_data_dir)
        info = parquet_info('schema_test', data_dir=temp_data_dir)

        assert 'schema' in info
        assert len(info['schema']) == 2

        schema_names = [f['name'] for f in info['schema']]
        assert 'int_col' in schema_names
        assert 'str_col' in schema_names
