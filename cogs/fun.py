import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
import datetime

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaways = {}

    @app_commands.command(name="poll", description="Create a quick poll with yes/no reactions.")
    async def poll(self, interaction: discord.Interaction, question: str):
        embed = discord.Embed(title="📊 Poll", description=question, color=discord.Color.blurple())
        embed.set_footer(text=f"Poll by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        message = await interaction.channel.send(embed=embed)
        await message.add_reaction("👍")
        await message.add_reaction("👎")
        await interaction.response.send_message("✅ Poll created!", ephemeral=True)

    @app_commands.command(name="giveaway", description="Start a simple giveaway.")
    async def giveaway(
        self,
        interaction: discord.Interaction,
        duration: int,
        prize: str,
        winners: int = 1
    ):
        embed = discord.Embed(
            title="🎉 Giveaway!",
            description=f"**Prize:** {prize}\nReact with 🎉 to enter!\n**Ends in:** {duration} seconds",
            color=discord.Color.random()
        )
        embed.set_footer(text=f"Hosted by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        message = await interaction.channel.send(embed=embed)
        await message.add_reaction("🎉")

        self.giveaways[message.id] = {
            "message": message,
            "prize": prize,
            "host": interaction.user,
            "end_time": datetime.datetime.utcnow() + datetime.timedelta(seconds=duration),
            "winners": winners
        }

        await interaction.response.send_message(f"✅ Giveaway for **{prize}** started!", ephemeral=True)
        await asyncio.sleep(duration)

        # Fetch updated message to get all reactions
        message = await interaction.channel.fetch_message(message.id)
        users = await message.reactions[0].users().flatten()
        users = [u for u in users if not u.bot]

        if len(users) == 0:
            await interaction.channel.send("❌ No valid entries, no winner.")
            return

        winners_list = random.sample(users, min(winners, len(users)))
        winner_mentions = ", ".join(w.mention for w in winners_list)

        await interaction.channel.send(f"🎉 Congratulations {winner_mentions}! You won **{prize}**!")

async def setup(bot):
    await bot.add_cog(Fun(bot))
