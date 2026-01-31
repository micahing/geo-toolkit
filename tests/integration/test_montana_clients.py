"""
Integration tests for Montana data clients.

Uses HTTP response mocking to test API client behavior.
"""

import pytest
import responses
import pandas as pd
from datetime import datetime, timedelta

from scripts.data_retrieval.montana import (
    MontanaMesonet,
    MontanaGWIC,
    MontanaDNRC,
    MontanaStateLibrary,
    get_montana_clients,
)


class TestMontanaMesonetGetStations:
    """Tests for MontanaMesonet.get_stations method."""

    @pytest.mark.integration
    @responses.activate
    def test_get_all_stations(self, mock_mesonet_stations_response):
        """Retrieves all stations."""
        responses.add(
            responses.GET,
            "https://mesonet.climate.umt.edu/api/v2/stations/",
            json=mock_mesonet_stations_response,
            status=200,
        )

        client = MontanaMesonet()
        result = client.get_stations()

        assert not result.empty
        assert 'station' in result.columns
        assert 'latitude' in result.columns
        assert 'longitude' in result.columns
        assert len(result) == 2

    @pytest.mark.integration
    @responses.activate
    def test_get_active_stations_only(self, mock_mesonet_stations_response):
        """Retrieves only active stations."""
        responses.add(
            responses.GET,
            "https://mesonet.climate.umt.edu/api/v2/stations/",
            json=mock_mesonet_stations_response,
            status=200,
        )

        client = MontanaMesonet()
        result = client.get_stations(active_only=True)

        # Verify active=true was passed
        assert responses.calls[0].request.params['active'] == 'true'

    @pytest.mark.integration
    @responses.activate
    def test_get_stations_as_geodataframe(self, mock_mesonet_stations_response):
        """Returns GeoDataFrame when requested."""
        responses.add(
            responses.GET,
            "https://mesonet.climate.umt.edu/api/v2/stations/",
            json=mock_mesonet_stations_response,
            status=200,
        )

        client = MontanaMesonet()
        result = client.get_stations(as_geodataframe=True)

        import geopandas as gpd
        assert isinstance(result, gpd.GeoDataFrame)
        assert result.crs.to_epsg() == 4326


class TestMontanaMesonetObservations:
    """Tests for observation retrieval methods."""

    @pytest.mark.integration
    @responses.activate
    def test_get_latest(self):
        """Retrieves latest observations."""
        latest_response = [
            {"station": "aceabsar", "air_temp": 5.2, "datetime": "2024-01-15T12:00:00Z"},
            {"station": "aceamste", "air_temp": 3.1, "datetime": "2024-01-15T12:00:00Z"},
        ]

        responses.add(
            responses.GET,
            "https://mesonet.climate.umt.edu/api/v2/latest/",
            json=latest_response,
            status=200,
        )

        client = MontanaMesonet()
        result = client.get_latest()

        assert not result.empty
        assert 'station' in result.columns

    @pytest.mark.integration
    @responses.activate
    def test_get_hourly_observations(self, mock_mesonet_observations_response):
        """Retrieves hourly observations."""
        responses.add(
            responses.GET,
            "https://mesonet.climate.umt.edu/api/v2/observations/hourly/",
            json=mock_mesonet_observations_response,
            status=200,
        )

        client = MontanaMesonet()
        result = client.get_hourly_observations(
            stations=["aceabsar"],
            start_date=datetime(2024, 1, 1),
            elements=["air_temp", "ppt"],
        )

        assert not result.empty
        assert pd.api.types.is_datetime64_any_dtype(result['datetime'])

    @pytest.mark.integration
    @responses.activate
    def test_get_daily_observations(self):
        """Retrieves daily observations."""
        daily_response = [
            {"station": "aceabsar", "date": "2024-01-01", "air_temp_max": 10.0, "air_temp_min": -5.0},
            {"station": "aceabsar", "date": "2024-01-02", "air_temp_max": 12.0, "air_temp_min": -3.0},
        ]

        responses.add(
            responses.GET,
            "https://mesonet.climate.umt.edu/api/v2/observations/daily/",
            json=daily_response,
            status=200,
        )

        client = MontanaMesonet()
        result = client.get_daily_observations(
            stations=["aceabsar"],
            start_date=datetime(2024, 1, 1),
        )

        assert not result.empty
        assert pd.api.types.is_datetime64_any_dtype(result['date'])


class TestMontanaMesonetSearchByCounty:
    """Tests for county search method."""

    @pytest.mark.integration
    @responses.activate
    def test_search_stations_by_county(self, mock_mesonet_stations_response):
        """Searches stations by county name."""
        responses.add(
            responses.GET,
            "https://mesonet.climate.umt.edu/api/v2/stations/",
            json=mock_mesonet_stations_response,
            status=200,
        )

        client = MontanaMesonet()
        result = client.search_stations_by_county("Gallatin")

        assert not result.empty
        assert len(result) == 1
        assert result.iloc[0]['county'] == 'Gallatin'

    @pytest.mark.integration
    @responses.activate
    def test_search_by_county_case_insensitive(self, mock_mesonet_stations_response):
        """County search is case-insensitive."""
        responses.add(
            responses.GET,
            "https://mesonet.climate.umt.edu/api/v2/stations/",
            json=mock_mesonet_stations_response,
            status=200,
        )

        client = MontanaMesonet()
        result = client.search_stations_by_county("GALLATIN")

        assert len(result) == 1


