"""
Generic REST API Client

A flexible client for interacting with any REST API endpoint.
Use this as a template for adding new data sources.
"""

import requests
import pandas as pd
from typing import Optional, Any
from urllib.parse import urljoin
import time


class RESTClient:
    """Generic REST API client with common patterns for data retrieval."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        api_key_header: str = "Authorization",
        api_key_prefix: str = "Bearer",
        default_headers: Optional[dict] = None,
        rate_limit_delay: float = 0.0,
    ):
        """
        Initialize REST client.

        Args:
            base_url: Base URL for the API
            api_key: API key if required
            api_key_header: Header name for API key
            api_key_prefix: Prefix for API key value (e.g., 'Bearer', 'Api-Key')
            default_headers: Additional headers to include in all requests
            rate_limit_delay: Seconds to wait between requests
        """
        self.base_url = base_url.rstrip("/")
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0

        self.session = requests.Session()

        # Set up headers
        headers = {"Accept": "application/json"}
        if default_headers:
            headers.update(default_headers)
        if api_key:
            if api_key_prefix:
                headers[api_key_header] = f"{api_key_prefix} {api_key}"
            else:
                headers[api_key_header] = api_key

        self.session.headers.update(headers)

    def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        **kwargs,
    ) -> dict:
        """
        Make GET request.

        Args:
            endpoint: API endpoint (will be joined with base_url)
            params: Query parameters
            **kwargs: Additional arguments passed to requests.get

        Returns:
            Response JSON as dict
        """
        self._respect_rate_limit()

        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        response = self.session.get(url, params=params, **kwargs)
        response.raise_for_status()

        return response.json()

    def get_dataframe(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        data_key: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Make GET request and return as DataFrame.

        Args:
            endpoint: API endpoint
            params: Query parameters
            data_key: Key in response containing the data array (e.g., 'results', 'data')
            **kwargs: Additional arguments

        Returns:
            DataFrame from response data
        """
        data = self.get(endpoint, params, **kwargs)

        if data_key:
            data = data.get(data_key, [])

        return pd.DataFrame(data)

    def get_paginated(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        data_key: str = "results",
        page_param: str = "page",
        limit_param: str = "limit",
        limit: int = 100,
        max_pages: Optional[int] = None,
        total_key: Optional[str] = None,
        next_url_key: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get paginated data from API.

        Supports two pagination styles:
        1. Page number based (page_param)
        2. Next URL based (next_url_key)

        Args:
            endpoint: API endpoint
            params: Query parameters
            data_key: Key containing data array in response
            page_param: Parameter name for page number
            limit_param: Parameter name for page size
            limit: Number of items per page
            max_pages: Maximum pages to retrieve (None for all)
            total_key: Key containing total count (for page-based)
            next_url_key: Key containing next page URL

        Returns:
            DataFrame with all paginated results
        """
        params = params or {}
        params[limit_param] = limit

        all_data = []
        page = 1
        next_url = None

        while True:
            if max_pages and page > max_pages:
                break

            if next_url:
                # Use next URL directly
                response = self.session.get(next_url)
                response.raise_for_status()
                data = response.json()
            else:
                params[page_param] = page
                data = self.get(endpoint, params)

            results = data.get(data_key, [])
            if not results:
                break

            all_data.extend(results)

            # Check for more pages
            if next_url_key and data.get(next_url_key):
                next_url = data[next_url_key]
            elif total_key:
                total = data.get(total_key, 0)
                if len(all_data) >= total:
                    break
                page += 1
            else:
                # No pagination info, assume we got everything
                if len(results) < limit:
                    break
                page += 1

        return pd.DataFrame(all_data)

    def post(
        self,
        endpoint: str,
        json: Optional[dict] = None,
        data: Optional[Any] = None,
        **kwargs,
    ) -> dict:
        """
        Make POST request.

        Args:
            endpoint: API endpoint
            json: JSON body
            data: Form data
            **kwargs: Additional arguments

        Returns:
            Response JSON as dict
        """
        self._respect_rate_limit()

        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        response = self.session.post(url, json=json, data=data, **kwargs)
        response.raise_for_status()

        return response.json()

    def _respect_rate_limit(self):
        """Wait if needed to respect rate limit."""
        if self.rate_limit_delay > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()


class CSVEndpointClient(RESTClient):
    """Client for APIs that return CSV data."""

    def get_csv(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        **read_csv_kwargs,
    ) -> pd.DataFrame:
        """
        Fetch CSV data from endpoint.

        Args:
            endpoint: API endpoint
            params: Query parameters
            **read_csv_kwargs: Arguments passed to pd.read_csv

        Returns:
            DataFrame from CSV response
        """
        self._respect_rate_limit()

        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))
        response = self.session.get(url, params=params)
        response.raise_for_status()

        from io import StringIO
        return pd.read_csv(StringIO(response.text), **read_csv_kwargs)


# Example: Creating a client for a hypothetical state water API
class ExampleStateWaterAPI(RESTClient):
    """
    Example of extending RESTClient for a specific API.

    This shows the pattern for adding new data sources.
    """

    def __init__(self, api_key: str):
        super().__init__(
            base_url="https://api.example-state-water.gov/v1",
            api_key=api_key,
            api_key_header="X-API-Key",
            api_key_prefix="",  # No prefix
            rate_limit_delay=0.5,  # Be nice to the API
        )

    def get_wells(self, county: Optional[str] = None) -> pd.DataFrame:
        """Get well locations."""
        params = {}
        if county:
            params["county"] = county
        return self.get_dataframe("/wells", params, data_key="wells")

    def get_measurements(
        self,
        well_id: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """Get measurements for a well."""
        return self.get_dataframe(
            f"/wells/{well_id}/measurements",
            params={"start": start_date, "end": end_date},
            data_key="measurements",
        )


# Example usage
if __name__ == "__main__":
    # Example: Fetch data from a public JSON API
    client = RESTClient("https://jsonplaceholder.typicode.com")

    # Simple GET
    posts = client.get_dataframe("/posts")
    print(f"Retrieved {len(posts)} posts")

    # With query params
    user_posts = client.get_dataframe("/posts", params={"userId": 1})
    print(f"User 1 has {len(user_posts)} posts")
