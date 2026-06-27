"""
Interfaces for configuring the package logger.
"""

import logging

def configure_logger(level: int = logging.INFO) -> None:
    """
    Configures the package logger.

    Other modules in the package should simply import the `logging` module then call
    `logging.getLogger(__name__)` to access the module-level logger to use for any needed logging.

    :param level: The logging level to configure
    """
    root = logging.getLogger()

    # Prevent duplicate configuration
    if root.handlers:
        return

    # Configure logger
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    root.addHandler(handler)
    root.setLevel(level)
