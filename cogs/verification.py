
import discord
from discord.ext import commands
from discord import app_commands
from utils.mongo import db
import random
import traceback
from typing import Optional

CHECK_EMOJI = "<:check:1372502146984968232>"
CROSS_EMOJI = "<:cross:1372502832695087147>"

class SetupModal(discord.ui.Modal):
    def __init__(self, parent_view):
        super().__init__(title="Set Verification Embed", timeout=600)
        self.parent_view = parent_view

        self.title_input = discord.ui.TextInput(
            label="Embed Title",
            placeholder="Verification Required",
            default=parent_view.embed.title if parent_view.embed else None,
            max_length=256,
            required=True
        )
        self.description_input = discord.ui.TextInput(
            label="Embed Description",
            style=discord.TextStyle.long,
            default=parent_view.embed.description if parent_view.embed else None,
            required=True
        )
        self.color_input = discord.ui.TextInput(
            label="Embed Color (HEX)",
            placeholder="FFFFFF",
            default=hex(parent_view.embed.color.value)[2:] if parent_view.embed and parent_view.embed.color else None,
            max_length=6,
            required=True
        )
        self.banner_url_input = discord.ui.TextInput(
            label="Banner Image URL (optional)",
            default=parent_view.embed.image.url if parent_view.embed and parent_view.embed.image else None,
            required=False
        )
        self.icon_url_input = discord.ui.TextInput(
            label="Icon URL (optional)",
            default=parent_view.embed.thumbnail.url if parent_view.embed and parent_view.embed.thumbnail else None,
            required=False
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.color_input)
        self.add_item(self.banner_url_input)
        self.add_item(self.icon_url_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Validate color
            try:
                color_str = self.color_input.value.strip().lstrip('#')
                color = int(color_str, 16)
                if color < 0 or color > 0xFFFFFF:
                    raise ValueError("Color out of range")
            except ValueError:
                color = 0xFFFFFF  # Default to white if invalid

            # Create embed
            embed = discord.Embed(
                title=self.title_input.value,
                description=self.description_input.value,
                color=discord.Color(color)
            )

            # Set image if provided
            banner_url = self.banner_url_input.value.strip()
            if banner_url and banner_url.lower() != 'none':
                if not banner_url.startswith(('http://', 'https://')):
                    raise ValueError("Banner URL must start with http:// or https://")
                embed.set_image(url=banner_url)

            # Set thumbnail if provided
            icon_url = self.icon_url_input.value.strip()
            if icon_url and icon_url.lower() != 'none':
                if not icon_url.startswith(('http://', 'https://')):
                    raise ValueError("Icon URL must start with http:// or https://")
                embed.set_thumbnail(url=icon_url)

            # Update view and database
            self.parent_view.embed = embed

            await db.verify_config.update_one(
                {"_id": str(interaction.guild.id)},
                {"$set": {
                    "embed": {
                        "title": embed.title,
                        "description": embed.description,
                        "color": hex(embed.color.value),
                        "banner_url": banner_url if banner_url else None,
                        "icon_url": icon_url if icon_url else None
                    }
                }},
                upsert=True
            )

            if interaction.response.is_done():
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self.parent_view)
            else:
                await interaction.response.edit_message(embed=embed, view=self.parent_view)
            
        except Exception as e:
            traceback.print_exc()
            error_msg = f"{CROSS_EMOJI} Failed to update embed: {str(e)}"
            if isinstance(e, ValueError):
                error_msg = f"{CROSS_EMOJI} Invalid input: {str(e)}"
            
            if interaction.response.is_done():
                await interaction.followup.send(error_msg, ephemeral=True)
            else:
                await interaction.response.send_message(error_msg, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        traceback.print_exc()
        if interaction.response.is_done():
            await interaction.followup.send(
                f"{CROSS_EMOJI} An unexpected error occurred while processing the modal.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"{CROSS_EMOJI} An unexpected error occurred while processing the modal.",
                ephemeral=True
            )


class ChannelSelect(discord.ui.Select):
    def __init__(self, parent_view):
        options = [
            discord.SelectOption(
                label=channel.name,
                value=str(channel.id),
                description=f"#{channel.name}",
                default=str(channel.id) == str(parent_view.verify_channel.id) if parent_view.verify_channel else False
            )
            for channel in sorted(parent_view.guild.text_channels, key=lambda c: c.position)
            if channel.permissions_for(parent_view.guild.me).send_messages
        ][:25]

        super().__init__(
            placeholder="Select Verification Channel",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="verification:channel_select"
        )
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        try:
            if interaction.user != self.parent_view.interaction.user:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} You cannot use this menu.",
                    ephemeral=True
                )

            channel_id = int(self.values[0])
            channel = self.parent_view.guild.get_channel(channel_id)
            
            if not channel:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} Channel not found.",
                    ephemeral=True
                )

            if not channel.permissions_for(self.parent_view.guild.me).send_messages:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} I don't have permission to send messages in that channel.",
                    ephemeral=True
                )

            self.parent_view.verify_channel = channel

            await db.verify_config.update_one(
                {"_id": str(interaction.guild.id)},
                {"$set": {"channel_id": channel.id}},
                upsert=True
            )

            embed = self.parent_view.embed or discord.Embed(
                title="Verification Setup",
                description="Configure your verification system using the buttons below.",
                color=discord.Color.light_gray()
            )

            if interaction.response.is_done():
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=self.parent_view)
            else:
                await interaction.response.edit_message(embed=embed, view=self.parent_view)
            
        except Exception as e:
            traceback.print_exc()
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"{CROSS_EMOJI} An error occurred while selecting the channel: {str(e)}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{CROSS_EMOJI} An error occurred while selecting the channel: {str(e)}",
                    ephemeral=True
                )


