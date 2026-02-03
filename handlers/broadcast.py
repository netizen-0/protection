import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from pyrogram.errors import (
    FloodWait, ChatWriteForbidden, PeerIdInvalid,
    UserIsBlocked, UserKicked
)

from config import OWNER_ID
from utils.db import (
    get_broadcast_groups,
    get_broadcast_users,
)
from utils.errors import catch_errors

logger = logging.getLogger(__name__)


def register(app: Client) -> None:
    logger.info("✅ Registered: broadcast.py")

    @app.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
    @catch_errors
    async def broadcast_cmd(client: Client, message: Message) -> None:
        """Broadcast a message to all stored groups from the DB."""
        logger.info("[BROADCAST] Triggered by %s", message.from_user.id)

        text = None
        payload_msg = None

        # Support `/broadcast text` or reply-to-message
        if message.reply_to_message:
            payload_msg = message.reply_to_message
        elif len(message.command) >= 2:
            text = message.text.split(None, 1)[1]
        else:
            await message.reply_text("❗ Usage:\nReply to a message or use `/broadcast <text>`")
            return

        groups = await get_broadcast_groups()
        users = await get_broadcast_users()
        targets = set(groups + users)
        logger.debug(
            "[BROADCAST] Sending to %d chats (%d groups, %d users)",
            len(targets), len(groups), len(users)
        )
        sent, failed = 0, 0

        for chat_id in targets:
            try:
                if payload_msg:
                    await payload_msg.copy(chat_id)
                else:
                    await client.send_message(chat_id, text, parse_mode=ParseMode.HTML)
                sent += 1
                logger.debug("[BROADCAST] Sent to %s", chat_id)

            except FloodWait as e:
                logger.warning("⏳ FloodWait for %s: %s sec", chat_id, e.value)
                await asyncio.sleep(e.value)
                try:
                    if payload_msg:
                        await payload_msg.copy(chat_id)
                    else:
                        await client.send_message(chat_id, text, parse_mode=ParseMode.HTML)
                    sent += 1
                except Exception as e2:
                    logger.error("❌ Retry failed for %s: %s", chat_id, str(e2))
                    failed += 1

            except (ChatWriteForbidden, UserKicked, PeerIdInvalid, UserIsBlocked) as e:
                logger.warning("⛔ Cannot send to %s: %s", chat_id, type(e).__name__)
                failed += 1

            except Exception as e:
                logger.error("❌ Unexpected error with %s: %s", chat_id, str(e))
                failed += 1

            await asyncio.sleep(0.1)

        # Report summary
        await message.reply_text(
            f"✅ <b>Broadcast complete</b>\n"
            f"Sent: <b>{sent}</b>\nFailed: <b>{failed}</b>",
            parse_mode=ParseMode.HTML
        )
