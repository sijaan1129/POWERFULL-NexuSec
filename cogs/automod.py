import discord
from discord.ext import commands
from discord import app_commands, ui
from datetime import datetime, timedelta
from db import set_antispam_settings, set_antilink_settings

class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam_enabled = {}
        self.antilink_enabled = {}
        self.badwords = {}  # This will hold the bad words list per guild
        self.antilink_whitelist = {}
        self.user_message_cache = {}

    def is_whitelisted(self, guild_id, user: discord.Member):
        wl = self.antilink_whitelist.get(guild_id, {"users": [], "roles": []})
        return user.id in wl["users"] or any(role.id in wl["roles"] for role in user.roles)

    async def timeout_user(self, member, minutes, reason):
        try:
            await member.timeout(until=discord.utils.utcnow() + timedelta(minutes=minutes), reason=reason)
            print(f"Timed out {member} for {minutes} minutes due to {reason}.")
        except discord.Forbidden:
            print(f"Permission error: Bot doesn't have permission to timeout {member}.")
            await member.send("I don't have permission to timeout members in this server.")
        except discord.HTTPException as e:
            print(f"HTTPException error when trying to timeout {member}: {e}")
        except Exception as e:
            print(f"Unexpected error when trying to timeout {member}: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        guild_id = message.guild.id
        user_id = message.author.id

        # Anti-Spam functionality
        if self.antispam_enabled.get(guild_id, False):
            now = datetime.utcnow()
            self.user_message_cache.setdefault(user_id, []).append(now)
            self.user_message_cache[user_id] = [
                t for t in self.user_message_cache[user_id] if (now - t).total_seconds() <= 5
            ]
            if len(self.user_message_cache[user_id]) >= 5:
                await self.timeout_user(message.author, 10, "Spamming")
                await message.channel.send(f"{message.author.mention} has been timed out for spamming.", delete_after=5)
                self.user_message_cache[user_id] = []

        # Anti-Link functionality
        if self.antilink_enabled.get(guild_id, False) and not self.is_whitelisted(guild_id, message.author):
            if any(link in message.content for link in ["http://", "https://", "discord.gg/"]):
                print(f"Link detected from {message.author} in message: {message.content}")  # Debug
                await message.delete()
                await self.timeout_user(message.author, 30, "Posting links")  # Timeout user after message delete
                await message.channel.send(f"{message.author.mention} sent a link and has been timed out (30 min).", delete_after=5)

        # Bad Word filtering
        for word in self.badwords.get(guild_id, []):
            if word.lower() in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention} used a blacklisted word.", delete_after=5)
                break

    @app_commands.command(name="addbadword", description="Add a word to the blacklist.")
    async def addbadword(self, interaction: discord.Interaction, word: str):
        self.badwords.setdefault(interaction.guild.id, []).append(word.lower())
        await interaction.response.send_message(f"Added `{word}` to the blacklist.")

    @app_commands.command(name="removebadword", description="Remove a word from the blacklist.")
    async def removebadword(self, interaction: discord.Interaction, word: str):
        self.badwords.get(interaction.guild.id, []).remove(word.lower())
        await interaction.response.send_message(f"Removed `{word}` from the blacklist.")

    @app_commands.command(name="badwords", description="View all blacklisted words.")
    async def view_badwords(self, interaction: discord.Interaction):
        words = self.badwords.get(interaction.guild.id, [])
        await interaction.response.send_message("Bad words list: " + ", ".join(words) if words else "No bad words added.")

    # Other existing commands like `allowantilink`, `disallowantilink` etc.
    
async def setup(bot):
    await bot.add_cog(Automod(bot))
