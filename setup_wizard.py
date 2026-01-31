#!/usr/bin/env python3
"""
Data Engineering Environment Setup Wizard

An interactive CLI tool that walks users through configuration options
and generates a customized environment based on their selections.

Usage:
    python setup_wizard.py [--output-dir PATH]
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional
import shutil


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def colored(text: str, color: str) -> str:
    """Wrap text in color codes."""
    return f"{color}{text}{Colors.END}"


def print_header(text: str):
    """Print a section header."""
    print()
    print(colored("=" * 60, Colors.CYAN))
    print(colored(f"  {text}", Colors.BOLD + Colors.CYAN))
    print(colored("=" * 60, Colors.CYAN))
    print()


def print_option(num: int, label: str, description: str, recommended: bool = False):
    """Print a menu option."""
    rec_tag = colored(" (Recommended)", Colors.GREEN) if recommended else ""
    print(f"  {colored(str(num), Colors.BOLD)}. {colored(label, Colors.YELLOW)}{rec_tag}")
    print(f"     {description}")
    print()


def get_choice(prompt: str, valid_choices: list[int], default: Optional[int] = None) -> int:
    """Get a validated choice from the user."""
    while True:
        default_hint = f" [{default}]" if default else ""
        try:
            raw = input(f"{prompt}{default_hint}: ").strip()
            if not raw and default:
                return default
            choice = int(raw)
            if choice in valid_choices:
                return choice
            print(colored(f"  Please enter one of: {valid_choices}", Colors.RED))
        except ValueError:
            print(colored("  Please enter a number.", Colors.RED))


def ask_env_manager() -> dict:
    """Ask about environment/package manager preference."""
    print_header("Environment Manager")
    print("Choose how you want to manage Python dependencies:\n")

    print_option(1, "conda/mamba",
                 "Best for GDAL and geospatial deps. conda-forge handles\n"
                 "     compiled C libraries seamlessly. Familiar to scientific community.",
                 recommended=True)
    print_option(2, "uv",
                 "Fast, modern Python package installer. Lightweight but requires\n"
                 "     system GDAL install as a prerequisite.")
    print_option(3, "pip + venv",
                 "Standard Python tooling. Same GDAL challenges as uv,\n"
                 "     slower dependency resolution.")

    choice = get_choice("Your choice", [1, 2, 3], default=1)

    return {
        1: {"name": "conda", "file": "environment.yml"},
        2: {"name": "uv", "file": "pyproject.toml"},
        3: {"name": "pip", "file": "requirements.txt"},
    }[choice]


def ask_data_storage() -> dict:
    """Ask about data storage preference."""
    print_header("Data Storage Format")
    print("Choose how you want to store retrieved data locally:\n")

    print_option(1, "Parquet",
                 "Columnar format, great for analytics. Fast, compressed,\n"
                 "     preserves types. GeoParquet for spatial data.",
                 recommended=True)
    print_option(2, "DuckDB",
                 "Embedded analytics database. SQL queries on files,\n"
                 "     very fast but another tool to learn.")
    print_option(3, "SQLite",
                 "Lightweight relational database. Good for complex joins\n"
                 "     but requires SQL for everything.")
    print_option(4, "CSV/JSON",
                 "Human-readable, universal formats. Simple but slow,\n"
                 "     large files, loses type information.")

    choice = get_choice("Your choice", [1, 2, 3, 4], default=1)

    return {
        1: {"name": "parquet", "packages": ["pyarrow"]},
        2: {"name": "duckdb", "packages": ["duckdb", "pyarrow"]},
        3: {"name": "sqlite", "packages": []},
        4: {"name": "csv", "packages": []},
    }[choice]


def ask_mapping() -> dict:
    """Ask about geospatial visualization preference."""
    print_header("Geospatial Visualization")
    print("Choose your mapping and geospatial visualization approach:\n")

    print_option(1, "Folium + GeoPandas",
                 "Best of both: Folium for interactive web maps,\n"
                 "     GeoPandas + matplotlib for static/print maps.",
                 recommended=True)
    print_option(2, "Plotly/Mapbox",
                 "Modern interactive visualizations. Requires Mapbox\n"
                 "     token for satellite imagery features.")
    print_option(3, "All options",
                 "Maximum flexibility with all mapping libraries.\n"
                 "     Larger dependency footprint.")

    choice = get_choice("Your choice", [1, 2, 3], default=1)

    packages_map = {
        1: ["folium", "geopandas", "mapclassify"],
        2: ["plotly"],
        3: ["folium", "geopandas", "mapclassify", "plotly"],
    }

    return {
        "name": ["folium_geopandas", "plotly", "all"][choice - 1],
        "packages": packages_map[choice],
    }


def ask_data_sources() -> dict:
    """Ask about data source templates to include."""
    print_header("Data Source Templates")
    print("Choose which API client templates to include:\n")

    print_option(1, "Federal + Montana sources",
                 "USGS, EPA, NOAA plus Montana-specific sources\n"
                 "     (Mesonet, GWIC, DNRC). Best for MT/regional work.",
                 recommended=True)
    print_option(2, "Federal sources only",
                 "USGS, EPA, NOAA - nationwide coverage without\n"
                 "     state-specific clients.")
    print_option(3, "Montana sources only",
                 "Montana Mesonet (Climate Office), GWIC, DNRC.\n"
                 "     For Montana-focused projects.")
    print_option(4, "USGS + generic templates",
                 "USGS Water Services plus reusable REST API\n"
                 "     patterns for custom sources.")
    print_option(5, "Generic templates only",
                 "Just REST API patterns you can adapt to any\n"
                 "     data source yourself.")

    choice = get_choice("Your choice", [1, 2, 3, 4, 5], default=1)

    return {
        1: {"name": "federal_montana", "sources": ["usgs", "epa", "noaa", "montana", "generic"]},
        2: {"name": "federal", "sources": ["usgs", "epa", "noaa", "generic"]},
        3: {"name": "montana_only", "sources": ["montana", "generic"]},
        4: {"name": "usgs_generic", "sources": ["usgs", "generic"]},
        5: {"name": "generic_only", "sources": ["generic"]},
    }[choice]


def ask_python_version() -> str:
    """Ask about Python version."""
    print_header("Python Version")
    print("Choose your Python version:\n")

    print_option(1, "Python 3.11",
                 "Recommended for compatibility with most packages.",
                 recommended=True)
    print_option(2, "Python 3.12",
                 "Latest stable release. Some packages may have issues.")
    print_option(3, "Python 3.10",
                 "Older but very stable. Good for conservative setups.")

    choice = get_choice("Your choice", [1, 2, 3], default=1)

    return {1: "3.11", 2: "3.12", 3: "3.10"}[choice]


def generate_conda_env(config: dict, output_dir: Path) -> Path:
    """Generate conda environment.yml file."""
    python_version = config["python_version"]

    # Base packages
    packages = [
        f"python={python_version}",
        "pip",
        "",
        "# Jupyter",
        "jupyterlab",
        "notebook",
        "ipykernel",
        "ipywidgets",
        "",
        "# Data manipulation",
        "pandas",
        "numpy",
    ]

    # Storage-specific packages
    if config["storage"]["name"] == "parquet":
        packages.append("pyarrow  # Parquet support")
    elif config["storage"]["name"] == "duckdb":
        packages.extend(["pyarrow", "duckdb"])

    packages.extend([
        "",
        "# HTTP/API requests",
        "requests",
        "aiohttp",
        "httpx",
    ])

    # Geospatial packages
    packages.extend([
        "",
        "# Geospatial",
        "gdal",
        "rasterio",
        "fiona",
        "shapely",
        "pyproj",
    ])

    if "geopandas" in config["mapping"]["packages"]:
        packages.append("geopandas")
    if "folium" in config["mapping"]["packages"]:
        packages.extend(["folium", "mapclassify"])

    # Visualization
    packages.extend([
        "",
        "# Visualization",
        "matplotlib",
        "seaborn",
    ])

    if "plotly" in config["mapping"]["packages"]:
        packages.append("plotly")

    # Utilities
    packages.extend([
        "",
        "# Utilities",
        "pyyaml",
        "python-dotenv",
        "tqdm",
        "",
        "# Development",
        "black",
        "ruff",
    ])

    content = f"""name: data-eng
