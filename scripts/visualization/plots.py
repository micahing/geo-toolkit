"""
Common Plot Functions

Matplotlib/Seaborn-based plotting utilities for data analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Union, Tuple
from pathlib import Path


# Set default style
sns.set_theme(style="whitegrid")

# Default figure save directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "outputs"


def time_series_plot(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    group_col: Optional[str] = None,
    title: Optional[str] = None,
    xlabel: str = "Date",
    ylabel: Optional[str] = None,
    figsize: Tuple[int, int] = (12, 6),
    rolling_window: Optional[int] = None,
    show_trend: bool = False,
    save_path: Optional[Path] = None,
) -> plt.Figure:
    """
    Create a time series line plot.

    Args:
        df: Input DataFrame
        date_col: Column containing dates
        value_col: Column containing values to plot
        group_col: Column to group/color by (creates multiple lines)
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label (defaults to value_col)
        figsize: Figure size
        rolling_window: Add rolling average line with this window size
        show_trend: Add linear trend line
        save_path: Path to save figure

    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    if group_col:
        for name, group in df.groupby(group_col):
            ax.plot(group[date_col], group[value_col], label=name, alpha=0.8)
        ax.legend(title=group_col)
    else:
        ax.plot(df[date_col], df[value_col], alpha=0.8)

        if rolling_window:
            rolling = df[value_col].rolling(window=rolling_window).mean()
            ax.plot(df[date_col], rolling, color='red', linewidth=2,
                   label=f'{rolling_window}-period moving average')
            ax.legend()

        if show_trend:
            # Add linear trend
            x_numeric = pd.to_numeric(df[date_col])
            z = np.polyfit(x_numeric, df[value_col].ffill(), 1)
            p = np.poly1d(z)
            ax.plot(df[date_col], p(x_numeric), "r--", alpha=0.8, label='Trend')
            ax.legend()

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel or value_col)
    ax.set_title(title or f"{value_col} Over Time")

    plt.xticks(rotation=45)
    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    size_col: Optional[str] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 8),
    alpha: float = 0.6,
    show_regression: bool = False,
    save_path: Optional[Path] = None,
) -> plt.Figure:
    """
    Create a scatter plot.

    Args:
        df: Input DataFrame
        x_col: Column for x-axis
        y_col: Column for y-axis
        color_col: Column for point colors
        size_col: Column for point sizes
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size
        alpha: Point transparency
        show_regression: Add regression line
        save_path: Path to save figure

    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    scatter_kwargs = {
        'x': x_col,
        'y': y_col,
        'data': df,
        'alpha': alpha,
        'ax': ax,
    }

    if color_col:
        scatter_kwargs['hue'] = color_col
    if size_col:
        scatter_kwargs['size'] = size_col

    sns.scatterplot(**scatter_kwargs)

    if show_regression:
        # Add regression line
        mask = df[[x_col, y_col]].notna().all(axis=1)
        x = df.loc[mask, x_col]
        y = df.loc[mask, y_col]
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        x_line = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_line, p(x_line), "r--", alpha=0.8, label=f'y = {z[0]:.3f}x + {z[1]:.3f}')
        ax.legend()

    ax.set_xlabel(xlabel or x_col)
    ax.set_ylabel(ylabel or y_col)
    ax.set_title(title or f"{y_col} vs {x_col}")

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def histogram(
    df: pd.DataFrame,
    column: str,
    bins: int = 30,
    group_col: Optional[str] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
    show_kde: bool = True,
    show_stats: bool = True,
    save_path: Optional[Path] = None,
) -> plt.Figure:
    """
    Create a histogram with optional KDE.

    Args:
        df: Input DataFrame
        column: Column to plot
        bins: Number of bins
        group_col: Column to group by (overlapping histograms)
        title: Plot title
        xlabel: X-axis label
        figsize: Figure size
        show_kde: Overlay kernel density estimate
        show_stats: Show mean/median lines and text
        save_path: Path to save figure

    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    if group_col:
        for name, group in df.groupby(group_col):
            sns.histplot(group[column], bins=bins, kde=show_kde,
                        label=name, alpha=0.5, ax=ax)
        ax.legend(title=group_col)
    else:
        sns.histplot(df[column], bins=bins, kde=show_kde, ax=ax)

        if show_stats:
            mean_val = df[column].mean()
            median_val = df[column].median()
            ax.axvline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.2f}')
            ax.axvline(median_val, color='green', linestyle=':', label=f'Median: {median_val:.2f}')
            ax.legend()

    ax.set_xlabel(xlabel or column)
    ax.set_ylabel("Count")
    ax.set_title(title or f"Distribution of {column}")

    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def box_plot(
    df: pd.DataFrame,
    value_col: str,
    group_col: Optional[str] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 6),
    show_points: bool = False,
    horizontal: bool = False,
    save_path: Optional[Path] = None,
) -> plt.Figure:
    """
    Create a box plot.

    Args:
        df: Input DataFrame
        value_col: Column containing values
        group_col: Column to group by (creates multiple boxes)
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size
        show_points: Overlay individual data points
        horizontal: Make boxes horizontal
        save_path: Path to save figure

    Returns:
        Matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    if horizontal:
        x, y = value_col, group_col
    else:
        x, y = group_col, value_col

    sns.boxplot(data=df, x=x, y=y, ax=ax)

    if show_points:
        sns.stripplot(data=df, x=x, y=y, ax=ax,
                     color='black', alpha=0.3, size=3)

    if horizontal:
        ax.set_xlabel(xlabel or value_col)
        ax.set_ylabel(ylabel or group_col)
    else:
        ax.set_xlabel(xlabel or group_col)
        ax.set_ylabel(ylabel or value_col)

    ax.set_title(title or f"Distribution of {value_col}")

    plt.xticks(rotation=45 if not horizontal else 0)
    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


def correlation_heatmap(
    df: pd.DataFrame,
    columns: Optional[list[str]] = None,
    method: str = 'pearson',
    title: str = "Correlation Matrix",
    figsize: Tuple[int, int] = (10, 8),
    annot: bool = True,
    cmap: str = 'RdBu_r',
    save_path: Optional[Path] = None,
) -> plt.Figure:
    """
    Create a correlation heatmap.

    Args:
        df: Input DataFrame
        columns: Columns to include (all numeric if None)
        method: Correlation method ('pearson', 'spearman', 'kendall')
        title: Plot title
        figsize: Figure size
        annot: Show correlation values in cells
        cmap: Color map
        save_path: Path to save figure

    Returns:
        Matplotlib Figure object
    """
    if columns:
        corr_df = df[columns]
    else:
        corr_df = df.select_dtypes(include=[np.number])

    corr_matrix = corr_df.corr(method=method)

    fig, ax = plt.subplots(figsize=figsize)

    sns.heatmap(
        corr_matrix,
        annot=annot,
        cmap=cmap,
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.5,
        ax=ax,
        fmt='.2f' if annot else None,
    )

    ax.set_title(title)
    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    return fig


# Example usage
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'value': np.cumsum(np.random.randn(100)) + 50,
        'category': np.random.choice(['A', 'B', 'C'], 100),
        'x': np.random.randn(100),
        'y': np.random.randn(100),
    })

    # Time series
    fig = time_series_plot(df, 'date', 'value', rolling_window=7)
    plt.show()

    # Scatter
    fig = scatter_plot(df, 'x', 'y', color_col='category', show_regression=True)
    plt.show()

    # Histogram
    fig = histogram(df, 'value', show_stats=True)
    plt.show()

    # Box plot
    fig = box_plot(df, 'value', group_col='category', show_points=True)
    plt.show()
