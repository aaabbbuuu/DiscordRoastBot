"""Logging configuration for Smart Roast Bot.

Sets up root logger with:
- Console handler at INFO level
- Rotating file handler at DEBUG level (5 MB, 3 backups)
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR = "logs"
_LOG_FILE = os.path.join(_LOG_DIR, "bot.log")
_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3


def setup_logging() -> logging.Logger:
    """Configure the root logger with console and rotating file handlers.

    Returns:
        The root :class:`logging.Logger` instance.
    """
    os.makedirs(_LOG_DIR, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_LOG_FORMAT)

    # Console handler — INFO
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    # Rotating file handler — DEBUG, 5 MB, 3 backups
    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    root_logger.info("Logging initialised — console (INFO) + file (DEBUG)")
    return root_logger
