import discord
from discord.ext import commands
import asyncio
import os
import threading
from flask import Flask

# --- Web server for Render (FREE plan workaround) ---
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_web).start()
# -----------------------------------------------------

# Discord bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "cogs.moderation",
    "cogs.automod",
    "cogs.utility",
    "cogs.announcements",
    "cogs.fun",
    "cogs.custom_commands"
]

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    
    # Set the custom playing status
    await bot.change_presence(activity=discord.Game(name="Playing /help NexuSecbot.gg"))
    
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"❌ Slash command sync error: {e}")

    await bot.load_extension("anti_abuse")

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
            await bot.load_extension("anti_abuse")  # Add this line to load the anti-abuse cog
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())
