import re
import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import utcnow
from datetime import timedelta
from db import (
    add_badword,
    remove_badword,
    get_badwords,
    get_antilink_settings,
    set_antilink_settings,
    get_antispam_settings,
    set_antispam_settings
)

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_pattern = re.compile(r"(https?://\S+|discord\.gg/\S+)")
        self.spam_cache = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        user = message.author
        bot_member = message.guild.me

        if user.top_role >= bot_member.top_role:
            await self.bot.process_commands(message)
            return

        content = message.content.lower()

        # --- Bad Word Filter ---
        for word in get_badwords(guild_id):
            if word in content:
                await message.delete()
                await self._punish(user, message.channel, reason="Used a blacklisted word")
                await self.bot.process_commands(message)
                return

        # --- Anti-Link Filter ---
        al_enabled, al_punishment, al_timeout = get_antilink_settings(guild_id)
        if al_enabled and self.link_pattern.search(content):
            await message.delete()
            await self._punish(user, message.channel, punishment=al_punishment,
                               duration=al_timeout, reason="Posted a link")
            await self.bot.process_commands(message)
            return

        # --- Anti-Spam Filter ---
        sp_enabled, sp_punishment, sp_timeout = get_antispam_settings(guild_id)
        if sp_enabled:
            now = utcnow()
            guild_cache = self.spam_cache.setdefault(guild_id, {})
            user_times = guild_cache.setdefault(user.id, [])
            user_times.append(now)
            guild_cache[user.id] = [t for t in user_times if (now - t).total_seconds() <= 5]
            if len(guild_cache[user.id]) >= 5:
                await message.delete()
                await self._punish(user, message.channel, punishment=sp_punishment,
                                   duration=sp_timeout, reason="Spamming")
                guild_cache[user.id].clear()
                await self.bot.process_commands(message)
                return

        await self.bot.process_commands(message)

    async def _punish(self, user, channel, punishment="timeout", duration=5, reason=None):
        try:
            if punishment == "timeout":
                until = utcnow() + timedelta(minutes=duration)
                await user.timeout(until=until, reason=reason)
                await channel.send(f"🚫 {user.mention} timed out for {duration}m: {reason}", delete_after=5)
            elif punishment == "kick":
                await user.kick(reason=reason)
                await channel.send(f"👢 {user.mention} was kicked: {reason}", delete_after=5)
            elif punishment == "ban":
                await user.ban(reason=reason)
                await channel.send(f"🔨 {user.mention} was banned: {reason}", delete_after=5)
        except discord.Forbidden:
            await channel.send(f"❌ I lack permission to punish {user.mention}.")
        except Exception as e:
            print(f"Error punishing {user}: {e}")

# --- Define Commands as Standalone Functions Outside Class ---
@app_commands.command(name="addbadword", description="Add a word to the bad word list.")
@app_commands.describe(word="Word to block")
async def add_badword_cmd(interaction: discord.Interaction, word: str):
    add_badword(interaction.guild.id, word)
    await interaction.response.send_message(f"✅ Added `{word}` to the bad word list.", ephemeral=False)

@app_commands.command(name="removebadword", description="Remove a word from the bad word list.")
@app_commands.describe(word="Word to remove")
async def remove_badword_cmd(interaction: discord.Interaction, word: str):
    remove_badword(interaction.guild.id, word)
    await interaction.response.send_message(f"✅ Removed `{word}` from the bad word list.", ephemeral=False)

@app_commands.command(name="viewbadwords", description="View all blacklisted words.")
async def view_badwords_cmd(interaction: discord.Interaction):
    words = get_badwords(interaction.guild.id)
    if words:
        await interaction.response.send_message(
            "🚫 Blacklisted words: " + ", ".join(f"`{w}`" for w in words), ephemeral=False)
    else:
        await interaction.response.send_message("✅ No bad words set.", ephemeral=False)

@app_commands.command(name="antispam", description="Enable or disable anti-spam.")
@app_commands.describe(status="enable or disable")
async def antispam_cmd(interaction: discord.Interaction, status: str):
    enabled = status.lower() == "enable"
    _, pun, t = get_antispam_settings(interaction.guild.id)
    set_antispam_settings(interaction.guild.id, enabled, pun, t)
    await interaction.response.send_message(
        f"✅ Anti-spam {'enabled' if enabled else 'disabled'}.", ephemeral=False)

@app_commands.command(name="antilink", description="Enable or disable anti-link.")
@app_commands.describe(status="enable or disable")
async def antilink_cmd(interaction: discord.Interaction, status: str):
    enabled = status.lower() == "enable"
    _, pun, t = get_antilink_settings(interaction.guild.id)
    set_antilink_settings(interaction.guild.id, enabled, pun, t)
    await interaction.response.send_message(
        f"✅ Anti-link {'enabled' if enabled else 'disabled'}.", ephemeral=False)

# --- Register the Cog and Commands ---
async def setup(bot):
    await bot.add_cog(AutoMod(bot))
    bot.tree.add_command(add_badword_cmd)
    bot.tree.add_command(remove_badword_cmd)
    bot.tree.add_command(view_badwords_cmd)
    bot.tree.add_command(antispam_cmd)
    bot.tree.add_command(antilink_cmd)
