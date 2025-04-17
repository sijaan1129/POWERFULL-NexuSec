import sqlite3
import os

# Define the database path
db_path = "data/automod.db"  # Database file stored in the 'data' folder

# Initialize the SQLite database
def init_db():
    os.makedirs("data", exist_ok=True)  # Make sure the 'data' folder exists
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Create the necessary tables for automod settings
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

# Call this function at the beginning of your program to initialize the database
init_db()

# Functions to Get and Update Anti-Spam / Anti-Link Settings
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

def set_antispam_settings(guild_id, enabled, punishment, timeout):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("""
    INSERT INTO automod_settings (guild_id, antispam_enabled, antispam_punishment, antispam_timeout)
    VALUES (?, ?, ?, ?)
    ON CONFLICT (guild_id) DO UPDATE SET
        antispam_enabled = ?, antispam_punishment = ?, antispam_timeout = ?;
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
    settings = c.fetchone()
    
    conn.close()
    return settings

def set_antilink_settings(guild_id, enabled, punishment, timeout):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("""
    INSERT INTO automod_settings (guild_id, antilink_enabled, antilink_punishment, antilink_timeout)
    VALUES (?, ?, ?, ?)
    ON CONFLICT (guild_id) DO UPDATE SET
        antilink_enabled = ?, antilink_punishment = ?, antilink_timeout = ?;
    """, (guild_id, enabled, punishment, timeout, enabled, punishment, timeout))
    
    conn.commit()
    conn.close()