channels:
  - conda-forge
  - defaults
dependencies:
"""
    for pkg in packages:
        if pkg == "":
            content += "\n"
        elif pkg.startswith("#"):
            content += f"  {pkg}\n"
        else:
            content += f"  - {pkg}\n"

    env_path = output_dir / "environment.yml"
    env_path.write_text(content)
    return env_path


def generate_uv_config(config: dict, output_dir: Path) -> Path:
    """Generate uv pyproject.toml file."""
    python_version = config["python_version"]

    deps = [
        "pandas",
        "numpy",
        "jupyterlab",
        "notebook",
        "ipykernel",
        "ipywidgets",
        "requests",
        "aiohttp",
        "httpx",
        "matplotlib",
        "seaborn",
        "pyyaml",
        "python-dotenv",
        "tqdm",
        "black",
        "ruff",
    ]

    # Add storage-specific
    deps.extend(config["storage"]["packages"])

    # Add geospatial
    deps.extend(["shapely", "pyproj", "rasterio", "fiona"])
    deps.extend(config["mapping"]["packages"])

    deps_str = ",\n    ".join([f'"{d}"' for d in deps])

    content = f'''[project]
name = "data-eng"
version = "0.1.0"
description = "Scientific Data Engineering Environment"
requires-python = ">={python_version}"
dependencies = [
    {deps_str},
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest",
]
'''

    config_path = output_dir / "pyproject.toml"
    config_path.write_text(content)
    return config_path


def generate_pip_requirements(config: dict, output_dir: Path) -> Path:
    """Generate pip requirements.txt file."""
    deps = [
        "pandas",
        "numpy",
        "jupyterlab",
        "notebook",
        "ipykernel",
        "ipywidgets",
        "requests",
        "aiohttp",
        "httpx",
        "matplotlib",
        "seaborn",
        "pyyaml",
        "python-dotenv",
        "tqdm",
        "black",
        "ruff",
    ]

    deps.extend(config["storage"]["packages"])
    deps.extend(["shapely", "pyproj"])
    deps.extend(config["mapping"]["packages"])

    content = "\n".join(deps) + "\n"

    req_path = output_dir / "requirements.txt"
    req_path.write_text(content)
    return req_path


def generate_readme(config: dict, output_dir: Path) -> Path:
    """Generate a customized README."""
    env_manager = config["env_manager"]["name"]

    if env_manager == "conda":
        setup_instructions = """### Setup