class SetupView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=600)
        self.interaction = interaction
        self.guild = interaction.guild
        self.embed = None
        self.verify_channel = None
        self.loaded = False

    async def load_config(self):
        if self.loaded:
            return
            
        config = await db.verify_config.find_one({"_id": str(self.guild.id)})
        if config:
            if "embed" in config:
                embed_data = config["embed"]
                try:
                    color = int(embed_data["color"].lstrip("#"), 16)
                except (ValueError, KeyError):
                    color = 0xFFFFFF
                    
                self.embed = discord.Embed(
                    title=embed_data.get("title", "Verification Required"),
                    description=embed_data.get("description", "Please verify to access the server."),
                    color=discord.Color(color)
                )
                
                if "banner_url" in embed_data and embed_data["banner_url"]:
                    self.embed.set_image(url=embed_data["banner_url"])
                if "icon_url" in embed_data and embed_data["icon_url"]:
                    self.embed.set_thumbnail(url=embed_data["icon_url"])
            
            if "channel_id" in config:
                channel = self.guild.get_channel(config["channel_id"])
                if channel:
                    self.verify_channel = channel
        
        self.loaded = True

    @discord.ui.button(label="Set Embed", style=discord.ButtonStyle.secondary, custom_id="verification:set_embed")
    async def set_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user != self.interaction.user:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} You cannot use this button.",
                    ephemeral=True
                )

            await self.load_config()
            await interaction.response.send_modal(SetupModal(self))
            
        except Exception as e:
            traceback.print_exc()
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"{CROSS_EMOJI} Failed to open embed editor: {str(e)}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{CROSS_EMOJI} Failed to open embed editor: {str(e)}",
                    ephemeral=True
                )

    @discord.ui.button(label="Set Channel", style=discord.ButtonStyle.secondary, custom_id="verification:set_channel")
    async def set_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user != self.interaction.user:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} You cannot use this button.",
                    ephemeral=True
                )

            await self.load_config()
            
            select = ChannelSelect(self)
            temp_view = discord.ui.View(timeout=300)
            temp_view.add_item(select)
            
            embed = discord.Embed(
                title="Select Verification Channel",
                description="Choose the channel where verification messages will be sent.",
                color=discord.Color.blue()
            )
            
            if interaction.response.is_done():
                await interaction.followup.edit_message(interaction.message.id, embed=embed, view=temp_view)
            else:
                await interaction.response.edit_message(embed=embed, view=temp_view)
            
        except Exception as e:
            traceback.print_exc()
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"{CROSS_EMOJI} Failed to open channel selector: {str(e)}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{CROSS_EMOJI} Failed to open channel selector: {str(e)}",
                    ephemeral=True
                )

    @discord.ui.button(label="Finish Setup", style=discord.ButtonStyle.success, custom_id="verification:finish_setup")
    async def finish_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user != self.interaction.user:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} You cannot use this button.",
                    ephemeral=True
                )

            if not self.embed:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} Please set up the embed first.",
                    ephemeral=True
                )

            if not self.verify_channel:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} Please select a verification channel first.",
                    ephemeral=True
                )

            # Check if we have permission to manage roles
            if not self.guild.me.guild_permissions.manage_roles:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} I need the 'Manage Roles' permission to set up verification.",
                    ephemeral=True
                )

            # Create or get roles
            unverified_role = discord.utils.get(self.guild.roles, name="Unverified")
            verified_role = discord.utils.get(self.guild.roles, name="Verified")

            try:
                if not unverified_role:
                    unverified_role = await self.guild.create_role(
                        name="Unverified",
                        color=discord.Color.dark_grey(),
                        reason="Verification system setup",
                        permissions=discord.Permissions.none()
                    )
                
                if not verified_role:
                    verified_role = await self.guild.create_role(
                        name="Verified",
                        color=discord.Color.green(),
                        reason="Verification system setup"
                    )
                
                # Ensure our bot is above these roles to assign them
                if self.guild.me.top_role <= unverified_role:
                    await unverified_role.edit(position=self.guild.me.top_role.position - 1)
                if self.guild.me.top_role <= verified_role:
                    await verified_role.edit(position=self.guild.me.top_role.position - 1)
                    
            except discord.Forbidden:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} I don't have permission to create or manage roles.",
                    ephemeral=True
                )
            except discord.HTTPException as e:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} Failed to create roles: {str(e)}",
                    ephemeral=True
                )

            # Save configuration
            try:
                await db.verify_config.update_one(
                    {"_id": str(self.guild.id)},
                    {"$set": {
                        "unverified_role": unverified_role.id,
                        "verified_role": verified_role.id,
                        "channel_id": self.verify_channel.id,
                        "enabled": True  # Auto-enable when setup is complete
                    }},
                    upsert=True
                )
            except Exception as e:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} Failed to save configuration: {str(e)}",
                    ephemeral=True
                )

            # Configure channel permissions
            try:
                # First, reset @everyone permissions in verification channel
                await self.verify_channel.set_permissions(
                    self.guild.default_role,
                    view_channel=False,
                    send_messages=False,
                    read_message_history=False,
                    create_private_threads=False,
                    create_public_threads=False,
                    send_messages_in_threads=False
                )
                
                # Set unverified role permissions for verification channel
                await self.verify_channel.set_permissions(
                    unverified_role,
                    view_channel=True,
                    send_messages=False,
                    read_message_history=True,
                    add_reactions=False,
                    attach_files=False,
                    embed_links=False,
                    create_private_threads=False,
                    create_public_threads=False,
                    send_messages_in_threads=False
                )
                
                # Set verified role permissions for verification channel
                await self.verify_channel.set_permissions(
                    verified_role,
                    view_channel=False,  # Verified can see verification channel
                    send_messages=False,
                    read_message_history=True
                )

                # Disable all other channels for unverified role
                for channel in self.guild.channels:
                    if channel.id != self.verify_channel.id:
                        # Skip categories
                        if isinstance(channel, discord.CategoryChannel):
                            continue
                            
                        # For text channels
                        if isinstance(channel, discord.TextChannel):
                            await channel.set_permissions(
                                unverified_role,
                                view_channel=False,
                                send_messages=False,
                                read_message_history=False,
                                add_reactions=False,
                                attach_files=False,
                                embed_links=False,
                                create_private_threads=False,
                                create_public_threads=False,
                                send_messages_in_threads=False
                            )
                        
                        # For voice channels
                        elif isinstance(channel, discord.VoiceChannel):
                            await channel.set_permissions(
                                unverified_role,
                                view_channel=False,
                                connect=False,
                                speak=False
                            )
                        
                        # Reset verified role permissions to default for all other channels
                        await channel.set_permissions(
                            verified_role,
                            overwrite=None
                        )
                
            except discord.Forbidden:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} I don't have permission to configure channel permissions.",
                    ephemeral=True
                )
            except Exception as e:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} Failed to configure channel permissions: {str(e)}",
                    ephemeral=True
                )

            # Post verification message
            try:
                # First delete any existing verification messages
                async for message in self.verify_channel.history(limit=10):
                    if message.author == self.guild.me:
                        try:
                            await message.delete()
                        except:
                            continue
                
                panel_embed = self.embed.copy()
                panel_embed.set_footer(text="Click the button below to verify.")
                
                view = VerifyButtonView()
                await self.verify_channel.send(embed=panel_embed, view=view)
                
            except discord.Forbidden:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} I don't have permission to send messages in the verification channel.",
                    ephemeral=True
                )
            except Exception as e:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} Failed to post verification message: {str(e)}",
                    ephemeral=True
                )

            # Send success message
            success_embed = discord.Embed(
                title=f"{CHECK_EMOJI} Setup Complete",
                description=(
                    "The verification system has been set up successfully!\n\n"
                    f"- Verification channel: {self.verify_channel.mention}\n"
                    f"- Unverified role: {unverified_role.mention}\n"
                    f"- Verified role: {verified_role.mention}\n\n"
                    "**Permission Summary:**\n"
                    "- Unverified members can ONLY view the verification channel\n"
                    "- Unverified members CANNOT send messages or create threads\n"
                    "- Verified members can access all channels except sending in verification channel"
                ),
                color=discord.Color.green()
            )
            
            # Disable all buttons after setup is complete
            for item in self.children:
                item.disabled = True
            
            if interaction.response.is_done():
                await interaction.followup.edit_message(interaction.message.id, embed=success_embed, view=None)
            else:
                await interaction.response.edit_message(embed=success_embed, view=None)
            
        except Exception as e:
            traceback.print_exc()
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"{CROSS_EMOJI} An unexpected error occurred during setup: {str(e)}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{CROSS_EMOJI} An unexpected error occurred during setup: {str(e)}",
                    ephemeral=True
                )

    async def on_timeout(self):
        try:
            if hasattr(self, 'interaction') and self.interaction:
                await self.interaction.edit_original_response(view=None)
        except:
            pass


