"""
Interface for configuring the headers to attach to an HTTP request.
"""

import json
import logging
import pathlib
import typing

LOGGER = logging.getLogger(__name__)

def load_headers(
    path: pathlib.Path = pathlib.Path(__file__).parent / "config" / "headers.json"
) -> typing.Dict[str, typing.Any]:
    """
    Loads from a configuration file the headers to attach to an HTTP request.

    :param path: The path to a JSON file specifying the HTTP request headers to use
    :return: A dictionary of the HTTP request headers to use
    """
    LOGGER.info("Reading HTTP request headers from '%s'", path)
    with open(path, "r", encoding="utf-8") as file:
        headers = json.load(file)
    LOGGER.info("Loaded HTTP request headers:\n\t%s", headers)

    return headers
