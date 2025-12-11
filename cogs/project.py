import discord
import datetime
from discord import app_commands, ui
from discord.ext import commands
from typing import Literal
from database.models import Project, Task

class ProjectModule(commands.Cog, name="Project"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    project_group = app_commands.Group(name="project", description="Commands for project management")
    task_group = app_commands.Group(name="task", description="Commands for task management")

    @project_group.command(name="create", description="Creates a new project.")
    @app_commands.checks.has_permissions(manage_channels=True, manage_roles=True)
    async def project_create(self, interaction: discord.Interaction, name: str, description: str = None):
        # Check if project exists in guild with same name
        exists = await Project.find_one(Project.name == name, Project.guild_id == interaction.guild_id)
        if exists:
            return await interaction.response.send_message(f"❌ Project '{name}' already exists.", ephemeral=True)

        project_role = await interaction.guild.create_role(name=f"Project: {name}")
        category = discord.utils.get(interaction.guild.categories, name="Projects") or await interaction.guild.create_category("Projects")
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            project_role: discord.PermissionOverwrite(read_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        project_channel = await interaction.guild.create_text_channel(name=name, overwrites=overwrites, category=category)
        await interaction.user.add_roles(project_role)

        project_doc = Project(
            name=name,
            guild_id=interaction.guild_id,
            description=description,
            channel_id=project_channel.id,
            role_id=project_role.id
        )
        await project_doc.create()

        await self.update_project_embed(interaction.guild, project_doc)
        await interaction.response.send_message(f"✅ Project '{name}' created! Channel: {project_channel.mention}", ephemeral=True)

    @project_group.command(name="adduser", description="Adds a user to a project.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def project_adduser(self, interaction: discord.Interaction, project_name: str, user: discord.Member):
        project = await Project.find_one(Project.name == project_name, Project.guild_id == interaction.guild_id)
        if not project: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
        
        project_role = interaction.guild.get_role(project.role_id)
        await user.add_roles(project_role)
        await interaction.response.send_message(f"✅ Added {user.mention} to '{project_name}'.", ephemeral=True)

    @project_group.command(name="archive", description="Archives a project.")
    @app_commands.checks.has_permissions(manage_channels=True, manage_roles=True)
    async def project_archive(self, interaction: discord.Interaction, project_name: str):
        project = await Project.find_one(Project.name == project_name, Project.guild_id == interaction.guild_id)
        if not project: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
        
        project.status = "Archived"
        project.archived = True
        await project.save()
        
        channel = interaction.guild.get_channel(project.channel_id)
        role = interaction.guild.get_role(project.role_id)
        
        if channel:
             await channel.edit(name=f"archived-{channel.name}", overwrites={**channel.overwrites, role: discord.PermissionOverwrite(read_messages=True, send_messages=False)})
        if role:
             await role.edit(name=f"archived-{role.name}")
        
        await self.update_project_embed(interaction.guild, project)
        await interaction.response.send_message(f"✅ Project '{project_name}' has been archived.", ephemeral=True)
    
    @project_group.command(name="unarchive", description="Unarchives a project.")
    @app_commands.checks.has_permissions(manage_channels=True, manage_roles=True)
    async def project_unarchive(self, interaction: discord.Interaction, project_name: str):
        project = await Project.find_one(Project.name == project_name, Project.guild_id == interaction.guild_id)
        if not project: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
        
        project.status = "Unarchived"
        project.archived = False
        await project.save()
        
        channel = interaction.guild.get_channel(project.channel_id)
        role = interaction.guild.get_role(project.role_id)
        
        if channel:
            await channel.edit(name=f"{channel.name}", overwrites={**channel.overwrites, role: discord.PermissionOverwrite(read_messages=True, send_messages=False)})
        if role:
            await role.edit(name=f"{role.name}")
        
        await self.update_project_embed(interaction.guild, project)
        await interaction.response.send_message(f"✅ Project '{project_name}' has been unarchived.", ephemeral=True)

    @project_group.command(name="update", description="Updates a project's details.")
    async def project_update(self, interaction: discord.Interaction, project_name: str, field: Literal['description', 'status'], new_value: str):
        project = await Project.find_one(Project.name == project_name, Project.guild_id == interaction.guild_id)
        if not project: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
        
        if field == "description":
            project.description = new_value
        elif field == "status":
            project.status = new_value
            
        await project.save()
        await self.update_project_embed(interaction.guild, project)
        await interaction.response.send_message(f"✅ Project '{project_name}' has been updated.", ephemeral=True)

    @project_group.command(name="status", description="Shows the project's status.")
    async def project_status(self, interaction: discord.Interaction, project_name: str):
        project = await Project.find_one(
            Project.name == project_name,
            Project.guild_id == interaction.guild_id
        )

        if not project:
            return await interaction.response.send_message(
                "❌ Project not found.",
                ephemeral=True
            )

        # -----------------------------
        # Build Task List
        # -----------------------------
        if not project.tasks:
            tasks_text = "> No tasks found."
        else:
            tasks_text = ""
            for task in project.tasks:
                status_symbol = "✅" if task.completed else "❌"
                completed_by = (
                    f" • Completed by <@{task.completed_by}>"
                    if task.completed and task.completed_by else ""
                )
                tasks_text += f"{status_symbol} **{task.description}**{completed_by}\n"

        # -----------------------------
        # Create Aesthetic Embed
        # -----------------------------
        embed = discord.Embed(
            title=f"📌 Project Status — {project.name}",
            description=(
                f"**Status:** `{project.status}`\n"
                f"**Description:** {project.description or 'N/A'}`"
            ),
            color=discord.Color.from_rgb(145, 71, 255)  # Purple left border
        )

        embed.set_thumbnail(url="https://tenor.com/view/coffee-drink-cafe-morning-kopi-gif-26447308")
        embed.add_field(
            name="📝 Tasks",
            value=tasks_text,
            inline=False
        )

        embed.set_footer(
            text=f"Requested by {interaction.user.name}",
            icon_url=interaction.user.display_avatar.url
        )

        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed, ephemeral=True)


    @task_group.command(name="add", description="Adds a task to a project.")
    async def task_add(self, interaction: discord.Interaction, project_name: str, task_description: str):
        project = await Project.find_one(Project.name == project_name, Project.guild_id == interaction.guild_id)
        if not project: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)

        task_id = len(project.tasks) + 1
        new_task = Task(id=task_id, description=task_description, completed=False)
        project.tasks.append(new_task)
        await project.save()
        embed = discord.Embed(title=f"Task added to '{project_name}'.", color=discord.Color.yellow())
        embed.add_field(name="Task ID", value=task_id, inline=False)
        embed.add_field(name="Task Description", value=task_description, inline=False)
        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await self.update_project_embed(interaction.guild, project)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @task_group.command(name="complete", description="Marks a task as complete.")
    async def task_complete(self, interaction: discord.Interaction, project_name: str, task_id: int):

        project = await Project.find_one(Project.name == project_name, Project.guild_id == interaction.guild_id)
        if not project:
            return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
        
        task = next((t for t in project.tasks if t.id == task_id), None)
        if not task:
            return await interaction.response.send_message("❌ Task not found.", ephemeral=True)
        
        task.completed = True
        task.completed_by = interaction.user.id
        await project.save()

        GIF_LIST = [
            "https://tenor.com/view/yes-yeah-we-can-do-it-lets-go-baby-gif-15804427",
            "https://tenor.com/view/celebrate-weekend-vibe-friday-be-like-gif-19399428",
            "https://tenor.com/view/you-did-it-congratulations-congrats-smile-hands-up-gif-16733430",
            "https://tenor.com/view/mission-impossible-we-got-this-you-got-this-aja-oh-yeah-gif-9140872",
            "https://tenor.com/view/celebrate-happy-you-did-it-oprah-winfrey-gif-16871108",
            "https://tenor.com/view/i-knew-you-could-do-it-austin-evans-you-did-it-you-made-it-gif-25755531"
        ]
        
        gif_url = random.choice(GIF_LIST)

        embed = discord.Embed(
            title="🎯 Task Completed!",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url="https://tenor.com/view/you-did-it-way-to-go-medal-award-food-for-thought-gif-15952346")
        embed.set_image(url=gif_url)
        embed.add_field(name="Task ID", value=task_id, inline=False)
        embed.add_field(name="Task Description", value=task.description, inline=False)
        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        await self.update_project_embed(interaction.guild, project)
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @task_group.command(name="status", description="Shows the tasks status.")
    async def task_status(self, interaction: discord.Interaction, project_name: str):
        project = await Project.find_one(Project.name == project_name, Project.guild_id == interaction.guild_id)
        if not project: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
        await interaction.response.send_message(f"Status: {project.status}", ephemeral=True)

    async def update_project_embed(self, guild: discord.Guild, project: Project):
        channel = guild.get_channel(project.channel_id)
        if not channel: return

        task_list = "\n".join([
            f"- [`{'✅' if t.completed else '❌'}`] ID: {t.id} - {t.description}"
            for t in project.tasks
        ]) or "No tasks yet."
        embed = discord.Embed(title=f"Project Hub: {project.name}", color=discord.Color.dark_green(), timestamp=datetime.datetime.utcnow())
        embed.set_thumbnail(url="https://tenor.com/view/coffee-drink-cafe-morning-kopi-gif-26447308")
        embed.add_field(name="Status", value=project.status, inline=False)
        embed.add_field(name="Description", value=project.description or 'N/A', inline=False)
        embed.add_field(name="Tasks", value=task_list, inline=False)
        embed.set_footer(text=f"Project ID: {project.channel_id}")

        async for message in channel.history(limit=10):
            if message.author == self.bot.user and message.embeds and message.embeds[0].title == f"Project Hub: {project.name}":
                return await message.edit(embed=embed)
        await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ProjectModule(bot))