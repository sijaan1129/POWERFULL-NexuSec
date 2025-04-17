import discord
from discord.ext import commands
from discord import app_commands

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.custom_commands = {}  # guild_id: {command_name: response}

    @app_commands.command(name="custom_add", description="Add a custom command.")
    async def custom_add(self, interaction: discord.Interaction, name: str, response: str):
        guild_id = interaction.guild.id
        if guild_id not in self.custom_commands:
            self.custom_commands[guild_id] = {}

        self.custom_commands[guild_id][name.lower()] = response
        await interaction.response.send_message(f"✅ Custom command `{name}` added.")

    @app_commands.command(name="custom_delete", description="Delete a custom command.")
    async def custom_delete(self, interaction: discord.Interaction, name: str):
        guild_id = interaction.guild.id
        if name.lower() in self.custom_commands.get(guild_id, {}):
            del self.custom_commands[guild_id][name.lower()]
            await interaction.response.send_message(f"🗑️ Custom command `{name}` deleted.")
        else:
            await interaction.response.send_message("❌ That command doesn't exist.")

    @app_commands.command(name="custom_list", description="List all custom commands.")
    async def custom_list(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        commands_list = self.custom_commands.get(guild_id, {})
        if commands_list:
            embed = discord.Embed(title="💬 Custom Commands", color=discord.Color.purple())
            for name in commands_list:
                embed.add_field(name=name, value=commands_list[name], inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("📭 No custom commands found.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = message.guild.id
        command_name = message.content.lower().lstrip("!")

        if guild_id in self.custom_commands:
            response = self.custom_commands[guild_id].get(command_name)
            if response:
                await message.channel.send(response)

async def setup(bot):
    await bot.add_cog(CustomCommands(bot))
