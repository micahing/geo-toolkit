"""
Geospatial Visualization Utilities

Functions for creating interactive and static maps using Folium and GeoPandas.
"""

import pandas as pd
import numpy as np
import folium
from folium import plugins
import geopandas as gpd
import matplotlib.pyplot as plt
from typing import Optional, Union, Tuple, List
from pathlib import Path


# Default output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "outputs"

# Colorado River Basin approximate bounds (for default map centering)
COLORADO_BASIN_BOUNDS = {
    'center': [36.5, -111.5],
    'zoom': 6,
    'bounds': [[31.0, -117.5], [42.0, -105.5]],
}


def point_map(
    df: pd.DataFrame,
    lat_col: str = 'latitude',
    lon_col: str = 'longitude',
    popup_cols: Optional[list[str]] = None,
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    color_map: Optional[dict] = None,
    center: Optional[list[float]] = None,
    zoom: int = 6,
    tiles: str = 'OpenStreetMap',
    cluster: bool = False,
    save_path: Optional[Path] = None,
) -> folium.Map:
    """
    Create an interactive point map with Folium.

    Args:
        df: DataFrame with location data
        lat_col: Latitude column name
        lon_col: Longitude column name
        popup_cols: Columns to show in popup (all if None)
        color_col: Column to determine marker color
        size_col: Column to determine marker size
        color_map: Dict mapping values to colors
        center: Map center [lat, lon] (auto-calculated if None)
        zoom: Initial zoom level
        tiles: Base map tiles ('OpenStreetMap', 'CartoDB positron', etc.)
        cluster: Use marker clustering for many points
        save_path: Path to save HTML file

    Returns:
        Folium Map object
    """
    # Filter to valid coordinates
    valid_df = df.dropna(subset=[lat_col, lon_col])

    if valid_df.empty:
        raise ValueError("No valid coordinates found")

    # Calculate center if not provided
    if center is None:
        center = [valid_df[lat_col].mean(), valid_df[lon_col].mean()]

    # Create map
    m = folium.Map(location=center, zoom_start=zoom, tiles=tiles)

    # Set up clustering if requested
    if cluster:
        marker_cluster = plugins.MarkerCluster()
        m.add_child(marker_cluster)
        add_to = marker_cluster
    else:
        add_to = m

    # Default colors
    default_colors = ['blue', 'green', 'red', 'purple', 'orange', 'darkred',
                     'darkblue', 'darkgreen', 'cadetblue', 'pink']

    # Build color mapping
    if color_col and color_map is None:
        unique_vals = valid_df[color_col].unique()
        color_map = {val: default_colors[i % len(default_colors)]
                    for i, val in enumerate(unique_vals)}

    # Determine popup columns
    if popup_cols is None:
        popup_cols = [col for col in valid_df.columns
                     if col not in [lat_col, lon_col, 'geometry']]

    # Add markers
    for idx, row in valid_df.iterrows():
        lat, lon = row[lat_col], row[lon_col]

        # Build popup content
        popup_html = "<br>".join([
            f"<b>{col}:</b> {row[col]}"
            for col in popup_cols if col in row.index
        ])

        # Determine color
        color = 'blue'
        if color_col and color_map:
            color = color_map.get(row[color_col], 'blue')

        # Determine radius
        radius = 6
        if size_col and pd.notna(row.get(size_col)):
            # Scale radius between 4 and 20
            size_val = row[size_col]
            min_val = valid_df[size_col].min()
            max_val = valid_df[size_col].max()
            if max_val > min_val:
                radius = 4 + 16 * (size_val - min_val) / (max_val - min_val)

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            color=color,
            fill=True,
            fillOpacity=0.7,
        ).add_to(add_to)

    # Add legend if color_col provided
    if color_col and color_map:
        legend_html = _create_legend(color_col, color_map)
        m.get_root().html.add_child(folium.Element(legend_html))

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        m.save(str(save_path))

    return m


