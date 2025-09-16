import discord
import datetime
from discord import app_commands
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def create_mod_log_embed(self, interaction: discord.Interaction, action: str, user: discord.User, reason: str, color: discord.Color):
        embed = discord.Embed(
            title=f"{action}: {user.name}",
            color=color,
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_footer(text=f"User ID: {user.id}")
        return embed

    @app_commands.command(name="kick", description="Kicks a member from the server.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ You cannot kick a member with a higher or equal role.", ephemeral=True)
        
        try:
            await member.send(f"You have been kicked from **{interaction.guild.name}** for: {reason}")
        except discord.Forbidden:
            pass
        
        await member.kick(reason=reason)
        embed = await self.create_mod_log_embed(interaction, "Kick", member, reason, discord.Color.orange())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Bans a member from the server.")
    @app_commands.checks.has_permissions(administrator=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided."):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ You cannot ban a member with a higher or equal role.", ephemeral=True)
        
        try:
            await member.send(f"You have been banned from **{interaction.guild.name}** for: {reason}")
        except discord.Forbidden:
            pass

        await member.ban(reason=reason)
        embed = await self.create_mod_log_embed(interaction, "Ban", member, reason, discord.Color.red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unban", description="Unbans a user from the server.")
    @app_commands.checks.has_permissions(administrator=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided."):
        try:
            user = await self.bot.fetch_user(int(user_id))
        except (ValueError, discord.NotFound):
            return await interaction.response.send_message("❌ Invalid user ID or user not found.", ephemeral=True)

        try:
            await interaction.guild.unban(user, reason=reason)
            embed = await self.create_mod_log_embed(interaction, "Unban", user, reason, discord.Color.green())
            await interaction.response.send_message(embed=embed)
        except discord.NotFound:
            await interaction.response.send_message(f"❌ User {user.name} is not banned.", ephemeral=True)

    @app_commands.command(name="softban", description="Bans and then immediately unbans a member to delete their messages.")
    @app_commands.checks.has_permissions(administrator=True)
    async def softban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Message cleanup."):
        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ You cannot softban a member with a higher or equal role.", ephemeral=True)

        await member.ban(reason=f"Softban: {reason}", delete_message_days=7)
        await interaction.guild.unban(member, reason="Softban cleanup")

        embed = await self.create_mod_log_embed(interaction, "Softban", member, reason, discord.Color.dark_red())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="purge", description="Deletes a specified number of messages.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Deleted {len(deleted)} messages.")

    # --- Error Handling ---
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("❌ You do not have the required permissions to use this command.", ephemeral=True)
        elif isinstance(error, app_commands.errors.CommandInvokeError):
            await interaction.response.send_message("❌ An error occurred while executing the command.", ephemeral=True)
            print(error.original)
        else:
            await interaction.response.send_message("❌ An unexpected error occurred.", ephemeral=True)
            print(error)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
