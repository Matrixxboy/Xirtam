import discord
import datetime
from discord import app_commands, ui
from discord.ext import commands
from typing import Literal

projects = {}

class ProjectModule(commands.Cog, name="Project"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    project_group = app_commands.Group(name="project", description="Commands for project management")
    task_group = app_commands.Group(name="task", description="Commands for task management")

    @project_group.command(name="create", description="Creates a new project.")
    @app_commands.checks.has_permissions(manage_channels=True, manage_roles=True)
    async def project_create(self, interaction: discord.Interaction, name: str, description: str = None):
        project_role = await interaction.guild.create_role(name=f"Project: {name}")
        category = discord.utils.get(interaction.guild.categories, name="Projects") or await interaction.guild.create_category("Projects")
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            project_role: discord.PermissionOverwrite(read_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        project_channel = await interaction.guild.create_text_channel(name=name, overwrites=overwrites, category=category)
        await interaction.user.add_roles(project_role)

        projects[name] = {
            "description": description, "status": "In Progress",
            "channel_id": project_channel.id, "role_id": project_role.id,
            "tasks": [], "archived": False
        }
        await self.update_project_embed(interaction.guild, name)
        await interaction.response.send_message(f"✅ Project '{name}' created! Channel: {project_channel.mention}", ephemeral=True)

    @project_group.command(name="adduser", description="Adds a user to a project.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def project_adduser(self, interaction: discord.Interaction, project_name: str, user: discord.Member):
        if project_name not in projects: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
        project_role = interaction.guild.get_role(projects[project_name]["role_id"])
        await user.add_roles(project_role)
        await interaction.response.send_message(f"✅ Added {user.mention} to '{project_name}'.", ephemeral=True)

    @project_group.command(name="archive", description="Archives a project.")
    @app_commands.checks.has_permissions(manage_channels=True, manage_roles=True)
    async def project_archive(self, interaction: discord.Interaction, project_name: str):
        if project_name not in projects: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
        project = projects[project_name]
        project["status"] = "Archived"
        project["archived"] = True
        
        channel = interaction.guild.get_channel(project["channel_id"])
        role = interaction.guild.get_role(project["role_id"])
        
        await channel.edit(name=f"archived-{channel.name}", overwrites={{**channel.overwrites, role: discord.PermissionOverwrite(read_messages=True, send_messages=False)}})
        await role.edit(name=f"archived-{role.name}")
        
        await self.update_project_embed(interaction.guild, project_name)
        await interaction.response.send_message(f"✅ Project '{project_name}' has been archived.", ephemeral=True)

    @project_group.command(name="update", description="Updates a project's details.")
    async def project_update(self, interaction: discord.Interaction, project_name: str, field: Literal['description', 'status'], new_value: str):
        if project_name not in projects: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
        projects[project_name][field] = new_value
        await self.update_project_embed(interaction.guild, project_name)
        await interaction.response.send_message(f"✅ Project '{project_name}' has been updated.", ephemeral=True)

    @task_group.command(name="add", description="Adds a task to a project.")
    async def task_add(self, interaction: discord.Interaction, project_name: str, task_description: str):
        if project_name not in projects: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
        task_id = len(projects[project_name]["tasks"]) + 1
        projects[project_name]["tasks"].append({"id": task_id, "description": task_description, "completed": False})
        await self.update_project_embed(interaction.guild, project_name)
        await interaction.response.send_message(f"✅ Task added to '{project_name}'.", ephemeral=True)

    @task_group.command(name="complete", description="Marks a task as complete.")
    async def task_complete(self, interaction: discord.Interaction, project_name: str, task_id: int):
        if project_name not in projects: return await interaction.response.send_message("❌ Project not found.", ephemeral=True)
        task = next((t for t in projects[project_name]["tasks"] if t["id"] == task_id), None)
        if not task: return await interaction.response.send_message("❌ Task not found.", ephemeral=True)
        task["completed"] = True
        await self.update_project_embed(interaction.guild, project_name)
        await interaction.response.send_message(f"✅ Task {task_id} in '{project_name}' marked as complete.", ephemeral=True)

    async def update_project_embed(self, guild: discord.Guild, project_name: str):
        project = projects.get(project_name)
        if not project: return
        channel = guild.get_channel(project["channel_id"])
        if not channel: return

        task_list = "\n".join([f"- `[{'x' if t['completed'] else ' '}]` ID: {t['id']} - {t['description']}" for t in project["tasks"]]) or "No tasks yet."
        embed = discord.Embed(title=f"Project Hub: {project_name}", color=discord.Color.dark_green(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Status", value=project['status'], inline=True)
        embed.add_field(name="Description", value=project['description'] or 'N/A', inline=False)
        embed.add_field(name="Tasks", value=task_list, inline=False)
        embed.set_footer(text=f"Project ID: {project['channel_id']}")

        async for message in channel.history(limit=10):
            if message.author == self.bot.user and message.embeds and message.embeds[0].title == f"Project Hub: {project_name}":
                return await message.edit(embed=embed)
        await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ProjectModule(bot))