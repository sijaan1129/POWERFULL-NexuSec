import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show all commands and their descriptions")
    async def help(self, ctx):
        embed = discord.Embed(title="📖 NexuSec Help Menu", description="Here are all the available commands:", color=discord.Color.blurple())
        embed.set_footer(text="NexuSec - The Ultimate Discord Security Bot")

        # Automod section
        embed.add_field(
            name="🛡️ /antilink",
            value="Configure Anti-Link system: enable/disable, punishment (timeout/kick/ban), duration.",
            inline=False
        )
        embed.add_field(
            name="🛡️ /antispam",
            value="Configure Anti-Spam system: enable/disable, punishment (timeout/kick/ban), duration.",
            inline=False
        )

        # Moderation commands
        embed.add_field(name="🔨 !ban", value="Ban a user from the server.", inline=True)
        embed.add_field(name="👢 !kick", value="Kick a user from the server.", inline=True)
        embed.add_field(name="🔇 !mute", value="Mute a user with a timeout.", inline=True)
        embed.add_field(name="🔊 !unmute", value="Remove a user's timeout.", inline=True)
        embed.add_field(name="⚠️ !warn", value="Issue a warning to a user.", inline=True)
        embed.add_field(name="📋 !warnings", value="Check a user's warnings.", inline=True)
        embed.add_field(name="🧹 !clear", value="Delete messages from a channel.", inline=True)

        # Fun/utility commands
        embed.add_field(name="📢 !say", value="Make the bot say something.", inline=True)
        embed.add_field(name="🗳️ !poll", value="Create a simple yes/no poll.", inline=True)
        embed.add_field(name="🎁 !giveaway", value="Start a giveaway event.", inline=True)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
