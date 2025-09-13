import discord
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
client = AsyncIOMotorClient("your_mongodb_connection_url")
db = client["nexusec"]["guilds"]

# Permission check
async def has_permission(interaction: discord.Interaction):
    return interaction.user.guild_permissions.ban_members

# Role hierarchy checks
async def bot_has_higher_role(interaction: discord.Interaction, target: discord.Member):
    return interaction.guild.me.top_role > target.top_role

async def user_has_higher_role(interaction: discord.Interaction, target: discord.Member):
    return interaction.user.top_role > target.top_role

# Modlog embed sender
async def send_modlog(interaction: discord.Interaction, action: str, target: discord.Member, reason: str):
    guild_data = await db.find_one({"_id": str(interaction.guild.id)})
    if guild_data and guild_data.get("modlog_enabled"):
        channel_id = guild_data.get("modlog_channel")
        if channel_id:
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="🔒 Moderation Action",
                    description=f"**Action:** {action}\n**Target:** {target.mention}\n**Reason:** {reason}",
                    color=discord.Color.orange()
                )
                embed.set_footer(text=f"Moderator: {interaction.user}")
                await channel.send(embed=embed)

# ✅ is_verified: checks if the member has the "verified" role
async def is_verified(member: discord.Member):
    guild_data = await db.find_one({"_id": str(member.guild.id)})
    if not guild_data or "verified_role" not in guild_data:
        return False

    role_id = guild_data["verified_role"]
    role = member.guild.get_role(role_id)
    return role in member.roles

# ✅ should_skip: for automod whitelisting (antilink, antispam, etc.)
async def should_skip(guild_id: int, user_id: int, feature: str) -> bool:
    doc = await db.find_one({"_id": str(guild_id)})
    if doc:
        whitelist = doc.get(f"{feature}_whitelist", [])
        return str(user_id) in whitelist
    return False

# General Embed Helper Function
def create_embed(title: str, description: str, color: discord.Color):
    return discord.Embed(title=title, description=description, color=color)

# Embed helper functions

def permission_error():
    return create_embed("Permission Denied", "🚫 You don't have permission to use this command.", discord.Color.red())

def role_error():
    return create_embed("Role Error", "🚫 You can't take action on this member due to role hierarchy.", discord.Color.red())

def bot_role_error():
    return create_embed("Bot Role Error", "🚫 I don't have a high enough role to take action on this member.", discord.Color.red())

def error_embed(msg: str):
    return create_embed("Error", f"❌ {msg}", discord.Color.red())

# Additional helper for checking guild data presence
async def get_guild_data(guild_id: int):
    guild_data = await db.find_one({"_id": str(guild_id)})
    if not guild_data:
        return None
    return guild_data
