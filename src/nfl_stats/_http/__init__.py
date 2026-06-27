"""
Interface for specifying the parameters to attach to an HTTP request.

.. py:attribute:: TIMEOUT

    The connect/read timeouts to attach to an HTTP request.

.. py:attribute:: HEADERS

    The headers to attach to an HTTP request.
"""

from . import _headers

__all__ = [
    "HEADERS",
    "TIMEOUT"
]

TIMEOUT = 10
HEADERS = _headers.load_headers()
