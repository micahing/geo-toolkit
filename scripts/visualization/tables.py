"""
Table Formatting and Export Utilities

Functions for creating styled tables and exporting to various formats.
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, Callable, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from pandas.io.formats.style import Styler


# Default output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "outputs"


def summary_table(
    df: pd.DataFrame,
    columns: Optional[list[str]] = None,
    group_by: Optional[str] = None,
    stats: list[str] = ['count', 'mean', 'std', 'min', 'max'],
    percentiles: Optional[list[float]] = None,
    round_digits: int = 2,
) -> pd.DataFrame:
    """
    Create a summary statistics table.

    Args:
        df: Input DataFrame
        columns: Columns to summarize (all numeric if None)
        group_by: Column to group by
        stats: Statistics to compute
        percentiles: Percentiles to include (e.g., [0.25, 0.5, 0.75])
        round_digits: Decimal places to round to

    Returns:
        DataFrame with summary statistics
    """
    if columns:
        numeric_df = df[columns].select_dtypes(include=[np.number])
    else:
        numeric_df = df.select_dtypes(include=[np.number])

    if group_by:
        # Grouped summary
        agg_dict = {}
        for col in numeric_df.columns:
            agg_dict[col] = stats

        summary = df.groupby(group_by)[numeric_df.columns].agg(stats)

        if percentiles:
            for p in percentiles:
                pct_summary = df.groupby(group_by)[numeric_df.columns].quantile(p)
                pct_summary.columns = [f"{col}_p{int(p*100)}" for col in pct_summary.columns]
                summary = summary.join(pct_summary)
    else:
        # Overall summary
        summary = numeric_df.describe(percentiles=percentiles)

        # Add additional stats if requested
        additional_stats = {}
        if 'sum' in stats and 'sum' not in summary.index:
            additional_stats['sum'] = numeric_df.sum()
        if 'median' in stats and '50%' not in summary.index:
            additional_stats['median'] = numeric_df.median()
        if 'var' in stats:
            additional_stats['var'] = numeric_df.var()
        if 'skew' in stats:
            additional_stats['skew'] = numeric_df.skew()
        if 'kurtosis' in stats:
            additional_stats['kurtosis'] = numeric_df.kurtosis()

        if additional_stats:
            additional_df = pd.DataFrame(additional_stats).T
            summary = pd.concat([summary, additional_df])

    return summary.round(round_digits)


def styled_dataframe(
    df: pd.DataFrame,
    highlight_max: Optional[list[str]] = None,
    highlight_min: Optional[list[str]] = None,
    gradient_columns: Optional[list[str]] = None,
    bar_columns: Optional[list[str]] = None,
    format_dict: Optional[dict] = None,
    caption: Optional[str] = None,
) -> "Styler":
    """
    Create a styled DataFrame for display in Jupyter notebooks.

    Args:
        df: Input DataFrame
        highlight_max: Columns to highlight maximum value
        highlight_min: Columns to highlight minimum value
        gradient_columns: Columns to apply background color gradient
        bar_columns: Columns to show as horizontal bars
        format_dict: Column format strings (e.g., {'price': '${:.2f}'})
        caption: Table caption

    Returns:
        Styled DataFrame
    """
    styler = df.style

    if caption:
        styler = styler.set_caption(caption)

    if format_dict:
        styler = styler.format(format_dict)

    if highlight_max:
        styler = styler.highlight_max(
            subset=highlight_max,
            color='lightgreen'
        )

    if highlight_min:
        styler = styler.highlight_min(
            subset=highlight_min,
            color='lightcoral'
        )

    if gradient_columns:
        styler = styler.background_gradient(
            subset=gradient_columns,
            cmap='Blues'
        )

    if bar_columns:
        styler = styler.bar(
            subset=bar_columns,
            color='steelblue',
            align='left'
        )

    return styler


def export_table(
    df: pd.DataFrame,
    name: str,
    formats: list[str] = ['csv'],
    output_dir: Optional[Path] = None,
    index: bool = False,
    **kwargs,
) -> dict[str, Path]:
    """
    Export DataFrame to multiple formats.

    Args:
        df: DataFrame to export
        name: Base filename (without extension)
        formats: List of formats ('csv', 'excel', 'html', 'latex', 'markdown', 'json')
        output_dir: Output directory
        index: Include index in output
        **kwargs: Additional arguments passed to export methods

    Returns:
        Dict mapping format to output path
    """
    output_dir = output_dir or OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {}

    for fmt in formats:
        if fmt == 'csv':
            path = output_dir / f"{name}.csv"
            df.to_csv(path, index=index, **kwargs)

        elif fmt == 'excel':
            path = output_dir / f"{name}.xlsx"
            df.to_excel(path, index=index, **kwargs)

        elif fmt == 'html':
            path = output_dir / f"{name}.html"
            html = df.to_html(index=index, **kwargs)
            # Wrap in basic HTML structure
            full_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{name}</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #ddd; }}
    </style>
</head>
<body>
{html}
</body>
</html>"""
            path.write_text(full_html)

        elif fmt == 'latex':
            path = output_dir / f"{name}.tex"
            latex = df.to_latex(index=index, **kwargs)
            path.write_text(latex)

        elif fmt == 'markdown':
            path = output_dir / f"{name}.md"
            md = df.to_markdown(index=index, **kwargs)
            path.write_text(md)

        elif fmt == 'json':
            path = output_dir / f"{name}.json"
            df.to_json(path, orient='records', indent=2, **kwargs)

        else:
            raise ValueError(f"Unknown format: {fmt}")

        paths[fmt] = path

    return paths


