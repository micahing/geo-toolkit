"""
Smoke tests for map visualization functions.

These tests verify that each map function runs without errors
and produces valid output.
"""

import pytest
import pandas as pd
import numpy as np
import folium
import matplotlib.pyplot as plt

from scripts.visualization.maps import (
    point_map,
    choropleth_map,
    heatmap,
    cluster_map,
    static_map,
)


@pytest.fixture(autouse=True)
def close_plots():
    """Close all plots after each test."""
    yield
    plt.close('all')


class TestPointMap:
    """Smoke tests for point_map function."""

    @pytest.mark.smoke
    def test_basic_point_map(self, sample_water_data):
        """Creates basic point map."""
        m = point_map(sample_water_data)
        assert m is not None
        assert isinstance(m, folium.Map)

    @pytest.mark.smoke
    def test_point_map_with_color(self, sample_water_data):
        """Creates point map with color dimension."""
        m = point_map(sample_water_data, color_col='category')
        assert m is not None

    @pytest.mark.smoke
    def test_point_map_with_size(self, sample_water_data):
        """Creates point map with size dimension."""
        m = point_map(sample_water_data, size_col='ph')
        assert m is not None

    @pytest.mark.smoke
    def test_point_map_with_popups(self, sample_water_data):
        """Creates point map with specific popup columns."""
        m = point_map(
            sample_water_data,
            popup_cols=['site_id', 'ph', 'temperature_c']
        )
        assert m is not None

    @pytest.mark.smoke
    def test_point_map_with_clustering(self, sample_water_data):
        """Creates point map with marker clustering."""
        m = point_map(sample_water_data, cluster=True)
        assert m is not None

    @pytest.mark.smoke
    def test_point_map_custom_center(self, sample_water_data):
        """Creates point map with custom center."""
        m = point_map(sample_water_data, center=[38.0, -110.0], zoom=8)
        assert m is not None

    @pytest.mark.smoke
    def test_point_map_different_tiles(self, sample_water_data):
        """Creates point map with different tile layer."""
        m = point_map(sample_water_data, tiles='CartoDB positron')
        assert m is not None

    @pytest.mark.smoke
    def test_point_map_save(self, sample_water_data, temp_data_dir):
        """Saves point map to HTML file."""
        save_path = temp_data_dir / 'point_map.html'
        m = point_map(sample_water_data, save_path=save_path)
        assert save_path.exists()

    @pytest.mark.smoke
    def test_point_map_empty_data_raises(self):
        """Raises error for empty data."""
        empty_df = pd.DataFrame({
            'latitude': [],
            'longitude': [],
        })
        with pytest.raises(ValueError, match="No valid coordinates"):
            point_map(empty_df)

    @pytest.mark.smoke
    def test_point_map_handles_missing_coords(self, sample_water_data):
        """Handles rows with missing coordinates."""
        df = sample_water_data.copy()
        df.loc[0, 'latitude'] = None
        df.loc[1, 'longitude'] = None
        m = point_map(df)
        assert m is not None


class TestChoroplethMap:
    """Smoke tests for choropleth_map function."""

    @pytest.mark.smoke
    def test_basic_choropleth(self, sample_polygon_geodataframe):
        """Creates basic choropleth map."""
        m = choropleth_map(sample_polygon_geodataframe, 'value')
        assert m is not None
        assert isinstance(m, folium.Map)

    @pytest.mark.smoke
    def test_choropleth_with_tooltips(self, sample_polygon_geodataframe):
        """Creates choropleth with tooltips."""
        m = choropleth_map(
            sample_polygon_geodataframe, 'value',
            name_col='name'
        )
        assert m is not None

    @pytest.mark.smoke
    def test_choropleth_custom_colormap(self, sample_polygon_geodataframe):
        """Creates choropleth with custom colormap."""
        m = choropleth_map(
            sample_polygon_geodataframe, 'value',
            cmap='Blues'
        )
        assert m is not None

    @pytest.mark.smoke
    def test_choropleth_save(self, sample_polygon_geodataframe, temp_data_dir):
        """Saves choropleth to HTML file."""
        save_path = temp_data_dir / 'choropleth.html'
        m = choropleth_map(
            sample_polygon_geodataframe, 'value',
            save_path=save_path
        )
        assert save_path.exists()


