import discord
from discord.ext import commands
import os
import asyncio
import threading
import logging
from flask import Flask
from datetime import datetime
from db import init_db

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Web server for Render ---
app = Flask("")

@app.route("/")
def home():
    return f"NexuSec is online – {datetime.utcnow()} UTC"

def run_web():
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)

threading.Thread(target=run_web, daemon=True).start()

# ✅ Initialize database
init_db()

# Bot Setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "cogs.moderation",
    "cogs.automod",
    "cogs.utility",
    "cogs.announcements",
    "cogs.fun",
    "cogs.custom_commands",
    "cogs.whitelist",
    "cogs.help"  # 👈 Added Help cog
]

# --- Slash Commands ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="Use /help | NexuSec"))
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded cog: {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))

try:
    asyncio.run(main())
except Exception as e:
    print(f"❌ Bot crashed: {e}")
