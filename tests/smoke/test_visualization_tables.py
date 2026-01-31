"""
Smoke tests for table visualization functions.

These tests verify that each table function runs without errors
and produces valid output.
"""

import pytest
import pandas as pd
import numpy as np

from scripts.visualization.tables import (
    summary_table,
    styled_dataframe,
    export_table,
    pivot_table,
    comparison_table,
)


class TestSummaryTable:
    """Smoke tests for summary_table function."""

    @pytest.mark.smoke
    def test_basic_summary(self, sample_water_data):
        """Creates basic summary table."""
        result = summary_table(sample_water_data)
        assert result is not None
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    @pytest.mark.smoke
    def test_summary_specific_columns(self, sample_water_data):
        """Creates summary for specific columns."""
        result = summary_table(
            sample_water_data,
            columns=['ph', 'temperature_c', 'dissolved_oxygen']
        )
        assert result is not None
        # Should only have the specified columns (or stats as rows)
        assert len(result.columns) <= 3 or len(result.index) <= 10

    @pytest.mark.smoke
    def test_summary_grouped(self, sample_water_data):
        """Creates grouped summary table."""
        result = summary_table(sample_water_data, group_by='category')
        assert result is not None
        # Should have groups in index or columns

    @pytest.mark.smoke
    def test_summary_custom_stats(self, sample_water_data):
        """Creates summary with custom statistics."""
        result = summary_table(
            sample_water_data,
            stats=['count', 'mean', 'sum']
        )
        assert result is not None

    @pytest.mark.smoke
    def test_summary_with_percentiles(self, sample_water_data):
        """Creates summary with percentiles."""
        result = summary_table(
            sample_water_data,
            percentiles=[0.25, 0.5, 0.75]
        )
        assert result is not None


class TestStyledDataframe:
    """Smoke tests for styled_dataframe function."""

    @pytest.mark.smoke
    def test_basic_styling(self, sample_water_data):
        """Creates basic styled DataFrame."""
        result = styled_dataframe(sample_water_data.head(10))
        assert result is not None
        # Should return a Styler object
        assert hasattr(result, 'to_html')

    @pytest.mark.smoke
    def test_highlight_max(self, sample_water_data):
        """Creates styled DataFrame with max highlighting."""
        result = styled_dataframe(
            sample_water_data.head(10),
            highlight_max=['ph', 'temperature_c']
        )
        assert result is not None

    @pytest.mark.smoke
    def test_highlight_min(self, sample_water_data):
        """Creates styled DataFrame with min highlighting."""
        result = styled_dataframe(
            sample_water_data.head(10),
            highlight_min=['ph']
        )
        assert result is not None

    @pytest.mark.smoke
    def test_gradient_columns(self, sample_water_data):
        """Creates styled DataFrame with gradient colors."""
        result = styled_dataframe(
            sample_water_data.head(10),
            gradient_columns=['ph', 'temperature_c']
        )
        assert result is not None

    @pytest.mark.smoke
    def test_bar_columns(self, sample_water_data):
        """Creates styled DataFrame with bar charts."""
        result = styled_dataframe(
            sample_water_data.head(10),
            bar_columns=['ph']
        )
        assert result is not None

    @pytest.mark.smoke
    def test_format_dict(self, sample_water_data):
        """Creates styled DataFrame with custom formatting."""
        result = styled_dataframe(
            sample_water_data.head(10),
            format_dict={'ph': '{:.3f}', 'temperature_c': '{:.1f}'}
        )
        assert result is not None

    @pytest.mark.smoke
    def test_with_caption(self, sample_water_data):
        """Creates styled DataFrame with caption."""
        result = styled_dataframe(
            sample_water_data.head(10),
            caption='Water Quality Data'
        )
        assert result is not None


