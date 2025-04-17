import discord
from discord.ext import commands

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.whitelist = {}  # Store whitelisted users and roles

    def is_whitelisted(self, guild_id, member_or_role):
        """Check if user or role is whitelisted."""
        guild_whitelist = self.whitelist.get(guild_id, {"users": [], "roles": []})
        return member_or_role.id in guild_whitelist["users"] or any(role.id in guild_whitelist["roles"] for role in member_or_role.roles)

    @commands.command(name="whitelist", help="Whitelist a user or role.")
    async def whitelist(self, ctx, member_or_role: discord.abc.Snowflake):
        """Add user or role to whitelist."""
        guild_id = ctx.guild.id
        if isinstance(member_or_role, discord.Member):
            self.whitelist.setdefault(guild_id, {"users": [], "roles": []})["users"].append(member_or_role.id)
            await ctx.send(f"{member_or_role} has been added to the whitelist.")
        elif isinstance(member_or_role, discord.Role):
            self.whitelist.setdefault(guild_id, {"users": [], "roles": []})["roles"].append(member_or_role.id)
            await ctx.send(f"{member_or_role} role has been added to the whitelist.")
        else:
            await ctx.send("Please provide a valid user or role.")

    @commands.command(name="removewhitelist", help="Remove a user or role from the whitelist.")
    async def remove_whitelist(self, ctx, member_or_role: discord.abc.Snowflake):
        """Remove user or role from whitelist."""
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

    @commands.command(name="viewwhitelist", help="View the current whitelist.")
    async def view_whitelist(self, ctx):
        """View the current whitelist for users and roles."""
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
