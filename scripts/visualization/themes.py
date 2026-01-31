"""
Visualization Themes and Color Palettes

Provides consistent, high-quality visual styling across all visualizations.
Includes colorblind-safe palettes and publication-ready themes.
"""

from dataclasses import dataclass
from typing import Optional, Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns


# =============================================================================
# Color Palettes
# =============================================================================

PALETTES = {
    # Scientific palette - professional, clean
    "scientific": [
        "#2E86AB",  # Steel blue
        "#A23B72",  # Magenta
        "#F18F01",  # Orange
        "#C73E1D",  # Red
        "#3B1F2B",  # Dark purple
        "#44AF69",  # Green
        "#FCAB10",  # Gold
        "#2D3047",  # Navy
    ],

    # Earth tones - natural, environmental
    "earth": [
        "#264653",  # Dark teal
        "#2A9D8F",  # Teal
        "#E9C46A",  # Sand
        "#F4A261",  # Orange
        "#E76F51",  # Terracotta
        "#8AB17D",  # Sage
        "#5C4D7D",  # Purple
        "#C9ADA7",  # Dusty rose
    ],

    # Water-themed palette
    "water": [
        "#03045E",  # Navy
        "#023E8A",  # Dark blue
        "#0077B6",  # Blue
        "#0096C7",  # Light blue
        "#00B4D8",  # Cyan
        "#48CAE4",  # Sky
        "#90E0EF",  # Pale blue
        "#CAF0F8",  # Ice blue
    ],

    # Colorblind-safe palette (optimized for deuteranopia, protanopia, tritanopia)
    "colorblind_safe": [
        "#0077BB",  # Blue
        "#33BBEE",  # Cyan
        "#009988",  # Teal
        "#EE7733",  # Orange
        "#CC3311",  # Red
        "#EE3377",  # Magenta
        "#BBBBBB",  # Gray
        "#000000",  # Black
    ],

    # Categorical palette - high contrast
    "categorical": [
        "#4363d8",  # Blue
        "#e6194B",  # Red
        "#3cb44b",  # Green
        "#ffe119",  # Yellow
        "#911eb4",  # Purple
        "#42d4f4",  # Cyan
        "#f58231",  # Orange
        "#bfef45",  # Lime
    ],

    # Sequential blue (for continuous data)
    "sequential_blue": [
        "#f7fbff",
        "#deebf7",
        "#c6dbef",
        "#9ecae1",
        "#6baed6",
        "#4292c6",
        "#2171b5",
        "#084594",
    ],

    # Diverging (for data with meaningful center)
    "diverging": [
        "#d73027",
        "#f46d43",
        "#fdae61",
        "#fee090",
        "#e0f3f8",
        "#abd9e9",
        "#74add1",
        "#4575b4",
    ],
}


# =============================================================================
# Theme Dataclasses
# =============================================================================

@dataclass
class PlotTheme:
    """Configuration for matplotlib/seaborn plots."""
    name: str
    style: str  # seaborn style: 'whitegrid', 'darkgrid', 'white', 'dark', 'ticks'
    context: str  # seaborn context: 'paper', 'notebook', 'talk', 'poster'
    palette: str  # palette name from PALETTES
    font_family: str
    title_size: int
    label_size: int
    tick_size: int
    legend_size: int
    line_width: float
    marker_size: int
    figure_facecolor: str
    axes_facecolor: str
    grid_color: str
    text_color: str
    dpi: int
    figure_size: tuple


@dataclass
class MapTheme:
    """Configuration for Folium maps."""
    name: str
    tiles: str  # Folium tile layer
    marker_color: str
    marker_fill_opacity: float
    marker_line_opacity: float
    popup_max_width: int
    legend_position: str  # 'bottomleft', 'bottomright', 'topleft', 'topright'
    legend_bg_color: str
    legend_border_color: str
    control_position: str


@dataclass
class TableTheme:
    """Configuration for styled tables."""
    name: str
    header_bg_color: str
    header_text_color: str
    row_even_bg: str
    row_odd_bg: str
    row_hover_bg: str
    border_color: str
    font_family: str
    font_size: str


# =============================================================================
# Predefined Themes
# =============================================================================