class TestExportTable:
    """Smoke tests for export_table function."""

    @pytest.mark.smoke
    def test_export_csv(self, sample_water_data, temp_data_dir):
        """Exports table to CSV."""
        paths = export_table(
            sample_water_data.head(10),
            'test_export',
            formats=['csv'],
            output_dir=temp_data_dir
        )
        assert 'csv' in paths
        assert paths['csv'].exists()

    @pytest.mark.smoke
    def test_export_html(self, sample_water_data, temp_data_dir):
        """Exports table to HTML."""
        paths = export_table(
            sample_water_data.head(10),
            'test_export',
            formats=['html'],
            output_dir=temp_data_dir
        )
        assert 'html' in paths
        assert paths['html'].exists()
        # HTML should have proper structure
        content = paths['html'].read_text()
        assert '<html>' in content
        assert '<table' in content  # Table tag may have attributes

    @pytest.mark.smoke
    def test_export_json(self, sample_water_data, temp_data_dir):
        """Exports table to JSON."""
        paths = export_table(
            sample_water_data.head(10),
            'test_export',
            formats=['json'],
            output_dir=temp_data_dir
        )
        assert 'json' in paths
        assert paths['json'].exists()

    @pytest.mark.smoke
    def test_export_markdown(self, sample_water_data, temp_data_dir):
        """Exports table to Markdown."""
        pytest.importorskip('tabulate')  # Skip if tabulate not installed
        paths = export_table(
            sample_water_data.head(10),
            'test_export',
            formats=['markdown'],
            output_dir=temp_data_dir
        )
        assert 'markdown' in paths
        assert paths['markdown'].exists()

    @pytest.mark.smoke
    def test_export_multiple_formats(self, sample_water_data, temp_data_dir):
        """Exports table to multiple formats."""
        paths = export_table(
            sample_water_data.head(10),
            'multi_export',
            formats=['csv', 'html', 'json'],
            output_dir=temp_data_dir
        )
        assert len(paths) == 3
        for path in paths.values():
            assert path.exists()


class TestPivotTable:
    """Smoke tests for pivot_table function."""

    @pytest.mark.smoke
    def test_basic_pivot(self, sample_water_data):
        """Creates basic pivot table."""
        # Add a year column for pivoting
        df = sample_water_data.copy()
        df['year'] = df['measurement_date'].dt.year

        result = pivot_table(
            df,
            values='ph',
            index='category',
            columns='year'
        )
        assert result is not None
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.smoke
    def test_pivot_with_margins(self, sample_water_data):
        """Creates pivot table with margins."""
        df = sample_water_data.copy()
        df['year'] = 2024  # Single year for simplicity

        result = pivot_table(
            df,
            values='ph',
            index='category',
            columns='year',
            margins=True
        )
        assert result is not None
        assert 'Total' in result.index or 'Total' in result.columns

    @pytest.mark.smoke
    def test_pivot_different_aggfuncs(self, sample_water_data):
        """Creates pivot table with different aggregation functions."""
        df = sample_water_data.copy()
        df['year'] = 2024

        for aggfunc in ['mean', 'sum', 'count', 'min', 'max']:
            result = pivot_table(
                df,
                values='ph',
                index='category',
                columns='year',
                aggfunc=aggfunc
            )
            assert result is not None


class TestComparisonTable:
    """Smoke tests for comparison_table function."""

    @pytest.mark.smoke
    def test_basic_comparison(self, sample_water_data):
        """Creates comparison table for multiple DataFrames."""
        # Split data into groups
        df1 = sample_water_data[sample_water_data['category'] == 'High']
        df2 = sample_water_data[sample_water_data['category'] == 'Low']

        result = comparison_table(
            {'High': df1, 'Low': df2},
            columns=['ph', 'temperature_c']
        )
        assert result is not None
        assert 'High' in result.columns
        assert 'Low' in result.columns

    @pytest.mark.smoke
    def test_comparison_custom_stats(self, sample_water_data):
        """Creates comparison table with custom statistics."""
        df1 = sample_water_data.head(25)
        df2 = sample_water_data.tail(25)

        result = comparison_table(
            {'First Half': df1, 'Second Half': df2},
            columns=['ph'],
            labels=['mean', 'std', 'min', 'max']
        )
        assert result is not None
