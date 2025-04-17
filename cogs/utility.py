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
        await interaction.response.send_message(f"Pong! 🏓 `{round(self.bot.latency * 1000)}ms`")

    @app_commands.command(name="userinfo", description="Get information about a user.")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
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
        roles = [role.mention for role in interaction.guild.roles if role.name != "@everyone"]
        await interaction.response.send_message("Roles:\n" + ", ".join(roles) if roles else "No roles found.")

    @app_commands.command(name="roleinfo", description="Get info on a specific role.")
    async def roleinfo(self, interaction: discord.Interaction, role: discord.Role):
        embed = discord.Embed(title=f"Role Info - {role.name}", color=role.color)
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Mentionable", value=role.mentionable)
        embed.add_field(name="Members", value=len(role.members))
        embed.add_field(name="Position", value=role.position)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="channelinfo", description="Get info on a specific channel.")
    async def channelinfo(self, interaction: discord.Interaction, channel: discord.abc.GuildChannel):
        embed = discord.Embed(title=f"Channel Info - {channel.name}", color=discord.Color.teal())
        embed.add_field(name="ID", value=channel.id)
        embed.add_field(name="Type", value=str(channel.type).capitalize())
        embed.add_field(name="Created", value=channel.created_at.strftime("%Y-%m-%d %H:%M"))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Get a user's avatar.")
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        await interaction.response.send_message(user.display_avatar.url)

    @app_commands.command(name="uptime", description="Check how long the bot has been online.")
    async def uptime(self, interaction: discord.Interaction):
        now = datetime.datetime.utcnow()
        delta = now - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        await interaction.response.send_message(f"🕒 Uptime: {hours}h {minutes}m {seconds}s")

    @app_commands.command(name="afk", description="Set your AFK status.")
    async def afk(self, interaction: discord.Interaction, reason: str = "AFK"):
        self.afk_users[interaction.user.id] = reason
        await interaction.response.send_message(f"{interaction.user.mention} is now AFK: {reason}")

    @app_commands.command(name="verify", description="Bypass restrictions (fake).")
    async def verify(self, interaction: discord.Interaction):
        self.verified_users.add(interaction.user.id)
        await interaction.response.send_message("✅ You have been marked as verified.")

    @app_commands.command(name="unverify", description="Remove verification bypass.")
    async def unverify(self, interaction: discord.Interaction):
        self.verified_users.discard(interaction.user.id)
        await interaction.response.send_message("❌ You are no longer verified.")

    @app_commands.command(name="help", description="Show all available commands.")
async def help(self, interaction: discord.Interaction):
    embed = discord.Embed(title="🤖 NexuSec Help Menu", color=discord.Color.blue())

    # Moderation commands
    embed.add_field(name="🛡️ Moderation", value="`/ban` - Ban a member\n`/kick` - Kick a member\n`/mute` - Mute a member\n`/warn` - Warn a member\n`/lock` - Lock a channel", inline=False)

    # AutoMod commands
    embed.add_field(name="⚙️ AutoMod", value="`/antispam` - Configure anti-spam settings\n`/antilink` - Configure anti-link settings\n`/addbadword` - Add a word to the bad word filter\n`/removebadword` - Remove a word from the bad word filter\n`/badwords` - View the list of blacklisted words", inline=False)

    # Utility commands
    embed.add_field(name="🧰 Utility", value="`/ping` - Check the bot's latency\n`/userinfo` - Get information about a user\n`/uptime` - Check how long the bot has been online\n`/afk` - Set your AFK status\n`/verify` - Mark yourself as verified (bypass restrictions)\n`/unverify` - Remove verification bypass", inline=False)

    # Announcement commands
    embed.add_field(name="📢 Announcement", value="`/announce` - Send an announcement\n`/welcome` - Set up welcome messages\n`/log` - Set up logging channels\n`/autoroles` - Configure auto roles for new members", inline=False)

    # Fun commands
    embed.add_field(name="🎉 Fun", value="`/poll` - Create a poll\n`/giveaway` - Create a giveaway", inline=False)

    # Custom commands
    embed.add_field(name="💬 Custom Commands", value="`/custom add` - Add a custom command\n`/custom delete` - Delete a custom command\n`/custom list` - List all custom commands", inline=False)

    await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