PLOT_THEMES: Dict[str, PlotTheme] = {
    "light": PlotTheme(
        name="light",
        style="whitegrid",
        context="notebook",
        palette="scientific",
        font_family="sans-serif",
        title_size=14,
        label_size=12,
        tick_size=10,
        legend_size=10,
        line_width=1.5,
        marker_size=6,
        figure_facecolor="white",
        axes_facecolor="white",
        grid_color="#E5E5E5",
        text_color="#333333",
        dpi=100,
        figure_size=(10, 6),
    ),

    "dark": PlotTheme(
        name="dark",
        style="darkgrid",
        context="notebook",
        palette="scientific",
        font_family="sans-serif",
        title_size=14,
        label_size=12,
        tick_size=10,
        legend_size=10,
        line_width=1.5,
        marker_size=6,
        figure_facecolor="#1a1a2e",
        axes_facecolor="#16213e",
        grid_color="#404040",
        text_color="#E5E5E5",
        dpi=100,
        figure_size=(10, 6),
    ),

    "publication": PlotTheme(
        name="publication",
        style="ticks",
        context="paper",
        palette="colorblind_safe",
        font_family="serif",
        title_size=12,
        label_size=11,
        tick_size=10,
        legend_size=9,
        line_width=1.0,
        marker_size=5,
        figure_facecolor="white",
        axes_facecolor="white",
        grid_color="#CCCCCC",
        text_color="#000000",
        dpi=300,
        figure_size=(6.5, 4),  # ~half page width
    ),

    "presentation": PlotTheme(
        name="presentation",
        style="whitegrid",
        context="talk",
        palette="categorical",
        font_family="sans-serif",
        title_size=20,
        label_size=16,
        tick_size=14,
        legend_size=14,
        line_width=2.5,
        marker_size=10,
        figure_facecolor="white",
        axes_facecolor="white",
        grid_color="#E5E5E5",
        text_color="#333333",
        dpi=150,
        figure_size=(12, 7),
    ),
}


MAP_THEMES: Dict[str, MapTheme] = {
    "light": MapTheme(
        name="light",
        tiles="CartoDB positron",
        marker_color="#2E86AB",
        marker_fill_opacity=0.7,
        marker_line_opacity=0.9,
        popup_max_width=300,
        legend_position="bottomright",
        legend_bg_color="white",
        legend_border_color="#cccccc",
        control_position="topright",
    ),

    "dark": MapTheme(
        name="dark",
        tiles="CartoDB dark_matter",
        marker_color="#48CAE4",
        marker_fill_opacity=0.8,
        marker_line_opacity=1.0,
        popup_max_width=300,
        legend_position="bottomright",
        legend_bg_color="#2d3748",
        legend_border_color="#4a5568",
        control_position="topright",
    ),

    "satellite": MapTheme(
        name="satellite",
        tiles="Esri.WorldImagery",
        marker_color="#F18F01",
        marker_fill_opacity=0.9,
        marker_line_opacity=1.0,
        popup_max_width=300,
        legend_position="bottomleft",
        legend_bg_color="rgba(255,255,255,0.9)",
        legend_border_color="#666666",
        control_position="topright",
    ),

    "terrain": MapTheme(
        name="terrain",
        tiles="Stamen Terrain",
        marker_color="#C73E1D",
        marker_fill_opacity=0.8,
        marker_line_opacity=1.0,
        popup_max_width=300,
        legend_position="bottomright",
        legend_bg_color="white",
        legend_border_color="#999999",
        control_position="topright",
    ),
}


TABLE_THEMES: Dict[str, TableTheme] = {
    "light": TableTheme(
        name="light",
        header_bg_color="#4A90A4",
        header_text_color="white",
        row_even_bg="#f8f9fa",
        row_odd_bg="white",
        row_hover_bg="#e9ecef",
        border_color="#dee2e6",
        font_family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        font_size="14px",
    ),

    "dark": TableTheme(
        name="dark",
        header_bg_color="#2d3748",
        header_text_color="#e2e8f0",
        row_even_bg="#1a202c",
        row_odd_bg="#2d3748",
        row_hover_bg="#4a5568",
        border_color="#4a5568",
        font_family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        font_size="14px",
    ),

    "minimal": TableTheme(
        name="minimal",
        header_bg_color="transparent",
        header_text_color="#333333",
        row_even_bg="transparent",
        row_odd_bg="transparent",
        row_hover_bg="#f5f5f5",
        border_color="#e0e0e0",
        font_family="'Georgia', serif",
        font_size="13px",
    ),
}


# =============================================================================
# Theme Application Functions
# =============================================================================

# Global state for current theme
_current_theme = "light"


def set_theme(
    theme: str = "light",
    target: str = "all",
) -> None:
    """
    Set the visualization theme.

    Args:
        theme: Theme name ('light', 'dark', 'publication', 'presentation')
        target: What to apply theme to ('all', 'plots', 'maps', 'tables')

    Example:
        >>> set_theme('dark')  # Apply dark theme to all
        >>> set_theme('publication', target='plots')  # Just plots
    """
    global _current_theme
    _current_theme = theme

    if target in ("all", "plots"):
        _apply_plot_theme(theme)


