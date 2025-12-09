import discord
import asyncio
import random
import datetime
from discord import app_commands
from discord.ext import commands
from database.models import Giveaway

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
        # We can now rely on DB for active giveaways persistence
        # but for performance in small scale, a cache is fine.
        # However, for true persistence across restart, we should load from DB on startup.
        self.active_giveaways_cache = {}

    async def cog_load(self):
        # Load active giveaways from DB on startup
        active = await Giveaway.find(Giveaway.status == "active").to_list()
        for g in active:
            # Re-schedule the finish task if end time is in future
            remaining = (g.end_time - datetime.datetime.utcnow()).total_seconds()
            if remaining > 0:
                self.bot.loop.create_task(self.monitor_giveaway(g.message_id, remaining))
            else:
                 # It should have ended, run end logic immediately
                 self.bot.loop.create_task(self.end_giveaway(g.message_id))

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

        # Save to DB
        ga_doc = Giveaway(
            _id=giveaway_message.id,
            channel_id=interaction.channel.id,
            guild_id=interaction.guild_id,
            prize=prize,
            end_time=end_time,
            winners_count=winners,
            status="active"
        )
        await ga_doc.create()

        # Schedule end
        self.bot.loop.create_task(self.monitor_giveaway(giveaway_message.id, seconds))

    async def monitor_giveaway(self, message_id: int, duration: float):
        await asyncio.sleep(duration)
        await self.end_giveaway(message_id)

    async def end_giveaway(self, message_id: int):
        ga = await Giveaway.get(message_id)
        if not ga or ga.status != "active":
            return
        
        ga.status = "ended"
        
        channel = self.bot.get_channel(ga.channel_id)
        if not channel:
            # Channel deleted? Mark ended
            await ga.save()
            return
            
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            await ga.save()
            return

        reaction = discord.utils.get(message.reactions, emoji="🎉")
        if not reaction:
             participants = []
        else:
             participants = [user.id async for user in reaction.users() if not user.bot]
        
        ga.participants = participants
        await ga.save()

        if not participants:
            ended_embed = discord.Embed(title=f"Giveaway Ended: {ga.prize}", description="No one entered the giveaway.", color=discord.Color.dark_grey(), timestamp=datetime.datetime.utcnow())
            await message.edit(embed=ended_embed)
            return

        winner_ids = random.sample(participants, k=min(ga.winners_count, len(participants)))
        winner_mentions = ", ".join([f"<@{uid}>" for uid in winner_ids])
        
        result_embed = discord.Embed(
            title=f"🎉 Giveaway Ended: {ga.prize} 🎉",
            description=f"Congratulations to {winner_mentions}! You won the **{ga.prize}**.",
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        await message.reply(embed=result_embed)

    @giveaway_group.command(name="reroll", description="Rerolls a completed giveaway.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def giveaway_reroll(self, interaction: discord.Interaction, message_id: str):
        try:
            msg_id = int(message_id)
        except ValueError:
            return await interaction.response.send_message("❌ Invalid message ID.", ephemeral=True)

        ga = await Giveaway.get(msg_id)
        if not ga or ga.status != "ended":
             return await interaction.response.send_message("❌ This is not a completed giveaway or not found in DB.", ephemeral=True)

        if not ga.participants:
            return await interaction.response.send_message("❌ There were no participants in this giveaway.", ephemeral=True)

        new_winner_id = random.choice(ga.participants)
        
        embed = discord.Embed(
            title="🎉 Giveaway Reroll 🎉",
            description=f"The new winner is <@{new_winner_id}>! Congratulations!",
            color=discord.Color.gold(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

    @giveaway_group.command(name="list", description="Lists all active giveaways.")
    async def giveaway_list(self, interaction: discord.Interaction):
        active = await Giveaway.find(Giveaway.guild_id == interaction.guild_id, Giveaway.status == "active").to_list()
        
        if not active:
            embed = discord.Embed(
                title="No Active Giveaways",
                description="There are currently no active giveaways.",
                color=discord.Color.light_grey(),
                timestamp=datetime.datetime.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = discord.Embed(title="Active Giveaways", color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
        for ga in active:
            embed.add_field(
                name=f"Prize: {ga.prize}",
                value=f"Ends: <t:{int(ga.end_time.timestamp())}:F>\nWinners: {ga.winners_count}\n[Jump to Giveaway](https://discord.com/channels/{interaction.guild_id}/{ga.channel_id}/{ga.message_id})",
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