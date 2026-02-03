"""Helper utilities for Telegram webhooks."""

from __future__ import annotations

import asyncio
import logging
from urllib import request, parse, error

logger = logging.getLogger(__name__)


async def set_webhook(bot_token: str, url: str) -> None:
    """Set the Telegram bot webhook via the HTTP Bot API."""
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    data = parse.urlencode({"url": url}).encode("utf-8")
    req = request.Request(api_url, data=data)

    loop = asyncio.get_running_loop()

    try:
        logger.debug("Setting webhook to: %s", url)
        await loop.run_in_executor(None, request.urlopen, req)
        logger.info("✅ Webhook successfully set")
    except error.URLError as exc:
        logger.error("❌ Failed to set webhook: %s", exc.reason)
    except Exception as exc:  # noqa: BLE001
        logger.exception("🔥 Unexpected error while setting webhook: %s", exc)


async def delete_webhook(bot_token: str) -> None:
    """Remove the Telegram bot webhook via the HTTP Bot API."""
    api_url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
    data = parse.urlencode({"drop_pending_updates": "true"}).encode("utf-8")
    req = request.Request(api_url, data=data)

    loop = asyncio.get_running_loop()

    try:
        logger.debug("Deleting webhook via Bot API")
        await loop.run_in_executor(None, request.urlopen, req)
        logger.info("✅ Webhook deleted")
    except error.URLError as exc:
        logger.error("❌ Failed to delete webhook: %s", exc.reason)
    except Exception as exc:  # noqa: BLE001
        logger.exception("🔥 Unexpected error while deleting webhook: %s", exc)


__all__ = ["set_webhook", "delete_webhook"]

