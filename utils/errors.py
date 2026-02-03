"""Utility functions for error handling used across the bot."""

from __future__ import annotations

import functools
import logging
import traceback

logger = logging.getLogger(__name__)


def catch_errors(func):
    """Decorator that logs exceptions raised by async handlers."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:  # noqa: BLE001
            logger.exception("🚨 Unhandled exception in %s: %s", func.__name__, e)
            tb = traceback.format_exc()
            logger.debug("Traceback:\n%s", tb)

    return wrapper


__all__ = ["catch_errors"]
