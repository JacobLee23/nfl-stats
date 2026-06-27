"""
Unit tests for :py:mod:`nfl_stats._http`.
"""

import pytest
import requests

from nfl_stats._http import HEADERS, TIMEOUT

@pytest.mark.parametrize(
    "url", [
        "https://nfl.com/"
    ]
)
def test_get(url: str):
    """
    Send an HTTP GET request to the specified URL with the configured HTTP headers and
    source/target timeouts

    :param url: The URL to which to send the HTTP request
    """
    with requests.get(url, headers=HEADERS, timeout=TIMEOUT) as response:
        assert response.status_code == requests.codes.ok
