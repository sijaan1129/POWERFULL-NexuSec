import discord
from discord.ext import commands, tasks
from discord import ui, app_commands
import asyncio
from datetime import datetime
import aiohttp
import json
from utils.mongo import db

# Custom emojis
CHECK_EMOJI = "<:check:1372502146984968232>"
CROSS_EMOJI = "<:cross:1372502832695087147>"

class PersistentView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class SectionSetupView(PersistentView):
    def __init__(self, bot, section_name, ticket_name, original_embed):
        super().__init__()
        self.bot = bot
        self.section_name = section_name
        self.ticket_name = ticket_name
        self.original_embed = original_embed
        
    @ui.button(label="Set Name", style=discord.ButtonStyle.grey, custom_id="section_set_name")
    async def set_name(self, interaction: discord.Interaction, button: ui.Button):
        modal = SectionNameModal(
            self.bot, 
            self.original_embed, 
            self.ticket_name, 
            edit_mode=True, 
            existing_name=self.section_name
        )
        await interaction.response.send_modal(modal)
        
    @ui.button(label="Set Category", style=discord.ButtonStyle.grey, custom_id="section_set_category")
    async def set_category(self, interaction: discord.Interaction, button: ui.Button):
        select = ui.ChannelSelect(
            placeholder="Select a category",
            custom_id="section_category_select",
            channel_types=[discord.ChannelType.category],
            max_values=1
        )
        
        view = PersistentView()
        view.add_item(select)
        view.add_item(ui.Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cancel_category_select"))
        
        async def cancel_callback(interaction: discord.Interaction):
            embed = discord.Embed(
                title=f"Section Setup - {self.section_name}",
                description=self.original_embed.description or f"Configuring section for {self.ticket_name}",
                color=discord.Color.dark_theme()
            )
            
            guild_data = await db.tickets.find_one({"guild_id": interaction.guild.id, "name": self.ticket_name})
            if guild_data and "sections" in guild_data and self.section_name in guild_data["sections"]:
                section_data = guild_data["sections"][self.section_name]
                if "category_id" in section_data:
                    embed.add_field(name="Category", value=f"<#{section_data['category_id']}>", inline=False)
                if "support_role_id" in section_data:
                    embed.add_field(name="Support Role", value=f"<@&{section_data['support_role_id']}>", inline=False)
            
            view = SectionSetupView(self.bot, self.section_name, self.ticket_name, self.original_embed)
            await interaction.response.edit_message(embed=embed, view=view)
        
        for item in view.children:
            if isinstance(item, ui.Button) and item.custom_id == "cancel_category_select":
                item.callback = cancel_callback
        
        async def select_callback(interaction: discord.Interaction):
            if not select.values:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} No category selected.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            selected_category = select.values[0]
            
            await db.tickets.update_one(
                {"guild_id": interaction.guild.id, "name": self.ticket_name},
                {"$set": {f"sections.{self.section_name}.category_id": selected_category.id}}
            )
            
            guild_data = await db.tickets.find_one({"guild_id": interaction.guild.id, "name": self.ticket_name})
            if not guild_data or "sections" not in guild_data or self.section_name not in guild_data["sections"]:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} Failed to update section.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            section_data = guild_data["sections"][self.section_name]
            
            embed = discord.Embed(
                title=f"Section Setup - {self.section_name}",
                description=section_data.get("description", f"Configuring section for {self.ticket_name}"),
                color=discord.Color.dark_theme()
            )
            
            if "category_id" in section_data:
                embed.add_field(name="Category", value=f"<#{section_data['category_id']}>", inline=False)
            if "support_role_id" in section_data:
                embed.add_field(name="Support Role", value=f"<@&{section_data['support_role_id']}>", inline=False)
            
            view = SectionSetupView(self.bot, self.section_name, self.ticket_name, self.original_embed)
            await interaction.response.edit_message(embed=embed, view=view)
        
        select.callback = select_callback
        embed = discord.Embed(
            title=f"Select Category for {self.section_name}",
            description="Choose the category where tickets for this section will be created",
            color=discord.Color.dark_theme()
        )
        await interaction.response.edit_message(embed=embed, view=view)
        
    @ui.button(label="Set Support Role", style=discord.ButtonStyle.grey, custom_id="section_set_role")
    async def set_support_role(self, interaction: discord.Interaction, button: ui.Button):
        select = ui.RoleSelect(
            placeholder="Select a support role",
            custom_id="section_role_select",
            max_values=1
        )
        
        view = PersistentView()
        view.add_item(select)
        view.add_item(ui.Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cancel_role_select"))
        
        async def cancel_callback(interaction: discord.Interaction):
            embed = discord.Embed(
                title=f"Section Setup - {self.section_name}",
                description=self.original_embed.description or f"Configuring section for {self.ticket_name}",
                color=discord.Color.dark_theme()
            )
            
            guild_data = await db.tickets.find_one({"guild_id": interaction.guild.id, "name": self.ticket_name})
            if guild_data and "sections" in guild_data and self.section_name in guild_data["sections"]:
                section_data = guild_data["sections"][self.section_name]
                if "category_id" in section_data:
                    embed.add_field(name="Category", value=f"<#{section_data['category_id']}>", inline=False)
                if "support_role_id" in section_data:
                    embed.add_field(name="Support Role", value=f"<@&{section_data['support_role_id']}>", inline=False)
            
            view = SectionSetupView(self.bot, self.section_name, self.ticket_name, self.original_embed)
            await interaction.response.edit_message(embed=embed, view=view)
        
        for item in view.children:
            if isinstance(item, ui.Button) and item.custom_id == "cancel_role_select":
                item.callback = cancel_callback
        
        async def select_callback(interaction: discord.Interaction):
            if not select.values:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} No role selected.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            selected_role = select.values[0]
            
            if selected_role.is_bot_managed():
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} Bot roles cannot be set as support roles.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            await db.tickets.update_one(
                {"guild_id": interaction.guild.id, "name": self.ticket_name},
                {"$set": {f"sections.{self.section_name}.support_role_id": selected_role.id}}
            )
            
            guild_data = await db.tickets.find_one({"guild_id": interaction.guild.id, "name": self.ticket_name})
            if not guild_data or "sections" not in guild_data or self.section_name not in guild_data["sections"]:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} Failed to update section.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            section_data = guild_data["sections"][self.section_name]
            
            embed = discord.Embed(
                title=f"Section Setup - {self.section_name}",
                description=section_data.get("description", f"Configuring section for {self.ticket_name}"),
                color=discord.Color.dark_theme()
            )
            
            if "category_id" in section_data:
                embed.add_field(name="Category", value=f"<#{section_data['category_id']}>", inline=False)
            if "support_role_id" in section_data:
                embed.add_field(name="Support Role", value=f"<@&{section_data['support_role_id']}>", inline=False)
            
            view = SectionSetupView(self.bot, self.section_name, self.ticket_name, self.original_embed)
            await interaction.response.edit_message(embed=embed, view=view)
        
        select.callback = select_callback
        embed = discord.Embed(
            title=f"Select Support Role for {self.section_name}",
            description="Choose the role that can manage tickets for this section",
            color=discord.Color.dark_theme()
        )
        await interaction.response.edit_message(embed=embed, view=view)
        
    @ui.button(label="Finish", style=discord.ButtonStyle.green, custom_id="section_finish")
    async def finish_setup(self, interaction: discord.Interaction, button: ui.Button):
        guild_data = await db.tickets.find_one({
            "guild_id": interaction.guild.id,
            "name": self.ticket_name
        })
        
        if not guild_data or "sections" not in guild_data or self.section_name not in guild_data["sections"]:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} Please configure at least one option for this section.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        embed = self.original_embed
        embed.clear_fields()
        
        if "channel_id" in guild_data:
            embed.add_field(name="Panel Channel", value=f"<#{guild_data['channel_id']}>", inline=False)
        
        if "sections" in guild_data:
            sections_text = []
            for name, data in guild_data["sections"].items():
                section_info = f"- **{name}**"
                if "category_id" in data:
                    section_info += f" | Category: <#{data['category_id']}>"
                if "support_role_id" in data:
                    section_info += f" | Role: <@&{data['support_role_id']}>"
                sections_text.append(section_info)
            
            embed.add_field(
                name="Sections", 
                value="\n".join(sections_text) or "No sections configured", 
                inline=False
            )
        
        view = TicketSetupView(self.bot, embed, self.ticket_name)
        await interaction.response.edit_message(embed=embed, view=view)

