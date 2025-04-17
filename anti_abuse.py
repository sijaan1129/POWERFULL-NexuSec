import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import asyncio

class AntiAbuse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam_enabled = False
        self.antilink_enabled = False
        self.punishment_type = None
        self.timeout_duration = 10  # Default timeout (minutes)
        self.message_counts = {}

    # Anti-spam command
    @app_commands.command(name="antispam", description="Enable or disable anti-spam with punishment")
    @app_commands.describe(enable="Enable or disable anti-spam", punishment="timeout/kick/ban", time="Timeout duration in minutes (if using timeout)")
    async def antispam(self, interaction: discord.Interaction, enable: bool, punishment: str, time: int = 10):
        self.antispam_enabled = enable
        self.punishment_type = punishment.lower()
        self.timeout_duration = time
        await interaction.response.send_message(f"✅ Anti-spam is now {'enabled' if enable else 'disabled'} with punishment: **{punishment}**{' (' + str(time) + ' mins)' if punishment == 'timeout' else ''}.")

    # Anti-link command
    @app_commands.command(name="antilink", description="Enable or disable anti-link with punishment")
    @app_commands.describe(enable="Enable or disable anti-link", punishment="timeout/kick/ban", time="Timeout duration in minutes (if using timeout)")
    async def antilink(self, interaction: discord.Interaction, enable: bool, punishment: str, time: int = 10):
        self.antilink_enabled = enable
        self.punishment_type = punishment.lower()
        self.timeout_duration = time
        await interaction.response.send_message(f"✅ Anti-link is now {'enabled' if enable else 'disabled'} with punishment: **{punishment}**{' (' + str(time) + ' mins)' if punishment == 'timeout' else ''}.")

    # Unified message listener
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Anti-link logic
        if self.antilink_enabled and any(word in message.content for word in ["http", "www", ".com"]):
            await message.delete()
            await self.apply_punishment(message.author, message.channel, "link")
            return

        # Anti-spam logic
        if self.antispam_enabled:
            user_id = message.author.id
            self.message_counts[user_id] = self.message_counts.get(user_id, 0) + 1

            if self.message_counts[user_id] > 5:
                await message.delete()
                await self.apply_punishment(message.author, message.channel, "spam_
