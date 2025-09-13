import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from datetime import datetime

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_commands = set()

    # Slash command
    @app_commands.command(name="userinfo", description="Get information about a user.")
    @app_commands.describe(user="The user you want info about (optional).")
    async def userinfo_slash(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        user = user or interaction.user
        embed = await self.create_userinfo_embed(user, requester=interaction.user)
        await interaction.response.send_message(embed=embed)

    # Prefix command (.us)
    @commands.command(name="us", help="Get information about a user")
    async def userinfo_prefix(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        if ctx.message.id in self.active_commands:
            return

        self.active_commands.add(ctx.message.id)
        try:
            member = member or ctx.author
            embed = await self.create_userinfo_embed(member, requester=ctx.author)
            await ctx.send(embed=embed)
        finally:
            self.active_commands.discard(ctx.message.id)

    # Embed builder
    async def create_userinfo_embed(self, user: discord.Member, requester: discord.User) -> discord.Embed:
        roles = [role.mention for role in user.roles[1:]]  # Exclude @everyone

        embed = discord.Embed(
            title=f"{user}'s Information",
            color=discord.Color.from_rgb(255, 255, 255),  # White
            timestamp=datetime.utcnow()
        )

        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Name", value=f"{user}", inline=True)
        embed.add_field(name="ID", value=f"{user.id}", inline=True)
        embed.add_field(name="Nickname", value=user.nick if user.nick else "None", inline=True)

        embed.add_field(name="Bot", value="Yes" if user.bot else "No", inline=True)
        embed.add_field(name="Account Created", value=user.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.add_field(name="Server Joined", value=user.joined_at.strftime("%d/%m/%Y %H:%M"), inline=True)

        embed.add_field(name="Top Role", value=user.top_role.mention if user.top_role else "None", inline=True)
        embed.add_field(name=f"Roles [{len(roles)}]", value=", ".join(roles) if roles else "None", inline=False)

        embed.add_field(name="Boosting", value="Yes" if user.premium_since else "No", inline=True)
        embed.add_field(name="Voice Channel", value=user.voice.channel.mention if user.voice else "None", inline=True)

        embed.set_footer(text=f"Requested by {requester}", icon_url=requester.display_avatar.url)
        return embed

# Cog loader
async def setup(bot: commands.Bot):
    await bot.add_cog(UserInfo(bot))
