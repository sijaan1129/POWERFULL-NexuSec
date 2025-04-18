# cogs/help.py
import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all commands and their descriptions")
    async def slash_help(self, interaction: discord.Interaction):
        # (embed code from above)
        ...

async def setup(bot):
    await bot.add_cog(Help(bot))
