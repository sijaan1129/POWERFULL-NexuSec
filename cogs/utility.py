import discord
from discord.ext import commands
from discord import app_commands
import datetime

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_users = {}
        self.start_time = datetime.datetime.utcnow()
        self.verified_users = set()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.author.id in self.afk_users:
            del self.afk_users[message.author.id]
            await message.channel.send(f"Welcome back {message.author.mention}, I removed your AFK!")

        for user_id, afk_reason in self.afk_users.items():
            if f"<@{user_id}>" in message.content:
                user = message.guild.get_member(user_id)
                if user:
                    await message.channel.send(f"{user.mention} is AFK: {afk_reason}")

    @app_commands.command(name="ping", description="Check the bot's latency.")
    async def ping(self, interaction: discord.Interaction):
        """Check the bot's latency."""
        await interaction.response.send_message(f"Pong! 🏓 `{round(self.bot.latency * 1000)}ms`")

    @app_commands.command(name="userinfo", description="Get information about a user.")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        """Get information about a user."""
        user = user or interaction.user
        embed = discord.Embed(title=f"User Info - {user}", color=discord.Color.blurple())
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="ID", value=user.id)
        embed.add_field(name="Joined Server", value=user.joined_at.strftime("%Y-%m-%d %H:%M"))
        embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d %H:%M"))
        embed.add_field(name="Roles", value=", ".join([r.mention for r in user.roles if r.name != "@everyone"]))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="View server information.")
    async def serverinfo(self, interaction: discord.Interaction):
        """View server information."""
        guild = interaction.guild
        embed = discord.Embed(title="Server Info", color=discord.Color.green())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Name", value=guild.name)
        embed.add_field(name="ID", value=guild.id)
        embed.add_field(name="Owner", value=guild.owner.mention)
        embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d %H:%M"))
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Roles", value=len(guild.roles))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roles", description="List all roles in the server.")
    async def roles(self, interaction: discord.Interaction):
        """List all roles in the server."""
        roles = [role.mention for role in interaction.guild.roles if role.name != "@everyone"]
        await interaction.response.send_message("Roles:\n" + ", ".join(roles) if roles else "No roles found.")

    @app_commands.command(name="roleinfo", description="Get info on a specific role.")
    async def roleinfo(self, interaction: discord.Interaction, role: discord.Role):
        """Get info on a specific role."""
        embed = discord.Embed(title=f"Role Info - {role.name}", color=role.color)
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Mentionable", value=role.mentionable)
        embed.add_field(name="Members", value=len(role.members))
        embed.add_field(name="Position", value=role.position)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="channelinfo", description="Get info on a specific channel.")
    async def channelinfo(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel):
        """Get info on a specific channel."""
        embed = discord.Embed(title=f"Channel Info - {channel.name}", color=discord.Color.teal())
        embed.add_field(name="ID", value=channel.id)
        embed.add_field(name="Type", value=str(channel.type).capitalize())
        embed.add_field(name="Created", value=channel.created_at.strftime("%Y-%m-%d %H:%M"))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Get a user's avatar.")
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        """Get a user's avatar."""
        user = user or interaction.user
        await interaction.response.send_message(user.display_avatar.url)

    @app_commands.command(name="uptime", description="Check how long the bot has been online.")
    async def uptime(self, interaction: discord.Interaction):
        """Check how long the bot has been online."""
        now = datetime.datetime.utcnow()
        delta = now - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        await interaction.response.send_message(f"🕒 Uptime: {hours}h {minutes}m {seconds}s")

    @app_commands.command(name="afk", description="Set your AFK status.")
    async def afk(self, interaction: discord.Interaction, reason: str = "AFK"):
        """Set your AFK status."""
        self.afk_users[interaction.user.id] = reason
        await interaction.response.send_message(f"{interaction.user.mention} is now AFK: {reason}")

    @app_commands.command(name="verify", description="Bypass restrictions (fake).")
    async def verify(self, interaction: discord.Interaction):
        """Bypass restrictions (fake)."""
        self.verified_users.add(interaction.user.id)
        await interaction.response.send_message("✅ You have been marked as verified.")

    @app_commands.command(name="unverify", description="Remove verification bypass.")
    async def unverify(self, interaction: discord.Interaction):
        """Remove verification bypass."""
        self.verified_users.discard(interaction.user.id)
        await interaction.response.send_message("❌ You are no longer verified.")

    @app_commands.command(name="help", description="Show all commands and their descriptions")
async def slash_help(self, interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 NexuSec Help Menu",
        description="Here are all the available commands and what they do:",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Use these commands to configure NexuSec in your server!")

    # Automod
    embed.add_field(
        name="/antilink",
        value="Enable/disable link filtering; choose punishment (timeout/kick/ban) and duration",
        inline=False
    )
    embed.add_field(
        name="/antispam",
        value="Enable/disable spam filtering; choose punishment (timeout/kick/ban) and duration",
        inline=False
    )

    # Bad word management
    embed.add_field(
        name="/addbadword <word>",
        value="Add a word to the bad‑word list for this server",
        inline=False
    )
    embed.add_field(
        name="/removebadword <word>",
        value="Remove a word from the bad‑word list",
        inline=False
    )
    embed.add_field(
        name="/viewbadwords",
        value="Show all currently blocked words for this server",
        inline=False
    )

    # Moderation
    embed.add_field(name="/ban <user> [reason]", value="Ban a member", inline=False)
    embed.add_field(name="/kick <user> [reason]", value="Kick a member", inline=False)
    embed.add_field(name="/mute <user> [duration]", value="Timeout a member", inline=False)
    embed.add_field(name="/unmute <user>", value="Remove timeout from a member", inline=False)
    embed.add_field(name="/warn <user> [reason]", value="Issue a warning", inline=False)
    embed.add_field(name="/warnings <user>", value="View a user’s warnings", inline=False)
    embed.add_field(name="/clear <count>", value="Delete the last N messages", inline=False)

    # Utility / Fun
    embed.add_field(name="/ping", value="Check bot latency", inline=False)
    embed.add_field(name="/userinfo [user]", value="Get info about a user", inline=False)
    embed.add_field(name="/serverinfo", value="Get info about this server", inline=False)
    embed.add_field(name="/roles", value="List all server roles", inline=False)
    embed.add_field(name="/roleinfo <role>", value="Get info on a role", inline=False)
    embed.add_field(name="/avatar [user]", value="Show a user’s avatar", inline=False)
    embed.add_field(name="/uptime", value="Show how long the bot has been online", inline=False)
    embed.add_field(name="/afk [reason]", value="Set yourself as AFK", inline=False)
    embed.add_field(name="/verify", value="Mark yourself as verified (fake)", inline=False)
    embed.add_field(name="/unverify", value="Remove your verification bypass", inline=False)
    embed.add_field(name="/poll <question>", value="Create a quick yes/no poll", inline=False)
    embed.add_field(name="/giveaway <prize>", value="Start a giveaway", inline=False)
    embed.add_field(name="/announce <message>", value="Send an announcement", inline=False)
    embed.add_field(name="/welcome <channel>", value="Configure welcome messages", inline=False)
    embed.add_field(name="/autoroles <role>", value="Set up auto‑roles for new members", inline=False)
    embed.add_field(name="/custom add/delete/list", value="Manage custom commands", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Utility(bot))
