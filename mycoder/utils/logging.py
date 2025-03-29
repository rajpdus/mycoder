"""
Logging configuration for MyCoder.

This module sets up a rich logging system with hierarchical, color-coded output.
It provides factory functions for creating loggers with consistent configuration.
"""

import logging
import sys
from typing import Dict, Optional, Union

from rich.console import Console
from rich.logging import RichHandler

from src.mycoder.settings.config import LogLevel

# Map string log levels to logging module constants
LOG_LEVEL_MAP: Dict[LogLevel, int] = {
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.VERBOSE: 15,  # Custom level between DEBUG and INFO
    LogLevel.INFO: logging.INFO,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.ERROR: logging.ERROR,
}

# Add VERBOSE level to the logging module
logging.addLevelName(LOG_LEVEL_MAP[LogLevel.VERBOSE], "VERBOSE")


def verbose(self: logging.Logger, message: str, *args, **kwargs) -> None:
    """
    Log a message with VERBOSE level.

    Args:
        message: The message to log.
        *args: Additional positional arguments for the logger.
        **kwargs: Additional keyword arguments for the logger.
    """
    if self.isEnabledFor(LOG_LEVEL_MAP[LogLevel.VERBOSE]):
        self._log(LOG_LEVEL_MAP[LogLevel.VERBOSE], message, args, **kwargs)


# Add the verbose method to the Logger class
logging.Logger.verbose = verbose  # type: ignore


def configure_logging(
    log_level: Union[LogLevel, str] = LogLevel.INFO,
    show_path: bool = False,
    rich_tracebacks: bool = True,
) -> None:
    """
    Configure the root logger with rich output.

    Args:
        log_level: The minimum log level to display.
        show_path: Whether to show the file path in log messages.
        rich_tracebacks: Whether to use rich for traceback formatting.
    """
    # Convert string log level to enum if needed
    if isinstance(log_level, str):
        try:
            log_level = LogLevel(log_level.lower())
        except ValueError:
            log_level = LogLevel.INFO

    # Map the log level enum to the numeric value
    numeric_level = LOG_LEVEL_MAP.get(log_level, logging.INFO)

    # Configure the root logger
    console = Console(stderr=True)
    handler = RichHandler(
        console=console,
        show_path=show_path,
        rich_tracebacks=rich_tracebacks,
        markup=True,
        show_time=True,
    )

    # Set format for the formatter
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers and add our custom handler
    for existing_handler in root_logger.handlers[:]:
        root_logger.removeHandler(existing_handler)
    root_logger.addHandler(handler)


def get_logger(name: str, log_level: Optional[Union[LogLevel, str]] = None) -> logging.Logger:
    """
    Get a logger with the specified name and log level.

    Args:
        name: The name of the logger, typically the module name using dot notation.
        log_level: Optional override for the log level of this specific logger.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)

    # Set specific log level if provided, otherwise inherit from root
    if log_level is not None:
        if isinstance(log_level, str):
            try:
                log_level = LogLevel(log_level.lower())
            except ValueError:
                # Invalid log level string, use the logger's current level
                pass
            else:
                numeric_level = LOG_LEVEL_MAP.get(log_level, logging.INFO)
                logger.setLevel(numeric_level)
        else:
            numeric_level = LOG_LEVEL_MAP.get(log_level, logging.INFO)
            logger.setLevel(numeric_level)

    return logger 