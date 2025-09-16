import os
import discord
import datetime
from discord import app_commands, ui
from discord.ext import commands

GUILD_ID = int(os.getenv('GUILD_ID'))

def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        return await interaction.client.is_owner(interaction.user)
    return app_commands.check(predicate)

class HelpPaginator(ui.View):
    def __init__(self, embeds: list[discord.Embed]):
        super().__init__(timeout=180) # Timeout after 3 minutes of inactivity
        self.embeds = embeds
        self.current_page = 0
        self.update_buttons()

    def update_buttons(self):
        self.children[0].disabled = (self.current_page == 0) # Previous button
        self.children[1].disabled = (self.current_page == len(self.embeds) - 1) # Next button

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)

    @ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous_button(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.defer() # Do nothing if already on first page

    @ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: ui.Button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
        else:
            await interaction.response.defer() # Do nothing if already on last page

class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_help_pages(self) -> list[discord.Embed]:
        embeds = []
        for cog_name, cog in self.bot.cogs.items():
            commands_list = cog.get_app_commands()
            if commands_list:
                embed = discord.Embed(
                    title=f"NexGen Bot Help: {cog_name}",
                    description=f"Commands for the {cog_name} module:",
                    color=discord.Color.blue(),
                    timestamp=datetime.datetime.utcnow()
                )
                if self.bot.user.avatar:
                    embed.set_thumbnail(url=self.bot.user.avatar.url)
                
                for command in commands_list:
                    # Handle command groups
                    if isinstance(command, app_commands.Group):
                        subcommands_str = "\n".join([f"`/{command.name} {sub.name}` - {sub.description}" for sub in command.commands])
                        if subcommands_str:
                            embed.add_field(name=f"**/{command.name}** (Group)", value=subcommands_str, inline=False)
                    else:
                        embed.add_field(name=f"**/{command.name}**", value=command.description, inline=False)
                
                embed.set_footer(text=f"Page {len(embeds) + 1}/{len(self.bot.cogs)}")
                embeds.append(embed)
        return embeds

    # --- Commands ---
    @app_commands.command(name="help", description="Displays a list of all available commands.")
    async def help(self, interaction: discord.Interaction):
        embeds = await self.create_help_pages()
        if not embeds:
            return await interaction.response.send_message("No commands found.", ephemeral=True)
        
        paginator = HelpPaginator(embeds)
        paginator.message = await interaction.response.send_message(embed=embeds[0], view=paginator, ephemeral=True)

    @app_commands.command(name="serverinfo", description="Shows information about the server.")
    async def serverinfo(self, interaction: discord.Interaction):
        try:
            guild = interaction.guild
            
            # Fetch owner if not in cache
            owner = guild.owner
            if not owner:
                owner = await guild.fetch_member(guild.owner_id)

            embed = discord.Embed(
                title=f"Server Info: {guild.name}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            embed.add_field(name="Owner", value=owner.mention, inline=True)
            embed.add_field(name="Members", value=guild.member_count, inline=True)
            embed.add_field(name="Created At", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
            embed.add_field(name="Roles", value=len(guild.roles), inline=True)
            embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
            embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
            embed.set_footer(text=f"Server ID: {guild.id}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred while fetching server info: {e}", ephemeral=True)

    @app_commands.command(name="userinfo", description="Shows information about a user.")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(
            title=f"User Info: {member.display_name}",
            color=member.color,
            timestamp=datetime.datetime.utcnow()
        )
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Full Name", value=str(member), inline=True)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:D>", inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
        roles = [role.mention for role in member.roles[1:]] # Exclude @everyone
        embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles) if roles else "No roles", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sync", description="Sync slash commands (owner only)")
    @is_owner()
    async def sync(self, interaction: discord.Interaction):
        try:
            synced = await self.bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            await interaction.response.send_message(f"✅ Synced {len(synced)} command(s) to the server.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to sync commands: {e}", ephemeral=True)

    # --- Events ---
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
            
        welcome_channel_name = "welcome"
        channel = discord.utils.get(member.guild.text_channels, name=welcome_channel_name)
        if channel:
            embed = discord.Embed(
                title=f"Welcome to {member.guild.name}!",
                description=f"Hello {member.mention}, we're glad to have you here! Please check out the server rules and select your roles.",
                color=discord.Color.purple(),
                timestamp=datetime.datetime.utcnow()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaDB6d2Q4eXN6c3B6d2w0b3RzZ3g3d2g3d2cifQ/hJqsdhTUKd5E4/giphy.gif") # Example GIF
            embed.set_footer(text="We hope you enjoy your stay!")
            await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))