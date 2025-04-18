import sqlite3
import os

db_path = "data/automod.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Anti-spam/antilink settings
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

    # Bad word list
    c.execute("""
    CREATE TABLE IF NOT EXISTS badwords (
        guild_id INTEGER,
        word TEXT
    );
    """)

    conn.commit()
    conn.close()

# Bad word database functions
def add_badword(guild_id: int, word: str):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("INSERT INTO badwords (guild_id, word) VALUES (?, ?)", (guild_id, word.lower()))
    conn.commit()
    conn.close()

def remove_badword(guild_id: int, word: str):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM badwords WHERE guild_id = ? AND word = ?", (guild_id, word.lower()))
    conn.commit()
    conn.close()

def get_badwords(guild_id: int):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT word FROM badwords WHERE guild_id = ?", (guild_id,))
    words = [row[0] for row in c.fetchall()]
    conn.close()
    return words

# Anti-link / spam
def set_antilink_settings(guild_id, enabled, punishment, timeout):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
    INSERT INTO automod_settings (guild_id, antilink_enabled, antilink_punishment, antilink_timeout)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(guild_id) DO UPDATE SET
        antilink_enabled = ?, antilink_punishment = ?, antilink_timeout = ?;
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
    return result or (False, "timeout", 5)
