import discord
from discord.ext import commands
from discord.utils import utcnow
from datetime import timedelta
from db import (
    get_badwords,
    get_antilink_settings,
    get_antispam_settings
)
import re

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # For spam detection: {guild_id: {user_id: [timestamps]}}
        self.message_cache = {}
        # Regex for links
        self.link_pattern = re.compile(r"(https?://\S+|discord\.gg/\S+)")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignore bots and DMs
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        user = message.author
        bot_member = message.guild.get_member(self.bot.user.id)

        # Skip if message author has higher or equal top role than bot
        if user.top_role >= bot_member.top_role:
            # Let commands still be processed
            await self.bot.process_commands(message)
            return

        content = message.content.lower()

        # --- Bad Word Filter ---
        badwords = get_badwords(guild_id)
        for word in badwords:
            if word in content:
                await message.delete()
                await self._punish(user, guild_id, reason="Used bad word")
                # Stop further checks
                await self.bot.process_commands(message)
                return

        # --- Anti-Link Filter ---
        antilink_enabled, antilink_punishment, antilink_timeout = get_antilink_settings(guild_id)
        if antilink_enabled and self.link_pattern.search(content):
            await message.delete()
            await self._punish(user, guild_id, punishment=antilink_punishment,
                               duration=antilink_timeout, reason="Posted a link")
            await self.bot.process_commands(message)
            return

        # --- Anti-Spam Filter ---
        antispam_enabled, antispam_punishment, antispam_timeout = get_antispam_settings(guild_id)
        if antispam_enabled:
            # Initialize per-guild cache
            self.message_cache.setdefault(guild_id, {})
            user_times = self.message_cache[guild_id].setdefault(user.id, [])
            now = utcnow()
            # Keep only messages in last 5 seconds
            user_times.append(now)
            user_times[:] = [t for t in user_times if (now - t).total_seconds() <= 5]

            # Threshold: 5 messages
            if len(user_times) >= 5:
                # Clear cache for user
                self.message_cache[guild_id][user.id] = []
                await message.delete()
                await self._punish(user, guild_id, punishment=antispam_punishment,
                                   duration=antispam_timeout, reason="Spamming")
                await self.bot.process_commands(message)
                return

        # Finally, process other commands
        await self.bot.process_commands(message)

    async def _punish(self, user, guild_id, punishment=None, duration=None, reason=None):
        # Determine punishment type and duration
        # If punishment or duration not provided, fetch defaults from DB
        if not punishment or not duration:
            # For bad word or fallback, choose timeout 5 min
            punishment = punishment or "timeout"
            duration = duration or 5

        try:
            if punishment == "timeout":
                until = utcnow() + timedelta(minutes=duration)
                await user.timeout(until=until, reason=reason)
            elif punishment == "kick":
                await user.kick(reason=reason)
            elif punishment == "ban":
                await user.ban(reason=reason)
        except discord.Forbidden:
            print(f"Permission error punishing {user} for {reason}")
        except Exception as e:
            print(f"Error punishing {user}: {e}")

async def setup(bot):
    await bot.add_cog(AutoMod(bot))
