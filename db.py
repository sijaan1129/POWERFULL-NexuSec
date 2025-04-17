import sqlite3
import os

# Path to the SQLite database
db_path = "data/automod.db"

# Initialize the database
def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create the table if it doesn't exist
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

# Function to set/update anti-spam settings
def set_antispam_settings(guild_id, enabled, punishment, timeout):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Update or insert the anti-spam settings for the guild
    c.execute("""
    INSERT INTO automod_settings (guild_id, antispam_enabled, antispam_punishment, antispam_timeout)
    VALUES (?, ?, ?, ?)
    ON CONFLICT (guild_id) DO UPDATE SET
        antispam_enabled = ?, antispam_punishment = ?, antispam_timeout = ?;
    """, (guild_id, enabled, punishment, timeout, enabled, punishment, timeout))

    conn.commit()
    conn.close()

# Function to get anti-spam settings
def get_antispam_settings(guild_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
    SELECT antispam_enabled, antispam_punishment, antispam_timeout
    FROM automod_settings WHERE guild_id = ?;
    """, (guild_id,))
    settings = c.fetchone()

    conn.close()
    return settings

# Function to set/update anti-link settings
def set_antilink_settings(guild_id, enabled, punishment, timeout):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Update or insert the anti-link settings for the guild
    c.execute("""
    INSERT INTO automod_settings (guild_id, antilink_enabled, antilink_punishment, antilink_timeout)
    VALUES (?, ?, ?, ?)
    ON CONFLICT (guild_id) DO UPDATE SET
        antilink_enabled = ?, antilink_punishment = ?, antilink_timeout = ?;
    """, (guild_id, enabled, punishment, timeout, enabled, punishment, timeout))

    conn.commit()
    conn.close()

# Function to get anti-link settings
def get_antilink_settings(guild_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
    SELECT antilink_enabled, antilink_punishment, antilink_timeout
    FROM automod_settings WHERE guild_id = ?;
    """, (guild_id,))
    settings = c.fetchone()

    conn.close()
    return settings

# Initialize the database
init_db()
