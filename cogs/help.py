import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all commands and their descriptions")
    async def slash_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 NexuSec Help Menu",
            description="Here are all available commands organized by category:",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="NexuSec - Your server's security companion")

        # Automod
        embed.add_field(
            name="🛡️ Automod",
            value="`/antilink`, `/antispam`",
            inline=False
        )

        # Bad Words
        embed.add_field(
            name="🚫 Bad Words",
            value="`/addbadword`, `/removebadword`, `/viewbadwords`",
            inline=False
        )

        # Moderation
        embed.add_field(
            name="🔨 Moderation",
            value="`/ban`, `/kick`, `/mute`, `/unmute`, `/warn`, `/warnings`, `/clear`",
            inline=False
        )

        # Utility
        embed.add_field(
            name="🧰 Utility",
            value="`/ping`, `/userinfo`, `/serverinfo`, `/roles`, `/roleinfo`, `/avatar`, `/uptime`, `/afk`, `/verify`, `/unverify`",
            inline=False
        )

        # Fun
        embed.add_field(
            name="🎉 Fun",
            value="`/poll`, `/giveaway`",
            inline=False
        )

        # Announcements
        embed.add_field(
            name="📢 Announcements",
            value="`/announce`, `/welcome`, `/autoroles`",
            inline=False
        )

        # Custom Commands
        embed.add_field(
            name="💬 Custom Commands",
            value="`/custom add`, `/custom delete`, `/custom list`",
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
