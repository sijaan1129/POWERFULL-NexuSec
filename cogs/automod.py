import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam_enabled = {}
        self.antilink_enabled = {}
        self.badwords = {}
        self.antilink_whitelist = {}
        self.user_message_cache = {}

    # --- Helper Functions ---

    def is_whitelisted(self, guild_id, user: discord.Member):
        wl = self.antilink_whitelist.get(guild_id, {"users": [], "roles": []})
        return user.id in wl["users"] or any(role.id in wl["roles"] for role in user.roles)

    async def timeout_user(self, member, minutes, reason):
        await member.timeout(until=discord.utils.utcnow() + timedelta(minutes=minutes), reason=reason)

    # --- Event Listener ---
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        guild_id = message.guild.id
        user_id = message.author.id

        # --- AntiSpam ---
        if self.antispam_enabled.get(guild_id, False):
            now = datetime.utcnow()
            self.user_message_cache.setdefault(user_id, []).append(now)

            # Remove messages older than 5 sec
            self.user_message_cache[user_id] = [
                t for t in self.user_message_cache[user_id] if (now - t).total_seconds() <= 5
            ]

            if len(self.user_message_cache[user_id]) >= 5:
                await self.timeout_user(message.author, 10, "Spamming")
                await message.channel.send(f"{message.author.mention} has been timed out for spamming.", delete_after=5)
                self.user_message_cache[user_id] = []

        # --- AntiLink ---
        if self.antilink_enabled.get(guild_id, False) and not self.is_whitelisted(guild_id, message.author):
            if "http://" in message.content or "https://" in message.content or "discord.gg/" in message.content:
                await message.delete()
                await self.timeout_user(message.author, 30, "Posting links")
                await message.channel.send(f"{message.author.mention} sent a link and has been timed out (30 min).", delete_after=5)

        # --- Bad Word Filter ---
        for word in self.badwords.get(guild_id, []):
            if word.lower() in message.content.lower():
                await message.delete()
                await message.channel.send(f"{message.author.mention} used a blacklisted word.", delete_after=5)
                break

    # --- Commands ---

    @app_commands.command(name="antispam", description="Enable or disable anti-spam")
    async def antispam(self, interaction: discord.Interaction, status: str):
        self.antispam_enabled[interaction.guild.id] = status.lower() == "enable"
        await interaction.response.send_message(f"Anti-spam has been {'enabled' if status.lower() == 'enable' else 'disabled'}.")

    @app_commands.command(name="antilink", description="Enable or disable anti-link")
    async def antilink(self, interaction: discord.Interaction, status: str):
        self.antilink_enabled[interaction.guild.id] = status.lower() == "enable"
        await interaction.response.send_message(f"Anti-link has been {'enabled' if status.lower() == 'enable' else 'disabled'}.")

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

    @app_commands.command(name="allowantilink", description="Whitelist a user or role from anti-link.")
    async def allow_antilink(self, interaction: discord.Interaction, member_or_role: discord.Member):
        entry = self.antilink_whitelist.setdefault(interaction.guild.id, {"users": [], "roles": []})
        if isinstance(member_or_role, discord.Member):
            entry["users"].append(member_or_role.id)
        elif isinstance(member_or_role, discord.Role):
            entry["roles"].append(member_or_role.id)
        await interaction.response.send_message(f"{member_or_role} has been whitelisted from anti-link.")

    @app_commands.command(name="disallowantilink", description="Remove user or role from anti-link whitelist.")
    async def disallow_antilink(self, interaction: discord.Interaction, member_or_role: discord.Member):
        entry = self.antilink_whitelist.setdefault(interaction.guild.id, {"users": [], "roles": []})
        if isinstance(member_or_role, discord.Member):
            entry["users"].remove(member_or_role.id)
        elif isinstance(member_or_role, discord.Role):
            entry["roles"].remove(member_or_role.id)
        await interaction.response.send_message(f"{member_or_role} removed from anti-link whitelist.")

    @app_commands.command(name="viewantilinkwhitelist", description="View the anti-link whitelist.")
    async def view_whitelist(self, interaction: discord.Interaction):
        wl = self.antilink_whitelist.get(interaction.guild.id, {"users": [], "roles": []})
        users = [f"<@{uid}>" for uid in wl["users"]]
        roles = [f"<@&{rid}>" for rid in wl["roles"]]
        await interaction.response.send_message(
            f"Whitelisted Users: {', '.join(users) if users else 'None'}\n"
            f"Whitelisted Roles: {', '.join(roles) if roles else 'None'}"
        )

async def setup(bot):
    await bot.add_cog(Automod(bot))