def choropleth_map(
    gdf: gpd.GeoDataFrame,
    value_col: str,
    name_col: Optional[str] = None,
    cmap: str = 'YlOrRd',
    legend_name: Optional[str] = None,
    center: Optional[list[float]] = None,
    zoom: int = 6,
    tiles: str = 'CartoDB positron',
    save_path: Optional[Path] = None,
) -> folium.Map:
    """
    Create a choropleth (filled polygon) map.

    Args:
        gdf: GeoDataFrame with polygon geometry
        value_col: Column containing values for coloring
        name_col: Column for region names (shown in tooltip)
        cmap: Matplotlib colormap name
        legend_name: Legend title
        center: Map center
        zoom: Initial zoom level
        tiles: Base map tiles
        save_path: Path to save HTML

    Returns:
        Folium Map object
    """
    if center is None:
        center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]

    m = folium.Map(location=center, zoom_start=zoom, tiles=tiles)

    # Reset index to ensure we have a column for folium to use
    gdf_reset = gdf.reset_index()
    index_col = 'index' if 'index' in gdf_reset.columns else gdf_reset.columns[0]

    # Convert to GeoJSON
    geo_json = gdf_reset.__geo_interface__

    # Create choropleth
    folium.Choropleth(
        geo_data=geo_json,
        data=gdf_reset,
        columns=[index_col, value_col],
        key_on='feature.id',
        fill_color=cmap,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=legend_name or value_col,
    ).add_to(m)

    # Add tooltips
    if name_col:
        style_function = lambda x: {'fillColor': 'transparent', 'color': 'transparent'}
        highlight_function = lambda x: {'fillColor': 'black', 'fillOpacity': 0.2}

        tooltip = folium.GeoJsonTooltip(
            fields=[name_col, value_col],
            aliases=[name_col, legend_name or value_col],
        )

        folium.GeoJson(
            gdf_reset.__geo_interface__,
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=tooltip,
        ).add_to(m)

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        m.save(str(save_path))

    return m


def heatmap(
    df: pd.DataFrame,
    lat_col: str = 'latitude',
    lon_col: str = 'longitude',
    value_col: Optional[str] = None,
    radius: int = 15,
    blur: int = 10,
    max_zoom: int = 10,
    center: Optional[list[float]] = None,
    zoom: int = 6,
    tiles: str = 'CartoDB dark_matter',
    save_path: Optional[Path] = None,
) -> folium.Map:
    """
    Create a heatmap visualization.

    Args:
        df: DataFrame with location data
        lat_col: Latitude column
        lon_col: Longitude column
        value_col: Column for intensity weights (uniform if None)
        radius: Heatmap point radius
        blur: Amount of blur
        max_zoom: Max zoom level for heatmap effect
        center: Map center
        zoom: Initial zoom
        tiles: Base map tiles
        save_path: Path to save HTML

    Returns:
        Folium Map object
    """
    valid_df = df.dropna(subset=[lat_col, lon_col])

    if center is None:
        center = [valid_df[lat_col].mean(), valid_df[lon_col].mean()]

    m = folium.Map(location=center, zoom_start=zoom, tiles=tiles)

    # Prepare heatmap data
    if value_col:
        heat_data = [[row[lat_col], row[lon_col], row[value_col]]
                    for _, row in valid_df.iterrows()
                    if pd.notna(row.get(value_col))]
    else:
        heat_data = [[row[lat_col], row[lon_col]]
                    for _, row in valid_df.iterrows()]

    plugins.HeatMap(
        heat_data,
        radius=radius,
        blur=blur,
        max_zoom=max_zoom,
    ).add_to(m)

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        m.save(str(save_path))

    return m