def pivot_table(
    df: pd.DataFrame,
    values: str,
    index: str,
    columns: str,
    aggfunc: Union[str, Callable] = 'mean',
    fill_value: Optional[any] = None,
    margins: bool = False,
    margins_name: str = 'Total',
) -> pd.DataFrame:
    """
    Create a pivot table.

    Args:
        df: Input DataFrame
        values: Column to aggregate
        index: Column for row labels
        columns: Column for column labels
        aggfunc: Aggregation function
        fill_value: Value for missing combinations
        margins: Add row/column totals
        margins_name: Name for margins

    Returns:
        Pivot table DataFrame
    """
    return pd.pivot_table(
        df,
        values=values,
        index=index,
        columns=columns,
        aggfunc=aggfunc,
        fill_value=fill_value,
        margins=margins,
        margins_name=margins_name,
    )


def comparison_table(
    dfs: dict[str, pd.DataFrame],
    columns: list[str],
    labels: Optional[list[str]] = None,
    round_digits: int = 2,
) -> pd.DataFrame:
    """
    Create a side-by-side comparison of statistics from multiple DataFrames.

    Args:
        dfs: Dict of name -> DataFrame
        columns: Columns to compare
        labels: Statistics to compute (default: mean, std, count)
        round_digits: Decimal places

    Returns:
        Comparison DataFrame
    """
    if labels is None:
        labels = ['mean', 'std', 'count']

    comparisons = {}

    for name, df in dfs.items():
        stats = df[columns].agg(labels)
        # Flatten multi-index if needed
        if isinstance(stats, pd.DataFrame):
            stats = stats.unstack()
            stats.index = [f"{col}_{stat}" for stat, col in stats.index]
        comparisons[name] = stats

    result = pd.DataFrame(comparisons).round(round_digits)
    return result


def display_full_table(
    df: pd.DataFrame,
    max_rows: Optional[int] = None,
    max_cols: Optional[int] = None,
    precision: int = 2,
) -> None:
    """
    Display DataFrame without truncation in Jupyter notebooks.

    Uses pandas display options to show the full table without
    row or column truncation.

    Args:
        df: Input DataFrame
        max_rows: Maximum rows to display (None for unlimited)
        max_cols: Maximum columns to display (None for unlimited)
        precision: Decimal places for float display

    Example:
        >>> display_full_table(df)  # Shows all rows and columns
        >>> display_full_table(df, max_rows=200)  # Limit to 200 rows
    """
    with pd.option_context(
        'display.max_rows', max_rows,
        'display.max_columns', max_cols,
        'display.precision', precision,
        'display.width', None,
        'display.max_colwidth', None,
    ):
        try:
            from IPython.display import display
            display(df)
        except ImportError:
            # Fallback for non-Jupyter environments
            print(df.to_string())


def paginated_table(
    df: pd.DataFrame,
    page_size: int = 25,
    page: int = 1,
) -> pd.DataFrame:
    """
    Return a paginated view of a DataFrame.

    Useful for exploring large DataFrames one page at a time.

    Args:
        df: Input DataFrame
        page_size: Number of rows per page
        page: Page number (1-indexed)

    Returns:
        DataFrame slice for the requested page

    Example:
        >>> paginated_table(df, page_size=10, page=1)  # First 10 rows
        >>> paginated_table(df, page_size=10, page=3)  # Rows 21-30
    """
    if page < 1:
        raise ValueError("Page number must be 1 or greater")

    total_rows = len(df)
    total_pages = (total_rows + page_size - 1) // page_size

    if page > total_pages and total_pages > 0:
        raise ValueError(f"Page {page} exceeds total pages ({total_pages})")

    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)

    print(f"Page {page} of {total_pages} (rows {start_idx + 1}-{end_idx} of {total_rows})")

    return df.iloc[start_idx:end_idx]


