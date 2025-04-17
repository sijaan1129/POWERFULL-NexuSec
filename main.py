import discord
from discord.ext import commands
import os
import asyncio
import threading
import logging
from flask import Flask
from datetime import datetime
from db import set_antispam_settings, set_antilink_settings, init_db

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Web server for Render (FREE plan workaround) ---
app = Flask("")

@app.route("/")
def home():
    return f"NexuSec is online – {datetime.utcnow()} UTC"

def run_web():
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)

# Keep Flask thread alive
threading.Thread(target=run_web, daemon=True).start()

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
    "cogs.custom_commands",
    "cogs.whitelist"
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

            try:
                if self.feature == "antispam":
                    set_antispam_settings(guild_id, self.state == "enable", self.punishment, self.duration)
                elif self.feature == "antilink":
                    set_antilink_settings(guild_id, self.state == "enable", self.punishment, self.duration)

                await interaction.response.send_message(
                    f"✅ **{self.feature.capitalize()}** settings updated:\n"
                    f"• State: **{self.state}**\n"
                    f"• Punishment: **{self.punishment}**\n"
                    f"• Duration: **{self.duration} minutes**",
                    ephemeral=False
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ There was an error while updating the settings for {self.feature}. Please try again.",
                    ephemeral=False
                )
                print(f"Error updating {self.feature} settings: {e}")
        else:
            await interaction.response.send_message(
                "❌ Please select all options to update the settings.",
                ephemeral=False
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

    pass  # Cogs are already loaded in load_cogs()

@bot.tree.command(name="help", description="Show all available commands with descriptions.")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 NexuSec Help Menu", color=discord.Color.blue())

    embed.add_field(name="🛡️ **Moderation Commands**", value="`/ban`: Ban a user.\n`/kick`: Kick a user.\n`/mute`: Mute a user.\n`/warn`: Warn a user.\n`/lock`: Lock a channel.\n", inline=False)
    embed.add_field(name="⚙️ **Anti-Spam Commands**", value="`/antispam`: Configure anti-spam settings.\n", inline=False)
    embed.add_field(name="🔗 **Anti-Link Commands**", value="`/antilink`: Configure anti-link settings.\n", inline=False)
    embed.add_field(name="🧰 **Utility Commands**", value="`/ping`: Check the bot's latency.\n`/userinfo`: Get user info.\n`/uptime`: Get bot uptime.\n", inline=False)
    embed.add_field(name="📢 **Announcement Commands**", value="`/announce`: Send an announcement.\n", inline=False)
    embed.add_field(name="🎉 **Fun Commands**", value="`/poll`: Create a poll.\n`/giveaway`: Start a giveaway.\n", inline=False)
    embed.add_field(name="💬 **Custom Commands**", value="`/custom add`: Add a custom command.\n`/custom delete`: Delete a custom command.\n", inline=False)
    
    await interaction.response.send_message(embed=embed)

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

try:
    asyncio.run(main())
except Exception as e:
    print(f"❌ Bot crashed: {e}")
