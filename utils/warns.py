from utils.mongo import db
import time

async def add_warn(guild_id, user_id, moderator_id, reason):
    warn = {
        "moderator_id": moderator_id,
        "reason": reason,
        "date": time.time()
    }
    await db["warns"].update_one(
        {"guild_id": guild_id, "user_id": user_id},
        {"$push": {"warns": warn}},
        upsert=True
    )

async def get_warns(guild_id, user_id):
    data = await db["warns"].find_one({"guild_id": guild_id, "user_id": user_id})
    return data["warns"] if data and "warns" in data else []

async def clear_warns(guild_id, user_id):
    await db["warns"].delete_one({"guild_id": guild_id, "user_id": user_id})
