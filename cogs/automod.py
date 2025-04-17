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
        self.badwords = {}
        self.antilink_whitelist = {}
        self.user_message_cache = {}

    def is_whitelisted(self, guild_id, user: discord.Member):
        wl = self.antilink_whitelist.get(guild_id, {"users": [], "roles": []})
        return user.id in wl["users"] or any(role.id in wl["roles"] for role in user.roles)

    async def timeout_user(self, member, minutes, reason):
        await member.timeout(until=discord.utils.utcnow() + timedelta(minutes=minutes), reason=reason)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        guild_id = message.guild.id
        user_id = message.author.id

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

        if self.antilink_enabled.get(guild_id, False) and not self.is_whitelisted(guild_id, message.author):
            if any(link in message.content for link in ["http://", "https://", "discord.gg/"]):
                await message.delete()
                await self.timeout_user(message.author, 30, "Posting links")
                await message.channel.send(f"{message.author.mention} sent a link and has been timed out (30 min).", delete_after=5)

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

    @app_commands.command(name="allowantilink", description="Whitelist a user or role from anti-link.")
    async def allow_antilink(self, interaction: discord.Interaction, member: discord.Member = None, role: discord.Role = None):
        entry = self.antilink_whitelist.setdefault(interaction.guild.id, {"users": [], "roles": []})
        if member:
            entry["users"].append(member.id)
            await interaction.response.send_message(f"{member.mention} has been whitelisted from anti-link.")
        elif role:
            entry["roles"].append(role.id)
            await interaction.response.send_message(f"{role.mention} has been whitelisted from anti-link.")
        else:
            await interaction.response.send_message("Please specify a member or role to whitelist.")

    @app_commands.command(name="disallowantilink", description="Remove user or role from anti-link whitelist.")
    async def disallow_antilink(self, interaction: discord.Interaction, member: discord.Member = None, role: discord.Role = None):
        entry = self.antilink_whitelist.setdefault(interaction.guild.id, {"users": [], "roles": []})
        if member and member.id in entry["users"]:
            entry["users"].remove(member.id)
            await interaction.response.send_message(f"{member.mention} removed from anti-link whitelist.")
        elif role and role.id in entry["roles"]:
            entry["roles"].remove(role.id)
            await interaction.response.send_message(f"{role.mention} removed from anti-link whitelist.")
        else:
            await interaction.response.send_message("User or role not found in whitelist.")

    @app_commands.command(name="viewantilinkwhitelist", description="View the anti-link whitelist.")
    async def view_whitelist(self, interaction: discord.Interaction):
        wl = self.antilink_whitelist.get(interaction.guild.id, {"users": [], "roles": []})
        users = [f"<@{uid}>" for uid in wl["users"]]
        roles = [f"<@&{rid}>" for rid in wl["roles"]]
        await interaction.response.send_message(
            f"Whitelisted Users: {', '.join(users) if users else 'None'}\n"
            f"Whitelisted Roles: {', '.join(roles) if roles else 'None'}"
        )

    @app_commands.command(name="antispam", description="Configure Anti-spam settings.")
    async def antispam_ui(self, interaction: discord.Interaction):
        await interaction.response.send_message("Configure Anti-spam settings:", view=AntiSettingView("antispam"), ephemeral=True)

    @app_commands.command(name="antilink", description="Configure Anti-link settings.")
    async def antilink_ui(self, interaction: discord.Interaction):
        await interaction.response.send_message("Configure Anti-link settings:", view=AntiSettingView("antilink"), ephemeral=True)

class StateSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Enable", value="enable"),
            discord.SelectOption(label="Disable", value="disable"),
        ]
        super().__init__(placeholder="Select State", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.state = self.values[0]
        await interaction.response.defer()

class PunishmentSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Timeout", value="timeout"),
            discord.SelectOption(label="Kick", value="kick"),
            discord.SelectOption(label="Ban", value="ban"),
        ]
        super().__init__(placeholder="Select Punishment", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.punishment = self.values[0]
        await interaction.response.defer()

class DurationSelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="5 minutes", value="5"),
            discord.SelectOption(label="10 minutes", value="10"),
            discord.SelectOption(label="30 minutes", value="30"),
            discord.SelectOption(label="60 minutes", value="60"),
        ]
        super().__init__(placeholder="Select Duration", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        self.view.duration = int(self.values[0])
        await interaction.response.defer()

class AntiSettingView(ui.View):
    def __init__(self, setting_type):
        super().__init__(timeout=60)
        self.setting_type = setting_type
        self.state = None
        self.punishment = None
        self.duration = None
        self.add_item(StateSelect())
        self.add_item(PunishmentSelect())
        self.add_item(DurationSelect())

    @ui.button(label="Save Settings", style=discord.ButtonStyle.green)
    async def save_settings(self, interaction: discord.Interaction, button: ui.Button):
        guild_id = interaction.guild.id
        enabled = self.state == "enable"
        punishment = self.punishment or "timeout"
        duration = self.duration or 10

        if self.setting_type == "antispam":
            set_antispam_settings(guild_id, enabled, punishment, duration)
        elif self.setting_type == "antilink":
            set_antilink_settings(guild_id, enabled, punishment, duration)

        await interaction.response.edit_message(
            content=f"✅ {self.setting_type.title()} settings updated:\n"
                    f"- Enabled: {enabled}\n- Punishment: {punishment}\n- Duration: {duration} minutes",
            view=None
        )

async def setup(bot):
    await bot.add_cog(Automod(bot))