def cluster_map(
    df: pd.DataFrame,
    lat_col: str = 'latitude',
    lon_col: str = 'longitude',
    popup_cols: Optional[list[str]] = None,
    center: Optional[list[float]] = None,
    zoom: int = 6,
    tiles: str = 'OpenStreetMap',
    save_path: Optional[Path] = None,
) -> folium.Map:
    """
    Create a map with marker clustering.

    Alias for point_map with cluster=True.
    """
    return point_map(
        df=df,
        lat_col=lat_col,
        lon_col=lon_col,
        popup_cols=popup_cols,
        center=center,
        zoom=zoom,
        tiles=tiles,
        cluster=True,
        save_path=save_path,
    )


def static_map(
    gdf: gpd.GeoDataFrame,
    column: Optional[str] = None,
    cmap: str = 'viridis',
    figsize: Tuple[int, int] = (12, 10),
    title: Optional[str] = None,
    legend: bool = True,
    basemap: bool = True,
    save_path: Optional[Path] = None,
) -> plt.Figure:
    """
    Create a static map using GeoPandas/Matplotlib.

    Good for publication-quality maps.

    Args:
        gdf: GeoDataFrame with geometry
        column: Column for coloring (uniform if None)
        cmap: Matplotlib colormap
        figsize: Figure size
        title: Map title
        legend: Show color legend
        basemap: Add contextual basemap (requires contextily)
        save_path: Path to save figure

    Returns:
        Matplotlib Figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot GeoDataFrame
    plot_kwargs = {
        'ax': ax,
        'legend': legend and column is not None,
        'legend_kwds': {'shrink': 0.6} if legend and column else {},
    }

    if column:
        plot_kwargs['column'] = column
        plot_kwargs['cmap'] = cmap

    gdf.plot(**plot_kwargs)

    # Add basemap if requested
    if basemap:
        try:
            import contextily as ctx
            # Reproject to web mercator if needed
            if gdf.crs and gdf.crs.to_epsg() != 3857:
                gdf_web = gdf.to_crs(epsg=3857)
                gdf_web.plot(**plot_kwargs)
                ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
            else:
                ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
        except ImportError:
            print("Note: Install contextily for basemap support: conda install contextily")

    ax.set_title(title or '')
    ax.set_axis_off()

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def _create_legend(title: str, color_map: dict) -> str:
    """Create HTML legend for Folium map."""
    items = "".join([
        f'<li><span style="background:{color};width:12px;height:12px;'
        f'display:inline-block;margin-right:5px;"></span>{label}</li>'
        for label, color in color_map.items()
    ])

    return f'''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
                background-color: white; padding: 10px; border-radius: 5px;
                border: 2px solid grey;">
        <b>{title}</b>
        <ul style="list-style-type: none; padding-left: 0; margin: 5px 0;">
            {items}
        </ul>
    </div>
    '''


# Example usage
if __name__ == "__main__":
    # Sample point data
    np.random.seed(42)
    df = pd.DataFrame({
        'site_id': [f'SITE_{i:03d}' for i in range(50)],
        'latitude': np.random.uniform(35, 40, 50),
        'longitude': np.random.uniform(-115, -107, 50),
        'value': np.random.exponential(10, 50),
        'category': np.random.choice(['High', 'Medium', 'Low'], 50),
    })

    # Point map
    m = point_map(
        df,
        color_col='category',
        size_col='value',
        popup_cols=['site_id', 'value', 'category'],
    )
    m.save(str(OUTPUT_DIR / 'example_point_map.html'))
    print(f"Point map saved to {OUTPUT_DIR / 'example_point_map.html'}")

    # Heatmap
    m = heatmap(df, value_col='value')
    m.save(str(OUTPUT_DIR / 'example_heatmap.html'))
    print(f"Heatmap saved to {OUTPUT_DIR / 'example_heatmap.html'}")

    # Cluster map
    m = cluster_map(df, popup_cols=['site_id', 'value'])
    m.save(str(OUTPUT_DIR / 'example_cluster_map.html'))
    print(f"Cluster map saved to {OUTPUT_DIR / 'example_cluster_map.html'}")
