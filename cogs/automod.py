import discord
from discord.ext import commands
from db import get_badwords, get_antilink_settings, get_antispam_settings
from datetime import datetime

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Bad Word Check
        badwords = get_badwords(message.guild.id)
        for word in badwords:
            if word.lower() in message.content.lower():
                await self.handle_badword(message, word)
                return

        # Anti-Link Check
        link_enabled, punishment, _ = get_antilink_settings(message.guild.id)
        if link_enabled and any(keyword in message.content.lower() for keyword in ['http://', 'https://', 'discord.gg']):
            await self.handle_antilink(message, punishment)

        # Anti-Spam Check
        spam_enabled, _, _ = get_antispam_settings(message.guild.id)
        if spam_enabled:
            await self.handle_antisam(message)

    async def handle_badword(self, message: discord.Message, word: str):
        print(f"Bad word detected: {word}")
        # Delete the message
        await message.delete()
        # Apply punishment if needed (ban, kick, or timeout)
        # Punishment logic to be added here

    async def handle_antilink(self, message: discord.Message, punishment: str):
        print(f"Link detected in message: {message.content}")
        # Delete the message with the link
        await message.delete()
        # Apply punishment based on the selected punishment type (timeout, ban, kick)
        if punishment == "timeout":
            await message.author.timeout(datetime.utcnow(), reason="Sent a link while Anti-Link is enabled.")
        elif punishment == "ban":
            await message.guild.ban(message.author, reason="Sent a link while Anti-Link is enabled.")
        elif punishment == "kick":
            await message.guild.kick(message.author, reason="Sent a link while Anti-Link is enabled.")

    async def handle_antisam(self, message: discord.Message):
        print(f"Spam detected in message: {message.content}")
        # Implement Anti-Spam handling here (e.g., deleting spammy messages, applying timeouts)
        pass

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
