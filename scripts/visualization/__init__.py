# Visualization Module
from .plots import (
    time_series_plot,
    scatter_plot,
    histogram,
    box_plot,
    correlation_heatmap,
)
from .tables import (
    summary_table,
    styled_dataframe,
    export_table,
    pivot_table,
    comparison_table,
    display_full_table,
    paginated_table,
    table_to_html_scrollable,
    display_scrollable_table,
)
from .maps import (
    point_map,
    choropleth_map,
    heatmap,
    cluster_map,
    static_map,
)
from .themes import (
    set_theme,
    get_current_theme,
    get_palette,
    get_plot_theme,
    get_map_theme,
    get_table_theme,
    save_figure,
    list_themes,
    preview_palette,
    PALETTES,
    PLOT_THEMES,
    MAP_THEMES,
    TABLE_THEMES,
)

__all__ = [
    # Plots
    "time_series_plot",
    "scatter_plot",
    "histogram",
    "box_plot",
    "correlation_heatmap",
    # Tables
    "summary_table",
    "styled_dataframe",
    "export_table",
    "pivot_table",
    "comparison_table",
    "display_full_table",
    "paginated_table",
    "table_to_html_scrollable",
    "display_scrollable_table",
    # Maps
    "point_map",
    "choropleth_map",
    "heatmap",
    "cluster_map",
    "static_map",
    # Themes
    "set_theme",
    "get_current_theme",
    "get_palette",
    "get_plot_theme",
    "get_map_theme",
    "get_table_theme",
    "save_figure",
    "list_themes",
    "preview_palette",
    "PALETTES",
    "PLOT_THEMES",
    "MAP_THEMES",
    "TABLE_THEMES",
]
