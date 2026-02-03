import asyncio
import logging
import re
import time
from contextlib import suppress

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, ChatPermissions

from utils.errors import catch_errors
from utils.db import (
    get_setting,
    get_bio_filter,
    increment_warning,
    reset_warning,
    is_approved,
    get_approval_mode,
)
from utils.perms import is_admin

logger = logging.getLogger(__name__)

LINK_RE = re.compile(
    r"(?:https?://\S+|tg://\S+|t\.me/\S+|telegram\.me/\S+|(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})",
    re.IGNORECASE,
)

# Cache user bios to avoid excessive get_chat calls
_user_bio_cache: dict[int, tuple[str, float]] = {}
BIO_CACHE_TTL = 15 * 60  # 15 minutes

_bio_violation_cache: dict[tuple[int, int], float] = {}
BIO_VIOLATION_TTL = 20  # seconds - set low for easier debug

def contains_link(text: str) -> bool:
    return bool(LINK_RE.search(text or ""))

async def suppress_delete(message: Message):
    with suppress(Exception):
        await message.delete()

def build_warning(count: int, user, reason: str, is_final: bool = False):
    name = f"@{user.username}" if user.username else f"{user.first_name} ({user.id})"
    msg = (
        f"🔇 <b>Final Warning for {name}</b>\n\n{reason}\nYou have been <b>muted</b>."
        if is_final
        else f"⚠️ <b>Warning {count}/3 for {name}</b>\n\n{reason}\nFix this before you're muted."
    )
    return msg, None

async def handle_violation(client: Client, message: Message, user, chat_id: int, reason: str) -> None:
    logger.debug("[FILTER] Violation by %s in %s: %s", user.id, chat_id, reason)
    await suppress_delete(message)
    count = await increment_warning(chat_id, user.id)
    if count >= 3:
        try:
            await client.restrict_chat_member(
                chat_id,
                user.id,
                ChatPermissions(can_send_messages=False)
            )
        except Exception as e:
            logger.warning("Mute failed: %s", e)
        await reset_warning(chat_id, user.id)
    msg, _ = build_warning(count, user, reason, is_final=(count >= 3))
    try:
        await message.reply_text(msg, parse_mode=ParseMode.HTML, quote=True)
    except Exception as e:
        logger.warning("Failed to send violation reply: %s", e)

async def get_user_bio(client: Client, user) -> str:
    now = time.monotonic()
    cached = _user_bio_cache.get(user.id)
    if cached and now - cached[1] < BIO_CACHE_TTL:
        return cached[0]

    try:
        chat = await client.get_chat(user.id)
        bio = getattr(chat, "bio", "") or ""
        _user_bio_cache[user.id] = (bio, now)
        return bio
    except Exception as e:
        logger.warning("Failed to fetch bio for %s: %s", user.id, e)
        return cached[0] if cached else ""

async def bio_link_violation(client: Client, message: Message, user, chat_id: int) -> bool:
    if not await get_bio_filter(chat_id):
        logger.debug("Bio link filter OFF for chat %s", chat_id)
        return False

    now = time.monotonic()
    last = _bio_violation_cache.get((chat_id, user.id), 0)
    if now - last < BIO_VIOLATION_TTL:
        logger.debug("Bio violation check throttled for %s/%s", chat_id, user.id)
        return False

    bio = await get_user_bio(client, user)
    if not bio:
        logger.debug("No bio for user %s in chat %s", user.id, chat_id)
        return False
    logger.debug("User %s bio in %s: %r", user.id, chat_id, bio)

    if contains_link(bio):
        logger.info("[FILTER] Bio link detected for %s in %s", user.id, chat_id)
        await handle_violation(
            client,
            message,
            user,
            chat_id,
            "Your bio contains a link, which is not allowed.",
        )
        _bio_violation_cache[(chat_id, user.id)] = now
        return True
    else:
        logger.debug("User %s bio clean in %s", user.id, chat_id)
        return False

def register(app: Client) -> None:
    logger.info("✅ Registered: filters.py")

    edited_messages: set[tuple[int, int]] = set()

    async def delete_later(chat_id: int, msg_id: int, delay: int) -> None:
        await asyncio.sleep(delay)
        try:
            await app.delete_messages(chat_id, msg_id)
        except Exception as e:
            logger.warning("Failed to delete message %s/%s: %s", chat_id, msg_id, e)
        finally:
            edited_messages.discard((chat_id, msg_id))

    async def schedule_auto_delete(chat_id: int, msg_id: int, fallback: int | None = None):
        try:
            delay = int(await get_setting(chat_id, "autodelete_interval", "0") or 0)
        except (TypeError, ValueError):
            delay = 0
        if delay <= 0:
            delay = fallback or 0
        if delay > 0:
            asyncio.create_task(delete_later(chat_id, msg_id, delay))

    @app.on_message(filters.group & ~filters.service, group=1)
    @catch_errors
    async def moderate_message(client: Client, message: Message) -> None:
        if not message.from_user or message.from_user.is_bot:
            return
        if (await client.get_me()).id == message.from_user.id:
            return

        chat_id = message.chat.id
        user = message.from_user

        is_admin_user = await is_admin(client, message, user.id)
        is_approved_user = await is_approved(chat_id, user.id)
        needs_filtering = not is_admin_user and not is_approved_user

        if needs_filtering and await bio_link_violation(client, message, user, chat_id):
            return

        if needs_filtering and await get_approval_mode(chat_id):
            await suppress_delete(message)
            await message.reply_text("❌ You are not approved to speak here.", quote=True)
            return

        content = message.text or message.caption or ""
        if (
            content
            and needs_filtering
            and str(await get_setting(chat_id, "linkfilter", "0")) == "1"
            and contains_link(content)
        ):
            logger.debug("[FILTER] Link removed in %s from %s", chat_id, user.id)
            await handle_violation(
                client,
                message,
                user,
                chat_id,
                "You are not allowed to share links in this group.",
            )
            return

        if needs_filtering:
            await schedule_auto_delete(chat_id, message.id)

    @app.on_edited_message(filters.group & ~filters.service, group=1)
    @catch_errors
    async def on_edit(client: Client, message: Message):
        if not message.from_user or message.from_user.is_bot:
            return

        chat_id = message.chat.id
        user = message.from_user
        if await is_admin(client, message, user.id) or await is_approved(chat_id, user.id):
            return

        if str(await get_setting(chat_id, "editmode", "0")) != "1":
            return

        key = (chat_id, message.id)
        if key not in edited_messages:
            edited_messages.add(key)
            await schedule_auto_delete(chat_id, message.id, fallback=0)

    @app.on_message(filters.new_chat_members & filters.group, group=1)
    @catch_errors
    async def check_new_member_bio(client: Client, message: Message):
        chat_id = message.chat.id
        if not await get_bio_filter(chat_id):
            return

        for user in message.new_chat_members:
            if user.is_bot:
                continue
            if await is_admin(client, message, user.id) or await is_approved(chat_id, user.id):
                continue

            bio = await get_user_bio(client, user)
            if not bio:
                continue

            await bio_link_violation(client, message, user, chat_id)
