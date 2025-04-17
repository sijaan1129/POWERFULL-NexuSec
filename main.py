import discord
from discord.ext import commands
import asyncio
import os
import threading
from flask import Flask
from db import set_antispam_settings, get_antispam_settings, set_antilink_settings, get_antilink_settings
from discord.ui import Select, View

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

# --- Anti-Spam Dropdown View ---
class AntispamView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Select(
            placeholder="Select State",
            options=[
                discord.SelectOption(label="Enable", value="enable"),
                discord.SelectOption(label="Disable", value="disable"),
            ],
            custom_id="antispam_state"
        ))

        self.add_item(Select(
            placeholder="Select Punishment",
            options=[
                discord.SelectOption(label="Timeout", value="timeout"),
                discord.SelectOption(label="Ban", value="ban"),
                discord.SelectOption(label="Kick", value="kick"),
            ],
            custom_id="antispam_punishment"
        ))

        self.add_item(Select(
            placeholder="Select Duration (Minutes)",
            options=[
                discord.SelectOption(label="5 min", value="5"),
                discord.SelectOption(label="10 min", value="10"),
                discord.SelectOption(label="15 min", value="15"),
                discord.SelectOption(label="30 min", value="30"),
            ],
            custom_id="antispam_duration"
        ))

    async def on_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        state = interaction.data["values"][0]
        punishment = interaction.data["values"][1]
        duration = int(interaction.data["values"][2])

        guild_id = interaction.guild.id

        if state == "enable":
            set_antispam_settings(guild_id, True, punishment, duration)
        else:
            set_antispam_settings(guild_id, False, punishment, duration)

        await interaction.response.send_message(f"Anti-spam: {state}, Punishment: {punishment}, Duration: {duration} minutes.", ephemeral=True)


# --- Anti-Link Dropdown View ---
class AntilinkView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Select(
            placeholder="Select State",
            options=[
                discord.SelectOption(label="Enable", value="enable"),
                discord.SelectOption(label="Disable", value="disable"),
            ],
            custom_id="antilink_state"
        ))

        self.add_item(Select(
            placeholder="Select Punishment",
            options=[
                discord.SelectOption(label="Timeout", value="timeout"),
                discord.SelectOption(label="Ban", value="ban"),
                discord.SelectOption(label="Kick", value="kick"),
            ],
            custom_id="antilink_punishment"
        ))

        self.add_item(Select(
            placeholder="Select Duration (Minutes)",
            options=[
                discord.SelectOption(label="5 min", value="5"),
                discord.SelectOption(label="10 min", value="10"),
                discord.SelectOption(label="15 min", value="15"),
                discord.SelectOption(label="30 min", value="30"),
            ],
            custom_id="antilink_duration"
        ))

    async def on_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        state = interaction.data["values"][0]
        punishment = interaction.data["values"][1]
        duration = int(interaction.data["values"][2])

        guild_id = interaction.guild.id

        if state == "enable":
            set_antilink_settings(guild_id, True, punishment, duration)
        else:
            set_antilink_settings(guild_id, False, punishment, duration)

        await interaction.response.send_message(f"Anti-link: {state}, Punishment: {punishment}, Duration: {duration} minutes.", ephemeral=True)


# --- Slash Commands ---
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

    await bot.load_extension("cogs.automod")  # Load automod cog

# Command for configuring anti-spam
@bot.tree.command(name="antispam", description="Enable/Disable anti-spam, set punishment, and duration.")
async def antispam(interaction: discord.Interaction):
    view = AntispamView()
    await interaction.response.send_message("Configure Anti-spam settings:", view=view)

# Command for configuring anti-link
@bot.tree.command(name="antilink", description="Enable/Disable anti-link, set punishment, and duration.")
async def antilink(interaction: discord.Interaction):
    view = AntilinkView()
    await interaction.response.send_message("Configure Anti-link settings:", view=view)

# Initialize and run bot
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