class DeleteSectionView(PersistentView):
    def __init__(self, bot, ticket_name, original_embed):
        super().__init__()
        self.bot = bot
        self.ticket_name = ticket_name
        self.original_embed = original_embed
        
        self.section_select = SectionSelectDropdown(bot, ticket_name)
        self.add_item(self.section_select)
        
        self.add_item(ui.Button(
            label="Cancel", 
            style=discord.ButtonStyle.grey, 
            custom_id="delete_section_cancel",
            row=1
        ))
        
    async def refresh(self, interaction: discord.Interaction):
        await self.section_select.refresh_options(interaction)
        await interaction.response.edit_message(view=self)

class SectionSelectDropdown(ui.Select):
    def __init__(self, bot, ticket_name):
        self.bot = bot
        self.ticket_name = ticket_name
        super().__init__(
            placeholder="Loading sections...",
            custom_id="section_delete_select",
            options=[],
            disabled=True
        )
        
    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} Please select a section to delete.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        selected_section = self.values[0]
        
        embed = discord.Embed(
            title="Confirm Section Deletion",
            description=f"Are you sure you want to delete the section **{selected_section}**?",
            color=discord.Color.dark_theme()
        )
        
        view = PersistentView()
        confirm_button = ui.Button(
            label="Confirm", 
            style=discord.ButtonStyle.red, 
            custom_id=f"confirm_delete_{selected_section}"
        )
        cancel_button = ui.Button(
            label="Cancel", 
            style=discord.ButtonStyle.grey, 
            custom_id="delete_section_cancel"
        )
        
        async def confirm_callback(interaction: discord.Interaction):
            result = await db.tickets.update_one(
                {"guild_id": interaction.guild.id, "name": self.ticket_name},
                {"$unset": {f"sections.{selected_section}": ""}}
            )
            
            if result.modified_count == 0:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} Failed to delete section.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            await db.tickets.update_one(
                {"guild_id": interaction.guild.id, "name": self.ticket_name},
                {"$pull": {"tickets": {"section": selected_section}}}
            )
            
            guild_data = await db.tickets.find_one({
                "guild_id": interaction.guild.id,
                "name": self.ticket_name
            })
            
            if not guild_data:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} Ticket system data not found.",
                    color=discord.Color.default()
                )
                return await interaction.response.edit_message(embed=embed, view=None)
            
            embed = discord.Embed(
                title=f"Ticket System Setup - {self.ticket_name}",
                description=f"Section **{selected_section}** has been deleted.",
                color=discord.Color.dark_theme()
            )
            
            if "channel_id" in guild_data:
                embed.add_field(name="Panel Channel", value=f"<#{guild_data['channel_id']}>", inline=False)
            
            if "sections" in guild_data and guild_data["sections"]:
                sections_text = []
                for name, data in guild_data["sections"].items():
                    section_info = f"- **{name}**"
                    if "category_id" in data:
                        section_info += f" | Category: <#{data['category_id']}>"
                    if "support_role_id" in data:
                        section_info += f" | Role: <@&{data['support_role_id']}>"
                    sections_text.append(section_info)
                
                embed.add_field(
                    name="Sections", 
                    value="\n".join(sections_text) or "No sections configured", 
                    inline=False
                )
            else:
                embed.add_field(name="Sections", value="No sections configured", inline=False)
            
            view = TicketSetupView(self.bot, embed, self.ticket_name)
            await interaction.response.edit_message(embed=embed, view=view)
        
        confirm_button.callback = confirm_callback
        cancel_button.callback = lambda i: i.response.edit_message(
            embed=self.view.original_embed, 
            view=TicketSetupView(self.bot, self.view.original_embed, self.ticket_name)
        )
        
        view.add_item(confirm_button)
        view.add_item(cancel_button)
        
        await interaction.response.edit_message(embed=embed, view=view)
        
    async def refresh_options(self, interaction: discord.Interaction):
        guild_data = await db.tickets.find_one({
            "guild_id": interaction.guild.id,
            "name": self.ticket_name
        })
        
        self.options = []
        
        if guild_data and "sections" in guild_data:
            for section_name in guild_data["sections"].keys():
                self.options.append(
                    discord.SelectOption(
                        label=section_name[:100],
                        value=section_name
                    )
                )
        
        if not self.options:
            self.placeholder = "No sections available to delete"
            self.disabled = True
        else:
            self.placeholder = "Select a section to delete"
            self.disabled = False