class TestHeatmap:
    """Smoke tests for heatmap function."""

    @pytest.mark.smoke
    def test_basic_heatmap(self, sample_water_data):
        """Creates basic heatmap."""
        m = heatmap(sample_water_data)
        assert m is not None
        assert isinstance(m, folium.Map)

    @pytest.mark.smoke
    def test_heatmap_with_values(self, sample_water_data):
        """Creates heatmap weighted by values."""
        m = heatmap(sample_water_data, value_col='ph')
        assert m is not None

    @pytest.mark.smoke
    def test_heatmap_custom_radius(self, sample_water_data):
        """Creates heatmap with custom radius."""
        m = heatmap(sample_water_data, radius=25, blur=15)
        assert m is not None

    @pytest.mark.smoke
    def test_heatmap_dark_tiles(self, sample_water_data):
        """Creates heatmap with dark tile layer."""
        m = heatmap(sample_water_data, tiles='CartoDB dark_matter')
        assert m is not None

    @pytest.mark.smoke
    def test_heatmap_save(self, sample_water_data, temp_data_dir):
        """Saves heatmap to HTML file."""
        save_path = temp_data_dir / 'heatmap.html'
        m = heatmap(sample_water_data, save_path=save_path)
        assert save_path.exists()


class TestClusterMap:
    """Smoke tests for cluster_map function."""

    @pytest.mark.smoke
    def test_basic_cluster_map(self, sample_water_data):
        """Creates basic cluster map."""
        m = cluster_map(sample_water_data)
        assert m is not None
        assert isinstance(m, folium.Map)

    @pytest.mark.smoke
    def test_cluster_map_with_popups(self, sample_water_data):
        """Creates cluster map with popups."""
        m = cluster_map(
            sample_water_data,
            popup_cols=['site_id', 'ph']
        )
        assert m is not None

    @pytest.mark.smoke
    def test_cluster_map_save(self, sample_water_data, temp_data_dir):
        """Saves cluster map to HTML file."""
        save_path = temp_data_dir / 'cluster.html'
        m = cluster_map(sample_water_data, save_path=save_path)
        assert save_path.exists()


class TestStaticMap:
    """Smoke tests for static_map function."""

    @pytest.mark.smoke
    def test_basic_static_map(self, sample_geodataframe):
        """Creates basic static map."""
        fig = static_map(sample_geodataframe)
        assert fig is not None
        assert isinstance(fig, plt.Figure)

    @pytest.mark.smoke
    def test_static_map_with_column(self, sample_geodataframe):
        """Creates static map colored by column."""
        fig = static_map(sample_geodataframe, column='ph')
        assert fig is not None

    @pytest.mark.smoke
    def test_static_map_custom_colormap(self, sample_geodataframe):
        """Creates static map with custom colormap."""
        fig = static_map(sample_geodataframe, column='ph', cmap='coolwarm')
        assert fig is not None

    @pytest.mark.smoke
    def test_static_map_without_legend(self, sample_geodataframe):
        """Creates static map without legend."""
        fig = static_map(sample_geodataframe, column='ph', legend=False)
        assert fig is not None

    @pytest.mark.smoke
    def test_static_map_without_basemap(self, sample_geodataframe):
        """Creates static map without basemap."""
        fig = static_map(sample_geodataframe, basemap=False)
        assert fig is not None

    @pytest.mark.smoke
    def test_static_map_save(self, sample_geodataframe, temp_data_dir):
        """Saves static map to file."""
        save_path = temp_data_dir / 'static_map.png'
        fig = static_map(sample_geodataframe, save_path=save_path, basemap=False)
        assert save_path.exists()

    @pytest.mark.smoke
    def test_static_map_polygons(self, sample_polygon_geodataframe):
        """Creates static map with polygon geometry."""
        fig = static_map(sample_polygon_geodataframe, column='value')
        assert fig is not None
