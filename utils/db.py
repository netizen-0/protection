"""Database helpers using Motor (async MongoDB)."""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ReturnDocument

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


# ------------------ CORE ------------------ #
def get_db() -> AsyncIOMotorDatabase:
    """Return the active MongoDB database."""
    if _db is None:
        raise RuntimeError("Database has not been initialised")
    return _db


# ------------------ SETTINGS: linkfilter, editmode, etc ------------------ #
async def get_setting(chat_id: int, key: str, default: str | None = None) -> str | None:
    doc = await _db.kv_settings.find_one({"chat_id": chat_id, "key": key})
    return doc.get("value") if doc else default


async def set_setting(chat_id: int, key: str, value: str) -> None:
    await _db.kv_settings.update_one(
        {"chat_id": chat_id, "key": key},
        {"$set": {"value": value}},
        upsert=True,
    )


# ------------------ BIO FILTER ------------------ #
async def get_bio_filter(chat_id: int) -> bool:
    """Return True if the bio link filter is enabled for the chat."""
    value = await get_setting(chat_id, "biofilter", "0")
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "on", "yes"}


async def set_bio_filter(chat_id: int, enabled: bool) -> None:
    await set_setting(chat_id, "biofilter", "1" if enabled else "0")


# ------------------ APPROVAL SYSTEM ------------------ #
async def approve_user(chat_id: int, user_id: int) -> None:
    await _db.approved_users.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"approved": True}},
        upsert=True,
    )


async def unapprove_user(chat_id: int, user_id: int) -> None:
    await _db.approved_users.delete_one({"chat_id": chat_id, "user_id": user_id})


async def is_approved(chat_id: int, user_id: int) -> bool:
    return await _db.approved_users.find_one({"chat_id": chat_id, "user_id": user_id}) is not None


async def get_approved(chat_id: int) -> list[int]:
    cursor = _db.approved_users.find({"chat_id": chat_id})
    return [doc["user_id"] async for doc in cursor]


async def set_approval_mode(chat_id: int, enabled: bool) -> None:
    await set_setting(chat_id, "approval_mode", "1" if enabled else "0")


async def get_approval_mode(chat_id: int) -> bool:
    value = await get_setting(chat_id, "approval_mode", "0")
    return value == "1"


async def toggle_approval_mode(chat_id: int) -> bool:
    current = await get_approval_mode(chat_id)
    await set_approval_mode(chat_id, not current)
    return not current


# ------------------ WARNINGS ------------------ #
async def increment_warning(chat_id: int, user_id: int) -> int:
    doc = await _db.warnings.find_one_and_update(
        {"chat_id": chat_id, "user_id": user_id},
        {"$inc": {"count": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return doc["count"]


async def reset_warning(chat_id: int, user_id: int) -> None:
    await _db.warnings.delete_one({"chat_id": chat_id, "user_id": user_id})


# ------------------ BROADCAST STORAGE ------------------ #
async def add_broadcast_user(user_id: int) -> None:
    await _db.broadcast_users.update_one({"_id": user_id}, {"$set": {}}, upsert=True)


async def add_broadcast_group(chat_id: int) -> None:
    await _db.broadcast_groups.update_one({"_id": chat_id}, {"$set": {}}, upsert=True)


async def remove_broadcast_group(chat_id: int) -> None:
    await _db.broadcast_groups.delete_one({"_id": chat_id})


async def get_broadcast_users() -> list[int]:
    cursor = _db.broadcast_users.find()
    return [doc["_id"] async for doc in cursor]


async def get_broadcast_groups() -> list[int]:
    cursor = _db.broadcast_groups.find()
    return [doc["_id"] async for doc in cursor]


# ------------------ USER / GROUP LOGGING ------------------ #
async def add_user(user_id: int) -> None:
    await _db.users.update_one({"_id": user_id}, {"$set": {}}, upsert=True)


async def add_group(chat_id: int) -> None:
    await _db.groups.update_one({"_id": chat_id}, {"$set": {}}, upsert=True)


async def remove_group(chat_id: int) -> None:
    await _db.groups.delete_one({"_id": chat_id})


async def get_users() -> list[int]:
    cursor = _db.users.find()
    return [doc["_id"] async for doc in cursor]


async def get_groups() -> list[int]:
    cursor = _db.groups.find()
    return [doc["_id"] async for doc in cursor]


# ------------------ LIFECYCLE MANAGEMENT ------------------ #
async def init_db(uri: str, db_name: str) -> None:
    """Initialize MongoDB with required collections and indexes."""
    global _client, _db
    # Short timeout so startup fails fast if DB is unreachable
    _client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
    _db = _client[db_name]

    # Force a connection attempt to provide immediate feedback
    try:
        await _client.admin.command("ping")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Could not connect to MongoDB: {exc}") from exc

    await _db.kv_settings.create_index([("chat_id", 1), ("key", 1)], unique=True)
    await _db.approved_users.create_index([("chat_id", 1), ("user_id", 1)], unique=True)
    await _db.warnings.create_index([("chat_id", 1), ("user_id", 1)], unique=True)


async def close_db() -> None:
    """Close MongoDB client connection."""
    if _client:
        _client.close()