class SectionNameModal(ui.Modal, title="Section Configuration"):
    def __init__(self, bot, original_embed, ticket_name, edit_mode=False, existing_name=None):
        super().__init__()
        self.bot = bot
        self.original_embed = original_embed
        self.ticket_name = ticket_name
        self.edit_mode = edit_mode
        self.existing_name = existing_name
        
        self.name_input = ui.TextInput(
            label="Section Name",
            default=existing_name if edit_mode else None,
            required=True,
            max_length=100
        )
        
        self.description_input = ui.TextInput(
            label="Section Description",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=2000,
            default=None
        )
        
        self.add_item(self.name_input)
        self.add_item(self.description_input)
        
    async def on_submit(self, interaction: discord.Interaction):
        section_name = self.name_input.value.strip()
        description = self.description_input.value.strip() if self.description_input.value else None
        
        if not section_name:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} Section name cannot be empty.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        if self.edit_mode and self.existing_name and section_name != self.existing_name:
            result = await db.tickets.update_one(
                {"guild_id": interaction.guild.id, "name": self.ticket_name},
                {"$rename": {f"sections.{self.existing_name}": f"sections.{section_name}"}}
            )
            
            if result.modified_count == 0:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} Failed to rename section.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            if description:
                await db.tickets.update_one(
                    {"guild_id": interaction.guild.id, "name": self.ticket_name},
                    {"$set": {f"sections.{section_name}.description": description}}
                )
            
            embed = discord.Embed(
                description=f"{CHECK_EMOJI} Section renamed from '{self.existing_name}' to '{section_name}'",
                color=discord.Color.default()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            guild_data = await db.tickets.find_one({
                "guild_id": interaction.guild.id,
                "name": self.ticket_name
            })
            
            if not guild_data or "sections" not in guild_data or section_name not in guild_data["sections"]:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} Failed to load section data.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            section_data = guild_data["sections"][section_name]
            
            embed = discord.Embed(
                title=f"Section Setup - {section_name}",
                description=section_data.get("description", f"Configuring section for {self.ticket_name}"),
                color=discord.Color.dark_theme()
            )
            
            if "category_id" in section_data:
                embed.add_field(name="Category", value=f"<#{section_data['category_id']}>", inline=False)
            if "support_role_id" in section_data:
                embed.add_field(name="Support Role", value=f"<@&{section_data['support_role_id']}>", inline=False)
            
            view = SectionSetupView(self.bot, section_name, self.ticket_name, self.original_embed)
            await interaction.message.edit(embed=embed, view=view)
        else:
            guild_data = await db.tickets.find_one({
                "guild_id": interaction.guild.id,
                "name": self.ticket_name,
                f"sections.{section_name}": {"$exists": True}
            })
            
            if guild_data:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} A section named '{section_name}' already exists.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            section_data = {}
            if description:
                section_data["description"] = description
                
            await db.tickets.update_one(
                {"guild_id": interaction.guild.id, "name": self.ticket_name},
                {"$set": {f"sections.{section_name}": section_data}},
                upsert=True
            )
            
            embed = discord.Embed(
                title=f"Section Setup - {section_name}",
                description=description or f"Configuring section for {self.ticket_name}",
                color=discord.Color.dark_theme()
            )
            
            view = SectionSetupView(self.bot, section_name, self.ticket_name, self.original_embed)
            await interaction.response.edit_message(embed=embed, view=view)

