"""Permission utilities."""

import logging
from pyrogram import Client
from config import OWNER_ID
from pyrogram.types import Message, ChatMember
from pyrogram.enums import ChatType, ChatMemberStatus

logger = logging.getLogger(__name__)

async def is_admin(client: Client, message: Message, user_id: int | None = None) -> bool:
    """
    Check whether the specified user (or message sender) is an admin in the current chat.
    Returns False in private chats or on error.
    """
    if message.chat.type == ChatType.PRIVATE:
        return False

    chat_id = message.chat.id
    try:
        uid = user_id or (message.from_user.id if message.from_user else None)
        if uid is None:
            logger.debug("No user_id available for admin check in chat %s", chat_id)
            return False

        if uid == OWNER_ID:
            return True

        member: ChatMember = await client.get_chat_member(chat_id, uid)
        return member.status in {
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        }

    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Admin check failed for user %s in chat %s: %s",
            user_id or (message.from_user.id if message.from_user else "unknown"),
            chat_id,
            exc,
        )
        return False
