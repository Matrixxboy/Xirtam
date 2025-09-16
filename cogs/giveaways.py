import discord
import asyncio
import random
import datetime
from discord import app_commands
from discord.ext import commands

def parse_duration(duration_str: str) -> int:
    unit = duration_str[-1].lower()
    value = int(duration_str[:-1])
    if unit == 's': return value
    elif unit == 'm': return value * 60
    elif unit == 'h': return value * 3600
    elif unit == 'd': return value * 86400
    else: raise ValueError("Invalid duration unit. Use s, m, h, or d.")

class Giveaways(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.completed_giveaways = {}
        self.active_giveaways = {}

    giveaway_group = app_commands.Group(name="giveaway", description="Commands for managing giveaways.")

    @giveaway_group.command(name="start", description="Starts a giveaway.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_start(self, interaction: discord.Interaction, duration: str, winners: app_commands.Range[int, 1, None], prize: str):
        try:
            seconds = parse_duration(duration)
        except ValueError as e:
            return await interaction.response.send_message(f"❌ {e}", ephemeral=True)

        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)

        embed = discord.Embed(
            title=f"🎉 Giveaway: {prize} 🎉",
            description=f"React with 🎉 to enter!\nEnds <t:{int(end_time.timestamp())}:F>\nWinners: {winners}",
            color=discord.Color.magenta(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Started by {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

        await interaction.response.send_message("Giveaway started!", ephemeral=True)
        giveaway_message = await interaction.channel.send(embed=embed)
        await giveaway_message.add_reaction("🎉")

        debug_message = (
            f"**DEBUG INFO (Giveaway Time)**\n"
            f"Calculated UTC End Time: `{end_time}`\n"
            f"Raw Unix Timestamp: `{int(end_time.timestamp())}`\n"
            f"Timezone Info: `{end_time.tzinfo}`"
        )
        await interaction.followup.send(debug_message, ephemeral=True)

        self.active_giveaways[giveaway_message.id] = {
            "prize": prize,
            "end_time": end_time,
            "winners": winners,
            "channel_id": interaction.channel.id
        }

        await asyncio.sleep(seconds)

        try:
            updated_message = await interaction.channel.fetch_message(giveaway_message.id)
        except discord.NotFound:
            if giveaway_message.id in self.active_giveaways:
                del self.active_giveaways[giveaway_message.id]
            return

        reaction = discord.utils.get(updated_message.reactions, emoji="🎉")
        participants = [user async for user in reaction.users() if not user.bot]
        self.completed_giveaways[updated_message.id] = participants

        if giveaway_message.id in self.active_giveaways:
            del self.active_giveaways[giveaway_message.id]

        if not participants:
            ended_embed = discord.Embed(title=f"Giveaway Ended: {prize}", description="No one entered the giveaway.", color=discord.Color.dark_grey(), timestamp=datetime.datetime.utcnow())
            await updated_message.edit(embed=ended_embed)
            return

        winner_list = random.sample(participants, k=min(winners, len(participants)))
        winner_mentions = ", ".join([winner.mention for winner in winner_list])
        
        result_embed = discord.Embed(
            title=f"🎉 Giveaway Ended: {prize} 🎉",
            description=f"Congratulations to {winner_mentions}! You won the **{prize}**.",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        await updated_message.reply(embed=result_embed)

    @giveaway_group.command(name="reroll", description="Rerolls a completed giveaway.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        try:
            msg_id = int(message_id)
        except ValueError:
            return await interaction.response.send_message("❌ Invalid message ID.", ephemeral=True)

        if msg_id not in self.completed_giveaways:
            return await interaction.response.send_message("❌ This is not a completed giveaway message ID or it is too old.", ephemeral=True)

        participants = self.completed_giveaways[msg_id]
        if not participants:
            return await interaction.response.send_message("❌ There were no participants in this giveaway.", ephemeral=True)

        new_winner = random.choice(participants)
        
        embed = discord.Embed(
            title="🎉 Giveaway Reroll 🎉",
            description=f"The new winner is {new_winner.mention}! Congratulations!",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

    @giveaway_group.command(name="list", description="Lists all active giveaways.")
    async def giveaway_list(self, interaction: discord.Interaction):
        if not self.active_giveaways:
            embed = discord.Embed(
                title="No Active Giveaways",
                description="There are currently no active giveaways.",
                color=discord.Color.light_grey(),
                timestamp=datetime.datetime.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = discord.Embed(title="Active Giveaways", color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
        for msg_id, giveaway in self.active_giveaways.items():
            embed.add_field(
                name=f"Prize: {giveaway['prize']}",
                value=f"Ends: <t:{int(giveaway['end_time'].timestamp())}:F>\nWinners: {giveaway['winners']}\n[Jump to Giveaway](https://discord.com/channels/{interaction.guild.id}/{giveaway['channel_id']}/{msg_id})",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message("❌ You do not have the `Manage Server` permission to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ An unexpected error occurred: {error}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaways(bot))