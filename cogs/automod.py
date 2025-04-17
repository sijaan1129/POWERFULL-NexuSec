import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
from discord.ui import Select, View

class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam_enabled = {}
        self.antilink_enabled = {}

    async def timeout_user(self, member, minutes, reason):
        await member.timeout(until=discord.utils.utcnow() + timedelta(minutes=minutes), reason=reason)

    # --- Helper Function for Whitelisting ---
    def is_whitelisted(self, guild_id, user: discord.Member):
        # Logic to check if user/role is whitelisted (as you've done before)
        return False  # Placeholder for whitelist check

    # --- Anti-Spam Command ---
    @app_commands.command(name="antispam", description="Configure anti-spam")
    async def antispam(self, interaction: discord.Interaction):
        # Create dropdown for enable/disable
        select_enable = Select(
            placeholder="Choose whether to enable anti-spam",
            options=[
                discord.SelectOption(label="Enable", value="enable"),
                discord.SelectOption(label="Disable", value="disable")
            ]
        )

        # Create punishment dropdown (timeout, kick, ban)
        select_punishment = Select(
            placeholder="Select punishment for spamming",
            options=[
                discord.SelectOption(label="Timeout", value="timeout"),
                discord.SelectOption(label="Kick", value="kick"),
                discord.SelectOption(label="Ban", value="ban")
            ]
        )

        # Duration selection (e.g., minutes)
        select_duration = Select(
            placeholder="Choose the punishment duration (in minutes)",
            options=[discord.SelectOption(label=str(i), value=str(i)) for i in range(1, 31)]  # 1-30 minutes
        )

        # Store data when a selection is made
        async def select_callback(interaction):
            state = select_enable.values[0]
            punishment = select_punishment.values[0]
            duration = int(select_duration.values[0])

            # Save settings
            self.antispam_enabled[interaction.guild.id] = state == "enable"
            # Handle punishment logic, e.g., timeout, kick, ban
            await interaction.response.send_message(f"Anti-spam is now {state} with a punishment of {punishment} for {duration} minutes.")

        # Attach callback to each select menu
        select_enable.callback = select_callback
        select_punishment.callback = select_callback
        select_duration.callback = select_callback

        # Create a View to hold the dropdowns
        view = View()
        view.add_item(select_enable)
        view.add_item(select_punishment)
        view.add_item(select_duration)

        # Send the message with the dropdowns
        await interaction.response.send_message("Configure Anti-Spam:", view=view)

    # --- Anti-Link Command ---
    @app_commands.command(name="antilink", description="Configure anti-link")
    async def antilink(self, interaction: discord.Interaction):
        # Create dropdown for enable/disable
        select_enable = Select(
            placeholder="Choose whether to enable anti-link",
            options=[
                discord.SelectOption(label="Enable", value="enable"),
                discord.SelectOption(label="Disable", value="disable")
            ]
        )

        # Create punishment dropdown (timeout, kick, ban)
        select_punishment = Select(
            placeholder="Select punishment for posting links",
            options=[
                discord.SelectOption(label="Timeout", value="timeout"),
                discord.SelectOption(label="Kick", value="kick"),
                discord.SelectOption(label="Ban", value="ban")
            ]
        )

        # Duration selection (e.g., minutes)
        select_duration = Select(
            placeholder="Choose the punishment duration (in minutes)",
            options=[discord.SelectOption(label=str(i), value=str(i)) for i in range(1, 31)]  # 1-30 minutes
        )

        # Store data when a selection is made
        async def select_callback(interaction):
            state = select_enable.values[0]
            punishment = select_punishment.values[0]
            duration = int(select_duration.values[0])

            # Save settings
            self.antilink_enabled[interaction.guild.id] = state == "enable"
            # Handle punishment logic, e.g., timeout, kick, ban
            await interaction.response.send_message(f"Anti-link is now {state} with a punishment of {punishment} for {duration} minutes.")

        # Attach callback to each select menu
        select_enable.callback = select_callback
        select_punishment.callback = select_callback
        select_duration.callback = select_callback

        # Create a View to hold the dropdowns
        view = View()
        view.add_item(select_enable)
        view.add_item(select_punishment)
        view.add_item(select_duration)

        # Send the message with the dropdowns
        await interaction.response.send_message("Configure Anti-Link:", view=view)

# Setup function to add cog to the bot
async def setup(bot):
    await bot.add_cog(Automod(bot))
