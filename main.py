import discord
from discord.ext import commands
import asyncio
import os
import threading
from flask import Flask
from db import set_antispam_settings, set_antilink_settings, init_db

# --- Web server for Render (FREE plan workaround) ---
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_web).start()

# ✅ Initialize database
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

# --- Dropdown Components ---

class StateSelect(discord.ui.Select):
    def __init__(self, feature: str):
        self.feature = feature
        options = [
            discord.SelectOption(label="Enable", value="enable"),
            discord.SelectOption(label="Disable", value="disable")
        ]
        super().__init__(placeholder="Select State", options=options, custom_id=f"{feature}_state")

    async def callback(self, interaction: discord.Interaction):
        view: SettingView = self.view
        view.state = self.values[0]
        await view.update(interaction)


class PunishmentSelect(discord.ui.Select):
    def __init__(self, feature: str):
        self.feature = feature
        options = [
            discord.SelectOption(label="Timeout", value="timeout"),
            discord.SelectOption(label="Ban", value="ban"),
            discord.SelectOption(label="Kick", value="kick")
        ]
        super().__init__(placeholder="Select Punishment", options=options, custom_id=f"{feature}_punishment")

    async def callback(self, interaction: discord.Interaction):
        view: SettingView = self.view
        view.punishment = self.values[0]
        await view.update(interaction)


class DurationSelect(discord.ui.Select):
    def __init__(self, feature: str):
        self.feature = feature
        options = [
            discord.SelectOption(label="5 min", value="5"),
            discord.SelectOption(label="10 min", value="10"),
            discord.SelectOption(label="15 min", value="15"),
            discord.SelectOption(label="30 min", value="30"),
        ]
        super().__init__(placeholder="Select Duration (Minutes)", options=options, custom_id=f"{feature}_duration")

    async def callback(self, interaction: discord.Interaction):
        view: SettingView = self.view
        view.duration = int(self.values[0])
        await view.update(interaction)


class SettingView(discord.ui.View):
    def __init__(self, feature: str):
        super().__init__(timeout=None)
        self.feature = feature
        self.state = None
        self.punishment = None
        self.duration = None

        self.add_item(StateSelect(feature))
        self.add_item(PunishmentSelect(feature))
        self.add_item(DurationSelect(feature))

    async def update(self, interaction: discord.Interaction):
        if all([self.state, self.punishment, self.duration is not None]):
            guild_id = interaction.guild.id

            if self.feature == "antispam":
                set_antispam_settings(guild_id, self.state == "enable", self.punishment, self.duration)
            elif self.feature == "antilink":
                set_antilink_settings(guild_id, self.state == "enable", self.punishment, self.duration)

            await interaction.response.send_message(
                f"✅ **{self.feature.capitalize()}** settings updated:\n"
                f"• State: **{self.state}**\n"
                f"• Punishment: **{self.punishment}**\n"
                f"• Duration: **{self.duration} minutes**",
                ephemeral=True
            )


# --- Slash Commands ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="Playing /help NexuSecbot.gg"))
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"❌ Slash command sync error: {e}")

    await bot.load_extension("cogs.automod")


@bot.tree.command(name="antispam", description="Configure anti-spam system")
async def antispam(interaction: discord.Interaction):
    view = SettingView("antispam")
    await interaction.response.send_message("⚙️ Configure **Anti-Spam** settings:", view=view, ephemeral=True)


@bot.tree.command(name="antilink", description="Configure anti-link system")
async def antilink(interaction: discord.Interaction):
    view = SettingView("antilink")
    await interaction.response.send_message("⚙️ Configure **Anti-Link** settings:", view=view, ephemeral=True)


# --- Run Bot ---
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
