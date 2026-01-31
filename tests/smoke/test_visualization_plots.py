"""
Smoke tests for plot visualization functions.

These tests verify that each plot function runs without errors
and produces valid output. They don't verify plot aesthetics.
"""

import pytest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from scripts.visualization.plots import (
    time_series_plot,
    scatter_plot,
    histogram,
    box_plot,
    correlation_heatmap,
)


@pytest.fixture(autouse=True)
def close_plots():
    """Close all plots after each test to prevent memory issues."""
    yield
    plt.close('all')


class TestTimeSeriesPlot:
    """Smoke tests for time_series_plot function."""

    @pytest.mark.smoke
    def test_basic_time_series(self, sample_timeseries_data):
        """Creates basic time series plot."""
        fig = time_series_plot(sample_timeseries_data, 'date', 'value')
        assert fig is not None
        assert isinstance(fig, plt.Figure)

    @pytest.mark.smoke
    def test_time_series_with_rolling_average(self, sample_timeseries_data):
        """Creates time series with rolling average."""
        fig = time_series_plot(
            sample_timeseries_data, 'date', 'value',
            rolling_window=7
        )
        assert fig is not None

    @pytest.mark.smoke
    def test_time_series_with_trend(self, sample_timeseries_data):
        """Creates time series with trend line."""
        fig = time_series_plot(
            sample_timeseries_data, 'date', 'value',
            show_trend=True
        )
        assert fig is not None

    @pytest.mark.smoke
    def test_time_series_with_groups(self, sample_timeseries_data):
        """Creates grouped time series."""
        fig = time_series_plot(
            sample_timeseries_data, 'date', 'value',
            group_col='category'
        )
        assert fig is not None

    @pytest.mark.smoke
    def test_time_series_with_custom_labels(self, sample_timeseries_data):
        """Creates time series with custom labels."""
        fig = time_series_plot(
            sample_timeseries_data, 'date', 'value',
            title='Test Title',
            xlabel='Custom X',
            ylabel='Custom Y'
        )
        assert fig is not None

    @pytest.mark.smoke
    def test_time_series_save(self, sample_timeseries_data, temp_data_dir):
        """Saves time series plot to file."""
        save_path = temp_data_dir / 'time_series.png'
        fig = time_series_plot(
            sample_timeseries_data, 'date', 'value',
            save_path=save_path
        )
        assert save_path.exists()


class TestScatterPlot:
    """Smoke tests for scatter_plot function."""

    @pytest.mark.smoke
    def test_basic_scatter(self, sample_water_data):
        """Creates basic scatter plot."""
        fig = scatter_plot(sample_water_data, 'ph', 'temperature_c')
        assert fig is not None
        assert isinstance(fig, plt.Figure)

    @pytest.mark.smoke
    def test_scatter_with_color(self, sample_water_data):
        """Creates scatter plot with color dimension."""
        fig = scatter_plot(
            sample_water_data, 'ph', 'temperature_c',
            color_col='category'
        )
        assert fig is not None

    @pytest.mark.smoke
    def test_scatter_with_size(self, sample_water_data):
        """Creates scatter plot with size dimension."""
        fig = scatter_plot(
            sample_water_data, 'ph', 'temperature_c',
            size_col='dissolved_oxygen'
        )
        assert fig is not None

    @pytest.mark.smoke
    def test_scatter_with_regression(self, sample_water_data):
        """Creates scatter plot with regression line."""
        fig = scatter_plot(
            sample_water_data, 'ph', 'temperature_c',
            show_regression=True
        )
        assert fig is not None

    @pytest.mark.smoke
    def test_scatter_save(self, sample_water_data, temp_data_dir):
        """Saves scatter plot to file."""
        save_path = temp_data_dir / 'scatter.png'
        fig = scatter_plot(
            sample_water_data, 'ph', 'temperature_c',
            save_path=save_path
        )
        assert save_path.exists()


