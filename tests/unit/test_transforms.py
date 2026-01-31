"""
Unit tests for data transformation functions.

These test pure functions with no external dependencies.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from scripts.normalization.transforms import (
    normalize_column_names,
    standardize_dates,
    standardize_coordinates,
    convert_units,
    handle_missing_values,
    normalize_water_data,
    UNIT_CONVERSIONS,
)


class TestNormalizeColumnNames:
    """Tests for normalize_column_names function."""

    @pytest.mark.unit
    def test_spaces_to_snake_case(self):
        """Converts spaces to underscores."""
        df = pd.DataFrame({'Site Name': [1], 'Water Temp': [2]})
        result = normalize_column_names(df)
        assert 'site_name' in result.columns
        assert 'water_temp' in result.columns

    @pytest.mark.unit
    def test_camel_case_to_snake_case(self):
        """Converts camelCase to snake_case."""
        df = pd.DataFrame({'siteID': [1], 'waterTemperature': [2]})
        result = normalize_column_names(df)
        assert 'site_id' in result.columns
        assert 'water_temperature' in result.columns

    @pytest.mark.unit
    def test_uppercase_to_lowercase(self):
        """Converts UPPERCASE to lowercase."""
        df = pd.DataFrame({'SITE_NAME': [1], 'VALUE': [2]})
        result = normalize_column_names(df)
        assert 'site_name' in result.columns
        assert 'value' in result.columns

    @pytest.mark.unit
    def test_special_characters_removed(self):
        """Removes special characters."""
        df = pd.DataFrame({'Site@Name!': [1], 'Value#123': [2]})
        result = normalize_column_names(df)
        assert 'sitename' in result.columns
        assert 'value123' in result.columns

    @pytest.mark.unit
    def test_multiple_underscores_collapsed(self):
        """Collapses multiple underscores."""
        df = pd.DataFrame({'site__name': [1], 'value___test': [2]})
        result = normalize_column_names(df)
        assert 'site_name' in result.columns
        assert 'value_test' in result.columns

    @pytest.mark.unit
    def test_dots_to_underscores(self):
        """Converts dots to underscores."""
        df = pd.DataFrame({'site.name': [1], 'value.test': [2]})
        result = normalize_column_names(df)
        assert 'site_name' in result.columns
        assert 'value_test' in result.columns

    @pytest.mark.unit
    def test_dashes_to_underscores(self):
        """Converts dashes to underscores."""
        df = pd.DataFrame({'site-name': [1], 'value-test': [2]})
        result = normalize_column_names(df)
        assert 'site_name' in result.columns
        assert 'value_test' in result.columns

    @pytest.mark.unit
    def test_leading_trailing_underscores_removed(self):
        """Removes leading and trailing underscores."""
        df = pd.DataFrame({'_site_name_': [1], '__value__': [2]})
        result = normalize_column_names(df)
        assert 'site_name' in result.columns
        assert 'value' in result.columns

    @pytest.mark.unit
    def test_does_not_modify_original(self):
        """Original DataFrame is not modified."""
        df = pd.DataFrame({'Site Name': [1]})
        original_columns = list(df.columns)
        normalize_column_names(df)
        assert list(df.columns) == original_columns

    @pytest.mark.unit
    def test_mixed_naming_conventions(self, column_name_variations_df):
        """Handles mixed naming conventions."""
        result = normalize_column_names(column_name_variations_df)
        # All columns should be snake_case
        for col in result.columns:
            assert col == col.lower()
            assert ' ' not in col
            assert '.' not in col
            assert '-' not in col


class TestStandardizeDates:
    """Tests for standardize_dates function."""

    @pytest.mark.unit
    def test_auto_detects_date_columns(self):
        """Auto-detects columns with date-related names."""
        df = pd.DataFrame({
            'measurement_date': ['2024-01-01'],
            'datetime': ['2024-01-02'],
            'created_at': ['2024-01-03'],
            'value': [1],
        })
        result = standardize_dates(df)
        assert pd.api.types.is_datetime64_any_dtype(result['measurement_date'])
        assert pd.api.types.is_datetime64_any_dtype(result['datetime'])
        assert pd.api.types.is_datetime64_any_dtype(result['created_at'])

    @pytest.mark.unit
    def test_explicit_date_columns(self):
        """Processes explicitly specified date columns."""
        df = pd.DataFrame({
            'col_a': ['2024-01-01'],
            'col_b': ['2024-01-02'],
        })
        result = standardize_dates(df, date_columns=['col_a'])
        assert pd.api.types.is_datetime64_any_dtype(result['col_a'])
        assert not pd.api.types.is_datetime64_any_dtype(result['col_b'])

    @pytest.mark.unit
    def test_various_date_formats(self):
        """Handles various date format strings."""
        df = pd.DataFrame({
            'date1': ['2024-01-01'],
            'date2': ['01/15/2024'],
            'date3': ['January 1, 2024'],
            'date4': ['2024-01-01T12:00:00'],
        })
        result = standardize_dates(df, date_columns=['date1', 'date2', 'date3', 'date4'])
        for col in ['date1', 'date2', 'date3', 'date4']:
            assert pd.api.types.is_datetime64_any_dtype(result[col])

    @pytest.mark.unit
    def test_output_format_string(self):
        """Converts to specified output format."""
        df = pd.DataFrame({'date': ['2024-01-15']})
        result = standardize_dates(df, date_columns=['date'], output_format='%Y/%m/%d')
        assert result['date'].iloc[0] == '2024/01/15'

    @pytest.mark.unit
    def test_invalid_dates_become_nat(self):
        """Invalid dates become NaT."""
        df = pd.DataFrame({'date': ['2024-01-01', 'invalid', 'not a date']})
        result = standardize_dates(df, date_columns=['date'])
        assert pd.notna(result['date'].iloc[0])
        assert pd.isna(result['date'].iloc[1])
        assert pd.isna(result['date'].iloc[2])

    @pytest.mark.unit
    def test_does_not_modify_original(self):
        """Original DataFrame is not modified."""
        df = pd.DataFrame({'date': ['2024-01-01']})
        original_value = df['date'].iloc[0]
        standardize_dates(df, date_columns=['date'])
        assert df['date'].iloc[0] == original_value

    @pytest.mark.unit
    def test_missing_columns_ignored(self):
        """Missing columns are silently ignored."""
        df = pd.DataFrame({'date': ['2024-01-01']})
        result = standardize_dates(df, date_columns=['date', 'nonexistent'])
        assert 'date' in result.columns


class TestStandardizeCoordinates:
    """Tests for standardize_coordinates function."""

    @pytest.mark.unit
    def test_finds_lat_lon_variations(self):
        """Finds latitude/longitude under various column names."""
        df = pd.DataFrame({
            'LAT': [39.5],
            'LONG': [-105.0],
        })
        result = standardize_coordinates(df)
        assert 'latitude' in result.columns
        assert 'longitude' in result.columns
        assert result['latitude'].iloc[0] == 39.5
        assert result['longitude'].iloc[0] == -105.0

    @pytest.mark.unit
    def test_validates_latitude_range(self, capsys):
        """Invalid latitudes are set to NaN with warning."""
        df = pd.DataFrame({
            'latitude': [39.5, 91.0, -91.0],  # 91 and -91 are invalid
            'longitude': [-105.0, -105.0, -105.0],
        })
        result = standardize_coordinates(df)
        assert pd.notna(result['latitude'].iloc[0])
        assert pd.isna(result['latitude'].iloc[1])
        assert pd.isna(result['latitude'].iloc[2])

    @pytest.mark.unit
    def test_validates_longitude_range(self, capsys):
        """Invalid longitudes are set to NaN with warning."""
        df = pd.DataFrame({
            'latitude': [39.5, 39.5, 39.5],
            'longitude': [-105.0, 181.0, -181.0],  # 181 and -181 are invalid
        })
        result = standardize_coordinates(df)
        assert pd.notna(result['longitude'].iloc[0])
        assert pd.isna(result['longitude'].iloc[1])
        assert pd.isna(result['longitude'].iloc[2])

    @pytest.mark.unit
    def test_converts_strings_to_numeric(self):
        """Converts string coordinates to numeric."""
        df = pd.DataFrame({
            'latitude': ['39.5', '40.0'],
            'longitude': ['-105.0', '-104.5'],
        })
        result = standardize_coordinates(df)
        assert pd.api.types.is_numeric_dtype(result['latitude'])
        assert pd.api.types.is_numeric_dtype(result['longitude'])

    @pytest.mark.unit
    def test_create_geometry(self):
        """Creates geometry column when requested."""
        df = pd.DataFrame({
            'latitude': [39.5, 40.0],
            'longitude': [-105.0, -104.5],
        })
        result = standardize_coordinates(df, create_geometry=True)
        import geopandas as gpd
        assert isinstance(result, gpd.GeoDataFrame)
        assert result.crs.to_epsg() == 4326
        assert result.geometry.iloc[0].x == -105.0
        assert result.geometry.iloc[0].y == 39.5

    @pytest.mark.unit
    def test_handles_missing_coordinates(self):
        """Handles missing coordinate values."""
        df = pd.DataFrame({
            'latitude': [39.5, None, 40.0],
            'longitude': [-105.0, -104.5, None],
        })
        result = standardize_coordinates(df)
        assert pd.notna(result['latitude'].iloc[0])
        assert pd.isna(result['latitude'].iloc[1])
        assert pd.isna(result['longitude'].iloc[2])


class TestConvertUnits:
    """Tests for convert_units function."""

    @pytest.mark.unit
    def test_feet_to_meters(self):
        """Converts feet to meters."""
        df = pd.DataFrame({'depth_ft': [100.0, 200.0, 300.0]})
        result = convert_units(df, 'depth_ft', 'feet', 'meters', 'depth_m')
        expected = [30.48, 60.96, 91.44]
        np.testing.assert_array_almost_equal(result['depth_m'], expected, decimal=2)

    @pytest.mark.unit
    def test_meters_to_feet(self):
        """Converts meters to feet."""
        df = pd.DataFrame({'depth_m': [30.48]})
        result = convert_units(df, 'depth_m', 'meters', 'feet', 'depth_ft')
        assert abs(result['depth_ft'].iloc[0] - 100.0) < 0.01

    @pytest.mark.unit
    def test_cfs_to_m3s(self):
        """Converts cubic feet per second to cubic meters per second."""
        df = pd.DataFrame({'discharge_cfs': [1000.0]})
        result = convert_units(df, 'discharge_cfs', 'cfs', 'm3/s', 'discharge_m3s')
        assert abs(result['discharge_m3s'].iloc[0] - 28.3168) < 0.01

    @pytest.mark.unit
    def test_fahrenheit_to_celsius(self):
        """Converts Fahrenheit to Celsius."""
        df = pd.DataFrame({'temp_f': [32.0, 212.0, 68.0]})
        result = convert_units(df, 'temp_f', 'fahrenheit', 'celsius', 'temp_c')
        expected = [0.0, 100.0, 20.0]
        np.testing.assert_array_almost_equal(result['temp_c'], expected, decimal=2)

    @pytest.mark.unit
    def test_celsius_to_fahrenheit(self):
        """Converts Celsius to Fahrenheit."""
        df = pd.DataFrame({'temp_c': [0.0, 100.0, 20.0]})
        result = convert_units(df, 'temp_c', 'celsius', 'fahrenheit', 'temp_f')
        expected = [32.0, 212.0, 68.0]
        np.testing.assert_array_almost_equal(result['temp_f'], expected, decimal=2)

    @pytest.mark.unit
    def test_overwrites_column_when_no_new_name(self):
        """Overwrites original column when no new column name given."""
        df = pd.DataFrame({'temp': [32.0]})
        result = convert_units(df, 'temp', 'fahrenheit', 'celsius')
        assert 'temp' in result.columns
        assert abs(result['temp'].iloc[0] - 0.0) < 0.01

    @pytest.mark.unit
    def test_handles_missing_values(self):
        """NaN values remain NaN after conversion."""
        df = pd.DataFrame({'temp': [32.0, None, 212.0]})
        result = convert_units(df, 'temp', 'fahrenheit', 'celsius')
        assert pd.notna(result['temp'].iloc[0])
        assert pd.isna(result['temp'].iloc[1])
        assert pd.notna(result['temp'].iloc[2])

    @pytest.mark.unit
    def test_unknown_conversion_raises_error(self):
        """Unknown unit conversion raises ValueError."""
        df = pd.DataFrame({'value': [1.0]})
        with pytest.raises(ValueError, match="Unknown conversion"):
            convert_units(df, 'value', 'unknown_unit', 'another_unit')

    @pytest.mark.unit
    def test_case_insensitive_units(self):
        """Unit names are case-insensitive."""
        df = pd.DataFrame({'temp': [32.0]})
        result = convert_units(df, 'temp', 'FAHRENHEIT', 'CELSIUS')
        assert abs(result['temp'].iloc[0] - 0.0) < 0.01


class TestHandleMissingValues:
    """Tests for handle_missing_values function."""

    @pytest.mark.unit
    def test_drop_strategy(self, dataframe_with_missing_values):
        """Drop strategy removes rows with missing values."""
        result = handle_missing_values(dataframe_with_missing_values, strategy='drop')
        assert len(result) == 1  # Only row 3 has all non-null values

    @pytest.mark.unit
    def test_fill_with_specific_value(self):
        """Fill strategy with specific value."""
        df = pd.DataFrame({'value': [1.0, None, 3.0]})
        result = handle_missing_values(df, strategy='fill', fill_value=0)
        assert result['value'].iloc[1] == 0

    @pytest.mark.unit
    def test_fill_numeric_with_mean(self):
        """Fill numeric columns with mean."""
        df = pd.DataFrame({'value': [1.0, None, 5.0]})
        result = handle_missing_values(df, strategy='fill', numeric_fill='mean')
        assert result['value'].iloc[1] == 3.0  # mean of 1 and 5

    @pytest.mark.unit
    def test_fill_numeric_with_median(self):
        """Fill numeric columns with median."""
        df = pd.DataFrame({'value': [1.0, None, 5.0, 10.0]})
        result = handle_missing_values(df, strategy='fill', numeric_fill='median')
        assert result['value'].iloc[1] == 5.0  # median of 1, 5, 10

    @pytest.mark.unit
    def test_fill_numeric_with_zero(self):
        """Fill numeric columns with zero."""
        df = pd.DataFrame({'value': [1.0, None, 5.0]})
        result = handle_missing_values(df, strategy='fill', numeric_fill='zero')
        assert result['value'].iloc[1] == 0

    @pytest.mark.unit
    def test_fill_non_numeric_with_unknown(self):
        """Fill non-numeric columns with 'Unknown'."""
        df = pd.DataFrame({'name': ['a', None, 'c']})
        result = handle_missing_values(df, strategy='fill')
        assert result['name'].iloc[1] == 'Unknown'

    @pytest.mark.unit
    def test_interpolate_strategy(self):
        """Interpolate strategy for time series."""
        df = pd.DataFrame({'value': [1.0, None, 3.0]})
        result = handle_missing_values(df, strategy='interpolate')
        assert result['value'].iloc[1] == 2.0  # Linear interpolation

    @pytest.mark.unit
    def test_specific_columns_only(self):
        """Only processes specified columns."""
        df = pd.DataFrame({
            'keep_missing': [1.0, None, 3.0],
            'process_this': [1.0, None, 3.0],
        })
        result = handle_missing_values(df, strategy='fill', fill_value=0, columns=['process_this'])
        assert pd.isna(result['keep_missing'].iloc[1])
        assert result['process_this'].iloc[1] == 0


class TestNormalizeWaterData:
    """Tests for normalize_water_data convenience function."""

    @pytest.mark.unit
    def test_applies_all_normalizations(self, usgs_style_dataframe):
        """Applies column names, dates, and coordinates standardization."""
        result = normalize_water_data(usgs_style_dataframe, source='usgs')
        # Column names normalized
        assert 'site_name' in result.columns or 'site_id' in result.columns
        # USGS-specific renames applied
        if 'site_id' in result.columns:
            assert result['site_id'].iloc[0] == '01234567'

    @pytest.mark.unit
    def test_usgs_source_renames(self, usgs_style_dataframe):
        """USGS-specific column renames are applied."""
        result = normalize_water_data(usgs_style_dataframe, source='usgs')
        # site_no should be renamed to site_id
        assert 'site_id' in result.columns

    @pytest.mark.unit
    def test_generic_source_works(self, sample_water_data):
        """Generic source normalization works."""
        result = normalize_water_data(sample_water_data, source='generic')
        assert not result.empty
