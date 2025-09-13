import discord
from typing import Union
from utils.mongo import get_guild_config

CHECK_EMOJI = "<:check:1372502146984968232>"
CROSS_EMOJI = "<:cross:1372502832695087147>"

async def is_whitelisted(guild: discord.Guild, target: Union[discord.Member, discord.Role], system: str) -> bool:
    """
    Check if a user/role is whitelisted for specific protection system
    system: protection system key (e.g., "antibot", "antispam")
    """
    config = await get_guild_config(guild.id)
    whitelist = config.get("whitelist", {})
    
    # Check user directly
    if isinstance(target, discord.Member):
        user_id = f"user_{target.id}"
        if user_id in whitelist:
            if "all" in whitelist[user_id] or system in whitelist[user_id]:
                return True
        
        # Check roles
        for role in target.roles:
            role_id = f"role_{role.id}"
            if role_id in whitelist:
                if "all" in whitelist[role_id] or system in whitelist[role_id]:
                    return True
    
    # Check role directly
    elif isinstance(target, discord.Role):
        role_id = f"role_{target.id}"
        if role_id in whitelist:
            if "all" in whitelist[role_id] or system in whitelist[role_id]:
                return True
    
    return False