class VerifyModal(discord.ui.Modal):
    def __init__(self, code: str):
        super().__init__(title="Enter Verification Code", timeout=600)
        self.code = code

        self.input = discord.ui.TextInput(
            label="Verification Code",
            placeholder=f"Enter the code: {code}",
            min_length=3,
            max_length=10,
            required=True
        )
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if self.input.value.strip() != self.code:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} Incorrect code. Please try again.",
                    ephemeral=True
                )

            config = await db.verify_config.find_one({"_id": str(interaction.guild.id)})
            if not config or not config.get("enabled", False):
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} Verification is not currently enabled in this server.",
                    ephemeral=True
                )

            verified_role = interaction.guild.get_role(config.get("verified_role"))
            unverified_role = interaction.guild.get_role(config.get("unverified_role"))
            
            if not verified_role or not unverified_role:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} The verification system is not properly configured.",
                    ephemeral=True
                )

            # Add verified role and remove unverified role
            try:
                if unverified_role in interaction.user.roles:
                    await interaction.user.remove_roles(unverified_role)
                
                if verified_role not in interaction.user.roles:
                    await interaction.user.add_roles(verified_role)
                    
                await interaction.response.send_message(
                    f"{CHECK_EMOJI} You have been successfully verified!",
                    ephemeral=True
                )
                
            except discord.Forbidden:
                await interaction.response.send_message(
                    f"{CROSS_EMOJI} I don't have permission to manage your roles.",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    f"{CROSS_EMOJI} An error occurred during verification: {str(e)}",
                    ephemeral=True
                )
                
        except Exception as e:
            traceback.print_exc()
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"{CROSS_EMOJI} An unexpected error occurred: {str(e)}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{CROSS_EMOJI} An unexpected error occurred: {str(e)}",
                    ephemeral=True
                )


class VerifyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.success,
        emoji=CHECK_EMOJI,
        custom_id="verification:verify_button"
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Check if verification is enabled
            config = await db.verify_config.find_one({"_id": str(interaction.guild.id)})
            if not config or not config.get("enabled", False):
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} Verification is not currently enabled in this server.",
                    ephemeral=True
                )

            # Check if user is already verified
            verified_role = interaction.guild.get_role(config.get("verified_role"))
            if verified_role and verified_role in interaction.user.roles:
                return await interaction.response.send_message(
                    f"{CHECK_EMOJI} You are already verified!",
                    ephemeral=True
                )

            # Generate and send verification code
            code = str(random.randint(100, 999))
            await interaction.response.send_modal(VerifyModal(code))
            
        except discord.NotFound:
            await interaction.response.send_message(
                f"{CROSS_EMOJI} This button session expired. Please try again.",
                ephemeral=True
            )
        except Exception as e:
            traceback.print_exc()
            error_msg = f"{CROSS_EMOJI} An error occurred: {str(e)}"
            if "interaction failed" in str(e).lower():
                error_msg = f"{CROSS_EMOJI} Please try again. If the problem persists, update your Discord app."
            
            if interaction.response.is_done():
                await interaction.followup.send(error_msg, ephemeral=True)
            else:
                await interaction.response.send_message(error_msg, ephemeral=True)