class TestHistogram:
    """Smoke tests for histogram function."""

    @pytest.mark.smoke
    def test_basic_histogram(self, sample_water_data):
        """Creates basic histogram."""
        fig = histogram(sample_water_data, 'ph')
        assert fig is not None
        assert isinstance(fig, plt.Figure)

    @pytest.mark.smoke
    def test_histogram_with_kde(self, sample_water_data):
        """Creates histogram with KDE overlay."""
        fig = histogram(sample_water_data, 'ph', show_kde=True)
        assert fig is not None

    @pytest.mark.smoke
    def test_histogram_without_kde(self, sample_water_data):
        """Creates histogram without KDE."""
        fig = histogram(sample_water_data, 'ph', show_kde=False)
        assert fig is not None

    @pytest.mark.smoke
    def test_histogram_with_stats(self, sample_water_data):
        """Creates histogram with statistics."""
        fig = histogram(sample_water_data, 'ph', show_stats=True)
        assert fig is not None

    @pytest.mark.smoke
    def test_histogram_grouped(self, sample_water_data):
        """Creates grouped histogram."""
        fig = histogram(sample_water_data, 'ph', group_col='category')
        assert fig is not None

    @pytest.mark.smoke
    def test_histogram_custom_bins(self, sample_water_data):
        """Creates histogram with custom bin count."""
        fig = histogram(sample_water_data, 'ph', bins=50)
        assert fig is not None

    @pytest.mark.smoke
    def test_histogram_save(self, sample_water_data, temp_data_dir):
        """Saves histogram to file."""
        save_path = temp_data_dir / 'histogram.png'
        fig = histogram(sample_water_data, 'ph', save_path=save_path)
        assert save_path.exists()


class TestBoxPlot:
    """Smoke tests for box_plot function."""

    @pytest.mark.smoke
    def test_basic_box_plot(self, sample_water_data):
        """Creates basic box plot."""
        fig = box_plot(sample_water_data, 'ph')
        assert fig is not None
        assert isinstance(fig, plt.Figure)

    @pytest.mark.smoke
    def test_box_plot_grouped(self, sample_water_data):
        """Creates grouped box plot."""
        fig = box_plot(sample_water_data, 'ph', group_col='category')
        assert fig is not None

    @pytest.mark.smoke
    def test_box_plot_with_points(self, sample_water_data):
        """Creates box plot with data points overlay."""
        fig = box_plot(sample_water_data, 'ph', group_col='category', show_points=True)
        assert fig is not None

    @pytest.mark.smoke
    def test_box_plot_horizontal(self, sample_water_data):
        """Creates horizontal box plot."""
        fig = box_plot(sample_water_data, 'ph', group_col='category', horizontal=True)
        assert fig is not None

    @pytest.mark.smoke
    def test_box_plot_save(self, sample_water_data, temp_data_dir):
        """Saves box plot to file."""
        save_path = temp_data_dir / 'boxplot.png'
        fig = box_plot(sample_water_data, 'ph', save_path=save_path)
        assert save_path.exists()


class TestCorrelationHeatmap:
    """Smoke tests for correlation_heatmap function."""

    @pytest.mark.smoke
    def test_basic_heatmap(self, sample_water_data):
        """Creates basic correlation heatmap."""
        fig = correlation_heatmap(sample_water_data)
        assert fig is not None
        assert isinstance(fig, plt.Figure)

    @pytest.mark.smoke
    def test_heatmap_specific_columns(self, sample_water_data):
        """Creates heatmap for specific columns."""
        fig = correlation_heatmap(
            sample_water_data,
            columns=['ph', 'temperature_c', 'dissolved_oxygen']
        )
        assert fig is not None

    @pytest.mark.smoke
    def test_heatmap_spearman(self, sample_water_data):
        """Creates heatmap with Spearman correlation."""
        fig = correlation_heatmap(sample_water_data, method='spearman')
        assert fig is not None

    @pytest.mark.smoke
    def test_heatmap_without_annotations(self, sample_water_data):
        """Creates heatmap without value annotations."""
        fig = correlation_heatmap(sample_water_data, annot=False)
        assert fig is not None

    @pytest.mark.smoke
    def test_heatmap_custom_colormap(self, sample_water_data):
        """Creates heatmap with custom colormap."""
        fig = correlation_heatmap(sample_water_data, cmap='coolwarm')
        assert fig is not None

    @pytest.mark.smoke
    def test_heatmap_save(self, sample_water_data, temp_data_dir):
        """Saves heatmap to file."""
        save_path = temp_data_dir / 'heatmap.png'
        fig = correlation_heatmap(sample_water_data, save_path=save_path)
        assert save_path.exists()