1. **Create the conda environment:**
   ```bash
   conda env create -f environment.yml
   ```

   Or with mamba (faster):
   ```bash
   mamba env create -f environment.yml
   ```

2. **Activate the environment:**
   ```bash
   conda activate data-eng
   ```"""
    elif env_manager == "uv":
        setup_instructions = """### Setup

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install system GDAL** (required for geospatial):
   ```bash
   # macOS
   brew install gdal

   # Ubuntu/Debian
   sudo apt install libgdal-dev
   ```

3. **Create the environment and install dependencies:**
   ```bash
   uv sync
   ```

4. **Activate the environment:**
   ```bash
   source .venv/bin/activate
   ```"""
    else:  # pip
        setup_instructions = """### Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # or: .venv\\Scripts\\activate  # Windows
   ```

2. **Install system GDAL** (required for geospatial):
   ```bash
   # macOS
   brew install gdal

   # Ubuntu/Debian
   sudo apt install libgdal-dev
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```"""

    content = f"""# Scientific Data Engineering Environment

A self-contained Python environment for scientific data engineering.

## Quick Start

{setup_instructions}

3. **Start Jupyter:**
   ```bash
   jupyter lab
   ```

4. **Open `notebooks/getting_started.ipynb`** to begin.

## Configuration

- **Environment Manager:** {env_manager}
- **Data Storage:** {config['storage']['name']}
- **Mapping:** {config['mapping']['name']}
- **Data Sources:** {', '.join(config['data_sources']['sources'])}

## Directory Structure

```
.
├── config/             # API configuration
├── data/
│   ├── raw/           # Raw data from APIs
│   ├── processed/     # Transformed data
│   └── outputs/       # Visualizations
├── notebooks/         # Jupyter notebooks
└── scripts/           # Python modules
    ├── data_retrieval/
    ├── data_storage/
    ├── normalization/
    └── visualization/
