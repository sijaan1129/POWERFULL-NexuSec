import discord
from discord.ext import commands
from discord import app_commands
import re
from datetime import timedelta

class AntiAbuse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam_enabled = {}  # guild_id: {"enabled": bool, "punishment": "timeout"}
        self.antilink_enabled = {}  # guild_id: {"enabled": bool, "punishment": "ban"}
        self.message_cache = {}     # user_id: [timestamps]

    def is_spam(self, user_id):
        from time import time
        now = time()
        timestamps = self.message_cache.get(user_id, [])
        timestamps = [t for t in timestamps if now - t < 5]  # only keep last 5 seconds
        timestamps.append(now)
        self.message_cache[user_id] = timestamps
        return len(timestamps) >= 5

    def is_link(self, content):
        return bool(re.search(r"https?://\S+", content))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        user = message.author

        # Anti-Spam
        antispam = self.antispam_enabled.get(guild_id, {"enabled": False, "punishment": "timeout"})
        if antispam["enabled"] and self.is_spam(user.id):
            try:
                if antispam["punishment"] == "timeout":
                    await user.timeout(timedelta(minutes=10))
                elif antispam["punishment"] == "kick":
                    await message.guild.kick(user)
                elif antispam["punishment"] == "ban":
                    await message.guild.ban(user, reason="Anti-spam")
                await message.channel.send(f"🚫 {user.mention} was punished for spamming.")
            except Exception as e:
                print(f"Spam punishment error: {e}")

        # Anti-Link
        antilink = self.antilink_enabled.get(guild_id, {"enabled": False, "punishment": "timeout"})
        if antilink["enabled"] and self.is_link(message.content):
            try:
                await message.delete()
                if antilink["punishment"] == "timeout":
                    await user.timeout(timedelta(minutes=30))
                elif antilink["punishment"] == "kick":
                    await message.guild.kick(user)
                elif antilink["punishment"] == "ban":
                    await message.guild.ban(user, reason="Anti-link")
                await message.channel.send(f"🔗 {user.mention} sent a link and was punished.")
            except Exception as e:
                print(f"Link punishment error: {e}")

    @app_commands.command(name="antispam", description="Enable/disable anti-spam and set punishment")
    @app_commands.describe(enable="Enable or disable", punishment="timeout/kick/ban")
    async def antispam(self, interaction: discord.Interaction, enable: bool, punishment: str = "timeout"):
        self.antispam_enabled[interaction.guild.id] = {"enabled": enable, "punishment": punishment}
        await interaction.response.send_message(f"🛡️ Anti-spam is now {'enabled' if enable else 'disabled'} with `{punishment}` punishment.")

    @app_commands.command(name="antilink", description="Enable/disable anti-link and set punishment")
    @app_commands.describe(enable="Enable or disable", punishment="timeout/kick/ban")
    async def antilink(self, interaction: discord.Interaction, enable: bool, punishment: str = "timeout"):
        self.antilink_enabled[interaction.guild.id] = {"enabled": enable, "punishment": punishment}
        await interaction.response.send_message(f"🔗 Anti-link is now {'enabled' if enable else 'disabled'} with `{punishment}` punishment.")

async def setup(bot):
    await bot.add_cog(AntiAbuse(bot))
