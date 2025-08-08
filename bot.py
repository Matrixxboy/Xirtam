import os
from dotenv import load_dotenv
import discord
from discord import app_commands

# Load BOT TOKEN from .env
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Replace this with your actual Discord Server ID
GUILD_ID = int(os.getenv('GUILD_ID'))

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        # Sync only to the specific guild (instant updates)
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"✅ Logged in as {self.user}")
        print("✅ Slash commands synced to your server instantly!")

# Intents setup
intents = discord.Intents.default()
intents.message_content = True

# Create client
client = MyClient(intents=intents)

# Slash command: hello
@client.tree.command(name="hello", description="The bot says hello back to you")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Hello, {interaction.user.mention}! I'm now using slash commands."
    )

# Slash command: sync (owner only)
@client.tree.command(name="sync", description="Sync slash commands (owner only)")
async def sync(interaction: discord.Interaction):
    OWNER_ID = int(os.getenv("OWNER_ID"))  # Replace with your Discord ID
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ You are not the owner!", ephemeral=True)
        return

    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await client.tree.sync(guild=guild)
        await interaction.response.send_message(f"✅ Synced {len(synced)} command(s) to the server.")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to sync commands: {e}")

# Run bot
try:
    client.run(BOT_TOKEN)
except Exception as e:
    print(f"Error occurred: {e}")
