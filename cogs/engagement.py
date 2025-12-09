import discord
import random
import re
import aiohttp
import datetime
from discord import app_commands
from discord.ext import commands

class Engagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    @app_commands.command(name="poll", description="Creates a poll with up to 10 options.")
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None, option5: str = None, option6: str = None, option7: str = None, option8: str = None, option9: str = None, option10: str = None):
        options = [opt for opt in [option1, option2, option3, option4, option5, option6, option7, option8, option9, option10] if opt is not None]
        
        if len(options) < 2:
            return await interaction.response.send_message("❌ Please provide at least two options for the poll.", ephemeral=True)
        if len(options) > 10:
            return await interaction.response.send_message("❌ You can only provide up to 10 options for a poll.", ephemeral=True)

        embed = discord.Embed(
            title=f"📊 Poll: {question}", 
            description="\n".join([f"{self.number_emojis[i]} {opt}" for i, opt in enumerate(options)]),
            color=discord.Color.dark_purple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f"Poll started by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()

        for i in range(len(options)):
            await message.add_reaction(self.number_emojis[i])

    @app_commands.command(name="techfact", description="Fetches a random tech fact.")
    async def techfact(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://techy-api.vercel.app/api/json") as response:
                if response.status == 200:
                    data = await response.json()
                    fact = data['message']
                    embed = discord.Embed(title="💡 Tech Fact", description=fact, color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
                    await interaction.followup.send(embed=embed)
                else:
                    await interaction.followup.send("❌ Could not fetch a tech fact at this time.", ephemeral=True)

    @app_commands.command(name="coinflip", description="Flips a coin.")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        if result == "Heads":
            file = discord.File("public/coin/heads.png", filename="heads.png")
            embed = discord.Embed(title="Coin Flip", description=f"The coin landed on **{result}**!", color=discord.Color.gold(), timestamp=datetime.datetime.utcnow())
            embed.set_thumbnail(url="attachment://heads.png")
        else:
            file = discord.File("public/coin/tails.png", filename="tails.png")
            embed = discord.Embed(title="Coin Flip", description=f"The coin landed on **{result}**!", color=discord.Color.gold(), timestamp=datetime.datetime.utcnow())
            embed.set_thumbnail(url="attachment://tails.png")
        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="rolldice", description="Rolls dice in NdN format (e.g., 2d6).")
    async def rolldice(self, interaction: discord.Interaction, dice: str):
        match = re.match(r"(\d+)d(\d+)", dice.lower())
        if not match:
            return await interaction.response.send_message("❌ Invalid format! Please use NdN format (e.g., `2d6`).", ephemeral=True)
        
        num_dice, num_sides = int(match.group(1)), int(match.group(2))
        if not (1 <= num_dice <= 25) or not (1 <= num_sides <= 100):
            return await interaction.response.send_message("❌ Please use reasonable numbers for dice (1-25 dice, 1-100 sides).", ephemeral=True)

        rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
        total = sum(rolls)

        embed = discord.Embed(
            title=f"🎲 Dice Roll: {dice}",
            description=f"**Total:** {total}\n**Rolls:** {', '.join(map(str, rolls))}",
            color=discord.Color.dark_red(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Engagement(bot))