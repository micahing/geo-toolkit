"""
Integration tests for USGS Water Services client.

Uses HTTP response mocking to test API client behavior.
"""

import pytest
import responses
import pandas as pd
from datetime import datetime, timedelta

from scripts.data_retrieval.usgs import USGSWaterServices


class TestUSGSWaterServicesGetSites:
    """Tests for USGSWaterServices.get_sites method."""

    @pytest.mark.integration
    @responses.activate
    def test_get_sites_by_state(self, mock_usgs_rdb_response):
        """Retrieves sites filtered by state code."""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/site/",
            body=mock_usgs_rdb_response,
            status=200,
        )

        client = USGSWaterServices()
        result = client.get_sites(state_code="AZ")

        assert not result.empty
        assert 'site_no' in result.columns
        assert len(result) == 3

    @pytest.mark.integration
    @responses.activate
    def test_get_sites_by_huc(self, mock_usgs_rdb_response):
        """Retrieves sites filtered by HUC code."""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/site/",
            body=mock_usgs_rdb_response,
            status=200,
        )

        client = USGSWaterServices()
        result = client.get_sites(huc="14")

        assert not result.empty
        # Verify HUC was passed in request
        assert 'huc' in responses.calls[0].request.params

    @pytest.mark.integration
    @responses.activate
    def test_get_sites_by_bbox(self, mock_usgs_rdb_response):
        """Retrieves sites filtered by bounding box."""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/site/",
            body=mock_usgs_rdb_response,
            status=200,
        )

        client = USGSWaterServices()
        bbox = (-115.0, 35.0, -110.0, 40.0)
        result = client.get_sites(bbox=bbox)

        assert not result.empty
        # Verify bbox was passed in request
        assert 'bBox' in responses.calls[0].request.params

    @pytest.mark.integration
    @responses.activate
    def test_handles_empty_response(self):
        """Handles empty response gracefully."""
        empty_response = """#
# No data found
#
"""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/site/",
            body=empty_response,
            status=200,
        )

        client = USGSWaterServices()
        result = client.get_sites(state_code="XX")

        assert result.empty


class TestUSGSWaterServicesTimeSeries:
    """Tests for time series data retrieval methods."""

    @pytest.mark.integration
    @responses.activate
    def test_get_instantaneous_values(self, mock_usgs_json_response):
        """Retrieves instantaneous values."""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/iv/",
            json=mock_usgs_json_response,
            status=200,
        )

        client = USGSWaterServices()
        result = client.get_instantaneous_values(
            sites=["09380000"],
            parameter_codes=["00060"],
            period="P7D",
        )

        assert not result.empty
        assert 'datetime' in result.columns
        assert 'value' in result.columns
        assert 'site_code' in result.columns
        assert pd.api.types.is_datetime64_any_dtype(result['datetime'])

    @pytest.mark.integration
    @responses.activate
    def test_get_daily_values(self, mock_usgs_json_response):
        """Retrieves daily values."""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/dv/",
            json=mock_usgs_json_response,
            status=200,
        )

        client = USGSWaterServices()
        result = client.get_daily_values(
            sites=["09380000"],
            parameter_codes=["00060"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )

        assert not result.empty

    @pytest.mark.integration
    @responses.activate
    def test_get_groundwater_levels(self, mock_usgs_json_response):
        """Retrieves groundwater level data."""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/gwlevels/",
            json=mock_usgs_json_response,
            status=200,
        )

        client = USGSWaterServices()
        result = client.get_groundwater_levels(
            state_code="CO",
            start_date=datetime(2024, 1, 1),
        )

        assert not result.empty

    @pytest.mark.integration
    @responses.activate
    def test_parses_coordinates(self, mock_usgs_json_response):
        """Parses latitude and longitude from response."""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/iv/",
            json=mock_usgs_json_response,
            status=200,
        )

        client = USGSWaterServices()
        result = client.get_instantaneous_values(
            sites=["09380000"],
            parameter_codes=["00060"],
            period="P1D",
        )

        assert 'latitude' in result.columns
        assert 'longitude' in result.columns
        assert pd.api.types.is_numeric_dtype(result['latitude'])
        assert pd.api.types.is_numeric_dtype(result['longitude'])

    @pytest.mark.integration
    @responses.activate
    def test_parses_qualifiers(self, mock_usgs_json_response):
        """Parses data quality qualifiers."""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/iv/",
            json=mock_usgs_json_response,
            status=200,
        )

        client = USGSWaterServices()
        result = client.get_instantaneous_values(
            sites=["09380000"],
            parameter_codes=["00060"],
            period="P1D",
        )

        assert 'qualifiers' in result.columns


class TestUSGSWaterServicesConvenienceMethods:
    """Tests for convenience methods."""

    @pytest.mark.integration
    @responses.activate
    def test_get_colorado_basin_sites(self, mock_usgs_rdb_response):
        """Gets Colorado basin sites."""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/site/",
            body=mock_usgs_rdb_response,
            status=200,
        )

        client = USGSWaterServices()
        result = client.get_colorado_basin_sites(basin="upper")

        assert not result.empty
        # Verify correct HUC was requested
        assert responses.calls[0].request.params['huc'] == '14'


class TestUSGSWaterServicesErrorHandling:
    """Tests for error handling."""

    @pytest.mark.integration
    @responses.activate
    def test_handles_http_error(self):
        """Raises exception on HTTP error."""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/site/",
            status=500,
        )

        client = USGSWaterServices()
        with pytest.raises(Exception):
            client.get_sites(state_code="CO")

    @pytest.mark.integration
    @responses.activate
    def test_handles_invalid_json(self):
        """Raises exception on invalid JSON response."""
        responses.add(
            responses.GET,
            "https://waterservices.usgs.gov/nwis/iv/",
            body="not valid json",
            status=200,
        )

        client = USGSWaterServices()
        with pytest.raises(Exception):
            client.get_instantaneous_values(
                sites=["09380000"],
                parameter_codes=["00060"],
                period="P1D",
            )
