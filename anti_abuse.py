import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import asyncio

class AntiAbuse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antispam_enabled = False
        self.antilink_enabled = False
        self.punishment_type = "timeout"  # Default punishment
        self.timeout_duration = 5  # Default timeout duration in minutes

    # Command to enable or disable anti-spam
    @app_commands.command(name="antispam", description="Enable or disable anti-spam with punishment selection.")
    @app_commands.describe(enable="Enable or disable anti-spam", punishment="Choose punishment for spammer")
    async def antispam(self, interaction: discord.Interaction, enable: bool, punishment: str):
        self.antispam_enabled = enable
        self.punishment_type = punishment
        await interaction.response.send_message(f"Anti-spam has been {'enabled' if enable else 'disabled'} with punishment set to {punishment}.")
    
    # Command to enable or disable anti-link
    @app_commands.command(name="antilink", description="Enable or disable anti-link with punishment selection.")
    @app_commands.describe(enable="Enable or disable anti-link", punishment="Choose punishment for link spammers")
    async def antilink(self, interaction: discord.Interaction, enable: bool, punishment: str):
        self.antilink_enabled = enable
        self.punishment_type = punishment
        await interaction.response.send_message(f"Anti-link has been {'enabled' if enable else 'disabled'} with punishment set to {punishment}.")
    
    # Punishment Application based on settings
    async def apply_punishment(self, member, punishment_type):
        if punishment_type == "timeout":
            await member.timeout(timedelta(minutes=self.timeout_duration))
            await member.send(f"You have been timed out for {self.timeout_duration} minutes due to rule violations.")
        elif punishment_type == "kick":
            await member.kick()
            await member.send("You have been kicked for violating server rules.")
        elif punishment_type == "ban":
            await member.ban()
            await member.send("You have been banned for violating server rules.")
        else:
            await member.send("Unknown punishment.")

    # Event to detect messages with links (antilink system)
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.antilink_enabled and any(url in message.content for url in ["http", "www", ".com"]):
            if message.author.bot:
                return
            # Apply punishment based on user settings
            await self.apply_punishment(message.author, self.punishment_type)
            await message.delete()
            await message.channel.send(f"🔗 {message.author.mention} was punished for posting a link!")

    # Event to detect rapid messages (antispam system)
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.antispam_enabled:
            user = message.author
            # Your anti-spam logic, such as rapid message detection (5 messages in 5 seconds)
            if user not in self.message_timers:
                self.message_timers[user] = 0
            self.message_timers[user] += 1

            # If user sends 5 messages within 5 seconds
            if self.message_timers[user] >= 5:
                await self.apply_punishment(user, self.punishment_type)
                await message.delete()
                await message.channel.send(f"🚫 {user.mention} was punished for spamming!")
            await asyncio.sleep(1)

    @app_commands.command(name="settimeout", description="Set timeout duration in minutes.")
    async def settimeout(self, interaction: discord.Interaction, duration: int):
        self.timeout_duration = duration
        await interaction.response.send_message(f"Timeout duration has been set to {duration} minutes.")

async def setup(bot):
    await bot.add_cog(AntiAbuse(bot))
