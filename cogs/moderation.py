import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}  # In-memory warning storage; switch to DB for persistence
        self.modlog_channel_id = None

    def get_modlog(self, guild: discord.Guild):
        if self.modlog_channel_id:
            return guild.get_channel(self.modlog_channel_id)
        return None

    @app_commands.command(name="ban", description="Ban a user.")
    @app_commands.describe(user="User to ban", reason="Reason for ban")
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        await interaction.response.defer()  # Let Discord know you're working
        await user.ban(reason=reason)
        await interaction.followup.send(f"🔨 {user.mention} has been banned. Reason: {reason}")
    
        log = self.get_modlog(interaction.guild)
        if log:
            await log.send(f"🔨 {user.mention} was banned by {interaction.user.mention}. Reason: {reason}")

    @app_commands.command(name="unban", description="Unban a user.")
    @app_commands.describe(user_id="User ID to unban")
    async def unban(self, interaction: discord.Interaction, user_id: str):
        await interaction.response.defer()  # Prevent the timeout

        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.followup.send(f"✅ {user.mention} has been unbanned.")
        
            log = self.get_modlog(interaction.guild)
            if log:
                await log.send(f"✅ {user.mention} was unbanned by {interaction.user.mention}.")
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to unban: {e}")

    
    @app_commands.command(name="kick", description="Kick a user.")
    @app_commands.describe(user="User to kick", reason="Reason for kick")
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        await interaction.response.defer()
        await user.kick(reason=reason)
        await interaction.followup.send(f"👢 {user.mention} has been kicked. Reason: {reason}")
    
        log = self.get_modlog(interaction.guild)
        if log:
            await log.send(f"👢 {user.mention} was kicked by {interaction.user.mention}. Reason: {reason}")

    @app_commands.command(name="mute", description="Timeout a user.")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int):
        await interaction.response.defer(ephemeral=True)  # Defer the response
        try:
            await member.timeout(timedelta(minutes=duration))
            await interaction.followup.send(f"🔇 {member.mention} has been muted for {duration} minutes.")
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to mute: {e}", ephemeral=True)

    @app_commands.command(name="unmute", description="Unmute a user.")
    async def unmute(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        await user.timeout(None)
        await interaction.followup.send(f"{user.mention} has been unmuted.")

    @app_commands.command(name="warn", description="Warn a user.")
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        await interaction.response.defer(ephemeral=True)
        self.warnings.setdefault(user.id, []).append(reason)
        await interaction.followup.send(f"{user.mention} has been warned. Reason: {reason}")

    @app_commands.command(name="warnings", description="View a user's warnings.")
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        warns = self.warnings.get(user.id, [])
        if not warns:
            await interaction.followup.send(f"{user.mention} has no warnings.")
        else:
            await interaction.followup.send(f"Warnings for {user.mention}: " + "; ".join(warns))

    @app_commands.command(name="clear", description="Bulk delete messages.")
    async def clear(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)  # Defer the response
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)

    @app_commands.command(name="lock", description="Lock the channel.")
    async def lock(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.followup.send("🔒 Channel locked.")

    @app_commands.command(name="unlock", description="Unlock the channel.")
    async def unlock(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = None
        await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
        await interaction.followup.send("🔓 Channel unlocked.")

    @app_commands.command(name="slowmode", description="Set slowmode for the channel.")
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.edit(slowmode_delay=seconds)
        await interaction.followup.send(f"Slowmode set to {seconds} seconds.")

    @app_commands.command(name="softban", description="Ban and then unban (deletes messages).")
    async def softban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Softban"):
        await interaction.response.defer(ephemeral=True)
        await interaction.guild.ban(user, reason=reason)
        await asyncio.sleep(1)
        await interaction.guild.unban(user)
        await interaction.followup.send(f"{user} has been softbanned.")

    @app_commands.command(name="modlogs", description="Set the modlog channel.")
    async def modlogs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        self.modlog_channel_id = channel.id
        await interaction.followup.send(f"Modlog channel set to {channel.mention}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
