"""
USGS Water Services API Client

Documentation: https://waterservices.usgs.gov/
Provides access to NWIS (National Water Information System) data including:
- Groundwater levels
- Surface water discharge
- Water quality measurements
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from io import StringIO


class USGSWaterServices:
    """Client for USGS Water Services REST API."""

    BASE_URL = "https://waterservices.usgs.gov/nwis"

    # Common parameter codes
    PARAM_CODES = {
        "discharge": "00060",          # Discharge, cubic feet per second
        "gage_height": "00065",        # Gage height, feet
        "water_temp": "00010",         # Temperature, water, degrees Celsius
        "groundwater_level": "72019",  # Depth to water level, feet below land surface
        "specific_conductance": "00095",
        "dissolved_oxygen": "00300",
        "ph": "00400",
    }

    # HUC codes for Colorado River Basin regions
    COLORADO_BASIN_HUCS = {
        "upper_colorado": "14",  # Upper Colorado Region
        "lower_colorado": "15",  # Lower Colorado Region
    }

    def __init__(self, format: str = "json"):
        """
        Initialize USGS client.

        Args:
            format: Response format ('json' or 'rdb' for tab-delimited)
        """
        self.format = format
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json" if format == "json" else "text/plain"
        })

    def get_sites(
        self,
        state_code: Optional[str] = None,
        huc: Optional[str] = None,
        site_type: Optional[str] = None,
        bbox: Optional[tuple] = None,
        parameter_code: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get information about monitoring sites.

        Args:
            state_code: Two-letter state code (e.g., 'CO', 'AZ')
            huc: Hydrologic Unit Code (e.g., '14' for Upper Colorado)
            site_type: Site type code (e.g., 'GW' for groundwater, 'ST' for stream)
            bbox: Bounding box as (west, south, east, north) in decimal degrees
            parameter_code: Filter sites that have this parameter

        Returns:
            DataFrame with site information
        """
        params = {
            "format": "rdb",
            "siteOutput": "expanded",
        }

        if state_code:
            params["stateCd"] = state_code
        if huc:
            params["huc"] = huc
        if site_type:
            params["siteType"] = site_type
        if bbox:
            params["bBox"] = ",".join(map(str, bbox))
        if parameter_code:
            params["parameterCd"] = parameter_code

        response = self.session.get(f"{self.BASE_URL}/site/", params=params)
        response.raise_for_status()

        return self._parse_rdb(response.text)

    def get_instantaneous_values(
        self,
        sites: list[str],
        parameter_codes: list[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get instantaneous (real-time) values.

        Args:
            sites: List of site numbers
            parameter_codes: List of parameter codes
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            period: ISO 8601 duration (e.g., 'P7D' for past 7 days)

        Returns:
            DataFrame with instantaneous values
        """
        params = {
            "format": "json",
            "sites": ",".join(sites),
            "parameterCd": ",".join(parameter_codes),
        }

        if period:
            params["period"] = period
        else:
            if start_date:
                params["startDT"] = start_date.strftime("%Y-%m-%d")
            if end_date:
                params["endDT"] = end_date.strftime("%Y-%m-%d")

        response = self.session.get(f"{self.BASE_URL}/iv/", params=params)
        response.raise_for_status()

        return self._parse_json_timeseries(response.json())

    def get_daily_values(
        self,
        sites: list[str],
        parameter_codes: list[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        stat_code: str = "00003",  # Mean
    ) -> pd.DataFrame:
        """
        Get daily statistical values.

        Args:
            sites: List of site numbers
            parameter_codes: List of parameter codes
            start_date: Start date
            end_date: End date
            stat_code: Statistic code ('00001'=max, '00002'=min, '00003'=mean)

        Returns:
            DataFrame with daily values
        """
        params = {
            "format": "json",
            "sites": ",".join(sites),
            "parameterCd": ",".join(parameter_codes),
            "statCd": stat_code,
        }

        if start_date:
            params["startDT"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["endDT"] = end_date.strftime("%Y-%m-%d")

        response = self.session.get(f"{self.BASE_URL}/dv/", params=params)
        response.raise_for_status()

        return self._parse_json_timeseries(response.json())

    def get_groundwater_levels(
        self,
        sites: Optional[list[str]] = None,
        state_code: Optional[str] = None,
        huc: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Get groundwater level measurements.

        Args:
            sites: List of site numbers
            state_code: Two-letter state code
            huc: Hydrologic Unit Code
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with groundwater levels
        """
        params = {
            "format": "json",
        }

        if sites:
            params["sites"] = ",".join(sites)
        if state_code:
            params["stateCd"] = state_code
        if huc:
            params["huc"] = huc
        if start_date:
            params["startDT"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["endDT"] = end_date.strftime("%Y-%m-%d")

        response = self.session.get(f"{self.BASE_URL}/gwlevels/", params=params)
        response.raise_for_status()

        return self._parse_json_timeseries(response.json())

    def get_colorado_basin_sites(self, basin: str = "upper") -> pd.DataFrame:
        """
        Convenience method to get all groundwater sites in Colorado River Basin.

        Args:
            basin: 'upper' or 'lower' Colorado basin

        Returns:
            DataFrame with site information
        """
        huc = self.COLORADO_BASIN_HUCS.get(f"{basin}_colorado", "14")
        return self.get_sites(huc=huc, site_type="GW")

    def _parse_rdb(self, text: str) -> pd.DataFrame:
        """Parse USGS RDB (tab-delimited) format."""
        lines = [line for line in text.split("\n") if not line.startswith("#")]
        if len(lines) < 2:
            return pd.DataFrame()

        # Skip the format line (second line after headers)
        data = "\n".join([lines[0]] + lines[2:])
        return pd.read_csv(StringIO(data), sep="\t", dtype=str)

    def _parse_json_timeseries(self, data: dict) -> pd.DataFrame:
        """Parse USGS JSON timeseries response."""
        records = []

        ts_data = data.get("value", {}).get("timeSeries", [])

        for series in ts_data:
            site_code = series.get("sourceInfo", {}).get("siteCode", [{}])[0].get("value")
            site_name = series.get("sourceInfo", {}).get("siteName")

            # Get coordinates
            geo_location = series.get("sourceInfo", {}).get("geoLocation", {}).get("geogLocation", {})
            latitude = geo_location.get("latitude")
            longitude = geo_location.get("longitude")

            variable = series.get("variable", {})
            param_code = variable.get("variableCode", [{}])[0].get("value")
            param_name = variable.get("variableName")
            unit = variable.get("unit", {}).get("unitCode")

            for value_set in series.get("values", []):
                for point in value_set.get("value", []):
                    records.append({
                        "site_code": site_code,
                        "site_name": site_name,
                        "latitude": latitude,
                        "longitude": longitude,
                        "parameter_code": param_code,
                        "parameter_name": param_name,
                        "datetime": point.get("dateTime"),
                        "value": point.get("value"),
                        "unit": unit,
                        "qualifiers": ",".join(point.get("qualifiers", [])),
                    })

        df = pd.DataFrame(records)

        if not df.empty and "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
            df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

        return df


# Example usage
if __name__ == "__main__":
    client = USGSWaterServices()

    # Get groundwater sites in Upper Colorado Basin
    sites = client.get_colorado_basin_sites("upper")
    print(f"Found {len(sites)} groundwater sites in Upper Colorado Basin")

    # Get recent groundwater levels for Colorado
    from datetime import datetime, timedelta

    levels = client.get_groundwater_levels(
        state_code="CO",
        start_date=datetime.now() - timedelta(days=30),
    )
    print(f"Retrieved {len(levels)} groundwater level measurements")
