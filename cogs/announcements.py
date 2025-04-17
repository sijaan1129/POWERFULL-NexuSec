import discord
from discord.ext import commands
from discord import app_commands

class Announcement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channels = {}         # guild_id: channel_id
        self.welcome_messages = {}     # guild_id: welcome text
        self.goodbye_messages = {}     # guild_id: goodbye text
        self.auto_roles = {}           # guild_id: role_id

    # --- Event Listener ---

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id

        # Send welcome
        welcome = self.welcome_messages.get(guild_id)
        if welcome:
            try:
                await member.send(welcome.replace("{user}", member.mention))
            except discord.Forbidden:
                pass

        # Auto role
        role_id = self.auto_roles.get(guild_id)
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                await member.add_roles(role, reason="AutoRole")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        goodbye = self.goodbye_messages.get(member.guild.id)
        if goodbye:
            try:
                await member.send(goodbye.replace("{user}", member.name))
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if channel_id := self.log_channels.get(guild.id):
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.send(f"🚫 {user.name} has been **banned**.")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        if channel_id := self.log_channels.get(guild.id):
            channel = guild.get_channel(channel_id)
            if channel:
                await channel.send(f"✅ {user.name} has been **unbanned**.")

    # --- Commands ---

    @app_commands.command(name="announce", description="Send an embed announcement.")
    async def announce(self, interaction: discord.Interaction, title: str, message: str, channel: discord.TextChannel = None):
        embed = discord.Embed(title=title, description=message, color=discord.Color.gold())
        channel = channel or interaction.channel
        await channel.send(embed=embed)
        await interaction.response.send_message("📢 Announcement sent!", ephemeral=True)

    @app_commands.command(name="log", description="Set the moderation log channel.")
    async def set_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.log_channels[interaction.guild.id] = channel.id
        await interaction.response.send_message(f"✅ Mod log channel set to {channel.mention}")

    @app_commands.command(name="welcome", description="Set the welcome message. Use {user} to mention the user.")
    async def welcome(self, interaction: discord.Interaction, message: str):
        self.welcome_messages[interaction.guild.id] = message
        await interaction.response.send_message("✅ Welcome message set!")

    @app_commands.command(name="goodbye", description="Set the goodbye message.")
    async def goodbye(self, interaction: discord.Interaction, message: str):
        self.goodbye_messages[interaction.guild.id] = message
        await interaction.response.send_message("👋 Goodbye message set!")

    @app_commands.command(name="autoroles", description="Set the autorole to assign on member join.")
    async def autoroles(self, interaction: discord.Interaction, role: discord.Role):
        self.auto_roles[interaction.guild.id] = role.id
        await interaction.response.send_message(f"✅ Autorole set to {role.mention}")

async def setup(bot):
    await bot.add_cog(Announcement(bot))