def _apply_plot_theme(theme_name: str) -> None:
    """Apply theme settings to matplotlib/seaborn."""
    theme = PLOT_THEMES.get(theme_name, PLOT_THEMES["light"])

    # Set seaborn style and context
    sns.set_theme(style=theme.style, context=theme.context)

    # Set color palette
    if theme.palette in PALETTES:
        sns.set_palette(PALETTES[theme.palette])

    # Configure matplotlib rcParams
    plt.rcParams.update({
        'figure.facecolor': theme.figure_facecolor,
        'axes.facecolor': theme.axes_facecolor,
        'axes.edgecolor': theme.text_color,
        'axes.labelcolor': theme.text_color,
        'axes.titlesize': theme.title_size,
        'axes.labelsize': theme.label_size,
        'xtick.color': theme.text_color,
        'ytick.color': theme.text_color,
        'xtick.labelsize': theme.tick_size,
        'ytick.labelsize': theme.tick_size,
        'legend.fontsize': theme.legend_size,
        'legend.framealpha': 0.8,
        'grid.color': theme.grid_color,
        'lines.linewidth': theme.line_width,
        'lines.markersize': theme.marker_size,
        'figure.dpi': theme.dpi,
        'figure.figsize': theme.figure_size,
        'font.family': theme.font_family,
        'text.color': theme.text_color,
    })


def get_current_theme() -> str:
    """Get the name of the current theme."""
    return _current_theme


def get_palette(name: str = "scientific") -> List[str]:
    """
    Get a color palette by name.

    Args:
        name: Palette name from PALETTES

    Returns:
        List of hex color codes
    """
    return PALETTES.get(name, PALETTES["scientific"])


def get_plot_theme(name: Optional[str] = None) -> PlotTheme:
    """
    Get plot theme configuration.

    Args:
        name: Theme name (uses current theme if None)

    Returns:
        PlotTheme dataclass
    """
    theme_name = name or _current_theme
    return PLOT_THEMES.get(theme_name, PLOT_THEMES["light"])


def get_map_theme(name: Optional[str] = None) -> MapTheme:
    """
    Get map theme configuration.

    Args:
        name: Theme name (uses current theme if None)

    Returns:
        MapTheme dataclass
    """
    theme_name = name or _current_theme
    return MAP_THEMES.get(theme_name, MAP_THEMES["light"])


def get_table_theme(name: Optional[str] = None) -> TableTheme:
    """
    Get table theme configuration.

    Args:
        name: Theme name (uses current theme if None)

    Returns:
        TableTheme dataclass
    """
    theme_name = name or _current_theme
    return TABLE_THEMES.get(theme_name, TABLE_THEMES["light"])


def save_figure(
    fig: plt.Figure,
    path: str,
    quality: str = "high",
    transparent: bool = False,
) -> None:
    """
    Save figure with quality presets.

    Args:
        fig: Matplotlib figure to save
        path: Output path
        quality: 'draft', 'high', or 'publication'
        transparent: Transparent background

    Example:
        >>> fig = time_series_plot(df, 'date', 'value')
        >>> save_figure(fig, 'output.png', quality='publication')
    """
    quality_settings = {
        "draft": {"dpi": 100, "bbox_inches": "tight"},
        "high": {"dpi": 200, "bbox_inches": "tight"},
        "publication": {"dpi": 300, "bbox_inches": "tight", "pad_inches": 0.1},
    }

    settings = quality_settings.get(quality, quality_settings["high"])
    settings["transparent"] = transparent

    fig.savefig(path, **settings)


def list_themes() -> Dict[str, List[str]]:
    """
    List all available themes.

    Returns:
        Dict with theme names for each category
    """
    return {
        "plot_themes": list(PLOT_THEMES.keys()),
        "map_themes": list(MAP_THEMES.keys()),
        "table_themes": list(TABLE_THEMES.keys()),
        "palettes": list(PALETTES.keys()),
    }


def preview_palette(name: str = "scientific") -> plt.Figure:
    """
    Create a visual preview of a color palette.

    Args:
        name: Palette name

    Returns:
        Figure showing the palette colors
    """
    colors = get_palette(name)

    fig, ax = plt.subplots(figsize=(len(colors) * 1.2, 2))

    for i, color in enumerate(colors):
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, facecolor=color))
        ax.text(i + 0.5, -0.15, color, ha='center', va='top', fontsize=8, rotation=45)

    ax.set_xlim(0, len(colors))
    ax.set_ylim(-0.5, 1)
    ax.set_title(f'Palette: {name}', fontsize=12)
    ax.axis('off')

    plt.tight_layout()
    return fig


# Initialize with default theme on import
set_theme("light")


# Example usage
if __name__ == "__main__":
    import numpy as np
    import pandas as pd

    # List available themes
    print("Available themes:")
    for category, themes in list_themes().items():
        print(f"  {category}: {themes}")

    # Preview a palette
    fig = preview_palette("scientific")
    plt.show()

    # Example with different themes
    np.random.seed(42)
    df = pd.DataFrame({
        'x': range(50),
        'y': np.cumsum(np.random.randn(50)),
    })

    for theme_name in ["light", "dark", "publication"]:
        set_theme(theme_name)
        fig, ax = plt.subplots()
        ax.plot(df['x'], df['y'], marker='o')
        ax.set_title(f'{theme_name.title()} Theme Example')
        plt.tight_layout()
        plt.show()
