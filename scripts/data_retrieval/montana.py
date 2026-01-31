"""
Montana State Data API Clients

Data sources for Montana climate, water, and groundwater information:

1. Montana Mesonet (Montana Climate Office) - Weather and soil moisture stations
   API Docs: https://climate.umt.edu/mesonet/api/

2. GWIC (Ground Water Information Center) - Well logs and groundwater data
   Website: https://mbmggwic.mtech.edu/

3. DNRC StAGE (Stream and Gage Explorer) - Stream gage data
   Website: https://gis.dnrc.mt.gov/apps/stage/

4. Montana State Library - GIS datasets
   Website: https://msl.mt.gov/geoinfo/
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Union
from io import StringIO
import warnings


class MontanaMesonet:
    """
    Client for Montana Mesonet API (Montana Climate Office).

    The Montana Mesonet is a network of 200+ weather and soil moisture
    monitoring stations across Montana. Data includes air temperature,
    precipitation, soil moisture, wind, and derived agricultural metrics.

    API Documentation: https://climate.umt.edu/mesonet/api/
    Interactive Docs: https://mesonet.climate.umt.edu/api/v2/docs
    """

    BASE_URL = "https://mesonet.climate.umt.edu/api/v2"

    # Common elements (variables) available
    ELEMENTS = {
        # Atmospheric
        "air_temp": "Air temperature (°C)",
        "relative_humidity": "Relative humidity (%)",
        "ppt": "Precipitation (mm)",
        "wind_speed": "Wind speed (m/s)",
        "wind_direction": "Wind direction (degrees)",
        "solar_radiation": "Solar radiation (W/m²)",
        "atmospheric_pressure": "Atmospheric pressure (kPa)",

        # Soil
        "soil_temp_5": "Soil temperature at 5cm (°C)",
        "soil_temp_20": "Soil temperature at 20cm (°C)",
        "soil_temp_50": "Soil temperature at 50cm (°C)",
        "soil_vwc_5": "Soil volumetric water content at 5cm (%)",
        "soil_vwc_20": "Soil volumetric water content at 20cm (%)",
        "soil_vwc_50": "Soil volumetric water content at 50cm (%)",

        # Snow (HydroMet stations)
        "snow_depth": "Snow depth (mm)",
        "snow_water_equiv": "Snow water equivalent (mm)",

        # Derived
        "eto": "Reference evapotranspiration (mm)",
        "gdd": "Growing degree days",
    }

    # Station network types
    NETWORKS = {
        "agrinet": "Agricultural monitoring stations",
        "hydromet": "Hydrological/snow monitoring stations",
    }

    def __init__(self):
        """Initialize Montana Mesonet client."""
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def get_stations(
        self,
        active_only: bool = True,
        as_geodataframe: bool = False,
    ) -> Union[pd.DataFrame, "geopandas.GeoDataFrame"]:
        """
        Get list of all Mesonet stations.

        Args:
            active_only: Only return currently active stations
            as_geodataframe: Return as GeoDataFrame with geometry

        Returns:
            DataFrame or GeoDataFrame with station information
        """
        params = {"type": "json"}
        if active_only:
            params["active"] = "true"

        response = self.session.get(f"{self.BASE_URL}/stations/", params=params)
        response.raise_for_status()

        df = pd.DataFrame(response.json())

        if as_geodataframe:
            import geopandas as gpd
            from shapely.geometry import Point

            geometry = [
                Point(row["longitude"], row["latitude"])
                for _, row in df.iterrows()
            ]
            return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

        return df

    def get_latest(
        self,
        stations: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Get latest observations from all or selected stations.

        Data is updated every 5 minutes.

        Args:
            stations: List of station identifiers (all if None)

        Returns:
            DataFrame with latest observations
        """
        params = {"type": "json"}
        if stations:
            params["stations"] = ",".join(stations)

        response = self.session.get(f"{self.BASE_URL}/latest/", params=params)
        response.raise_for_status()

        return pd.DataFrame(response.json())

    def get_hourly_observations(
        self,
        stations: list[str],
        start_date: datetime,
        end_date: Optional[datetime] = None,
        elements: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Get hourly aggregated observations.

        Args:
            stations: List of station identifiers
            start_date: Start date
            end_date: End date (defaults to current time)
            elements: Specific elements to retrieve (all if None)

        Returns:
            DataFrame with hourly observations
        """
        params = {
            "type": "json",
            "stations": ",".join(stations),
            "start_time": start_date.strftime("%Y-%m-%d"),
        }

        if end_date:
            params["end_time"] = end_date.strftime("%Y-%m-%d")
        if elements:
            params["elements"] = ",".join(elements)

        response = self.session.get(
            f"{self.BASE_URL}/observations/hourly/",
            params=params,
        )
        response.raise_for_status()

        df = pd.DataFrame(response.json())

        if not df.empty and "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])

        return df

    def get_daily_observations(
        self,
        stations: list[str],
        start_date: datetime,
        end_date: Optional[datetime] = None,
        elements: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Get daily aggregated observations (min, max, mean).

        Args:
            stations: List of station identifiers
            start_date: Start date
            end_date: End date (defaults to current day)
            elements: Specific elements to retrieve

        Returns:
            DataFrame with daily observations
        """
        params = {
            "type": "json",
            "stations": ",".join(stations),
            "start_time": start_date.strftime("%Y-%m-%d"),
        }

        if end_date:
            params["end_time"] = end_date.strftime("%Y-%m-%d")
        if elements:
            params["elements"] = ",".join(elements)

        response = self.session.get(
            f"{self.BASE_URL}/observations/daily/",
            params=params,
        )
        response.raise_for_status()

        df = pd.DataFrame(response.json())

        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        return df

    def get_derived_metrics(
        self,
        stations: list[str],
        start_date: datetime,
        end_date: Optional[datetime] = None,
        elements: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Get derived agricultural metrics (ETo, GDD, etc.).

        Args:
            stations: List of station identifiers
            start_date: Start date
            end_date: End date
            elements: Metrics to retrieve (default: all available)

        Returns:
            DataFrame with derived metrics
        """
        params = {
            "type": "json",
            "stations": ",".join(stations),
            "start_time": start_date.strftime("%Y-%m-%d"),
        }

        if end_date:
            params["end_time"] = end_date.strftime("%Y-%m-%d")
        if elements:
            params["elements"] = ",".join(elements)

        response = self.session.get(
            f"{self.BASE_URL}/derived/daily/",
            params=params,
        )
        response.raise_for_status()

        df = pd.DataFrame(response.json())

        if not df.empty and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        return df

    def search_stations_by_county(
        self,
        county: str,
        active_only: bool = True,
    ) -> pd.DataFrame:
        """
        Find stations in a specific Montana county.

        Args:
            county: County name (e.g., 'Gallatin', 'Yellowstone')
            active_only: Only return active stations

        Returns:
            DataFrame with matching stations
        """
        stations = self.get_stations(active_only=active_only)

        # Filter by county (case-insensitive)
        county_lower = county.lower()
        mask = stations["county"].str.lower().str.contains(county_lower, na=False)

        return stations[mask]


class MontanaGWIC:
    """
    Client for Montana Ground Water Information Center (GWIC).

    GWIC is the central repository for groundwater information in Montana,
    maintained by the Montana Bureau of Mines and Geology (MBMG).

    Website: https://mbmggwic.mtech.edu/
    GIS Data Hub: https://gis-data-hub-mbmg.hub.arcgis.com/

    Note: GWIC does not have a public REST API. This client provides
    utilities for working with downloadable datasets and ArcGIS services.
    """

    # ArcGIS REST service endpoints
    ARCGIS_BASE = "https://services1.arcgis.com/KyHQVZVT08EIH1v8/arcgis/rest/services"

    # Known feature service layers
    FEATURE_SERVICES = {
        "gwic_wells": "GWIC_Wells/FeatureServer/0",
        "monitoring_wells": "Monitoring_Wells/FeatureServer/0",
    }

    def __init__(self):
        """Initialize GWIC client."""
        self.session = requests.Session()

    def get_wells_from_arcgis(
        self,
        bbox: Optional[tuple] = None,
        county: Optional[str] = None,
        where_clause: str = "1=1",
        max_records: int = 2000,
    ) -> pd.DataFrame:
        """
        Query GWIC wells from ArcGIS Feature Service.

        Args:
            bbox: Bounding box as (xmin, ymin, xmax, ymax) in WGS84
            county: Filter by county name
            where_clause: SQL WHERE clause for filtering
            max_records: Maximum records to return

        Returns:
            DataFrame with well information
        """
        # Build query parameters
        params = {
            "where": where_clause,
            "outFields": "*",
            "returnGeometry": "true",
            "f": "json",
            "resultRecordCount": max_records,
        }

        if county:
            params["where"] = f"COUNTY = '{county.upper()}'"

        if bbox:
            params["geometry"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"
            params["inSR"] = "4326"

        # Try to query the wells layer
        url = f"{self.ARCGIS_BASE}/GWIC_Wells/FeatureServer/0/query"

        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            if "features" in data:
                records = [f["attributes"] for f in data["features"]]

                # Add geometry
                for i, feature in enumerate(data["features"]):
                    if "geometry" in feature:
                        records[i]["longitude"] = feature["geometry"].get("x")
                        records[i]["latitude"] = feature["geometry"].get("y")

                return pd.DataFrame(records)
            else:
                warnings.warn("No features returned from GWIC ArcGIS service")
                return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            warnings.warn(f"Could not query GWIC ArcGIS service: {e}")
            return pd.DataFrame()

    def get_monitoring_network_wells(self) -> pd.DataFrame:
        """
        Get statewide groundwater monitoring network wells.

        These are long-term monitoring sites with historical water level data.

        Returns:
            DataFrame with monitoring well information
        """
        url = f"{self.ARCGIS_BASE}/Statewide_Monitoring_Network/FeatureServer/0/query"

        params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "json",
        }

        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            if "features" in data:
                records = []
                for feature in data["features"]:
                    record = feature["attributes"]
                    if "geometry" in feature:
                        record["longitude"] = feature["geometry"].get("x")
                        record["latitude"] = feature["geometry"].get("y")
                    records.append(record)

                return pd.DataFrame(records)
            return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            warnings.warn(f"Could not query monitoring network: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_gwic_url(gwic_id: str) -> str:
        """
        Get the GWIC website URL for a specific well.

        Args:
            gwic_id: GWIC well identifier

        Returns:
            URL to the well's GWIC page
        """
        return f"https://mbmggwic.mtech.edu/sqlserver/v11/reports/SiteSummary.asp?gwicid={gwic_id}"


class MontanaDNRC:
    """
    Client for Montana DNRC (Department of Natural Resources and Conservation).

    Provides access to:
    - StAGE (Stream and Gage Explorer) - Stream gage data
    - Water Rights Query System
    - Surface water monitoring data

    StAGE Website: https://gis.dnrc.mt.gov/apps/stage/
    DNRC Water Resources: https://dnrc.mt.gov/Water-Resources/
    """

    # ArcGIS REST service base
    ARCGIS_BASE = "https://gis.dnrc.mt.gov/arcgis/rest/services"

    def __init__(self):
        """Initialize DNRC client."""
        self.session = requests.Session()

    def get_stream_gages(
        self,
        bbox: Optional[tuple] = None,
        active_only: bool = True,
    ) -> pd.DataFrame:
        """
        Get stream gage locations from DNRC.

        Args:
            bbox: Bounding box as (xmin, ymin, xmax, ymax)
            active_only: Only return active gages

        Returns:
            DataFrame with gage information
        """
        # DNRC Stream Gages feature service
        url = f"{self.ARCGIS_BASE}/WRD/DNRC_Stream_Gages/MapServer/0/query"

        params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "json",
        }

        if bbox:
            params["geometry"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"
            params["inSR"] = "4326"

        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            if "features" in data:
                records = []
                for feature in data["features"]:
                    record = feature["attributes"]
                    if "geometry" in feature:
                        record["longitude"] = feature["geometry"].get("x")
                        record["latitude"] = feature["geometry"].get("y")
                    records.append(record)

                df = pd.DataFrame(records)

                # Filter for active gages if requested
                if active_only and not df.empty:
                    # Check for common active status column names
                    status_cols = [c for c in df.columns if 'status' in c.lower() or 'active' in c.lower()]
                    if status_cols:
                        status_col = status_cols[0]
                        # Filter for active status (common values: 'Active', 'active', 'A', 1, True)
                        active_mask = df[status_col].astype(str).str.lower().isin(['active', 'a', '1', 'true', 'yes'])
                        df = df[active_mask]

                return df
            return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            warnings.warn(f"Could not query DNRC stream gages: {e}")
            return pd.DataFrame()

    def get_water_rights_pou(
        self,
        bbox: Optional[tuple] = None,
        county: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get Places of Use (POU) from water rights database.

        Args:
            bbox: Bounding box
            county: Filter by county

        Returns:
            DataFrame with water rights POU data
        """
        url = f"{self.ARCGIS_BASE}/WRD/WaterRights/MapServer/1/query"

        params = {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "f": "json",
            "resultRecordCount": 2000,
        }

        if county:
            params["where"] = f"COUNTY = '{county.upper()}'"

        if bbox:
            params["geometry"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            params["geometryType"] = "esriGeometryEnvelope"
            params["spatialRel"] = "esriSpatialRelIntersects"
            params["inSR"] = "4326"

        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            if "features" in data:
                records = [f["attributes"] for f in data["features"]]
                return pd.DataFrame(records)
            return pd.DataFrame()

        except requests.exceptions.RequestException as e:
            warnings.warn(f"Could not query water rights: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_stage_url(site_id: str) -> str:
        """
        Get the StAGE gage report URL.

        Args:
            site_id: Stream gage site identifier

        Returns:
            URL to the gage report page
        """
        return f"https://gis.dnrc.mt.gov/apps/stage/gage-report/?site={site_id}"

    @staticmethod
    def get_wrqs_url() -> str:
        """Get URL for Water Rights Query System."""
        return "https://wrqs.dnrc.mt.gov/"


class MontanaStateLibrary:
    """
    Client for Montana State Library GIS datasets.

    The Montana State Library provides various statewide GIS datasets
    through their MSDI (Montana Spatial Data Infrastructure).

    Website: https://msl.mt.gov/geoinfo/
    Data List: https://mslservices.mt.gov/geographic_information/data/datalist/
    """

    DOWNLOAD_BASE = "https://ftpgeoinfo.msl.mt.gov"

    # Common dataset paths
    DATASETS = {
        "counties": "/Data/Spatial/MSDI/AdministrativeBoundaries/MontanaCounties.zip",
        "hydrography": "/Data/Spatial/MSDI/Hydrography/",
        "watersheds": "/Data/Spatial/MSDI/Hydrography/HUC/",
        "climate": "/Data/Spatial/MSDI/Climate/",
    }

    def __init__(self):
        """Initialize Montana State Library client."""
        self.session = requests.Session()

    def list_datasets(self, category: str) -> list[str]:
        """
        List available datasets in a category.

        Note: This requires FTP directory listing which may not always work.
        Visit https://mslservices.mt.gov/geographic_information/data/datalist/
        for the full catalog.

        Args:
            category: Dataset category key from DATASETS

        Returns:
            List of available file paths
        """
        # This is a placeholder - actual implementation would need FTP access
        # or web scraping of the data catalog
        return list(self.DATASETS.keys())

    @staticmethod
    def get_data_catalog_url() -> str:
        """Get URL for the Montana State Library data catalog."""
        return "https://mslservices.mt.gov/geographic_information/data/datalist/"


# Convenience function for all Montana data
def get_montana_clients() -> dict:
    """
    Get all Montana data clients.

    Returns:
        Dict with initialized clients for each data source
    """
    return {
        "mesonet": MontanaMesonet(),
        "gwic": MontanaGWIC(),
        "dnrc": MontanaDNRC(),
        "state_library": MontanaStateLibrary(),
    }


# Example usage
if __name__ == "__main__":
    print("=== Montana Mesonet ===")
    mesonet = MontanaMesonet()

    # Get stations
    stations = mesonet.get_stations()
    print(f"Found {len(stations)} Mesonet stations")

    # Get latest data
    latest = mesonet.get_latest()
    print(f"Latest observations from {len(latest)} stations")

    # Get stations in Gallatin County
    gallatin = mesonet.search_stations_by_county("Gallatin")
    print(f"Found {len(gallatin)} stations in Gallatin County")

    if not gallatin.empty:
        # Get daily data for first station
        station_id = gallatin.iloc[0]["station"]
        daily = mesonet.get_daily_observations(
            stations=[station_id],
            start_date=datetime.now() - timedelta(days=7),
            elements=["air_temp", "ppt"],
        )
        print(f"Retrieved {len(daily)} daily observations for {station_id}")

    print("\n=== Montana GWIC ===")
    gwic = MontanaGWIC()

    # Try to get monitoring network wells
    monitoring = gwic.get_monitoring_network_wells()
    if not monitoring.empty:
        print(f"Found {len(monitoring)} monitoring network wells")
    else:
        print("Could not retrieve monitoring wells (service may require direct access)")

    print("\n=== Montana DNRC ===")
    dnrc = MontanaDNRC()

    # Get stream gages
    gages = dnrc.get_stream_gages()
    if not gages.empty:
        print(f"Found {len(gages)} DNRC stream gages")
    else:
        print("Could not retrieve stream gages (check ArcGIS service availability)")

    print("\n=== Data Source URLs ===")
    print(f"Mesonet Dashboard: https://mesonet.climate.umt.edu/dash/")
    print(f"GWIC Website: https://mbmggwic.mtech.edu/")
    print(f"DNRC StAGE: https://gis.dnrc.mt.gov/apps/stage/")
    print(f"MT State Library Data: {MontanaStateLibrary.get_data_catalog_url()}")