class SectionSelect(ui.Select):
    def __init__(self, ticket_name, sections):
        options = []
        
        for section in sections:
            if not section or not isinstance(section, str):
                continue
                
            options.append(discord.SelectOption(
                label=section[:100],
                value=section,
                description=f"Create a {section[:50]} ticket"[:100]
            ))
        
        super().__init__(
            placeholder="Select a ticket type"[:100],
            options=options,
            custom_id=f"section_select_{ticket_name}"[:100]
        )
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        
        selected_value = self.values[0]
        
        guild_data = await db.tickets.find_one({
            "guild_id": interaction.guild.id,
            "name": self.view.ticket_name
        })
        
        if not guild_data:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} Ticket system not found.",
                color=discord.Color.default()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
        
        existing_ticket = await db.tickets.find_one({
            "guild_id": interaction.guild.id,
            "tickets": {
                "$elemMatch": {
                    "user_id": interaction.user.id,
                    "status": "open",
                    "ticket_name": self.view.ticket_name,
                    "section": selected_value
                }
            }
        })
        
        if existing_ticket:
            ticket = next(
                t for t in existing_ticket["tickets"] 
                if t["user_id"] == interaction.user.id 
                and t["status"] == "open"
                and t["ticket_name"] == self.view.ticket_name
                and t.get("section") == selected_value
            )
            
            channel = interaction.guild.get_channel(ticket["channel_id"])
            if channel:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} You already have an open {selected_value} ticket: <#{ticket['channel_id']}>",
                    color=discord.Color.default()
                )
                return await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await db.tickets.update_one(
                    {"guild_id": interaction.guild.id, "name": self.view.ticket_name},
                    {"$pull": {"tickets": {"channel_id": ticket["channel_id"]}}}
                )
        
        section_data = guild_data["sections"].get(selected_value, {})
        category_id = section_data.get("category_id")
        support_role_id = section_data.get("support_role_id")
        
        if not category_id:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} No category set for this section.",
                color=discord.Color.default()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
            
        category = interaction.guild.get_channel(category_id)
        if not category:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} Ticket category not found.",
                color=discord.Color.default()
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)
            
        support_role = interaction.guild.get_role(support_role_id) if support_role_id else None
        
        ticket_count = await db.tickets.count_documents({
            "guild_id": interaction.guild.id,
            "name": self.view.ticket_name,
            "tickets.section": selected_value
        })
        ticket_number = f"{ticket_count + 1:03d}"
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        try:
            channel_name = f"{selected_value.lower().replace(' ', '-')}-{ticket_number}"[:100]
            
            ticket_channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites
            )
            
            ticket_data = {
                "channel_id": ticket_channel.id,
                "user_id": interaction.user.id,
                "status": "open",
                "created_at": datetime.utcnow(),
                "ticket_name": self.view.ticket_name,
                "number": ticket_number,
                "section": selected_value
            }
            
            await db.tickets.update_one(
                {"guild_id": interaction.guild.id, "name": self.view.ticket_name},
                {"$push": {"tickets": ticket_data}}
            )
            
            # Private message for ticket creator
            await interaction.followup.send(
                f"{CHECK_EMOJI} Ticket Created {ticket_channel.mention}",
                ephemeral=True
            )
            
            # Ticket channel message
            embed = discord.Embed(
                title=f"Ticket - {selected_value}"[:256],
                description="Support will be with you shortly.\nTo close this ticket, press the close button.",
                color=discord.Color.dark_theme()
            )
            embed.set_footer(text=f"Created by {interaction.user}"[:2048])
            
            view = TicketCloseView(self.view.bot, self.view.ticket_name)
            await ticket_channel.send(
                content=f"{interaction.user.mention}" + (f" {support_role.mention}" if support_role else ""),
                embed=embed,
                view=view
            )
            
        except Exception as e:
            if 'ticket_channel' in locals():
                await ticket_channel.delete()
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} Failed to create ticket: {str(e)}",
                color=discord.Color.default()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class SectionSelectView(PersistentView):
    def __init__(self, bot, ticket_name, sections):
        super().__init__()
        self.bot = bot
        self.ticket_name = ticket_name
        self.sections = sections
        
        if len(sections) == 1:
            button = ui.Button(
                label="Open Ticket",
                style=discord.ButtonStyle.grey,
                custom_id=f"single_section_{ticket_name}_{sections[0]}"
            )
            
            async def button_callback(interaction: discord.Interaction):
                # Defer the interaction first
                await interaction.response.defer(thinking=True, ephemeral=True)
                
                # Get the guild data
                guild_data = await db.tickets.find_one({
                    "guild_id": interaction.guild.id,
                    "name": self.ticket_name
                })
                
                if not guild_data:
                    embed = discord.Embed(
                        description=f"{CROSS_EMOJI} Ticket system not found.",
                        color=discord.Color.default()
                    )
                    return await interaction.followup.send(embed=embed, ephemeral=True)
                
                # Check for existing ticket
                existing_ticket = await db.tickets.find_one({
                    "guild_id": interaction.guild.id,
                    "tickets": {
                        "$elemMatch": {
                            "user_id": interaction.user.id,
                            "status": "open",
                            "ticket_name": self.ticket_name,
                            "section": self.sections[0]
                        }
                    }
                })
                
                if existing_ticket:
                    ticket = next(
                        t for t in existing_ticket["tickets"] 
                        if t["user_id"] == interaction.user.id 
                        and t["status"] == "open"
                        and t["ticket_name"] == self.ticket_name
                        and t.get("section") == self.sections[0]
                    )
                    
                    channel = interaction.guild.get_channel(ticket["channel_id"])
                    if channel:
                        embed = discord.Embed(
                            description=f"{CROSS_EMOJI} You already have an open {self.sections[0]} ticket: <#{ticket['channel_id']}>",
                            color=discord.Color.default()
                        )
                        return await interaction.followup.send(embed=embed, ephemeral=True)
                    else:
                        await db.tickets.update_one(
                            {"guild_id": interaction.guild.id, "name": self.ticket_name},
                            {"$pull": {"tickets": {"channel_id": ticket["channel_id"]}}}
                        )
                
                # Get section data
                section_data = guild_data["sections"].get(self.sections[0], {})
                category_id = section_data.get("category_id")
                support_role_id = section_data.get("support_role_id")
                
                if not category_id:
                    embed = discord.Embed(
                        description=f"{CROSS_EMOJI} No category set for this section.",
                        color=discord.Color.default()
                    )
                    return await interaction.followup.send(embed=embed, ephemeral=True)
                    
                category = interaction.guild.get_channel(category_id)
                if not category:
                    embed = discord.Embed(
                        description=f"{CROSS_EMOJI} Ticket category not found.",
                        color=discord.Color.default()
                    )
                    return await interaction.followup.send(embed=embed, ephemeral=True)
                    
                support_role = interaction.guild.get_role(support_role_id) if support_role_id else None
                
                ticket_count = await db.tickets.count_documents({
                    "guild_id": interaction.guild.id,
                    "name": self.ticket_name,
                    "tickets.section": self.sections[0]
                })
                ticket_number = f"{ticket_count + 1:03d}"
                
                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                }
                
                if support_role:
                    overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                
                try:
                    channel_name = f"{self.sections[0].lower().replace(' ', '-')}-{ticket_number}"[:100]
                    
                    ticket_channel = await category.create_text_channel(
                        name=channel_name,
                        overwrites=overwrites
                    )
                    
                    ticket_data = {
                        "channel_id": ticket_channel.id,
                        "user_id": interaction.user.id,
                        "status": "open",
                        "created_at": datetime.utcnow(),
                        "ticket_name": self.ticket_name,
                        "number": ticket_number,
                        "section": self.sections[0]
                    }
                    
                    await db.tickets.update_one(
                        {"guild_id": interaction.guild.id, "name": self.ticket_name},
                        {"$push": {"tickets": ticket_data}}
                    )
                    
                    # Private message for ticket creator
                    await interaction.followup.send(
                        f"{CHECK_EMOJI} Ticket Created {ticket_channel.mention}",
                        ephemeral=True
                    )
                    
                    # Ticket channel message
                    embed = discord.Embed(
                        title=f"Ticket - {self.sections[0]}"[:256],
                        description="Support will be with you shortly.\nTo close this ticket, press the close button.",
                        color=discord.Color.dark_theme()
                    )
                    embed.set_footer(text=f"Created by {interaction.user}"[:2048])
                    
                    view = TicketCloseView(self.bot, self.ticket_name)
                    await ticket_channel.send(
                        content=f"{interaction.user.mention}" + (f" {support_role.mention}" if support_role else ""),
                        embed=embed,
                        view=view
                    )
                    
                except Exception as e:
                    if 'ticket_channel' in locals():
                        await ticket_channel.delete()
                    embed = discord.Embed(
                        description=f"{CROSS_EMOJI} Failed to create ticket: {str(e)}",
                        color=discord.Color.default()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
            
            button.callback = button_callback
            self.add_item(button)
        else:
            self.add_item(SectionSelect(ticket_name, sections))

class TicketEmbedModal(ui.Modal, title="Ticket Embed Setup"):
    def __init__(self, bot, original_embed):
        super().__init__()
        self.bot = bot
        self.original_embed = original_embed
        
        self.title_input = ui.TextInput(
            label="Embed Title",
            default=original_embed.title if original_embed.title else None,
            required=True,
            max_length=256
        )
        self.description_input = ui.TextInput(
            label="Embed Description",
            style=discord.TextStyle.paragraph,
            default=original_embed.description if original_embed.description else None,
            required=True,
            max_length=4000
        )
        self.color_input = ui.TextInput(
            label="Hex Color (e.g., #FFFFFF)",
            default=str(original_embed.color) if original_embed.color else "#000000",
            required=True,
            max_length=7
        )
        self.banner_input = ui.TextInput(
            label="Banner URL (1920x1080 recommended)",
            default=original_embed.image.url if original_embed.image else None,
            required=False,
            max_length=2000
        )
        self.icon_input = ui.TextInput(
            label="Icon URL (512x512 recommended)",
            default=original_embed.thumbnail.url if original_embed.thumbnail else None,
            required=False,
            max_length=2000
        )
        
        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.color_input)
        self.add_item(self.banner_input)
        self.add_item(self.icon_input)
        
    async def on_submit(self, interaction: discord.Interaction):
        try:
            color = discord.Color.from_str(self.color_input.value)
        except:
            color = discord.Color.dark_theme()
            
        embed = discord.Embed(
            title=self.title_input.value,
            description=self.description_input.value,
            color=color
        )
        
        if self.banner_input.value and self.banner_input.value.startswith(('http://', 'https://')):
            embed.set_image(url=self.banner_input.value)
                
        if self.icon_input.value and self.icon_input.value.startswith(('http://', 'https://')):
            embed.set_thumbnail(url=self.icon_input.value)
                
        view = TicketSetupView(self.bot, embed)
        await interaction.response.edit_message(embed=embed, view=view)

