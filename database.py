import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(DATABASE_URL)

    async def create_tables(self):
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id BIGINT PRIMARY KEY,
                antispam_enabled BOOLEAN DEFAULT FALSE,
                antilink_enabled BOOLEAN DEFAULT FALSE,
                antispam_punishment TEXT DEFAULT 'timeout',
                antilink_punishment TEXT DEFAULT 'timeout',
                antispam_timeout_minutes INT DEFAULT 10,
                antilink_timeout_minutes INT DEFAULT 30
            );
        """)

    async def get_settings(self, guild_id):
        row = await self.pool.fetchrow("SELECT * FROM guild_settings WHERE guild_id = $1", guild_id)
        if not row:
            await self.pool.execute("INSERT INTO guild_settings (guild_id) VALUES ($1)", guild_id)
            row = await self.pool.fetchrow("SELECT * FROM guild_settings WHERE guild_id = $1", guild_id)
        return row

    async def update_setting(self, guild_id, column, value):
        await self.get_settings(guild_id)  # ensure row exists
        await self.pool.execute(f"UPDATE guild_settings SET {column} = $1 WHERE guild_id = $2", value, guild_id)

db = Database()
