"""
Integration tests for EPA Water Quality Portal client.

Uses HTTP response mocking to test API client behavior.
"""

import pytest
import responses
import pandas as pd
from datetime import datetime

from scripts.data_retrieval.epa import EPAWaterQuality


class TestEPAWaterQualityGetStations:
    """Tests for EPAWaterQuality.get_stations method."""

    @pytest.mark.integration
    @responses.activate
    def test_get_stations_by_state(self, mock_epa_csv_response):
        """Retrieves stations filtered by state code."""
        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Station/search",
            body=mock_epa_csv_response,
            status=200,
        )

        client = EPAWaterQuality()
        result = client.get_stations(state_code="CO")

        assert not result.empty
        assert 'MonitoringLocationIdentifier' in result.columns
        assert len(result) == 3

    @pytest.mark.integration
    @responses.activate
    def test_state_code_formatting(self, mock_epa_csv_response):
        """Formats state code correctly for WQP."""
        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Station/search",
            body=mock_epa_csv_response,
            status=200,
        )

        client = EPAWaterQuality()
        # Should accept either format
        client.get_stations(state_code="CO")
        assert responses.calls[0].request.params['statecode'] == 'US:CO'

        responses.reset()
        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Station/search",
            body=mock_epa_csv_response,
            status=200,
        )
        client.get_stations(state_code="US:CO")
        assert responses.calls[0].request.params['statecode'] == 'US:CO'

    @pytest.mark.integration
    @responses.activate
    def test_get_stations_by_huc(self, mock_epa_csv_response):
        """Retrieves stations filtered by HUC."""
        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Station/search",
            body=mock_epa_csv_response,
            status=200,
        )

        client = EPAWaterQuality()
        result = client.get_stations(huc="14010001")

        assert 'huc' in responses.calls[0].request.params

    @pytest.mark.integration
    @responses.activate
    def test_get_stations_by_site_type(self, mock_epa_csv_response):
        """Filters stations by site type."""
        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Station/search",
            body=mock_epa_csv_response,
            status=200,
        )

        client = EPAWaterQuality()
        result = client.get_stations(state_code="CO", site_type="Well")

        assert responses.calls[0].request.params['siteType'] == 'Well'


class TestEPAWaterQualityGetResults:
    """Tests for EPAWaterQuality.get_results method."""

    @pytest.mark.integration
    @responses.activate
    def test_get_results_basic(self):
        """Retrieves measurement results."""
        csv_response = """OrganizationIdentifier,MonitoringLocationIdentifier,ActivityStartDate,CharacteristicName,ResultMeasureValue,ResultMeasure/MeasureUnitCode
EPA-CO,CO-001,2024-01-01,pH,7.2,None
EPA-CO,CO-001,2024-01-02,pH,7.3,None
EPA-CO,CO-002,2024-01-01,pH,7.5,None"""

        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Result/search",
            body=csv_response,
            status=200,
        )

        client = EPAWaterQuality()
        result = client.get_results(
            state_code="CO",
            characteristic_name="pH",
        )

        assert not result.empty
        assert 'ResultMeasureValue' in result.columns or 'resultmeasurevalue' in [c.lower() for c in result.columns]

    @pytest.mark.integration
    @responses.activate
    def test_get_results_with_dates(self):
        """Retrieves results within date range."""
        csv_response = """OrganizationIdentifier,MonitoringLocationIdentifier,ActivityStartDate,CharacteristicName,ResultMeasureValue
EPA-CO,CO-001,2024-01-15,pH,7.2"""

        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Result/search",
            body=csv_response,
            status=200,
        )

        client = EPAWaterQuality()
        result = client.get_results(
            state_code="CO",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        # Verify date parameters were passed
        params = responses.calls[0].request.params
        assert 'startDateLo' in params
        assert 'startDateHi' in params

    @pytest.mark.integration
    @responses.activate
    def test_parses_dates(self):
        """Parses ActivityStartDate as datetime."""
        csv_response = """OrganizationIdentifier,MonitoringLocationIdentifier,ActivityStartDate,ResultMeasureValue
EPA-CO,CO-001,2024-01-15,7.2"""

        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Result/search",
            body=csv_response,
            status=200,
        )

        client = EPAWaterQuality()
        result = client.get_results(state_code="CO")

        assert pd.api.types.is_datetime64_any_dtype(result['ActivityStartDate'])


class TestEPAWaterQualityColoradoBasin:
    """Tests for Colorado River Basin convenience method."""

    @pytest.mark.integration
    @responses.activate
    def test_get_colorado_basin_results(self):
        """Retrieves data from both upper and lower basins."""
        csv_response = """MonitoringLocationIdentifier,ActivityStartDate,ResultMeasureValue
SITE-001,2024-01-01,7.2"""

        # Add responses for both HUC regions
        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Result/search",
            body=csv_response,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Result/search",
            body=csv_response,
            status=200,
        )

        client = EPAWaterQuality()
        result = client.get_colorado_basin_results(characteristic="ph")

        # Should have made two requests (upper and lower)
        assert len(responses.calls) == 2
        # Result should include basin column
        assert 'basin' in result.columns

    @pytest.mark.integration
    @responses.activate
    def test_characteristic_name_lookup(self):
        """Looks up full characteristic name from shorthand."""
        csv_response = """MonitoringLocationIdentifier,ResultMeasureValue
SITE-001,7.2"""

        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Result/search",
            body=csv_response,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Result/search",
            body=csv_response,
            status=200,
        )

        client = EPAWaterQuality()
        client.get_colorado_basin_results(characteristic="temperature")

        # Should have used full characteristic name
        params = responses.calls[0].request.params
        assert params['characteristicName'] == 'Temperature, water'


class TestEPAWaterQualitySearchCharacteristics:
    """Tests for characteristic search method."""

    @pytest.mark.integration
    @responses.activate
    def test_search_characteristics(self):
        """Searches for characteristics by keyword."""
        json_response = {
            "codes": [
                {"value": "Arsenic"},
                {"value": "Arsenic, Inorganic"},
                {"value": "Arsenic, dissolved"},
                {"value": "Iron"},
            ]
        }

        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/Codes/characteristicname",
            json=json_response,
            status=200,
        )

        client = EPAWaterQuality()
        result = client.search_characteristics("arsenic")

        assert len(result) == 3  # Should find 3 arsenic-related
        assert all("arsenic" in c.lower() for c in result)


class TestEPAWaterQualityErrorHandling:
    """Tests for error handling."""

    @pytest.mark.integration
    @responses.activate
    def test_handles_http_error(self):
        """Raises exception on HTTP error."""
        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Station/search",
            status=500,
        )

        client = EPAWaterQuality()
        with pytest.raises(Exception):
            client.get_stations(state_code="CO")

    @pytest.mark.integration
    @responses.activate
    def test_handles_empty_response(self):
        """Handles empty CSV response - pandas raises EmptyDataError."""
        empty_csv = ""

        responses.add(
            responses.GET,
            "https://www.waterqualitydata.us/data/Station/search",
            body=empty_csv,
            status=200,
        )

        client = EPAWaterQuality()
        # Empty CSV causes pandas to raise EmptyDataError
        with pytest.raises(Exception):
            client.get_stations(state_code="XX")