class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.persistent_views_added = False

    async def cog_load(self):
        # Register persistent views when cog loads
        if not self.persistent_views_added:
            self.bot.add_view(VerifyButtonView(), message_id=None)  # For all messages
            self.persistent_views_added = True
            print("Verification cog loaded with persistent views")

    @app_commands.command(name="set_verify_system", description="Setup the verification system")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_verify_system(self, interaction: discord.Interaction):
        """Initialize the verification system setup"""
        try:
            if not interaction.user.guild_permissions.administrator:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} You need administrator permissions to use this command.",
                    ephemeral=True
                )

            # Check bot permissions
            required_perms = discord.Permissions(
                manage_roles=True,
                manage_channels=True,
                view_channel=True,
                send_messages=True,
                embed_links=True
            )
            
            if not interaction.guild.me.guild_permissions >= required_perms:
                missing = [
                    perm.replace('_', ' ').title()
                    for perm, value in required_perms
                    if value and not getattr(interaction.guild.me.guild_permissions, perm)
                ]
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} I need the following permissions to set up verification:\n"
                    f"- {', '.join(missing)}",
                    ephemeral=True
                )

            embed = discord.Embed(
                title="Verification Setup",
                description="Configure your verification system using the buttons below.",
                color=discord.Color.blue()
            )
            
            view = SetupView(interaction)
            await view.load_config()  # Load any existing config
            
            await interaction.response.send_message(embed=embed, view=view)
            
        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message(
                f"{CROSS_EMOJI} Failed to start setup: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="verify_system", description="Enable or disable verification system")
    @app_commands.describe(action="Enable or disable the system")
    @app_commands.choices(action=[
        app_commands.Choice(name="Enable", value="enable"),
        app_commands.Choice(name="Disable", value="disable")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_system(self, interaction: discord.Interaction, action: app_commands.Choice[str]):
        """Enable or disable the verification system"""
        try:
            config = await db.verify_config.find_one({"_id": str(interaction.guild.id)})
            if not config:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} The verification system hasn't been set up yet.",
                    ephemeral=True
                )

            if action.value == "enable":
                # Validate configuration before enabling
                required_fields = ["channel_id", "unverified_role", "verified_role", "embed"]
                missing = [field for field in required_fields if field not in config]
                
                if missing:
                    return await interaction.response.send_message(
                        f"{CROSS_EMOJI} The verification system is not fully configured. Missing: {', '.join(missing)}",
                        ephemeral=True
                    )

                await db.verify_config.update_one(
                    {"_id": str(interaction.guild.id)},
                    {"$set": {"enabled": True}}
                )
                
                # Update channel permissions when enabling
                unverified_role = interaction.guild.get_role(config["unverified_role"])
                verified_role = interaction.guild.get_role(config["verified_role"])
                verify_channel = interaction.guild.get_channel(config["channel_id"])
                
                if not unverified_role or not verified_role or not verify_channel:
                    return await interaction.response.send_message(
                        f"{CROSS_EMOJI} Some roles or channel are missing. Please check the configuration.",
                        ephemeral=True
                    )
                
                # Configure permissions for all channels
                for channel in interaction.guild.channels:
                    if channel.id == verify_channel.id:
                        # Verification channel permissions
                        await channel.set_permissions(
                            interaction.guild.default_role,
                            view_channel=False,
                            send_messages=False,
                            read_message_history=False,
                            create_private_threads=False,
                            create_public_threads=False,
                            send_messages_in_threads=False
                        )
                        
                        await channel.set_permissions(
                            unverified_role,
                            view_channel=True,
                            send_messages=False,
                            read_message_history=True,
                            add_reactions=False,
                            attach_files=False,
                            embed_links=False,
                            create_private_threads=False,
                            create_public_threads=False,
                            send_messages_in_threads=False
                        )
                        
                        await channel.set_permissions(
                            verified_role,
                            view_channel=True,
                            send_messages=False,
                            read_message_history=True
                        )
                    else:
                        # Skip categories
                        if isinstance(channel, discord.CategoryChannel):
                            continue
                            
                        # For text channels
                        if isinstance(channel, discord.TextChannel):
                            await channel.set_permissions(
                                unverified_role,
                                view_channel=False,
                                send_messages=False,
                                read_message_history=False,
                                add_reactions=False,
                                attach_files=False,
                                embed_links=False,
                                create_private_threads=False,
                                create_public_threads=False,
                                send_messages_in_threads=False
                            )
                        
                        # For voice channels
                        elif isinstance(channel, discord.VoiceChannel):
                            await channel.set_permissions(
                                unverified_role,
                                view_channel=False,
                                connect=False,
                                speak=False
                            )
                        
                        # Reset verified role permissions to default
                        await channel.set_permissions(
                            verified_role,
                            overwrite=None
                        )
                
                await interaction.response.send_message(
                    f"{CHECK_EMOJI} Verification system has been enabled!\n"
                    "Unverified members can view but cannot send messages in the verification channel.",
                    ephemeral=True
                )
            else:
                await db.verify_config.update_one(
                    {"_id": str(interaction.guild.id)},
                    {"$set": {"enabled": False}}
                )
                
                await interaction.response.send_message(
                    f"{CHECK_EMOJI} Verification system has been disabled.",
                    ephemeral=True
                )
                
        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message(
                f"{CROSS_EMOJI} Failed to update verification system: {str(e)}",
                ephemeral=True
            )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def update_verify_message(self, ctx):
        """Force update the verification message"""
        try:
            config = await db.verify_config.find_one({"_id": str(ctx.guild.id)})
            if not config:
                return await ctx.send("Verification system not set up.")
            
            channel = ctx.guild.get_channel(config["channel_id"])
            if not channel:
                return await ctx.send("Verification channel not found.")
            
            # Clear old messages
            async for message in channel.history(limit=10):
                if message.author == ctx.guild.me:
                    try:
                        await message.delete()
                    except:
                        continue
            
            # Post new message
            embed_data = config["embed"]
            embed = discord.Embed(
                title=embed_data["title"],
                description=embed_data["description"],
                color=int(embed_data["color"].lstrip("#"), 16)
            )
            if "banner_url" in embed_data:
                embed.set_image(url=embed_data["banner_url"])
            if "icon_url" in embed_data:
                embed.set_thumbnail(url=embed_data["icon_url"])
            
            await channel.send(embed=embed, view=VerifyButtonView())
            await ctx.send("Verification message updated!")
        except Exception as e:
            await ctx.send(f"Failed to update verification message: {str(e)}")

    @commands.command()
    async def verify_help(self, ctx):
        """Get help with verification on mobile"""
        embed = discord.Embed(
            title="Mobile Verification Help",
            description=(
                "If buttons aren't working on mobile:\n"
                "1. Update your Discord app\n"
                "2. Restart the app\n"
                "3. Try clicking the button again\n"
                "4. If still not working, contact server staff"
            ),
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle new members joining the server"""
        try:
            config = await db.verify_config.find_one({"_id": str(member.guild.id)})
            if not config or not config.get("enabled", False):
                return

            unverified_role_id = config.get("unverified_role")
            if not unverified_role_id:
                return

            unverified_role = member.guild.get_role(unverified_role_id)
            if not unverified_role:
                return

            # Assign unverified role with proper error handling
            try:
                await member.add_roles(unverified_role, reason="Automatic unverified role assignment")
                print(f"Assigned Unverified role to {member} in {member.guild.name}")
                
                verify_channel = member.guild.get_channel(config["channel_id"])
                if verify_channel:
                    # Configure permissions for all channels
                    for channel in member.guild.channels:
                        if channel.id == verify_channel.id:
                            # Verification channel permissions
                            await channel.set_permissions(
                                unverified_role,
                                view_channel=True,
                                send_messages=False,
                                read_message_history=True,
                                add_reactions=False,
                                attach_files=False,
                                embed_links=False,
                                create_private_threads=False,
                                create_public_threads=False,
                                send_messages_in_threads=False
                            )
                        else:
                            # Skip categories
                            if isinstance(channel, discord.CategoryChannel):
                                continue
                                
                            # For text channels
                            if isinstance(channel, discord.TextChannel):
                                await channel.set_permissions(
                                    unverified_role,
                                    view_channel=False,
                                    send_messages=False,
                                    read_message_history=False,
                                    add_reactions=False,
                                    attach_files=False,
                                    embed_links=False,
                                    create_private_threads=False,
                                    create_public_threads=False,
                                    send_messages_in_threads=False
                                )
                            
                            # For voice channels
                            elif isinstance(channel, discord.VoiceChannel):
                                await channel.set_permissions(
                                    unverified_role,
                                    view_channel=False,
                                    connect=False,
                                    speak=False
                                )
                
            except discord.Forbidden:
                print(f"Missing permissions to assign unverified role in {member.guild.name}")
            except discord.HTTPException as e:
                print(f"Error assigning unverified role in {member.guild.name}: {str(e)}")
            except Exception as e:
                print(f"Unexpected error in on_member_join for {member.guild.name}: {str(e)}")

        except Exception as e:
            traceback.print_exc()
            print(f"Error in on_member_join for {member.guild.name}: {str(e)}")

    @app_commands.command(name="set_verified_role", description="Set the role to assign after verification")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(role="Role to assign after verification")
    async def set_verified_role(self, interaction: discord.Interaction, role: discord.Role):
        """Change the verified role"""
        try:
            if role.position >= interaction.guild.me.top_role.position:
                return await interaction.response.send_message(
                    f"{CROSS_EMOJI} That role is higher than my highest role. I can't assign it.",
                    ephemeral=True
                )

            await db.verify_config.update_one(
                {"_id": str(interaction.guild.id)},
                {"$set": {"verified_role": role.id}},
                upsert=True
            )
            
            await interaction.response.send_message(
                f"{CHECK_EMOJI} Verified role set to {role.mention}",
                ephemeral=True
            )
            
        except Exception as e:
            traceback.print_exc()
            await interaction.response.send_message(
                f"{CROSS_EMOJI} Failed to set verified role: {str(e)}",
                ephemeral=True
            )

    async def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.persistent_views_added = False


async def setup(bot: commands.Bot):
    """Add the cog to the bot"""
    await bot.add_cog(Verification(bot))