```

See the notebooks for usage examples.
"""

    readme_path = output_dir / "README.md"
    readme_path.write_text(content)
    return readme_path


def create_directory_structure(output_dir: Path):
    """Create the directory structure."""
    dirs = [
        "config",
        "data/raw",
        "data/processed",
        "data/outputs",
        "notebooks/examples",
        "scripts/data_retrieval",
        "scripts/data_storage",
        "scripts/normalization",
        "scripts/visualization",
    ]

    for d in dirs:
        (output_dir / d).mkdir(parents=True, exist_ok=True)

    # Create .gitkeep files
    for d in ["data/raw", "data/processed", "data/outputs"]:
        (output_dir / d / ".gitkeep").touch()


def copy_scripts(config: dict, output_dir: Path, source_dir: Path):
    """Copy script files based on configuration."""
    # Always copy these
    always_copy = [
        "scripts/__init__.py",
        "scripts/data_storage/__init__.py",
        "scripts/data_storage/parquet_utils.py",
        "scripts/normalization/__init__.py",
        "scripts/normalization/transforms.py",
        "scripts/visualization/__init__.py",
        "scripts/visualization/plots.py",
        "scripts/visualization/tables.py",
        "scripts/visualization/maps.py",
        "config/api_config.example.yml",
        ".gitignore",
    ]

    for path in always_copy:
        src = source_dir / path
        dst = output_dir / path
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # Copy data retrieval based on selection
    retrieval_init = output_dir / "scripts/data_retrieval/__init__.py"
    sources = config["data_sources"]["sources"]

    init_imports = []
    init_all = []

    if "generic" in sources:
        shutil.copy2(
            source_dir / "scripts/data_retrieval/generic_rest.py",
            output_dir / "scripts/data_retrieval/generic_rest.py"
        )
        init_imports.append("from .generic_rest import RESTClient")
        init_all.append("RESTClient")

    if "usgs" in sources:
        shutil.copy2(
            source_dir / "scripts/data_retrieval/usgs.py",
            output_dir / "scripts/data_retrieval/usgs.py"
        )
        init_imports.append("from .usgs import USGSWaterServices")
        init_all.append("USGSWaterServices")

    if "epa" in sources:
        shutil.copy2(
            source_dir / "scripts/data_retrieval/epa.py",
            output_dir / "scripts/data_retrieval/epa.py"
        )
        init_imports.append("from .epa import EPAWaterQuality")
        init_all.append("EPAWaterQuality")

    if "noaa" in sources:
        shutil.copy2(
            source_dir / "scripts/data_retrieval/noaa.py",
            output_dir / "scripts/data_retrieval/noaa.py"
        )
        init_imports.append("from .noaa import NOAAClimate")
        init_all.append("NOAAClimate")

    if "montana" in sources:
        shutil.copy2(
            source_dir / "scripts/data_retrieval/montana.py",
            output_dir / "scripts/data_retrieval/montana.py"
        )
        init_imports.append("from .montana import (")
        init_imports.append("    MontanaMesonet,")
        init_imports.append("    MontanaGWIC,")
        init_imports.append("    MontanaDNRC,")
        init_imports.append("    MontanaStateLibrary,")
        init_imports.append("    get_montana_clients,")
        init_imports.append(")")
        init_all.extend([
            "MontanaMesonet",
            "MontanaGWIC",
            "MontanaDNRC",
            "MontanaStateLibrary",
            "get_montana_clients",
        ])

    init_content = "# Data Retrieval Module\n"
    init_content += "\n".join(init_imports)
    init_content += f"\n\n__all__ = {init_all}\n"
    retrieval_init.write_text(init_content)


def copy_notebooks(config: dict, output_dir: Path, source_dir: Path):
    """Copy notebook files."""
    notebooks = [
        "notebooks/getting_started.ipynb",
        "notebooks/examples/data_retrieval_demo.ipynb",
        "notebooks/examples/visualization_demo.ipynb",
        "notebooks/examples/geospatial_demo.ipynb",
    ]

    # Add Montana notebook if Montana sources are included
    if "montana" in config["data_sources"]["sources"]:
        notebooks.append("notebooks/examples/montana_data_demo.ipynb")

    for path in notebooks:
        src = source_dir / path
        dst = output_dir / path
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def print_summary(config: dict, output_dir: Path):
    """Print a summary of what was created."""
    print_header("Setup Complete!")

    print(f"Environment created at: {colored(str(output_dir), Colors.GREEN)}\n")

    print(colored("Configuration:", Colors.BOLD))
    print(f"  - Environment Manager: {config['env_manager']['name']}")
    print(f"  - Python Version: {config['python_version']}")
    print(f"  - Data Storage: {config['storage']['name']}")
    print(f"  - Mapping: {config['mapping']['name']}")
    print(f"  - Data Sources: {', '.join(config['data_sources']['sources'])}")

    print()
    print(colored("Next steps:", Colors.BOLD))

    env_manager = config["env_manager"]["name"]
    if env_manager == "conda":
        print(f"  1. cd {output_dir}")
        print("  2. conda env create -f environment.yml")
        print("  3. conda activate data-eng")
        print("  4. jupyter lab")
    elif env_manager == "uv":
        print(f"  1. cd {output_dir}")
        print("  2. uv sync")
        print("  3. source .venv/bin/activate")
        print("  4. jupyter lab")
    else:
        print(f"  1. cd {output_dir}")
        print("  2. python -m venv .venv && source .venv/bin/activate")
        print("  3. pip install -r requirements.txt")
        print("  4. jupyter lab")

    print()
    print("  5. Open notebooks/getting_started.ipynb")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Interactive setup wizard for data engineering environment"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: creates 'data-eng-env' in current directory)"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Use default options without prompting"
    )
    args = parser.parse_args()

    print()
    print(colored("╔════════════════════════════════════════════════════════════╗", Colors.CYAN))
    print(colored("║     Scientific Data Engineering Environment Setup          ║", Colors.CYAN))
    print(colored("╚════════════════════════════════════════════════════════════╝", Colors.CYAN))
    print()
    print("This wizard will help you create a customized Python environment")
    print("for scientific data engineering and analysis.")
    print()

    # Collect configuration
    if args.non_interactive:
        config = {
            "env_manager": {"name": "conda", "file": "environment.yml"},
            "storage": {"name": "parquet", "packages": ["pyarrow"]},
            "mapping": {"name": "folium_geopandas", "packages": ["folium", "geopandas", "mapclassify"]},
            "data_sources": {"name": "federal_montana", "sources": ["usgs", "epa", "noaa", "montana", "generic"]},
            "python_version": "3.11",
        }
    else:
        config = {
            "env_manager": ask_env_manager(),
            "storage": ask_data_storage(),
            "mapping": ask_mapping(),
            "data_sources": ask_data_sources(),
            "python_version": ask_python_version(),
        }

    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        print_header("Output Directory")
        default_dir = Path.cwd() / "data-eng-env"
        print(f"Where should the environment be created?")
        print(f"Default: {default_dir}")
        print()
        user_dir = input("Directory path (press Enter for default): ").strip()
        output_dir = Path(user_dir) if user_dir else default_dir

    output_dir = output_dir.resolve()

    # Check if directory exists
    if output_dir.exists() and any(output_dir.iterdir()):
        print(colored(f"\nWarning: {output_dir} already exists and is not empty.", Colors.YELLOW))
        confirm = input("Continue and potentially overwrite files? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            sys.exit(0)

    # Source directory (where this script and templates are)
    source_dir = Path(__file__).parent

    print()
    print(colored("Generating environment...", Colors.CYAN))

    # Create structure
    create_directory_structure(output_dir)

    # Generate configuration files
    env_manager = config["env_manager"]["name"]
    if env_manager == "conda":
        generate_conda_env(config, output_dir)
    elif env_manager == "uv":
        generate_uv_config(config, output_dir)
    else:
        generate_pip_requirements(config, output_dir)

    # Generate README
    generate_readme(config, output_dir)

    # Copy scripts and notebooks
    copy_scripts(config, output_dir, source_dir)
    copy_notebooks(config, output_dir, source_dir)

    # Print summary
    print_summary(config, output_dir)


if __name__ == "__main__":
    main()
