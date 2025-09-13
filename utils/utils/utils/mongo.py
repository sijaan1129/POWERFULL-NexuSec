
import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any, List

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://aimbot:ep2FbCU8f9Orm7Gl@ac-msvg4pj-shard-00-00.aq8uup5.mongodb.net:27017,"
    "ac-msvg4pj-shard-00-01.aq8uup5.mongodb.net:27017,"
    "ac-msvg4pj-shard-00-02.aq8uup5.mongodb.net:27017/"
    "?replicaSet=atlas-ochm2q-shard-0&ssl=true&authSource=admin&retryWrites=true&w=majority"
    "&appName=Cluster0"
)

# MongoDB client setup
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["nexusec"]  # Use the 'nexusec' database

# Collections
guilds_collection = db["guilds"]
afk_collection = db["afk_users"]
tags_collection = db["tags"]  # Collection for tags

async def check_db_connection() -> bool:
    """Check if the database connection is alive."""
    try:
        await mongo_client.admin.command('ping')
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

async def get_guild_config(guild_id: int) -> Optional[Dict[str, Any]]:
    """
    Get guild configuration from database.
    Creates a new config if one doesn't exist.
    
    Args:
        guild_id: The ID of the guild to get config for
        
    Returns:
        The guild config dictionary or None if error occurs
    """
    guild_id = str(guild_id)
    try:
        config = await guilds_collection.find_one({"_id": guild_id})
        if not config:
            config = {"_id": guild_id}
            await guilds_collection.insert_one(config)
        return config
    except Exception as e:
        print(f"Error retrieving guild config for {guild_id}: {e}")
        return None

async def update_guild_config(guild_id: int, update_data: Dict[str, Any]) -> bool:
    """
    Update guild configuration in database.
    
    Args:
        guild_id: The ID of the guild to update
        update_data: The data to update (can include MongoDB operators)
        
    Returns:
        bool: True if update was successful, False otherwise
    """
    guild_id = str(guild_id)
    try:
        # If update_data doesn't contain MongoDB operators, wrap it in $set
        if not any(key.startswith('$') for key in update_data.keys()):
            update_data = {'$set': update_data}
            
        result = await guilds_collection.update_one(
            {"_id": guild_id},
            update_data,
            upsert=True
        )
        
        return result.acknowledged
    except Exception as e:
        print(f"Error updating guild config for {guild_id}: {e}")
        return False

# AFK system functions
async def get_afk_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Get AFK status for a user."""
    user_id = str(user_id)
    try:
        return await afk_collection.find_one({"_id": user_id})
    except Exception as e:
        print(f"Error retrieving AFK data for user {user_id}: {e}")
        return None

async def set_afk_user(user_id: int, afk_data: Dict[str, Any]) -> bool:
    """Set AFK status for a user."""
    user_id = str(user_id)
    try:
        result = await afk_collection.update_one(
            {"_id": user_id},
            {"$set": afk_data},
            upsert=True
        )
        return result.acknowledged
    except Exception as e:
        print(f"Error setting AFK data for user {user_id}: {e}")
        return False

async def remove_afk_user(user_id: int) -> bool:
    """Remove AFK status for a user."""
    user_id = str(user_id)
    try:
        result = await afk_collection.delete_one({"_id": user_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error removing AFK data for user {user_id}: {e}")
        return False

# Tag system functions
async def get_tag(guild_id: int, name: str) -> Optional[Dict[str, Any]]:
    """Get a tag by name for a specific guild."""
    guild_id = str(guild_id)
    name = name.lower()
    try:
        return await tags_collection.find_one({"guild_id": guild_id, "name": name})
    except Exception as e:
        print(f"Error retrieving tag {name} for guild {guild_id}: {e}")
        return None

async def create_or_update_tag(guild_id: int, name: str, response: str) -> bool:
    """Create or update a tag."""
    guild_id = str(guild_id)
    tag_data = {
        "guild_id": guild_id,
        "name": name.lower(),
        "response": response
    }
    try:
        existing_tag = await tags_collection.find_one({"guild_id": guild_id, "name": name.lower()})
        if existing_tag:
            result = await tags_collection.update_one(
                {"guild_id": guild_id, "name": name.lower()},
                {"$set": tag_data}
            )
        else:
            result = await tags_collection.insert_one(tag_data)
        return True
    except Exception as e:
        print(f"Error creating/updating tag {name} for guild {guild_id}: {e}")
        return False

async def delete_tag(guild_id: int, name: str) -> bool:
    """Delete a tag."""
    guild_id = str(guild_id)
    name = name.lower()
    try:
        result = await tags_collection.delete_one({"guild_id": guild_id, "name": name})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting tag {name} for guild {guild_id}: {e}")
        return False

async def get_all_tags(guild_id: int) -> Optional[List[Dict[str, Any]]]:
    """Get all tags for a guild."""
    guild_id = str(guild_id)
    try:
        return await tags_collection.find({"guild_id": guild_id}).to_list(None)
    except Exception as e:
        print(f"Error retrieving tags for guild {guild_id}: {e}")
        return None
