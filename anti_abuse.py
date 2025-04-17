from discord import app_commands
from discord.ext import commands
import discord
import asyncpg
import os

class AntiAbuse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def save_setting(self, guild_id, setting, value):
        await self.bot.db.execute(
            f"UPDATE automod_settings SET {setting} = $1 WHERE guild_id = $2",
            value, guild_id
        )

    async def ensure_guild_row(self, guild_id):
        exists = await self.bot.db.fetchrow("SELECT * FROM automod_settings WHERE guild_id = $1", guild_id)
        if not exists:
            await self.bot.db.execute("INSERT INTO automod_settings (guild_id) VALUES ($1)", guild_id)

    @app_commands.command(name="antispam", description="Enable or disable anti-spam.")
    @app_commands.describe(enable="Enable or disable anti-spam", timeout="Timeout duration (if using timeout)")
    async def antispam(
        self,
        interaction: discord.Interaction,
        enable: bool,
        punishment: app_commands.Choice[str] = app_commands.Choice(name="timeout", value="timeout"),
        timeout: int = 10
    ):
        await self.ensure_guild_row(interaction.guild.id)

        # Save the settings
        await self.save_setting(interaction.guild.id, "antispam_enabled", enable)
        await self.save_setting(interaction.guild.id, "antispam_punishment", punishment)
        await self.save_setting(interaction.guild.id, "antispam_timeout", timeout)

        await interaction.response.send_message(
            f"🛡️ Anti-spam set to `{enable}` with punishment: `{punishment}`" +
            (f" and timeout of `{timeout} minutes`" if punishment == "timeout" else "")
        )

    @app_commands.command(name="antilink", description="Enable or disable anti-link.")
    @app_commands.describe(enable="Enable or disable anti-link", timeout="Timeout duration (if using timeout)")
    async def antilink(
        self,
        interaction: discord.Interaction,
        enable: bool,
        punishment: app_commands.Choice[str] = app_commands.Choice(name="timeout", value="timeout"),
        timeout: int = 30
    ):
        await self.ensure_guild_row(interaction.guild.id)

        # Save the settings
        await self.save_setting(interaction.guild.id, "antilink_enabled", enable)
        await self.save_setting(interaction.guild.id, "antilink_punishment", punishment)
        await self.save_setting(interaction.guild.id, "antilink_timeout", timeout)

        await interaction.response.send_message(
            f"🔗 Anti-link set to `{enable}` with punishment: `{punishment}`" +
            (f" and timeout of `{timeout} minutes`" if punishment == "timeout" else "")
        )
