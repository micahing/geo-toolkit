"""
EPA Water Quality Data API Client

Documentation: https://www.epa.gov/waterdata/water-quality-data-wqp
Uses the Water Quality Portal (WQP) which aggregates data from EPA, USGS, and states.
"""

import requests
import pandas as pd
from datetime import datetime
from typing import Optional
from io import StringIO


class EPAWaterQuality:
    """Client for EPA Water Quality Portal API."""

    BASE_URL = "https://www.waterqualitydata.us"

    # Common characteristic names
    CHARACTERISTICS = {
        "temperature": "Temperature, water",
        "ph": "pH",
        "dissolved_oxygen": "Dissolved oxygen (DO)",
        "conductivity": "Specific conductance",
        "turbidity": "Turbidity",
        "nitrate": "Nitrate",
        "phosphorus": "Phosphorus",
        "arsenic": "Arsenic",
        "lead": "Lead",
        "mercury": "Mercury",
    }

    def __init__(self):
        """Initialize EPA WQP client."""
        self.session = requests.Session()

    def get_stations(
        self,
        state_code: Optional[str] = None,
        huc: Optional[str] = None,
        bbox: Optional[tuple] = None,
        site_type: Optional[str] = None,
        organization: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get monitoring station information.

        Args:
            state_code: Two-letter state code (e.g., 'US:CO')
            huc: Hydrologic Unit Code
            bbox: Bounding box as (west, south, east, north)
            site_type: Site type (e.g., 'Well', 'Stream', 'Lake')
            organization: Organization identifier

        Returns:
            DataFrame with station information
        """
        params = {
            "mimeType": "csv",
            "zip": "no",
        }

        if state_code:
            # WQP uses format 'US:CO' for states
            if ":" not in state_code:
                state_code = f"US:{state_code}"
            params["statecode"] = state_code
        if huc:
            params["huc"] = huc
        if bbox:
            params["bBox"] = ",".join(map(str, bbox))
        if site_type:
            params["siteType"] = site_type
        if organization:
            params["organization"] = organization

        response = self.session.get(
            f"{self.BASE_URL}/data/Station/search",
            params=params,
            timeout=120,
        )
        response.raise_for_status()

        return pd.read_csv(StringIO(response.text))

    def get_results(
        self,
        state_code: Optional[str] = None,
        huc: Optional[str] = None,
        site_id: Optional[str] = None,
        characteristic_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sample_media: str = "Water",
    ) -> pd.DataFrame:
        """
        Get water quality measurement results.

        Args:
            state_code: Two-letter state code
            huc: Hydrologic Unit Code
            site_id: Specific monitoring location ID
            characteristic_name: What was measured (e.g., 'pH', 'Temperature, water')
            start_date: Start date for results
            end_date: End date for results
            sample_media: Media type ('Water', 'Sediment', etc.)

        Returns:
            DataFrame with measurement results
        """
        params = {
            "mimeType": "csv",
            "zip": "no",
            "sampleMedia": sample_media,
        }

        if state_code:
            if ":" not in state_code:
                state_code = f"US:{state_code}"
            params["statecode"] = state_code
        if huc:
            params["huc"] = huc
        if site_id:
            params["siteid"] = site_id
        if characteristic_name:
            params["characteristicName"] = characteristic_name
        if start_date:
            params["startDateLo"] = start_date.strftime("%m-%d-%Y")
        if end_date:
            params["startDateHi"] = end_date.strftime("%m-%d-%Y")

        response = self.session.get(
            f"{self.BASE_URL}/data/Result/search",
            params=params,
            timeout=300,  # WQP can be slow
        )
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))

        # Parse dates if present
        if "ActivityStartDate" in df.columns:
            df["ActivityStartDate"] = pd.to_datetime(df["ActivityStartDate"], errors="coerce")

        return df

    def get_colorado_basin_results(
        self,
        characteristic: str = "ph",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Get water quality data for Colorado River Basin.

        Args:
            characteristic: Key from CHARACTERISTICS dict or full name
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with results
        """
        char_name = self.CHARACTERISTICS.get(characteristic, characteristic)

        # Upper Colorado HUC region
        upper = self.get_results(
            huc="14",
            characteristic_name=char_name,
            start_date=start_date,
            end_date=end_date,
        )
        upper["basin"] = "upper_colorado"

        # Lower Colorado HUC region
        lower = self.get_results(
            huc="15",
            characteristic_name=char_name,
            start_date=start_date,
            end_date=end_date,
        )
        lower["basin"] = "lower_colorado"

        return pd.concat([upper, lower], ignore_index=True)

    def search_characteristics(self, keyword: str) -> list[str]:
        """
        Search for characteristic names containing a keyword.

        Args:
            keyword: Search term

        Returns:
            List of matching characteristic names
        """
        # Get list of all characteristics from WQP
        response = self.session.get(
            f"{self.BASE_URL}/Codes/characteristicname",
            params={"mimeType": "json"},
        )
        response.raise_for_status()

        data = response.json()
        all_chars = [item.get("value", "") for item in data.get("codes", [])]

        # Filter by keyword
        keyword_lower = keyword.lower()
        return [c for c in all_chars if keyword_lower in c.lower()]


# Example usage
if __name__ == "__main__":
    client = EPAWaterQuality()

    # Get monitoring stations in Colorado
    stations = client.get_stations(state_code="CO", site_type="Well")
    print(f"Found {len(stations)} well monitoring stations in Colorado")

    # Search for arsenic-related characteristics
    arsenic_chars = client.search_characteristics("arsenic")
    print(f"Arsenic characteristics: {arsenic_chars[:5]}")
