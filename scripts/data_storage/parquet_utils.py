"""
Parquet Storage Utilities

Helper functions for saving and loading data in Parquet format.
Parquet is a columnar storage format that provides:
- Efficient compression (often 10x smaller than CSV)
- Fast read/write performance
- Type preservation (dates, numbers, etc. stay as their proper types)
- Support for geospatial data via GeoParquet
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union
from datetime import datetime


# Default data directories (relative to project root)
RAW_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
PROCESSED_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"


def save_parquet(
    df: pd.DataFrame,
    name: str,
    data_dir: Optional[Path] = None,
    partition_cols: Optional[list[str]] = None,
    compression: str = "snappy",
    add_timestamp: bool = False,
) -> Path:
    """
    Save DataFrame to Parquet format.

    Args:
        df: DataFrame to save
        name: Base name for the file (without extension)
        data_dir: Directory to save to (default: data/processed)
        partition_cols: Columns to partition by (creates directory structure)
        compression: Compression algorithm ('snappy', 'gzip', 'brotli', 'zstd')
        add_timestamp: Add timestamp to filename

    Returns:
        Path to saved file/directory
    """
    data_dir = data_dir or PROCESSED_DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    if add_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{name}_{timestamp}"

    if partition_cols:
        # Partitioned dataset (creates directory structure)
        output_path = data_dir / name
        df.to_parquet(
            output_path,
            partition_cols=partition_cols,
            compression=compression,
            index=False,
        )
    else:
        # Single file
        output_path = data_dir / f"{name}.parquet"
        df.to_parquet(output_path, compression=compression, index=False)

    return output_path


def load_parquet(
    name: str,
    data_dir: Optional[Path] = None,
    columns: Optional[list[str]] = None,
    filters: Optional[list] = None,
) -> pd.DataFrame:
    """
    Load DataFrame from Parquet format.

    Args:
        name: File or directory name (with or without .parquet extension)
        data_dir: Directory to load from (default: data/processed)
        columns: Specific columns to load (None for all)
        filters: Row group filters for partitioned data
                 e.g., [("year", ">=", 2020), ("state", "==", "CO")]

    Returns:
        DataFrame
    """
    data_dir = data_dir or PROCESSED_DATA_DIR

    # Handle with or without extension
    if not name.endswith(".parquet"):
        path = data_dir / f"{name}.parquet"
        if not path.exists():
            path = data_dir / name  # Try as directory
    else:
        path = data_dir / name

    return pd.read_parquet(path, columns=columns, filters=filters)


def save_geoparquet(
    gdf: "geopandas.GeoDataFrame",
    name: str,
    data_dir: Optional[Path] = None,
    compression: str = "snappy",
    add_timestamp: bool = False,
) -> Path:
    """
    Save GeoDataFrame to GeoParquet format.

    GeoParquet preserves:
    - Geometry column with proper CRS
    - All attribute columns with types
    - Spatial metadata for tool interoperability

    Args:
        gdf: GeoDataFrame to save
        name: Base name for the file
        data_dir: Directory to save to
        compression: Compression algorithm
        add_timestamp: Add timestamp to filename

    Returns:
        Path to saved file
    """
    data_dir = data_dir or PROCESSED_DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)

    if add_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{name}_{timestamp}"

    output_path = data_dir / f"{name}.parquet"
    gdf.to_parquet(output_path, compression=compression, index=False)

    return output_path


def load_geoparquet(
    name: str,
    data_dir: Optional[Path] = None,
    columns: Optional[list[str]] = None,
) -> "geopandas.GeoDataFrame":
    """
    Load GeoDataFrame from GeoParquet format.

    Args:
        name: File name (with or without .parquet extension)
        data_dir: Directory to load from
        columns: Specific columns to load

    Returns:
        GeoDataFrame with geometry and CRS preserved
    """
    import geopandas as gpd

    data_dir = data_dir or PROCESSED_DATA_DIR

    if not name.endswith(".parquet"):
        path = data_dir / f"{name}.parquet"
    else:
        path = data_dir / name

    return gpd.read_parquet(path, columns=columns)


def list_datasets(
    data_dir: Optional[Path] = None,
    pattern: str = "*.parquet",
) -> list[dict]:
    """
    List available Parquet datasets.

    Args:
        data_dir: Directory to search
        pattern: Glob pattern to match

    Returns:
        List of dicts with dataset info (name, path, size, modified)
    """
    data_dir = data_dir or PROCESSED_DATA_DIR

    datasets = []
    for path in data_dir.glob(pattern):
        stat = path.stat()
        datasets.append({
            "name": path.stem,
            "path": path,
            "size_mb": stat.st_size / (1024 * 1024),
            "modified": datetime.fromtimestamp(stat.st_mtime),
        })

    # Also check for partitioned datasets (directories)
    for path in data_dir.iterdir():
        if path.is_dir() and list(path.glob("**/*.parquet")):
            # Sum size of all parquet files in directory
            total_size = sum(f.stat().st_size for f in path.glob("**/*.parquet"))
            datasets.append({
                "name": path.name,
                "path": path,
                "size_mb": total_size / (1024 * 1024),
                "modified": datetime.fromtimestamp(path.stat().st_mtime),
                "partitioned": True,
            })

    return sorted(datasets, key=lambda x: x["modified"], reverse=True)


def parquet_info(
    name: str,
    data_dir: Optional[Path] = None,
) -> dict:
    """
    Get metadata about a Parquet file.

    Args:
        name: File name
        data_dir: Directory

    Returns:
        Dict with schema, row count, size, etc.
    """
    import pyarrow.parquet as pq

    data_dir = data_dir or PROCESSED_DATA_DIR

    if not name.endswith(".parquet"):
        path = data_dir / f"{name}.parquet"
    else:
        path = data_dir / name

    pf = pq.ParquetFile(path)
    metadata = pf.metadata

    schema_info = []
    for i in range(len(pf.schema)):
        field = pf.schema[i]
        schema_info.append({
            "name": field.name,
            "type": str(field.physical_type),
            "logical_type": str(field.logical_type) if field.logical_type else None,
        })

    return {
        "num_rows": metadata.num_rows,
        "num_columns": metadata.num_columns,
        "num_row_groups": metadata.num_row_groups,
        "created_by": metadata.created_by,
        "size_mb": path.stat().st_size / (1024 * 1024),
        "schema": schema_info,
    }


# Example usage
if __name__ == "__main__":
    # Create sample data
    df = pd.DataFrame({
        "site_id": ["SITE001", "SITE002", "SITE003"],
        "measurement_date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        "value": [10.5, 11.2, 9.8],
        "state": ["CO", "CO", "AZ"],
    })

    # Save
    path = save_parquet(df, "example_data", data_dir=PROCESSED_DATA_DIR)
    print(f"Saved to: {path}")

    # Load
    loaded = load_parquet("example_data")
    print(f"Loaded {len(loaded)} rows")
    print(f"Types preserved: {loaded.dtypes.to_dict()}")

    # List datasets
    datasets = list_datasets()
    print(f"Available datasets: {[d['name'] for d in datasets]}")
