import discord
from discord.ext import commands
from discord.ui import Select, View

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.whitelist = {}

    # Helper function to check if a user/role is whitelisted
    def is_whitelisted(self, guild_id, member_or_role):
        guild_whitelist = self.whitelist.get(guild_id, {"users": [], "roles": []})
        return member_or_role.id in guild_whitelist["users"] or any(role.id in guild_whitelist["roles"] for role in member_or_role.roles)

    # Command to add a user or role to the whitelist
    @commands.command(name="whitelist", help="Whitelist a user or role to bypass anti-spam/anti-link.")
    async def whitelist(self, ctx, member_or_role: discord.abc.Snowflake):
        guild_id = ctx.guild.id
        # Check if it's a user or a role
        if isinstance(member_or_role, discord.Member):
            self.whitelist.setdefault(guild_id, {"users": [], "roles": []})["users"].append(member_or_role.id)
            await ctx.send(f"{member_or_role} has been added to the whitelist.")
        elif isinstance(member_or_role, discord.Role):
            self.whitelist.setdefault(guild_id, {"users": [], "roles": []})["roles"].append(member_or_role.id)
            await ctx.send(f"{member_or_role} role has been added to the whitelist.")
        else:
            await ctx.send("Please provide a valid user or role.")

    # Command to remove a user or role from the whitelist
    @commands.command(name="removewhitelist", help="Remove a user or role from the whitelist.")
    async def remove_whitelist(self, ctx, member_or_role: discord.abc.Snowflake):
        guild_id = ctx.guild.id
        if isinstance(member_or_role, discord.Member):
            if member_or_role.id in self.whitelist.get(guild_id, {}).get("users", []):
                self.whitelist[guild_id]["users"].remove(member_or_role.id)
                await ctx.send(f"{member_or_role} has been removed from the whitelist.")
            else:
                await ctx.send(f"{member_or_role} is not on the whitelist.")
        elif isinstance(member_or_role, discord.Role):
            if member_or_role.id in self.whitelist.get(guild_id, {}).get("roles", []):
                self.whitelist[guild_id]["roles"].remove(member_or_role.id)
                await ctx.send(f"{member_or_role} role has been removed from the whitelist.")
            else:
                await ctx.send(f"{member_or_role} role is not on the whitelist.")
        else:
            await ctx.send("Please provide a valid user or role.")

    # Command to view the current whitelist
    @commands.command(name="viewwhitelist", help="View the current whitelist for users and roles.")
    async def view_whitelist(self, ctx):
        guild_id = ctx.guild.id
        guild_whitelist = self.whitelist.get(guild_id, {"users": [], "roles": []})
        users = [f"<@{user_id}>" for user_id in guild_whitelist["users"]]
        roles = [f"<@&{role_id}>" for role_id in guild_whitelist["roles"]]
        
        if users or roles:
            await ctx.send(f"Whitelisted Users: {', '.join(users) if users else 'None'}\nWhitelisted Roles: {', '.join(roles) if roles else 'None'}")
        else:
            await ctx.send("No users or roles are currently whitelisted.")

async def setup(bot):
    await bot.add_cog(Whitelist(bot))
