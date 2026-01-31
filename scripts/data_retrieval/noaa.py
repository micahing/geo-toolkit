"""
NOAA Climate Data API Client

Documentation: https://www.ncdc.noaa.gov/cdo-web/webservices/v2
Provides access to historical climate and weather data.

Note: Requires a free API token from https://www.ncdc.noaa.gov/cdo-web/token
"""

import requests
import pandas as pd
from datetime import datetime
from typing import Optional
import os


class NOAAClimate:
    """Client for NOAA Climate Data Online (CDO) API."""

    BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2"

    # Common dataset IDs
    DATASETS = {
        "daily_summaries": "GHCND",      # Global Historical Climatology Network - Daily
        "monthly_summaries": "GSOM",      # Global Summary of the Month
        "normals_daily": "NORMAL_DLY",    # Climate Normals Daily
        "normals_monthly": "NORMAL_MLY",  # Climate Normals Monthly
        "precipitation_15min": "PRECIP_15", # Precipitation 15 Minute
        "precipitation_hourly": "PRECIP_HLY", # Precipitation Hourly
    }

    # Common data type IDs for GHCND
    DATA_TYPES = {
        "precip": "PRCP",           # Precipitation (tenths of mm)
        "snow": "SNOW",             # Snowfall (mm)
        "snow_depth": "SNWD",       # Snow depth (mm)
        "temp_max": "TMAX",         # Maximum temperature (tenths of degrees C)
        "temp_min": "TMIN",         # Minimum temperature (tenths of degrees C)
        "temp_avg": "TAVG",         # Average temperature (tenths of degrees C)
        "evaporation": "EVAP",      # Evaporation (tenths of mm)
        "wind_avg": "AWND",         # Average wind speed (tenths of m/s)
    }

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize NOAA client.

        Args:
            api_token: NOAA CDO API token. If not provided, looks for
                      NOAA_API_TOKEN environment variable.
        """
        self.api_token = api_token or os.environ.get("NOAA_API_TOKEN")
        if not self.api_token:
            raise ValueError(
                "NOAA API token required. Get one at: "
                "https://www.ncdc.noaa.gov/cdo-web/token\n"
                "Then set NOAA_API_TOKEN environment variable or pass to constructor."
            )

        self.session = requests.Session()
        self.session.headers.update({"token": self.api_token})

    def get_datasets(self) -> pd.DataFrame:
        """Get list of available datasets."""
        response = self._get("/datasets", {"limit": 100})
        return pd.DataFrame(response.get("results", []))

    def get_locations(
        self,
        location_category: str = "ST",  # States
        dataset_id: str = "GHCND",
    ) -> pd.DataFrame:
        """
        Get available locations.

        Args:
            location_category: 'ST' (state), 'CNTY' (county), 'HYD' (hydrologic)
            dataset_id: Dataset to filter by

        Returns:
            DataFrame with location information
        """
        params = {
            "datasetid": dataset_id,
            "locationcategoryid": location_category,
            "limit": 1000,
        }

        response = self._get("/locations", params)
        return pd.DataFrame(response.get("results", []))

    def get_stations(
        self,
        dataset_id: str = "GHCND",
        location_id: Optional[str] = None,
        bbox: Optional[tuple] = None,
        data_type_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get weather stations.

        Args:
            dataset_id: Dataset ID
            location_id: Location filter (e.g., 'FIPS:08' for Colorado)
            bbox: Bounding box as (south, west, north, east)
            data_type_id: Filter by data type availability

        Returns:
            DataFrame with station information
        """
        params = {
            "datasetid": dataset_id,
            "limit": 1000,
        }

        if location_id:
            params["locationid"] = location_id
        if bbox:
            # NOAA uses south,west,north,east order
            params["extent"] = ",".join(map(str, bbox))
        if data_type_id:
            params["datatypeid"] = data_type_id

        response = self._get("/stations", params)
        return pd.DataFrame(response.get("results", []))

    def get_data(
        self,
        dataset_id: str = "GHCND",
        data_type_ids: Optional[list[str]] = None,
        location_id: Optional[str] = None,
        station_id: Optional[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        units: str = "metric",
    ) -> pd.DataFrame:
        """
        Get climate/weather data.

        Args:
            dataset_id: Dataset ID
            data_type_ids: List of data types to retrieve
            location_id: Location filter
            station_id: Station filter
            start_date: Start date (required)
            end_date: End date (required)
            units: 'metric' or 'standard'

        Returns:
            DataFrame with weather data
        """
        if not start_date or not end_date:
            raise ValueError("start_date and end_date are required")

        params = {
            "datasetid": dataset_id,
            "startdate": start_date.strftime("%Y-%m-%d"),
            "enddate": end_date.strftime("%Y-%m-%d"),
            "units": units,
            "limit": 1000,
        }

        if data_type_ids:
            params["datatypeid"] = ",".join(data_type_ids)
        if location_id:
            params["locationid"] = location_id
        if station_id:
            params["stationid"] = station_id

        # Paginate through all results
        all_results = []
        offset = 0

        while True:
            params["offset"] = offset
            response = self._get("/data", params)
            results = response.get("results", [])

            if not results:
                break

            all_results.extend(results)

            metadata = response.get("metadata", {}).get("resultset", {})
            total = metadata.get("count", 0)

            if len(all_results) >= total:
                break

            offset += 1000

        df = pd.DataFrame(all_results)

        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        return df

    def get_colorado_basin_precipitation(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """
        Get precipitation data for Colorado River Basin states.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with precipitation data
        """
        # FIPS codes for Colorado River Basin states
        basin_states = {
            "FIPS:04": "Arizona",
            "FIPS:06": "California",
            "FIPS:08": "Colorado",
            "FIPS:32": "Nevada",
            "FIPS:35": "New Mexico",
            "FIPS:49": "Utah",
            "FIPS:56": "Wyoming",
        }

        all_data = []

        for fips, state_name in basin_states.items():
            try:
                data = self.get_data(
                    dataset_id="GHCND",
                    data_type_ids=["PRCP", "SNOW"],
                    location_id=fips,
                    start_date=start_date,
                    end_date=end_date,
                )
                if not data.empty:
                    data["state"] = state_name
                    all_data.append(data)
            except Exception as e:
                print(f"Warning: Could not get data for {state_name}: {e}")

        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()

    def _get(self, endpoint: str, params: dict) -> dict:
        """Make GET request to NOAA API."""
        response = self.session.get(
            f"{self.BASE_URL}{endpoint}",
            params=params,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    # Note: Requires NOAA_API_TOKEN environment variable
    try:
        client = NOAAClimate()

        # Get available datasets
        datasets = client.get_datasets()
        print(f"Available datasets: {datasets['id'].tolist()}")

        # Get stations in Colorado
        stations = client.get_stations(location_id="FIPS:08")
        print(f"Found {len(stations)} stations in Colorado")

    except ValueError as e:
        print(f"Setup required: {e}")
