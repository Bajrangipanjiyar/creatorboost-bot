# -*- coding: utf-8 -*-
"""
Logger setup for CreatorBoost Bot
"""

import logging
import sys

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("CreatorBoost")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logger()
