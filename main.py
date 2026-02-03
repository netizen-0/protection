import logging
import signal
import asyncio

from pyrogram import Client, idle
from pyrogram.enums import ParseMode

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    MONGO_URI,
    MONGO_DB,
    LOG_LEVEL,
)
from handlers import register_all
from utils.db import init_db, close_db
from utils.webhook import delete_webhook

# ───────────────── Logging ─────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)
logger = logging.getLogger("OxygenBot")

# ───────────────── Bot Client ─────────────────
bot = Client(
    name="oxygen_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    parse_mode=ParseMode.HTML,
)

# ───────────────── Graceful Shutdown (Heroku safe) ─────────────────
def _shutdown(*_):
    logger.warning("⚠️ Shutdown signal received. Stopping bot...")
    loop = asyncio.get_event_loop()
    loop.stop()

signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)

# ───────────────── Main Lifecycle ─────────────────
async def main() -> None:
    logger.info("🚀 Starting OxygenBot...")

    # Database
    await init_db(MONGO_URI, MONGO_DB)
    logger.info("✅ MongoDB connected.")

    # Ensure polling mode
    await delete_webhook(BOT_TOKEN)
    logger.info("🔌 Webhook deleted. Polling mode active.")

    # Start bot
    async with bot:
        register_all(bot)
        logger.info("🤖 Bot started successfully. Waiting for updates...")
        await idle()

    # Cleanup
    await close_db()
    logger.info("🛑 Bot stopped. MongoDB connection closed.")

# ───────────────── Entrypoint ─────────────────
if __name__ == "__main__":
    bot.run(main())
