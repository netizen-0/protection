import os
import logging
from html import escape
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatType
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from utils.perms import is_admin
from utils.db import (
    get_setting,
    get_bio_filter,
    add_group,
    add_user,
    add_broadcast_group,
    add_broadcast_user,
)
from utils.errors import catch_errors
from utils.messages import safe_edit_message
from config import OWNER_ID, LOG_GROUP_ID

logger = logging.getLogger(__name__)

PANEL_IMAGE_URL = os.getenv("PANEL_IMAGE_URL", "https://files.catbox.moe/uvqeln.jpg")


def mention_html(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{escape(name)}</a>'


# 🔘 Start Panel (DM)
async def build_start_panel(is_admin: bool = False, *, is_owner: bool = False, include_back: bool = False) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton("📘 Commands", callback_data="cb_help_start")]]
    # Show settings button to everyone so non-admins can view the panel too
    buttons.insert(0, [InlineKeyboardButton("⚙️ Settings", callback_data="open_settings")])
    if is_owner:
        buttons.append([InlineKeyboardButton("📢 Broadcast", callback_data="help_broadcast")])
    if include_back:
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data="cb_back_panel")])
    return InlineKeyboardMarkup(buttons)


# ⚙️ Settings Panel (Group)
async def build_settings_panel(chat_id: int) -> InlineKeyboardMarkup:
    bio = await get_bio_filter(chat_id)
    link = str(await get_setting(chat_id, "linkfilter", "0")) == "1"
    edit = str(await get_setting(chat_id, "editmode", "0")) == "1"
    delay = int(await get_setting(chat_id, "autodelete_interval", "0") or 0)

    buttons = [
        [InlineKeyboardButton(f"🌐 BioLink {'✅' if bio else '❌'}", callback_data="toggle_biolink")],
        [InlineKeyboardButton(f"🔗 LinkFilter {'✅' if link else '❌'}", callback_data="toggle_linkfilter")],
        [InlineKeyboardButton(f"✏️ EditFilter {'✅' if edit else '❌'}", callback_data="toggle_editfilter")],
        [InlineKeyboardButton(
            f"🧹 AutoDelete {delay}s" if delay else "🧹 AutoDelete Off",
            callback_data="toggle_autodelete"
        )],
        [InlineKeyboardButton("🔙 Back", callback_data="cb_start")],
    ]
    return InlineKeyboardMarkup(buttons)


# 📩 Welcome / Panel Sender
async def send_start(
    client: Client,
    message: Message,
    *,
    include_back: bool = False,
    log_panel: bool = True,
) -> None:
    bot_user = await client.get_me()
    user = message.from_user
    chat = message.chat
    is_owner = user.id == OWNER_ID

    is_admin_user = await is_admin(client, message)

    if chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        # Always track the group so broadcast works even if a non-admin
        await add_group(chat.id)
        await add_broadcast_group(chat.id)
    else:
        await add_user(user.id)
        await add_broadcast_user(user.id)

    markup = await build_start_panel(
        is_admin=is_admin_user,
        is_owner=is_owner,
        include_back=include_back,
    )
    caption = (
        f"🎉 <b>Welcome to {bot_user.first_name}</b>\n\n"
        f"Hello {mention_html(user.id, user.first_name)}!\n\n"
        "I'm here to help manage your group efficiently.\n"
        "Use the buttons below to access features and controls.\n\n"
        "✅ Group-ready\n🛠 Admin settings\n🧠 Smart moderation tools"
    )

    if chat.type in {ChatType.GROUP, ChatType.SUPERGROUP} and not is_admin_user:
        caption += "\n\n<em>Settings are read-only for non-admins.</em>"

    await message.reply_photo(
        photo=PANEL_IMAGE_URL,
        caption=caption,
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )

    if LOG_GROUP_ID and log_panel and chat.type == ChatType.PRIVATE:
        try:
            text = (
                f"📥 /start used in DM by {mention_html(user.id, user.first_name)}"
            )
            await client.send_message(LOG_GROUP_ID, text, parse_mode=ParseMode.HTML)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to send log: %s", exc)


# 🔁 Shortcut for /menu
async def send_control_panel(client: Client, message: Message) -> None:
    await send_start(client, message, log_panel=False)


# ❓ Help Menu Keyboard
def get_help_keyboard(back_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛡️ BioMode", callback_data="help_biomode")],
        [InlineKeyboardButton("🧹 AutoDelete", callback_data="help_autodelete")],
        [InlineKeyboardButton("🔗 LinkFilter", callback_data="help_linkfilter")],
        [InlineKeyboardButton("✏️ EditMode", callback_data="help_editmode")],
        [InlineKeyboardButton("👮 Admin", callback_data="help_admin")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="help_broadcast")],
        [
            InlineKeyboardButton("👨‍💻 Developer", callback_data="help_developer"),
            InlineKeyboardButton("🆘 Support", callback_data="help_support")
        ],
        [InlineKeyboardButton("🔙 Back", callback_data=back_cb)]
    ])


# 🔁 Render group settings panel for a message or callback
async def render_settings_panel(client: Client, message: Message) -> None:
    chat_id = message.chat.id
    markup = await build_settings_panel(chat_id)
    await safe_edit_message(
        message,
        caption="⚙️ <b>Group Settings</b>",
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )


# 📦 Register handlers
def register(app: Client) -> None:
    logger.info("✅ Registered: panels.py")

    # /menu shortcut
    @app.on_message(filters.command("menu") & filters.group)
    async def show_menu(client: Client, message: Message):
        await send_control_panel(client, message)

