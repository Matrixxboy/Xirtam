import discord
import datetime
import random
from discord import app_commands, ui
from discord.ext import commands, tasks

# This is a simple in-memory dictionary to store events.
# For a production bot, you would want to use a database like SQLite or PostgreSQL.
events = {}

# --- UI Components ---

class EventRSVPView(ui.View):
    """A persistent view for event RSVP buttons."""
    def __init__(self):
        super().__init__(timeout=None)

    async def handle_rsvp(self, interaction: discord.Interaction, new_status: str):
        event_id = interaction.message.id
        if event_id not in events:
            return await interaction.response.send_message("This event seems to have expired or been canceled.", ephemeral=True)

        user = interaction.user
        going_list = events[event_id]["going"]
        interested_list = events[event_id]["interested"]

        if new_status == "going":
            if user in going_list:
                return await interaction.response.send_message("You are already marked as going.", ephemeral=True)
            going_list.append(user)
            if user in interested_list:
                interested_list.remove(user)
            await interaction.response.send_message("You are now marked as **going**!", ephemeral=True)
        elif new_status == "interested":
            if user in interested_list or user in going_list:
                return await interaction.response.send_message("You are already marked as interested or going.", ephemeral=True)
            interested_list.append(user)
            await interaction.response.send_message("You are now marked as **interested**.", ephemeral=True)

    @ui.button(label="✅ Going", style=discord.ButtonStyle.green, custom_id="event_rsvp_going_persistent")
    async def going(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_rsvp(interaction, "going")

    @ui.button(label="🤔 Interested", style=discord.ButtonStyle.blurple, custom_id="event_rsvp_interested_persistent")
    async def interested(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_rsvp(interaction, "interested")

class EventModal(ui.Modal, title="Create a New Event"):
    """A modal for users to input event details."""
    title_input = ui.TextInput(label="Event Title", style=discord.TextStyle.short)
    description_input = ui.TextInput(label="Description", style=discord.TextStyle.long)
    datetime_input = ui.TextInput(label="Date and Time (YYYY-MM-DD HH:MM UTC)", placeholder="e.g., 2025-12-25 18:00")
    location_input = ui.TextInput(label="Location", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            event_time = datetime.datetime.strptime(str(self.datetime_input), "%Y-%m-%d %H:%M")
        except ValueError:
            return await interaction.response.send_message("❌ Invalid date format. Please use YYYY-MM-DD HH:MM UTC.", ephemeral=True)

        if event_time < datetime.datetime.utcnow():
            return await interaction.response.send_message("❌ You cannot create an event in the past.", ephemeral=True)

        embed = discord.Embed(
            title=f"🎉 New Event: {self.title_input}",
            description=f"**Description:**\n{self.description_input}\n\n**When:** <t:{int(event_time.timestamp())}:F>\n**Where:** {self.location_input}",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Event created by {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

        await interaction.response.send_message("Event created!", ephemeral=True)
        event_message = await interaction.channel.send(embed=embed, view=EventRSVPView())

        events[event_message.id] = {
            "title": str(self.title_input),
            "time": event_time,
            "guild_id": interaction.guild.id,
            "channel_id": interaction.channel.id,
            "going": [], "interested": [], "reminders_sent": []
        }

# --- Main Cog Class ---

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(EventRSVPView()) # Register persistent view on bot startup
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    event_group = app_commands.Group(name="event", description="Commands for event management.")

    @event_group.command(name="create", description="Creates a new event.")
    @app_commands.checks.has_permissions(manage_events=True)
    async def event_create(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EventModal())

    @event_group.command(name="cancel", description="Cancels an event.")
    @app_commands.checks.has_permissions(manage_events=True)
    async def event_cancel(self, interaction: discord.Interaction, event_message_id: str):
        try:
            msg_id = int(event_message_id)
        except ValueError:
            return await interaction.response.send_message("❌ Invalid message ID.", ephemeral=True)

        if msg_id in events:
            del events[msg_id]
            try:
                msg = await interaction.channel.fetch_message(msg_id)
                await msg.delete()
            except discord.NotFound:
                pass # Message already deleted
            await interaction.response.send_message("✅ Event has been canceled.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No event found with that message ID.", ephemeral=True)

    @event_group.command(name="list", description="Lists all upcoming events.")
    async def event_list(self, interaction: discord.Interaction):
        if not events:
            embed = discord.Embed(
                title="No Upcoming Events",
                description="There are currently no scheduled events.\n*Note: Events are cleared when the bot restarts.*",
                color=discord.Color.light_grey(),
                timestamp=datetime.datetime.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = discord.Embed(title="Upcoming Events", color=discord.Color.dark_blue(), timestamp=datetime.datetime.utcnow())
        sorted_events = sorted(events.items(), key=lambda item: item[1]['time'])
        for msg_id, event in sorted_events:
            embed.add_field(
                name=event["title"],
                value=f"**Event ID:** `{msg_id}`\n<t:{int(event['time'].timestamp())}:F> - [Jump to Event](https://discord.com/channels/{interaction.guild.id}/{event['channel_id']}/{msg_id})",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @event_group.command(name="details", description="Shows the RSVP details for an event.")
    async def event_details(self, interaction: discord.Interaction, event_message_id: str):
        try:
            msg_id = int(event_message_id)
        except ValueError:
            return await interaction.response.send_message("❌ Invalid message ID.", ephemeral=True)

        if msg_id not in events:
            return await interaction.response.send_message("❌ No event found with that message ID.", ephemeral=True)

        event = events[msg_id]
        
        embed = discord.Embed(
            title=f"RSVP Details for: {event['title']}",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )

        going_users = "\n".join([user.mention for user in event["going"]]) or "No one yet."
        interested_users = "\n".join([user.mention for user in event["interested"]]) or "No one yet."

        embed.add_field(name=f"✅ Going ({len(event['going'])})", value=going_users, inline=False)
        embed.add_field(name=f"🤔 Interested ({len(event['interested'])})", value=interested_users, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        """Periodically checks and sends reminders for upcoming events."""
        now = datetime.datetime.utcnow()
        for event_id, event in list(events.items()):
            if event["time"] < now:
                del events[event_id]
                continue
            
            time_diff_24h = event["time"] - datetime.timedelta(hours=24)
            time_diff_1h = event["time"] - datetime.timedelta(hours=1)

            if '24h' not in event["reminders_sent"] and now > time_diff_24h:
                await self.send_reminder(event, "24 hours")
                event["reminders_sent"].append('24h')

            if '1h' not in event["reminders_sent"] and now > time_diff_1h:
                await self.send_reminder(event, "1 hour")
                event["reminders_sent"].append('1h')

    async def send_reminder(self, event, time_str):
        guild = self.bot.get_guild(event["guild_id"])
        if not guild: return
        channel = guild.get_channel(event["channel_id"])
        if not channel: return

        recipients = event["going"] + event["interested"]
        if not recipients: return

        mention_string = " ".join([user.mention for user in recipients])
        embed = discord.Embed(
            title=f"Reminder: {event['title']}",
            description=f"This event is starting in {time_str}!",
            color=discord.Color.gold()
        )
        await channel.send(content=mention_string, embed=embed)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

# This is the required setup function that discord.py looks for
async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))