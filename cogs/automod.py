import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View
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

    # --- View for Antispam ---
    class AntispamView(View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(Select(
                placeholder="Select State",
                options=[
                    discord.SelectOption(label="Enable", value="enable"),
                    discord.SelectOption(label="Disable", value="disable"),
                ],
                custom_id="antispam_state"
            ))

            self.add_item(Select(
                placeholder="Select Punishment",
                options=[
                    discord.SelectOption(label="Timeout", value="timeout"),
                    discord.SelectOption(label="Ban", value="ban"),
                    discord.SelectOption(label="Kick", value="kick"),
                ],
                custom_id="antispam_punishment"
            ))

            self.add_item(Select(
                placeholder="Select Duration (Minutes)",
                options=[
                    discord.SelectOption(label="5 min", value="5"),
                    discord.SelectOption(label="10 min", value="10"),
                    discord.SelectOption(label="15 min", value="15"),
                    discord.SelectOption(label="30 min", value="30"),
                ],
                custom_id="antispam_duration"
            ))

        async def on_select(self, interaction: discord.Interaction, select: discord.ui.Select):
            state = interaction.data["values"][0]
            punishment = interaction.data["values"][1]
            duration = int(interaction.data["values"][2])
            
            # Perform action based on selected options
            await interaction.response.send_message(f"Anti-spam: {state}, Punishment: {punishment}, Duration: {duration} minutes.", ephemeral=True)

    # --- View for Antilink ---
    class AntilinkView(View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(Select(
                placeholder="Select State",
                options=[
                    discord.SelectOption(label="Enable", value="enable"),
                    discord.SelectOption(label="Disable", value="disable"),
                ],
                custom_id="antilink_state"
            ))

            self.add_item(Select(
                placeholder="Select Punishment",
                options=[
                    discord.SelectOption(label="Timeout", value="timeout"),
                    discord.SelectOption(label="Ban", value="ban"),
                    discord.SelectOption(label="Kick", value="kick"),
                ],
                custom_id="antilink_punishment"
            ))

            self.add_item(Select(
                placeholder="Select Duration (Minutes)",
                options=[
                    discord.SelectOption(label="5 min", value="5"),
                    discord.SelectOption(label="10 min", value="10"),
                    discord.SelectOption(label="15 min", value="15"),
                    discord.SelectOption(label="30 min", value="30"),
                ],
                custom_id="antilink_duration"
            ))

        async def on_select(self, interaction: discord.Interaction, select: discord.ui.Select):
            state = interaction.data["values"][0]
            punishment = interaction.data["values"][1]
            duration = int(interaction.data["values"][2])
            
            # Perform action based on selected options
            await interaction.response.send_message(f"Anti-link: {state}, Punishment: {punishment}, Duration: {duration} minutes.", ephemeral=True)

    # --- Slash Commands ---
    @app_commands.command(name="antispam", description="Enable/Disable anti-spam, set punishment, and duration.")
    async def antispam(self, interaction: discord.Interaction):
        view = self.AntispamView()
        await interaction.response.send_message("Configure Anti-spam settings:", view=view)

    @app_commands.command(name="antilink", description="Enable/Disable anti-link, set punishment, and duration.")
    async def antilink(self, interaction: discord.Interaction):
        view = self.AntilinkView()
        await interaction.response.send_message("Configure Anti-link settings:", view=view)

async def setup(bot):
    await bot.add_cog(Automod(bot))