def table_to_html_scrollable(
    df: pd.DataFrame,
    height: str = "400px",
    caption: Optional[str] = None,
    striped: bool = True,
    hover: bool = True,
) -> str:
    """
    Create a scrollable HTML table with sticky headers.

    Generates an HTML string that can be displayed in Jupyter
    or saved to a file. The table has a fixed height with
    scrolling and sticky column headers.

    Args:
        df: Input DataFrame
        height: CSS height for scrollable container (e.g., '400px', '50vh')
        caption: Optional table caption
        striped: Alternate row colors
        hover: Highlight rows on hover

    Returns:
        HTML string with scrollable table

    Example:
        >>> html = table_to_html_scrollable(df, height='300px')
        >>> from IPython.display import HTML, display
        >>> display(HTML(html))
    """
    # Generate unique ID for this table
    import hashlib
    table_id = f"table_{hashlib.md5(str(id(df)).encode()).hexdigest()[:8]}"

    # Build CSS styles
    stripe_style = """
        #{table_id} tbody tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
    """ if striped else ""

    hover_style = """
        #{table_id} tbody tr:hover {{
            background-color: #e9ecef;
        }}
    """ if hover else ""

    caption_html = f"<caption style='caption-side: top; font-weight: bold; font-size: 1.1em; margin-bottom: 10px;'>{caption}</caption>" if caption else ""

    html = f"""
    <style>
        #{table_id}-container {{
            max-height: {height};
            overflow-y: auto;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }}
        #{table_id} {{
            border-collapse: collapse;
            width: 100%;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
        }}
        #{table_id} thead {{
            position: sticky;
            top: 0;
            z-index: 1;
        }}
        #{table_id} th {{
            background-color: #4A90A4;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #357a8a;
        }}
        #{table_id} td {{
            padding: 10px 8px;
            border-bottom: 1px solid #dee2e6;
        }}
        {stripe_style.format(table_id=table_id)}
        {hover_style.format(table_id=table_id)}
    </style>
    <div id="{table_id}-container">
        <table id="{table_id}">
            {caption_html}
            <thead>
                <tr>
                    {"".join(f'<th>{col}</th>' for col in df.columns)}
                </tr>
            </thead>
            <tbody>
    """

    for _, row in df.iterrows():
        html += "<tr>"
        for val in row:
            # Format values nicely
            if pd.isna(val):
                cell_val = '<span style="color: #999;">—</span>'
            elif isinstance(val, float):
                cell_val = f"{val:.4g}"
            else:
                cell_val = str(val)
            html += f"<td>{cell_val}</td>"
        html += "</tr>\n"

    html += """
            </tbody>
        </table>
    </div>
    """

    return html


def display_scrollable_table(
    df: pd.DataFrame,
    height: str = "400px",
    caption: Optional[str] = None,
    striped: bool = True,
    hover: bool = True,
) -> None:
    """
    Display a scrollable HTML table in Jupyter notebooks.

    Wrapper around table_to_html_scrollable that handles IPython display.

    Args:
        df: Input DataFrame
        height: CSS height for scrollable container
        caption: Optional table caption
        striped: Alternate row colors
        hover: Highlight rows on hover

    Example:
        >>> display_scrollable_table(large_df, height='500px', caption='My Data')
    """
    html = table_to_html_scrollable(df, height, caption, striped, hover)
    try:
        from IPython.display import HTML, display
        display(HTML(html))
    except ImportError:
        print("IPython not available. Use table_to_html_scrollable() to get HTML string.")
        print(df)


# Example usage
if __name__ == "__main__":
    # Sample data
    np.random.seed(42)
    df = pd.DataFrame({
        'site': np.random.choice(['A', 'B', 'C'], 100),
        'year': np.random.choice([2022, 2023, 2024], 100),
        'temperature': np.random.normal(20, 5, 100),
        'ph': np.random.normal(7, 0.5, 100),
        'discharge': np.random.exponential(100, 100),
    })

    # Summary table
    summary = summary_table(df, group_by='site')
    print("Summary by site:")
    print(summary)

    # Pivot table
    pivot = pivot_table(df, values='temperature', index='site', columns='year', margins=True)
    print("\nTemperature by site and year:")
    print(pivot)

    # Export
    paths = export_table(df.head(10), 'sample_data', formats=['csv', 'html', 'markdown'])
    print(f"\nExported to: {paths}")
