import os
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
from flask import Flask
import threading

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))

# --- Flask server for Render ---
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Xirtam Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))  # Render provides the PORT environment variable
    app.run(host="0.0.0.0", port=port)

# Start Flask server in a separate thread
threading.Thread(target=run_web).start()

# --- Discord Bot Setup ---
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='!',  # Prefix is required but we are using slash commands
            intents=discord.Intents.default()
        )

    async def setup_hook(self):
        # Load all cogs
        for root, dirs, files in os.walk('cogs'):
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    cog_name = path.replace(os.sep, '.')[:-3]
                    try:
                        await self.load_extension(cog_name)
                        print(f"✅ Loaded cog: {cog_name}")
                    except Exception as e:
                        print(f"❌ Failed to load cog {cog_name}: {e}")

        # Sync commands to guild
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"✅ Logged in as {self.user}")
        print("✅ Slash commands synced to your server!")

async def main():
    bot = MyBot()
    await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error occurred: {e}")
