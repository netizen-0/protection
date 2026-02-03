import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatType

from utils.errors import catch_errors
from handlers.panels import send_start  # ✅ Panel entry
from config import LOG_GROUP_ID

logger = logging.getLogger(__name__)


def register(app: Client) -> None:
    logger.info("✅ Registered: general.py")

    # ✅ Panel dispatcher (DM + group)
    @app.on_message(filters.command(["start", "help", "menu", "panel"]) & (filters.private | filters.group))
    @catch_errors
    async def send_panel(client: Client, message: Message):
        logger.debug(
            "[GENERAL] panel command chat=%s user=%s",
            message.chat.id,
            message.from_user.id if message.from_user else "?",
        )
        log_panel = (
            message.chat.type == ChatType.PRIVATE and message.command and message.command[0].lower() == "start"
        )
        await send_start(client, message, log_panel=log_panel)

    # ✅ ID command
    @app.on_message(filters.command("id") & (filters.private | filters.group))
    @catch_errors
    async def id_cmd(client: Client, message: Message) -> None:
        logger.info("[GENERAL] /id command in chat %s", message.chat.id)

        target = (
            message.reply_to_message.from_user
            if message.reply_to_message and message.reply_to_message.from_user
            else message.from_user
        )

        if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL}:
            text = f"<b>Chat ID:</b> <code>{message.chat.id}</code>"
            if target:
                text += f"\n<b>User ID:</b> <code>{target.id}</code>"
        else:
            text = f"<b>Your ID:</b> <code>{target.id}</code>"

        await message.reply_text(text, parse_mode=ParseMode.HTML)

    # ✅ Ping command
    @app.on_message(filters.command("ping") & (filters.private | filters.group))
    @catch_errors
    async def ping_cmd(client: Client, message: Message) -> None:
        logger.info("[GENERAL] /ping in chat %s", message.chat.id)
        await message.reply_text("🏓 Pong!")

    # ✅ DM fallback (non-command)
    @app.on_message(filters.private & ~filters.command(["start", "help", "menu", "panel", "id", "ping"]))
    @catch_errors
    async def dm_fallback(client: Client, message: Message) -> None:
        logger.info("[DM FALLBACK] %s: %s", message.from_user.id, message.text)
        # Do not reply to unknown private messages to avoid spamming users
        return

    # ✅ Group fallback (non-command, non-service)
    @app.on_message(filters.group & ~filters.command(["start", "help", "menu", "panel", "id", "ping"]) & ~filters.service)
    @catch_errors
    async def group_fallback(client: Client, message: Message) -> None:
        logger.debug(
            "[GROUP FALLBACK] chat=%s user=%s text=%s",
            message.chat.id,
            message.from_user.id if message.from_user else "?",
            message.text,
        )

    # 📌 Track when the bot is added to a group so broadcast works reliably
    @app.on_message(filters.new_chat_members & filters.group)
    @catch_errors
    async def track_bot_added(client: Client, message: Message):
        me = await client.get_me()
        if any(m.id == me.id for m in message.new_chat_members):
            from utils.db import add_group, add_broadcast_group
            await add_group(message.chat.id)
            await add_broadcast_group(message.chat.id)
            logger.info("[GENERAL] Bot added to group %s", message.chat.id)
            if LOG_GROUP_ID:
                try:
                    text = f"➕ Bot added to group {message.chat.id}"
                    await client.send_message(LOG_GROUP_ID, text)
                except Exception as exc:
                    logger.warning("Failed to send log: %s", exc)

    @app.on_message(filters.left_chat_member & filters.group)
    @catch_errors
    async def track_bot_left(client: Client, message: Message):
        me = await client.get_me()
        if message.left_chat_member and message.left_chat_member.id == me.id:
            from utils.db import remove_group, remove_broadcast_group
            await remove_group(message.chat.id)
            await remove_broadcast_group(message.chat.id)
            logger.info("[GENERAL] Bot removed from group %s", message.chat.id)
            if LOG_GROUP_ID:
                try:
                    text = f"➖ Bot removed from group {message.chat.id}"
                    await client.send_message(LOG_GROUP_ID, text)
                except Exception as exc:
                    logger.warning("Failed to send log: %s", exc)
