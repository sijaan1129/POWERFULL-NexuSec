import discord
from discord.ext import commands
from discord import app_commands
from db import set_antilink_settings, get_antilink_settings
from datetime import timedelta

class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam_enabled = {}
        self.antilink_enabled = {}
        self.user_message_cache = {}

    async def update_antilink_settings(self, guild_id, enabled, punishment, timeout):
        # Update the anti-link settings in the database
        set_antilink_settings(guild_id, enabled, punishment, timeout)
        self.antilink_enabled[guild_id] = enabled
        print(f"Updated Anti-Link settings for guild {guild_id}: Enabled={enabled}, Punishment={punishment}, Timeout={timeout}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        guild_id = message.guild.id

        # Fetch settings from DB (ensure settings are properly fetched and applied)
        settings = get_antilink_settings(guild_id)
        if settings and settings[0]:  # If anti-link is enabled
            self.antilink_enabled[guild_id] = settings[0]

        if self.antilink_enabled.get(guild_id, False):
            if "http://" in message.content or "https://" in message.content or "discord.gg/" in message.content:
                # Anti-link logic
                print(f"Link detected from {message.author}: {message.content}")
                await message.delete()
                punishment = settings[1] if settings[1] else 'timeout'  # Fallback to 'timeout' if no punishment is set
                timeout_duration = settings[2] if settings[2] else 30  # Fallback to 30 minutes if no duration is set
                
                # Perform the punishment (timeout)
                if punishment == 'timeout':
                    await self.timeout_user(message.author, timeout_duration)
                    await message.channel.send(f"{message.author.mention} has been timed out for posting a link.")

    async def timeout_user(self, member, minutes):
        """Timeout a member."""
        try:
            await member.timeout(until=discord.utils.utcnow() + timedelta(minutes=minutes), reason="Posting links")
        except discord.Forbidden:
            print(f"Bot doesn't have permission to timeout {member}.")
        except discord.HTTPException as e:
            print(f"HTTP error when trying to timeout {member}: {e}")

    @app_commands.command(name="antilink", description="Configure Anti-Link settings.")
    async def antilink(self, interaction: discord.Interaction, state: bool, punishment: str, timeout: int):
        """Allow the server to configure Anti-Link settings."""
        guild_id = interaction.guild.id

        if state is None or punishment is None or timeout is None:
            await interaction.response.send_message("❌ Please select all options to update the settings.")
            return

        # Update the settings in the database
        await self.update_antilink_settings(guild_id, state, punishment, timeout)

        await interaction.response.send_message(f"✅ Anti-Link settings updated:\n• State: {'enabled' if state else 'disabled'}\n• Punishment: {punishment}\n• Duration: {timeout} minutes")

async def setup(bot):
    await bot.add_cog(Automod(bot))
