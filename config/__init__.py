import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "oxygen")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "0"))
SUPPORT_CHAT_URL = os.getenv("SUPPORT_CHAT_URL", "https://t.me/botsyard")
DEVELOPER_URL = os.getenv("DEVELOPER_URL", "https://t.me/oxeign")
PANEL_IMAGE_URL = os.getenv("PANEL_IMAGE_URL", "https://files.catbox.moe/uvqeln.jpg")

_missing = [name for name, val in {"BOT_TOKEN": BOT_TOKEN, "API_ID": API_ID, "API_HASH": API_HASH}.items() if not val]
if _missing:
    missing = ", ".join(_missing)
    logger.error("Missing required env vars: %s", missing)
    raise RuntimeError(
        f"Missing required environment variables: {missing}. Copy .env.example and set them."
    )

if not MONGO_URI.startswith(("mongodb://", "mongodb+srv://")):
    raise RuntimeError("Invalid MONGO_URI. Must begin with mongodb:// or mongodb+srv://")
