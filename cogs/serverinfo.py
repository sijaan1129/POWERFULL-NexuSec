import discord
from discord.ext import commands
from discord import app_commands
from datetime import timezone

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_commands = set()

    # Optional check for aimbot (replace or customize this)
    async def check_if_aimbot(self, user: discord.User) -> bool:
        return True  # You can change this to a real permission check if needed

    # Slash command
    @app_commands.command(name="serverinfo", description="Get information about this server.")
    async def slash_serverinfo(self, interaction: discord.Interaction):
        try:
            guild = interaction.guild
            embed = await self.build_embed(guild)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message("❌ Something went wrong.", ephemeral=True)
            print(f"[ERROR] /serverinfo: {e}")

    # Prefix command using new format like roast_prefix
    @commands.command(name="serverinfo", aliases=["serv"], help="Show server information")
    async def prefix_serverinfo(self, ctx: commands.Context):
        if await self.check_if_aimbot(ctx.author):
            if ctx.message.id in self.active_commands:
                return
            self.active_commands.add(ctx.message.id)
            try:
                guild = ctx.guild
                embed = await self.build_embed(guild)
                await ctx.send(embed=embed)
            except Exception as e:
                await ctx.send("❌ Something went wrong.")
                print(f"[ERROR] .serverinfo/.serv: {e}")
            finally:
                self.active_commands.discard(ctx.message.id)
        else:
            embed = self.create_permission_error_embed()
            await ctx.send(embed=embed)

    # Embed builder
    async def build_embed(self, guild: discord.Guild) -> discord.Embed:
        owner = guild.owner or guild.get_member(guild.owner_id)
        owner_name = f"{owner.name}#{owner.discriminator}" if owner else "Unknown"
        created_at = guild.created_at.replace(tzinfo=timezone.utc).astimezone()
        tier = guild.premium_tier
        boosts = guild.premium_subscription_count

        category_channels = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)

        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.from_rgb(255, 255, 255)
        )
        embed.set_author(name="Server Info")
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

        embed.add_field(name="Owner", value=owner_name, inline=True)
        embed.add_field(name="Members", value=f"{guild.member_count:,}", inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)

        embed.add_field(name="Category Channels", value=str(category_channels), inline=True)
        embed.add_field(name="Text Channels", value=str(text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=str(voice_channels), inline=True)

        embed.add_field(name="Boost Count", value=f"{boosts} Boosts (Tier {tier})", inline=False)

        if guild.banner:
            embed.set_image(url=guild.banner.url)

        embed.set_footer(
            text=f"ID: {guild.id} | Server Created • {created_at.strftime('%d/%m/%Y %H:%M')}"
        )

        return embed

    # Optional permission error embed
    def create_permission_error_embed(self) -> discord.Embed:
        return discord.Embed(
            description="🚫 Permission Denied - You are not authorized to use this command.",
            color=discord.Color.red()
        )

# Required to load the cog
async def setup(bot: commands.Bot):
    await bot.add_cog(ServerInfo(bot))
