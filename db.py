import sqlite3
import os

db_path = "data/automod.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS automod_settings (
        guild_id INTEGER PRIMARY KEY,
        antispam_enabled BOOLEAN DEFAULT FALSE,
        antispam_punishment TEXT DEFAULT 'timeout',
        antispam_timeout INTEGER DEFAULT 10,
        antilink_enabled BOOLEAN DEFAULT FALSE,
        antilink_punishment TEXT DEFAULT 'timeout',
        antilink_timeout INTEGER DEFAULT 30
    );
    """)
    conn.commit()
    conn.close()

# Anti-Spam Settings
def set_antispam_settings(guild_id, enabled, punishment, timeout):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    INSERT INTO automod_settings (guild_id, antispam_enabled, antispam_punishment, antispam_timeout)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(guild_id) DO UPDATE SET
        antispam_enabled=?,
        antispam_punishment=?,
        antispam_timeout=?;
    """, (guild_id, enabled, punishment, timeout, enabled, punishment, timeout))
    conn.commit()
    conn.close()

def get_antispam_settings(guild_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    SELECT antispam_enabled, antispam_punishment, antispam_timeout
    FROM automod_settings WHERE guild_id = ?;
    """, (guild_id,))
    result = c.fetchone()
    conn.close()
    return result

# Anti-Link Settings
def set_antilink_settings(guild_id, enabled, punishment, timeout):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    INSERT INTO automod_settings (guild_id, antilink_enabled, antilink_punishment, antilink_timeout)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(guild_id) DO UPDATE SET
        antilink_enabled=?,
        antilink_punishment=?,
        antilink_timeout=?;
    """, (guild_id, enabled, punishment, timeout, enabled, punishment, timeout))
    conn.commit()
    conn.close()

def get_antilink_settings(guild_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    SELECT antilink_enabled, antilink_punishment, antilink_timeout
    FROM automod_settings WHERE guild_id = ?;
    """, (guild_id,))
    result = c.fetchone()
    conn.close()
    return result
