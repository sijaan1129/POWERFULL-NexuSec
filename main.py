import discord
from discord.ext import commands
import asyncio
import os
import threading
from flask import Flask
from db import init_db

# --- Web server for Render (FREE plan workaround) ---
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_web).start()
# -----------------------------------------------------

# ✅ Initialize database
init_db()

# Discord bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Cogs to load
COGS = [
    "cogs.moderation",
    "cogs.automod",
    "cogs.utility",
    "cogs.announcements",
    "cogs.fun",
    "cogs.custom_commands",
    "anti_abuse"  # if this is a file like anti_abuse.py
]

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="Playing /help | NexuSecBot.gg"))

    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"❌ Error syncing slash commands: {e}")

# Load all cogs
async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

# Start the bot
async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())
