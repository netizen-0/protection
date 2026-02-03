import logging
from pyrogram.types import Message

logger = logging.getLogger(__name__)

async def safe_edit_message(
    message: Message,
    *,
    text: str | None = None,
    caption: str | None = None,
    **kwargs
) -> None:
    """Edit message text or caption only if the content has changed."""

    try:
        if text is not None:
            if (message.text or "").strip() == text.strip():
                return
            await message.edit_text(text, **kwargs)

        elif caption is not None:
            if (message.caption or "").strip() == caption.strip():
                return
            await message.edit_caption(caption, **kwargs)

        else:
            logger.debug("safe_edit_message called without text or caption.")

    except Exception as exc:
        logger.warning(
            "Failed to edit message %s in chat %s: %s",
            message.id,
            message.chat.id,
            exc,
        )