class TestMontanaGWIC:
    """Tests for Montana GWIC client."""

    @pytest.mark.integration
    @responses.activate
    def test_get_wells_from_arcgis(self):
        """Retrieves wells from ArcGIS service."""
        arcgis_response = {
            "features": [
                {
                    "attributes": {"GWICID": "12345", "COUNTY": "GALLATIN"},
                    "geometry": {"x": -111.0, "y": 45.5}
                },
                {
                    "attributes": {"GWICID": "12346", "COUNTY": "GALLATIN"},
                    "geometry": {"x": -111.1, "y": 45.6}
                },
            ]
        }

        responses.add(
            responses.GET,
            "https://services1.arcgis.com/KyHQVZVT08EIH1v8/arcgis/rest/services/GWIC_Wells/FeatureServer/0/query",
            json=arcgis_response,
            status=200,
        )

        client = MontanaGWIC()
        result = client.get_wells_from_arcgis(county="GALLATIN")

        assert not result.empty
        assert 'GWICID' in result.columns
        assert 'latitude' in result.columns
        assert 'longitude' in result.columns

    @pytest.mark.integration
    @responses.activate
    def test_handles_arcgis_error(self):
        """Handles ArcGIS service error gracefully."""
        responses.add(
            responses.GET,
            "https://services1.arcgis.com/KyHQVZVT08EIH1v8/arcgis/rest/services/GWIC_Wells/FeatureServer/0/query",
            status=500,
        )

        client = MontanaGWIC()
        result = client.get_wells_from_arcgis()

        # Should return empty DataFrame, not raise
        assert result.empty

    @pytest.mark.integration
    def test_get_gwic_url(self):
        """Generates correct GWIC website URL."""
        url = MontanaGWIC.get_gwic_url("12345")
        assert "gwicid=12345" in url
        assert "mbmggwic.mtech.edu" in url


class TestMontanaDNRC:
    """Tests for Montana DNRC client."""

    @pytest.mark.integration
    @responses.activate
    def test_get_stream_gages(self):
        """Retrieves stream gages."""
        arcgis_response = {
            "features": [
                {
                    "attributes": {"SITE_ID": "DNRC001", "SITE_NAME": "Test Creek", "STATUS": "Active"},
                    "geometry": {"x": -110.5, "y": 46.0}
                },
            ]
        }

        responses.add(
            responses.GET,
            "https://gis.dnrc.mt.gov/arcgis/rest/services/WRD/DNRC_Stream_Gages/MapServer/0/query",
            json=arcgis_response,
            status=200,
        )

        client = MontanaDNRC()
        result = client.get_stream_gages()

        assert not result.empty
        assert 'SITE_ID' in result.columns

    @pytest.mark.integration
    @responses.activate
    def test_get_stream_gages_with_bbox(self):
        """Filters stream gages by bounding box."""
        arcgis_response = {"features": []}

        responses.add(
            responses.GET,
            "https://gis.dnrc.mt.gov/arcgis/rest/services/WRD/DNRC_Stream_Gages/MapServer/0/query",
            json=arcgis_response,
            status=200,
        )

        client = MontanaDNRC()
        bbox = (-112.0, 45.0, -110.0, 47.0)
        client.get_stream_gages(bbox=bbox)

        # Verify geometry parameters were passed
        params = responses.calls[0].request.params
        assert 'geometry' in params

    @pytest.mark.integration
    def test_get_stage_url(self):
        """Generates correct StAGE URL."""
        url = MontanaDNRC.get_stage_url("SITE001")
        assert "site=SITE001" in url
        assert "gis.dnrc.mt.gov" in url


class TestMontanaStateLibrary:
    """Tests for Montana State Library client."""

    @pytest.mark.integration
    def test_get_data_catalog_url(self):
        """Returns correct data catalog URL."""
        url = MontanaStateLibrary.get_data_catalog_url()
        assert "mslservices.mt.gov" in url

    @pytest.mark.integration
    def test_list_datasets(self):
        """Lists available dataset categories."""
        client = MontanaStateLibrary()
        datasets = client.list_datasets("hydrography")

        assert isinstance(datasets, list)


class TestGetMontanaClients:
    """Tests for convenience function."""

    @pytest.mark.integration
    def test_returns_all_clients(self):
        """Returns dict with all client instances."""
        clients = get_montana_clients()

        assert 'mesonet' in clients
        assert 'gwic' in clients
        assert 'dnrc' in clients
        assert 'state_library' in clients

        assert isinstance(clients['mesonet'], MontanaMesonet)
        assert isinstance(clients['gwic'], MontanaGWIC)
        assert isinstance(clients['dnrc'], MontanaDNRC)
        assert isinstance(clients['state_library'], MontanaStateLibrary)
