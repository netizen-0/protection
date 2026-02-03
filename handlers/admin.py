import logging
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ParseMode, ChatType, ChatMemberStatus

from utils.errors import catch_errors
from utils.db import (
    approve_user, unapprove_user, get_approved,
    increment_warning, reset_warning, set_setting,
    set_bio_filter, toggle_approval_mode, set_approval_mode,
)

logger = logging.getLogger(__name__)


def register(app: Client) -> None:
    logger.info("✅ Registered: admin.py")

    # Admin-only group check
    async def _require_admin_group(client: Client, message: Message) -> bool:
        if message.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await message.reply_text("❗ This command only works in groups.")
            return False

        try:
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
        except Exception as e:
            logger.warning("Failed to fetch member: %s", e)
            return False

        if member.status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
            await message.reply_text("🔒 You must be an admin to use this.")
            return False
        return True

    # Central admin action executor
    async def _admin_action(message: Message, action: str) -> None:
        if not await _require_admin_group(app, message):
            return

        user = message.reply_to_message.from_user if message.reply_to_message else None
        if not user:
            await message.reply_text("📌 Reply to a user's message.")
            return

        try:
            if action == "ban":
                await app.ban_chat_member(message.chat.id, user.id)
            elif action == "kick":
                await app.ban_chat_member(message.chat.id, user.id)
                await app.unban_chat_member(message.chat.id, user.id)
            elif action == "mute":
                await app.restrict_chat_member(message.chat.id, user.id, ChatPermissions())
            elif action == "unban":
                await app.unban_chat_member(message.chat.id, user.id)
            elif action == "unmute":
                await app.restrict_chat_member(
                    message.chat.id,
                    user.id,
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                        can_invite_users=True,
                    ),
                )
            await message.reply_text(f"{action.title()} successful ✅")
        except Exception as exc:
            logger.error("%s failed: %s", action, exc)
            await message.reply_text(f"❌ Failed to {action}: {exc}")

    # Basic moderation commands
    @app.on_message(filters.command("ban") & filters.group)
    @catch_errors
    async def ban_cmd(_, message: Message):
        await _admin_action(message, "ban")

    @app.on_message(filters.command("kick") & filters.group)
    @catch_errors
    async def kick_cmd(_, message: Message):
        await _admin_action(message, "kick")

    @app.on_message(filters.command("mute") & filters.group)
    @catch_errors
    async def mute_cmd(_, message: Message):
        await _admin_action(message, "mute")

    @app.on_message(filters.command("unban") & filters.group)
    @catch_errors
    async def unban_cmd(_, message: Message):
        await _admin_action(message, "unban")

    @app.on_message(filters.command("unmute") & filters.group)
    @catch_errors
    async def unmute_cmd(_, message: Message):
        await _admin_action(message, "unmute")

    @app.on_message(filters.command("warn") & filters.group)
    @catch_errors
    async def warn_cmd(_, message: Message):
        if not await _require_admin_group(app, message):
            return
        user = message.reply_to_message.from_user if message.reply_to_message else None
        if not user:
            await message.reply_text("📌 Reply to a user's message.")
            return

        count = await increment_warning(message.chat.id, user.id)
        if count >= 3:
            await app.restrict_chat_member(message.chat.id, user.id, ChatPermissions())
            await reset_warning(message.chat.id, user.id)
            await message.reply_text(f"🔇 {user.mention} muted (3 warnings)")
        else:
            await message.reply_text(f"⚠ Warned {user.mention} ({count}/3)")

    @app.on_message(filters.command(["resetwarn", "rmwarn"]) & filters.group)
    @catch_errors
    async def resetwarn_cmd(_, message: Message):
        if not await _require_admin_group(app, message):
            return
        user = message.reply_to_message.from_user if message.reply_to_message else None
        if not user:
            await message.reply_text("📌 Reply to a user's message.")
            return
        await reset_warning(message.chat.id, user.id)
        await message.reply_text(f"🧹 Warnings reset for {user.mention}")

    # Filter toggles
    async def _toggle_setting_cmd(message: Message, key: str, label: str):
        if len(message.command) < 2:
            await message.reply_text(f"Usage: /{key} on|off")
            return
        state = message.command[1].lower() in {"on", "enable", "1", "true"}
        await set_setting(message.chat.id, key, "1" if state else "0")
        status = "ENABLED ✅" if state else "DISABLED ❌"
        await message.reply_text(f"{label} {status}")

    @app.on_message(filters.command("biolink") & filters.group)
    @catch_errors
    async def biolink_cmd(_, message: Message):
        if len(message.command) < 2:
            await message.reply_text("Usage: /biolink on|off")
            return
        state = message.command[1].lower() in {"on", "enable", "1", "true"}
        await set_bio_filter(message.chat.id, state)
        await message.reply_text(f"🌐 Bio link filter {'ENABLED ✅' if state else 'DISABLED ❌'}")

    @app.on_message(filters.command("linkfilter") & filters.group)
    @catch_errors
    async def linkfilter_cmd(_, message: Message):
        await _toggle_setting_cmd(message, "linkfilter", "🔗 Link filter")

    @app.on_message(filters.command(["editfilter", "editdelete"]) & filters.group)
    @catch_errors
    async def editfilter_cmd(_, message: Message):
        await _toggle_setting_cmd(message, "editmode", "✏️ Edit filter")

    @app.on_message(filters.command("setautodelete") & filters.group)
    @catch_errors
    async def setautodelete_cmd(_, message: Message):
        if not await _require_admin_group(app, message):
            return
        try:
            seconds = int(message.command[1]) if len(message.command) > 1 else 0
            await set_setting(message.chat.id, "autodelete_interval", str(seconds))
            msg = f"🧹 Auto-delete set to {seconds}s" if seconds else "🧹 Auto-delete disabled"
            await message.reply_text(msg)
        except ValueError:
            await message.reply_text("❗ Provide a valid number of seconds.")

    # Approval system
    @app.on_message(filters.command("approve") & filters.group)
    @catch_errors
    async def approve_cmd(_, message: Message):
        if not await _require_admin_group(app, message):
            return
        user = message.reply_to_message.from_user if message.reply_to_message else None
        if not user:
            await message.reply_text("📌 Reply to a user's message.")
            return
        await approve_user(message.chat.id, user.id)
        await message.reply_text(f"✅ Approved {user.mention}")

    @app.on_message(filters.command("unapprove") & filters.group)
    @catch_errors
    async def unapprove_cmd(_, message: Message):
        if not await _require_admin_group(app, message):
            return
        user = message.reply_to_message.from_user if message.reply_to_message else None
        if not user:
            await message.reply_text("📌 Reply to a user's message.")
            return
        await unapprove_user(message.chat.id, user.id)
        await message.reply_text(f"❌ Unapproved {user.mention}")

    @app.on_message(filters.command("approved") & filters.group)
    @catch_errors
    async def approved_cmd(_, message: Message):
        if not await _require_admin_group(app, message):
            return
        users = await get_approved(message.chat.id)
        if not users:
            await message.reply_text("No approved users.")
        else:
            text = "<b>Approved Users:</b>\n" + "\n".join(f"• <code>{uid}</code>" for uid in users)
            await message.reply_text(text, parse_mode=ParseMode.HTML)

    @app.on_message(filters.command("approval") & filters.group)
    @catch_errors
    async def approval_mode_cmd(_, message: Message):
        if not await _require_admin_group(app, message):
            return
        if len(message.command) == 1:
            enabled = await toggle_approval_mode(message.chat.id)
        else:
            arg = message.command[1].lower()
            if arg in {"on", "enable", "true"}:
                await set_approval_mode(message.chat.id, True)
                enabled = True
            elif arg in {"off", "disable", "false"}:
                await set_approval_mode(message.chat.id, False)
                enabled = False
            else:
                await message.reply_text("Usage: /approval [on|off]")
                return
        await message.reply_text(f"👥 Approval mode is now {'ENABLED ✅' if enabled else 'DISABLED ❌'}")