class TicketCloseView(PersistentView):
    def __init__(self, bot, ticket_name):
        super().__init__()
        self.bot = bot
        self.ticket_name = ticket_name
        
    @ui.button(label="Close", style=discord.ButtonStyle.grey, custom_id="persistent_close")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        # Get ticket data from database
        ticket_data = await db.tickets.find_one({
            "guild_id": interaction.guild.id,
            "tickets.channel_id": interaction.channel.id
        })
        
        if not ticket_data:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} Ticket not found in database.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        # Find the specific ticket
        ticket = next(
            t for t in ticket_data.get("tickets", []) 
            if t["channel_id"] == interaction.channel.id
        )
        
        # Check if user has permission to close
        has_permission = (
            interaction.user.id == ticket["user_id"] or
            interaction.user.id == interaction.guild.owner_id or
            interaction.user.guild_permissions.administrator
        )
        
        # Check support role permissions if not admin/owner
        if not has_permission:
            guild_data = await db.tickets.find_one({
                "guild_id": interaction.guild.id,
                "name": self.ticket_name
            })
            
            if guild_data and "sections" in guild_data and ticket.get("section"):
                section_data = guild_data["sections"].get(ticket["section"], {})
                if "support_role_id" in section_data:
                    support_role = interaction.guild.get_role(section_data["support_role_id"])
                    if support_role and support_role in interaction.user.roles:
                        has_permission = True
                
        if not has_permission:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} Only ticket creator, admins, or support team can close tickets.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        # Confirmation embed
        embed = discord.Embed(
            description="Are you sure you would like to close this ticket?",
            color=discord.Color.dark_theme()
        )
        
        view = PersistentView()
        confirm = ui.Button(label="Confirm", style=discord.ButtonStyle.grey, custom_id=f"confirm_close_{interaction.channel.id}")
        cancel = ui.Button(label="Cancel", style=discord.ButtonStyle.grey, custom_id=f"cancel_close_{interaction.channel.id}")
        
        async def confirm_callback(interaction: discord.Interaction):
            try:
                # Update channel name to indicate closed status
                await interaction.channel.edit(name=f"closed-{interaction.channel.name}"[:100])
            except Exception as e:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} Failed to update channel name: {str(e)}",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Update ticket status in database
            await db.tickets.update_one(
                {
                    "guild_id": interaction.guild.id,
                    "tickets.channel_id": interaction.channel.id
                },
                {"$set": {"tickets.$.status": "closed"}}
            )
            
            # Update permissions for ticket creator
            user = interaction.guild.get_member(ticket["user_id"])
            if user:
                try:
                    await interaction.channel.set_permissions(
                        user,
                        read_messages=True,
                        add_reactions=False,
                        attach_files=False,
                        send_messages=False,
                        embed_links=False
                    )
                except Exception as e:
                    print(f"Failed to update permissions: {str(e)}")
            
            # First embed - Ticket Closed (visible to everyone)
            closed_embed = discord.Embed(
                title=f"Ticket Closed by {interaction.user.mention}",
                color=discord.Color.default()
            )
            
            # Edit the original message with closed status
            await interaction.response.edit_message(embed=closed_embed, view=None)
            
            # Get current ticket system data for permission checks
            guild_data = await db.tickets.find_one({
                "guild_id": interaction.guild.id,
                "name": self.ticket_name
            })
            
            # Second embed - Management Controls (visible to everyone)
            control_embed = discord.Embed(
                title="```Support team ticket controls```",
                color=discord.Color.dark_theme()
            )
            
            control_view = PersistentView()
            
            # Transcript button
            transcript = ui.Button(label="Transcript", style=discord.ButtonStyle.grey, custom_id=f"transcript_{interaction.channel.id}")
            
            async def transcript_callback(interaction: discord.Interaction):
                # Verify permissions when button is clicked
                is_admin = (interaction.user.id == interaction.guild.owner_id or 
                           interaction.user.guild_permissions.administrator)
                
                is_support = False
                if guild_data and "sections" in guild_data and ticket.get("section"):
                    section_data = guild_data["sections"].get(ticket["section"], {})
                    if "support_role_id" in section_data:
                        support_role = interaction.guild.get_role(section_data["support_role_id"])
                        if support_role and support_role in interaction.user.roles:
                            is_support = True
                
                if not is_admin and not is_support:
                    embed = discord.Embed(
                        description=f"{CROSS_EMOJI} Only administrators or support team can generate transcripts.",
                        color=discord.Color.default()
                    )
                    return await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # Start generating transcript
                embed = discord.Embed(
                    description=f"{CHECK_EMOJI} Generating transcript, please wait...",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # Fetch all messages from the channel
                messages = []
                async for message in interaction.channel.history(limit=None, oldest_first=True):
                    messages.append(message)
                
                # Format messages for sourceb.in
                transcript_content = []
                for message in messages:
                    # Format timestamp
                    timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Format author
                    author = f"{message.author.display_name} ({message.author.id})"
                    
                    # Format content
                    content = message.clean_content
                    
                    # Format attachments
                    attachments = ""
                    if message.attachments:
                        attachments = "\n" + "\n".join([f"Attachment: {a.url}" for a in message.attachments])
                    
                    # Format embeds
                    embeds = ""
                    if message.embeds:
                        embeds = "\n" + "\n".join([f"Embed: {e.to_dict()}" for e in message.embeds])
                    
                    # Combine everything
                    transcript_content.append(f"[{timestamp}] {author}: {content}{attachments}{embeds}")
                
                # Join all messages with newlines
                full_transcript = "\n".join(transcript_content)
                
                # Upload to sourceb.in
                try:
                    async with aiohttp.ClientSession() as session:
                        # Create a new paste
                        data = {
                            "title": f"Ticket Transcript - {interaction.channel.name}",
                            "description": f"Transcript for ticket {interaction.channel.name} in {interaction.guild.name}",
                            "files": [{
                                "name": "transcript.txt",
                                "content": full_transcript
                            }]
                        }
                        
                        headers = {
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        }
                        
                        async with session.post("https://sourceb.in/api/bins", json=data, headers=headers) as resp:
                            if resp.status == 200:
                                result = await resp.json()
                                paste_url = f"https://sourceb.in/{result['key']}"
                                
                                # Send the transcript link
                                embed = discord.Embed(
                                    title="Ticket Transcript",
                                    description=f"Transcript has been created and can be viewed at:\n{paste_url}",
                                    color=discord.Color.green()
                                )
                                await interaction.followup.send(embed=embed, ephemeral=True)
                            else:
                                error = await resp.text()
                                embed = discord.Embed(
                                    title="Error",
                                    description=f"Failed to create transcript: {error}",
                                    color=discord.Color.red()
                                )
                                await interaction.followup.send(embed=embed, ephemeral=True)
                except Exception as e:
                    embed = discord.Embed(
                        title="Error",
                        description=f"An error occurred while generating transcript: {str(e)}",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
            
            transcript.callback = transcript_callback
            control_view.add_item(transcript)
            
            # Delete button (visible to everyone)
            delete = ui.Button(label="Delete", style=discord.ButtonStyle.red, custom_id=f"delete_{interaction.channel.id}")
            
            async def delete_callback(interaction: discord.Interaction):
                # Verify permissions when button is clicked
                is_admin = (interaction.user.id == interaction.guild.owner_id or 
                           interaction.user.guild_permissions.administrator)
                
                is_support = False
                if guild_data and "sections" in guild_data and ticket.get("section"):
                    section_data = guild_data["sections"].get(ticket["section"], {})
                    if "support_role_id" in section_data:
                        support_role = interaction.guild.get_role(section_data["support_role_id"])
                        if support_role and support_role in interaction.user.roles:
                            is_support = True
                
                if not is_admin and not is_support:
                    embed = discord.Embed(
                        description=f"{CROSS_EMOJI} Only administrators or support team can delete tickets.",
                        color=discord.Color.default()
                    )
                    return await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # Delete confirmation embed
                embed = discord.Embed(
                    description="Are you sure you want to delete this ticket?",
                    color=discord.Color.dark_theme()
                )
                
                confirm_view = PersistentView()
                confirm_btn = ui.Button(label="Confirm", style=discord.ButtonStyle.red, custom_id=f"confirm_delete_{interaction.channel.id}")
                cancel_btn = ui.Button(label="Cancel", style=discord.ButtonStyle.grey, custom_id=f"cancel_delete_{interaction.channel.id}")
                
                async def confirm_delete(interaction: discord.Interaction):
                    # Update ticket status to deleted
                    await db.tickets.update_one(
                        {
                            "guild_id": interaction.guild.id,
                            "tickets.channel_id": interaction.channel.id
                        },
                        {"$set": {"tickets.$.status": "deleted"}}
                    )
                    
                    # Show deletion countdown
                    await interaction.response.edit_message(
                        embed=discord.Embed(
                            description="Deleting ticket in 5 seconds...",
                            color=discord.Color.dark_theme()
                        ),
                        view=None
                    )
                    await asyncio.sleep(5)
                    try:
                        await interaction.channel.delete()
                    except Exception as e:
                        print(f"Failed to delete channel: {str(e)}")
                
                confirm_btn.callback = confirm_delete
                cancel_btn.callback = lambda i: i.response.edit_message(embed=control_embed, view=control_view)
                confirm_view.add_item(confirm_btn)
                confirm_view.add_item(cancel_btn)
                
                await interaction.response.edit_message(embed=embed, view=confirm_view)
            
            delete.callback = delete_callback
            control_view.add_item(delete)
            
            # Send the management controls as a new message
            await interaction.followup.send(embed=control_embed, view=control_view)
        
        confirm.callback = confirm_callback
        cancel.callback = lambda i: i.response.edit_message(content="Cancelled", embed=None, view=None)
        view.add_item(confirm)
        view.add_item(cancel)
        
        await interaction.response.send_message(embed=embed, view=view)

class TicketSetupView(PersistentView):
    def __init__(self, bot, original_embed, ticket_name=None):
        super().__init__()
        self.bot = bot
        self.original_embed = original_embed
        self.ticket_name = ticket_name
        
    @ui.button(label="Set Embed", style=discord.ButtonStyle.grey, custom_id="ticket_set_embed")
    async def set_embed(self, interaction: discord.Interaction, button: ui.Button):
        modal = TicketEmbedModal(self.bot, self.original_embed)
        await interaction.response.send_modal(modal)
        
    @ui.button(label="Set Channel", style=discord.ButtonStyle.grey, custom_id="ticket_set_channel")
    async def set_channel(self, interaction: discord.Interaction, button: ui.Button):
        select = ui.ChannelSelect(
            placeholder="Select a text channel",
            custom_id="channel_select",
            channel_types=[discord.ChannelType.text],
            max_values=1
        )
        
        view = PersistentView()
        view.add_item(select)
        view.add_item(ui.Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cancel_channel_select"))
        
        async def cancel_callback(interaction: discord.Interaction):
            embed = self.original_embed
            embed.clear_fields()
            
            guild_data = await db.tickets.find_one({"guild_id": interaction.guild.id, "name": self.ticket_name})
            if guild_data:
                if "channel_id" in guild_data:
                    embed.add_field(name="Panel Channel", value=f"<#{guild_data['channel_id']}>", inline=False)
                
                if "sections" in guild_data:
                    sections_text = []
                    for name, data in guild_data["sections"].items():
                        section_info = f"- **{name}**"
                        if "category_id" in data:
                            section_info += f" | Category: <#{data['category_id']}>"
                        if "support_role_id" in data:
                            section_info += f" | Role: <@&{data['support_role_id']}>"
                        sections_text.append(section_info)
                    
                    embed.add_field(
                        name="Sections", 
                        value="\n".join(sections_text) or "No sections configured", 
                        inline=False
                    )
            
            view = TicketSetupView(self.bot, embed, self.ticket_name)
            await interaction.response.edit_message(embed=embed, view=view)
        
        for item in view.children:
            if isinstance(item, ui.Button) and item.custom_id == "cancel_channel_select":
                item.callback = cancel_callback
        
        async def select_callback(interaction: discord.Interaction):
            if not select.values:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} No channel selected.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
                
            selected_channel = select.values[0]
            
            await db.tickets.update_one(
                {"guild_id": interaction.guild.id, "name": self.ticket_name},
                {"$set": {"channel_id": selected_channel.id}}
            )
            
            embed = self.original_embed
            embed.clear_fields()
            
            embed.add_field(name="Panel Channel", value=f"{selected_channel.mention}", inline=False)
            
            guild_data = await db.tickets.find_one({"guild_id": interaction.guild.id, "name": self.ticket_name})
            if guild_data and "sections" in guild_data:
                sections_text = []
                for name, data in guild_data["sections"].items():
                    section_info = f"- **{name}**"
                    if "category_id" in data:
                        section_info += f" | Category: <#{data['category_id']}>"
                    if "support_role_id" in data:
                        section_info += f" | Role: <@&{data['support_role_id']}>"
                    sections_text.append(section_info)
                
                embed.add_field(
                    name="Sections", 
                    value="\n".join(sections_text) or "No sections configured", 
                    inline=False
                )
            
            view = TicketSetupView(self.bot, embed, self.ticket_name)
            await interaction.response.edit_message(embed=embed, view=view)
        
        select.callback = select_callback
        embed = discord.Embed(
            title="Select Ticket Channel",
            description="Choose the channel where the ticket message will be sent",
            color=discord.Color.dark_theme()
        )
        await interaction.response.edit_message(embed=embed, view=view)
        
    @ui.button(label="Add Section", style=discord.ButtonStyle.grey, custom_id="ticket_add_section")
    async def add_section(self, interaction: discord.Interaction, button: ui.Button):
        modal = SectionNameModal(self.bot, self.original_embed, self.ticket_name)
        await interaction.response.send_modal(modal)
        
    @ui.button(label="Edit Section", style=discord.ButtonStyle.grey, custom_id="ticket_edit_section")
    async def edit_section(self, interaction: discord.Interaction, button: ui.Button):
        guild_data = await db.tickets.find_one({
            "guild_id": interaction.guild.id,
            "name": self.ticket_name
        })
        
        if not guild_data or "sections" not in guild_data or not guild_data["sections"]:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} No sections exist to edit.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        select = ui.Select(
            placeholder="Select a section to edit",
            custom_id="edit_section_select"
        )
        
        for section_name in guild_data["sections"].keys():
            select.add_option(label=section_name[:100], value=section_name)
            
        view = PersistentView()
        view.add_item(select)
        view.add_item(ui.Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cancel_edit_section"))
        
        async def cancel_callback(interaction: discord.Interaction):
            embed = self.original_embed
            embed.clear_fields()
            
            if "channel_id" in guild_data:
                embed.add_field(name="Panel Channel", value=f"<#{guild_data['channel_id']}>", inline=False)
            
            if "sections" in guild_data:
                sections_text = []
                for name, data in guild_data["sections"].items():
                    section_info = f"- **{name}**"
                    if "category_id" in data:
                        section_info += f" | Category: <#{data['category_id']}>"
                    if "support_role_id" in data:
                        section_info += f" | Role: <@&{data['support_role_id']}>"
                    sections_text.append(section_info)
                
                embed.add_field(
                    name="Sections", 
                    value="\n".join(sections_text) or "No sections configured", 
                    inline=False
                )
            
            view = TicketSetupView(self.bot, embed, self.ticket_name)
            await interaction.response.edit_message(embed=embed, view=view)
        
        for item in view.children:
            if isinstance(item, ui.Button) and item.custom_id == "cancel_edit_section":
                item.callback = cancel_callback
            
        async def select_callback(interaction: discord.Interaction):
            selected_section = select.values[0]
            
            section_data = guild_data["sections"][selected_section]
            
            embed = discord.Embed(
                title=f"Section Setup - {selected_section}",
                description=section_data.get("description", f"Configuring section for {self.ticket_name}"),
                color=discord.Color.dark_theme()
            )
            
            if "category_id" in section_data:
                embed.add_field(name="Category", value=f"<#{section_data['category_id']}>", inline=False)
            if "support_role_id" in section_data:
                embed.add_field(name="Support Role", value=f"<@&{section_data['support_role_id']}>", inline=False)
            
            view = SectionSetupView(self.bot, selected_section, self.ticket_name, self.original_embed)
            await interaction.response.edit_message(embed=embed, view=view)
            
        select.callback = select_callback
        
        embed = discord.Embed(
            title="Edit Section",
            description="Select a section to edit from the dropdown below",
            color=discord.Color.dark_theme()
        )
        await interaction.response.edit_message(embed=embed, view=view)
        
    @ui.button(label="Delete Section", style=discord.ButtonStyle.grey, custom_id="ticket_delete_section")
    async def delete_section(self, interaction: discord.Interaction, button: ui.Button):
        guild_data = await db.tickets.find_one({
            "guild_id": interaction.guild.id,
            "name": self.ticket_name
        })
        
        if not guild_data or "sections" not in guild_data or not guild_data["sections"]:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} No sections exist to delete.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        embed = discord.Embed(
            title="Delete Section",
            description="Select a section to delete from the dropdown below",
            color=discord.Color.dark_theme()
        )
        
        view = DeleteSectionView(self.bot, self.ticket_name, self.original_embed)
        await view.section_select.refresh_options(interaction)
        await interaction.response.edit_message(embed=embed, view=view)
        
    @ui.button(label="Finish", style=discord.ButtonStyle.green, custom_id="ticket_finish")
    async def finish_setup(self, interaction: discord.Interaction, button: ui.Button):
        guild_data = await db.tickets.find_one({
            "guild_id": interaction.guild.id,
            "name": self.ticket_name
        })
        
        if not guild_data or "sections" not in guild_data or not guild_data["sections"]:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} Please add at least one section before finishing.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        channel_id = guild_data.get("channel_id")
        if not channel_id:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} No channel selected. Please select a channel first.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} Channel not found. Please select a valid channel.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        for section_name, section_data in guild_data["sections"].items():
            if "category_id" not in section_data:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} Section '{section_name}' is missing a category. Please configure all sections.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        sections = list(guild_data["sections"].keys())
        view = SectionSelectView(self.bot, self.ticket_name, sections)
            
        embed = discord.Embed(
            title=self.original_embed.title[:256] if self.original_embed.title else "Ticket System",
            description=self.original_embed.description[:4000] if self.original_embed.description else "Select a ticket type below",
            color=self.original_embed.color if self.original_embed.color else discord.Color.dark_theme()
        )
        
        if self.original_embed.image:
            embed.set_image(url=self.original_embed.image.url)
        if self.original_embed.thumbnail:
            embed.set_thumbnail(url=self.original_embed.thumbnail.url)
        
        try:
            await channel.send(embed=embed, view=view)
            
            await db.tickets.update_one(
                {"guild_id": interaction.guild.id, "name": self.ticket_name},
                {"$set": {"completed": True}}
            )
            
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title=f"{CHECK_EMOJI} Ticket System Setup Complete",
                    description=f"Ticket panel '{self.ticket_name}' has been successfully configured!",
                    color=discord.Color.dark_theme()
                ),
                view=None
            )
        except discord.Forbidden:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} I don't have permission to send messages in that channel.",
                color=discord.Color.default()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} An error occurred while sending the panel: {str(e)}",
                color=discord.Color.default()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_tickets.start()
        
    def cog_unload(self):
        self.cleanup_tickets.cancel()
        
    @tasks.loop(hours=24)
    async def cleanup_tickets(self):
        for guild in self.bot.guilds:
            ticket_systems = await db.tickets.find({"guild_id": guild.id}).to_list(None)
            for system in ticket_systems:
                if "tickets" not in system:
                    continue
                    
                updated_tickets = []
                for ticket in system["tickets"]:
                    channel = guild.get_channel(ticket["channel_id"])
                    if channel is None:
                        continue
                    updated_tickets.append(ticket)
                
                if len(updated_tickets) != len(system["tickets"]):
                    await db.tickets.update_one(
                        {"guild_id": guild.id, "name": system["name"]},
                        {"$set": {"tickets": updated_tickets}}
                    )
    
    @cleanup_tickets.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    # Create the main command group
    ticket = app_commands.Group(name="ticket", description="Manage ticket systems")

    @ticket.command(name="setup", description="Setup a new ticket system")
    @app_commands.describe(name="The name of the ticket system")
    async def ticket_setup(self, interaction: discord.Interaction, name: str):
        if interaction.user.id != interaction.guild.owner_id and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} You don't have administrator permissions to use this command.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        if not name or len(name) > 100:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} Ticket name must be between 1 and 100 characters.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        existing_ticket = await db.tickets.find_one({
            "guild_id": interaction.guild.id,
            "name": name,
            "completed": True
        })
        
        if existing_ticket:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} A completed ticket system with this name already exists. Use `/ticket edit {name}` to modify it.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        incomplete_ticket = await db.tickets.find_one({
            "guild_id": interaction.guild.id,
            "name": name,
            "completed": {"$ne": True}
        })
        
        if incomplete_ticket:
            embed = discord.Embed(
                title=f"Ticket System Setup - {name[:256]}",
                description="Continue configuring the ticket system using the buttons below",
                color=discord.Color.dark_theme()
            )
            
            if "channel_id" in incomplete_ticket:
                embed.add_field(
                    name="Panel Channel",
                    value=f"<#{incomplete_ticket['channel_id']}>",
                    inline=False
                )
                
            if "sections" in incomplete_ticket:
                sections_text = []
                for section_name, section_data in incomplete_ticket["sections"].items():
                    section_info = f"- **{section_name}**"
                    if "category_id" in section_data:
                        section_info += f" | Category: <#{section_data['category_id']}>"
                    if "support_role_id" in section_data:
                        section_info += f" | Role: <@&{section_data['support_role_id']}>"
                    sections_text.append(section_info)
                
                embed.add_field(
                    name="Sections",
                    value="\n".join(sections_text) or "No sections configured",
                    inline=False
                )
            
            view = TicketSetupView(self.bot, embed, name)
            return await interaction.response.send_message(embed=embed, view=view)
            
        embed = discord.Embed(
            title=f"Ticket System Setup - {name[:256]}",
            description="Configure the ticket system using the buttons below",
            color=discord.Color.dark_theme()
        )
        
        view = TicketSetupView(self.bot, embed, name)
        await interaction.response.send_message(embed=embed, view=view)
        
    @ticket.command(name="edit", description="Edit an existing ticket system")
    @app_commands.describe(name="The name of the ticket system to edit")
    async def ticket_edit(self, interaction: discord.Interaction, name: str):
        if interaction.user.id != interaction.guild.owner_id and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} You don't have administrator permissions to use this command.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        existing_ticket = await db.tickets.find_one({
            "guild_id": interaction.guild.id,
            "name": name
        })
        
        if not existing_ticket:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} No ticket system found with that name.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        embed = discord.Embed(
            title=f"Ticket System Setup - {name[:256]}",
            description="Edit the ticket system using the buttons below",
            color=discord.Color.dark_theme()
        )
        
        if "channel_id" in existing_ticket:
            embed.add_field(
                name="Panel Channel",
                value=f"<#{existing_ticket['channel_id']}>",
                inline=False
            )
            
        if "sections" in existing_ticket:
            sections_text = []
            for section_name, section_data in existing_ticket["sections"].items():
                section_info = f"- **{section_name}**"
                if "category_id" in section_data:
                    section_info += f" | Category: <#{section_data['category_id']}>"
                if "support_role_id" in section_data:
                    section_info += f" | Role: <@&{section_data['support_role_id']}>"
                sections_text.append(section_info)
            
            embed.add_field(
                name="Sections",
                value="\n".join(sections_text) or "No sections configured",
                inline=False
            )
        
        view = TicketSetupView(self.bot, embed, name)
        await interaction.response.send_message(embed=embed, view=view)
        
    @ticket.command(name="delete", description="Delete a ticket system")
    @app_commands.describe(name="The name of the ticket system to delete")
    async def ticket_delete(self, interaction: discord.Interaction, name: str):
        if interaction.user.id != interaction.guild.owner_id and not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} You don't have administrator permissions to use this command.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        result = await db.tickets.delete_one({
            "guild_id": interaction.guild.id,
            "name": name
        })
        
        if result.deleted_count == 0:
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} No ticket system named '{name}' found.",
                color=discord.Color.default()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
            
        await interaction.response.send_message(
            embed=discord.Embed(
                title=f"{CHECK_EMOJI} Ticket System Deleted",
                description=f"Ticket system '{name}' has been deleted.",
                color=discord.Color.dark_theme()
            ),
            ephemeral=True
        )
        
    @ticket.command(name="list", description="List all ticket systems")
    async def ticket_list(self, interaction: discord.Interaction):
        try:
            ticket_systems = await db.tickets.find({
                "guild_id": interaction.guild.id,
                "completed": True
            }).to_list(None)
            
            if not ticket_systems:
                embed = discord.Embed(
                    description=f"{CROSS_EMOJI} No ticket systems found for this server.",
                    color=discord.Color.default()
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            
            embed = discord.Embed(
                title="Server Ticket Systems",
                color=discord.Color.dark_theme()
            )
            
            for system in ticket_systems:
                name = system.get("name", "Unnamed")[:256]
                channel = f"<#{system['channel_id']}>" if system.get("channel_id") else "Not set"
                
                open_tickets = len([t for t in system.get("tickets", []) 
                                  if t.get("status") == "open" and t.get("ticket_name") == name])
                
                total_tickets = len([t for t in system.get("tickets", []) 
                                   if t.get("ticket_name") == name])
                
                sections_text = ""
                if "sections" in system:
                    sections_text = "\n".join([
                        f"- {section_name} (Cat: <#{data.get('category_id', 'None')}>, Role: <@&{data.get('support_role_id', 'None')}>)"
                        for section_name, data in system["sections"].items()
                    ])
                
                embed.add_field(
                    name=f"System: {name}",
                    value=(
                        f"**Channel:** {channel}\n"
                        f"**Sections:**\n{sections_text or 'None'}\n"
                        f"**Open Tickets:** {open_tickets}\n"
                        f"**Total Tickets:** {total_tickets}"
                    ),
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error in ticket list command: {str(e)}")
            embed = discord.Embed(
                description=f"{CROSS_EMOJI} An error occurred while fetching the ticket list. Please try again later.",
                color=discord.Color.default()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    cog = Ticket(bot)
    await bot.add_cog(cog)
    
    # Register the command group if not already present
    if not bot.tree.get_command("ticket"):
        bot.tree.add_command(cog.ticket)
    
    # Register all persistent views
    bot.add_view(TicketSetupView(bot, None))
    bot.add_view(SectionSetupView(bot, None, None, None))
    bot.add_view(SectionSelectView(bot, None, []))
    bot.add_view(TicketCloseView(bot, None))
    bot.add_view(DeleteSectionView(bot, None, None))
