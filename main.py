import discord
from discord.ext import commands
import asyncio
import os
import threading
from flask import Flask
from db import set_antispam_settings, get_antispam_settings, set_antilink_settings, get_antilink_settings

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
from db import init_db
init_db()

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

# Command for configuring anti-spam
@bot.command(name="antispam")
async def antispam(ctx, state: str, punishment: str = "timeout", timeout: int = 10):
    guild_id = ctx.guild.id
    
    if state.lower() == "true":
        set_antispam_settings(guild_id, True, punishment, timeout)
        await ctx.send(f"Anti-spam has been enabled with {punishment} punishment for {timeout} minutes.")
    elif state.lower() == "false":
        set_antispam_settings(guild_id, False, punishment, timeout)
        await ctx.send("Anti-spam has been disabled.")
    else:
        await ctx.send("Invalid state. Please use 'true' or 'false'.")

# Command for configuring anti-link
@bot.command(name="antilink")
async def antilink(ctx, state: str, punishment: str = "timeout", timeout: int = 30):
    guild_id = ctx.guild.id
    
    if state.lower() == "true":
        set_antilink_settings(guild_id, True, punishment, timeout)
        await ctx.send(f"Anti-link has been enabled with {punishment} punishment for {timeout} minutes.")
    elif state.lower() == "false":
        set_antilink_settings(guild_id, False, punishment, timeout)
        await ctx.send("Anti-link has been disabled.")
    else:
        await ctx.send("Invalid state. Please use 'true' or 'false'.")

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))

asyncio.run(main())
