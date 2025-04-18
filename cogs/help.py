# cogs/help.py
import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Show all commands and their descriptions"
    )
    async def slash_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 NexuSec Help Menu",
            description="Here’s a list of all available commands:",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Use these to configure NexuSec in your server")

        # — Automod —
        embed.add_field(
            name="/antilink",
            value="Enable/disable link filtering; pick punishment (timeout/kick/ban) and duration",
            inline=False
        )
        embed.add_field(
            name="/antispam",
            value="Enable/disable spam filtering; pick punishment (timeout/kick/ban) and duration",
            inline=False
        )

        # — Bad-Word Management —
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

        # — Moderation —
        embed.add_field(name="/ban <user> [reason]", value="Ban a member", inline=False)
        embed.add_field(name="/kick <user> [reason]", value="Kick a member", inline=False)
        embed.add_field(name="/mute <user> <minutes>", value="Timeout a member", inline=False)
        embed.add_field(name="/unmute <user>", value="Remove timeout", inline=False)
        embed.add_field(name="/warn <user> [reason]", value="Issue a warning", inline=False)
        embed.add_field(name="/warnings <user>", value="View a user’s warnings", inline=False)
        embed.add_field(name="/clear <count>", value="Delete the last N messages", inline=False)

        # — Utility & Fun —
        embed.add_field(name="/ping", value="Check bot latency", inline=False)
        embed.add_field(name="/userinfo [user]", value="Get information about a user", inline=False)
        embed.add_field(name="/serverinfo", value="Get information about this server", inline=False)
        embed.add_field(name="/roles", value="List all server roles", inline=False)
        embed.add_field(name="/roleinfo <role>", value="Get info on a specific role", inline=False)
        embed.add_field(name="/avatar [user]", value="Show a user’s avatar", inline=False)
        embed.add_field(name="/uptime", value="How long the bot has been online", inline=False)
        embed.add_field(name="/afk [reason]", value="Set your AFK status", inline=False)
        embed.add_field(name="/verify", value="Mark yourself as verified (fake)", inline=False)
        embed.add_field(name="/unverify", value="Remove your verification bypass", inline=False)
        embed.add_field(name="/poll <question>", value="Create a yes/no poll", inline=False)
        embed.add_field(name="/giveaway <prize>", value="Start a giveaway", inline=False)
        embed.add_field(name="/announce <message>", value="Send an announcement", inline=False)
        embed.add_field(name="/welcome <channel>", value="Configure welcome messages", inline=False)
        embed.add_field(name="/autoroles <role>", value="Set up auto‑roles", inline=False)
        embed.add_field(name="/custom add/delete/list", value="Manage custom commands", inline=False)

        # Send exactly one response
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
