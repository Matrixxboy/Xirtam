import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
from services.user_service import user_service

def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        return await interaction.client.is_owner(interaction.user)
    return app_commands.check(predicate)

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.shop_items = {
            "watch": {"price": 1000, "description": "A shiny new watch."},
            "laptop": {"price": 5000, "description": "A powerful new laptop."},
            "car": {"price": 10000, "description": "A brand new car."}
        }

    @app_commands.command(name="inventory", description="Check your inventory.")
    async def inventory(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        
        user_data = await user_service.get_user(user.id)
        inventory = user_data.inventory

        embed = discord.Embed(
            title=f"✨ {user.display_name}'s Inventory",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )

        if not inventory:
            embed.description = "Your inventory is empty."
        else:
            for item, count in inventory.items():
                embed.add_field(name=item.capitalize(), value=f"x{count}", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Buy an item from the shop.")
    async def buy(self, interaction: discord.Interaction, item: str):
        item = item.lower()
        if item not in self.shop_items:
            await interaction.response.send_message("❌ That item is not in the shop.", ephemeral=True)
            return

        user_id = interaction.user.id
        item_price = self.shop_items[item]["price"]

        user_data = await user_service.get_user(user_id)
        if user_data.balance < item_price:
                await interaction.response.send_message("❌ You don't have enough Matrixx to buy this item.", ephemeral=True)
                return
        
        await user_service.update_balance(user_id, -item_price)
        await user_service.update_inventory(user_id, item, 1)

        embed = discord.Embed(
            title="✨ Purchase Successful",
            description=f"You have successfully purchased a **{item}** for **{item_price}** Matrixx!",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="shop", description="View the item shop.")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="✨ Item Shop",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )

        for item, details in self.shop_items.items():
            embed.add_field(name=f"{item.capitalize()} - {details['price']} Matrixx", value=details['description'], inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reset-economy", description="Reset the entire economy (owner only).")
    @is_owner()
    async def reset_economy(self, interaction: discord.Interaction):
        from database.models import User
        # Beanie delete all
        await User.find_all().delete()

        embed = discord.Embed(
            title="✨ Economy Reset",
            description="The entire economy has been reset.",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="remove-money", description="Remove Matrixx from a user's balance (admin only).")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_money(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ Please enter a positive amount.", ephemeral=True)
            return

        await user_service.update_balance(user.id, -amount)

        embed = discord.Embed(
            title="✨ Money Removed",
            description=f"Successfully removed **{amount}** Matrixx from {user.mention}'s balance.",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add-money", description="Add Matrixx to a user's balance (admin only).")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_money(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ Please enter a positive amount.", ephemeral=True)
            return

        await user_service.update_balance(user.id, amount)

        embed = discord.Embed(
            title="✨ Money Added",
            description=f"Successfully added **{amount}** Matrixx to {user.mention}'s balance.",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roulette", description="Play roulette.")
    @app_commands.describe(bet_type="Choose what to bet on (red, black, or a number from 0-36)", amount="The amount of Matrixx to bet")
    async def roulette(self, interaction: discord.Interaction, bet_type: str, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ Please enter a positive amount to bet.", ephemeral=True)
            return

        user_id = interaction.user.id
        
        user_data = await user_service.get_user(user_id)
        if user_data.balance < amount:
                await interaction.response.send_message("❌ You don't have enough Matrixx to play.", ephemeral=True)
                return

        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

        result = random.randint(0, 36)
        winnings = 0
        message = ""

        if bet_type.lower() == "red":
            if result in red_numbers:
                winnings = amount
                message = f"🔴 The ball landed on {result} (red). You won {winnings} Matrixx! 🔴"
            else:
                winnings = -amount
                message = f"⚫ The ball landed on {result} (black). You lost. ⚫"
        elif bet_type.lower() == "black":
            if result in black_numbers:
                winnings = amount
                message = f"⚫ The ball landed on {result} (black). You won {winnings} Matrixx! ⚫"
            else:
                winnings = -amount
                message = f"🔴 The ball landed on {result} (red). You lost. 🔴"
        else:
            try:
                bet_number = int(bet_type)
                if 0 <= bet_number <= 36:
                    if result == bet_number:
                        winnings = amount * 35
                        message = f"🎉 The ball landed on {result}! You won {winnings} Matrixx! 🎉"
                    else:
                        winnings = -amount
                        message = f"💔 The ball landed on {result}. You lost. 💔"
                else:
                        await interaction.response.send_message("❌ Please enter a valid number between 0 and 36.", ephemeral=True)
                        return
            except ValueError:
                await interaction.response.send_message("❌ Invalid bet type. Please choose red, black, or a number.", ephemeral=True)
                return

        await user_service.update_balance(user_id, winnings)

        embed = discord.Embed(
            title="룰렛 Roulette 룰렛",
            description=message,
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="slots", description="Play the slot machine.")
    async def slots(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ Please enter a positive amount to bet.", ephemeral=True)
            return

        user_id = interaction.user.id
        
        user_data = await user_service.get_user(user_id)
        if user_data.balance < amount:
                await interaction.response.send_message("❌ You don't have enough Matrixx to play.", ephemeral=True)
                return

        reels = ["🍒", "🍊", "🍇", "💎", "🔔", "7️⃣"]
        result = [random.choice(reels) for _ in range(3)]

        if result[0] == result[1] == result[2]:
            winnings = amount * 10
            message = f"🎉 JACKPOT! You won {winnings} Matrixx! 🎉"
        elif result[0] == result[1] or result[1] == result[2]:
            winnings = amount * 2
            message = f"🎊 You won {winnings} Matrixx! 🎊"
        else:
            winnings = -amount
            message = "💔 You lost. Better luck next time! 💔"

        await user_service.update_balance(user_id, winnings)

        embed = discord.Embed(
            title="🎰 Slots 🎰",
            description=" ".join(result),
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Result", value=message)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="transfer", description="Transfer Matrixx to another user.")
    async def transfer(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if amount <= 0:
            await interaction.response.send_message("❌ Please enter a positive amount.", ephemeral=True)
            return

        sender_id = interaction.user.id
        receiver_id = user.id

        sender_data = await user_service.get_user(sender_id)
        if sender_data.balance < amount:
                await interaction.response.send_message("❌ You don't have enough Matrixx to make this transfer.", ephemeral=True)
                return
            
        await user_service.update_balance(sender_id, -amount)
        await user_service.update_balance(receiver_id, amount)

        embed = discord.Embed(
            title="✨ Transfer Successful",
            description=f"You have successfully transferred **{amount}** Matrixx to {user.mention}!",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Check the top 10 richest users.")
    async def leaderboard(self, interaction: discord.Interaction):
        users = await user_service.get_top_users(10)

        embed = discord.Embed(
            title="✨ Leaderboard",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )

        for i, user_data in enumerate(users):
            user = await self.bot.fetch_user(user_data.id)
            embed.add_field(name=f"{i+1}. {user.name}", value=f"**Balance:** {user_data.balance} Matrixx", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work", description="Work to earn some Matrixx.")
    async def work(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if not await user_service.can_work(user_id):
                await interaction.response.send_message("❌ You have already worked recently. Try again later.", ephemeral=True)
                return

        amount = random.randint(50, 200)
        await user_service.work(user_id, amount)

        embed = discord.Embed(
            title="✨ Work",
            description=f"You worked hard and earned **{amount}** Matrixx!",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url="attachment://coin.png")
        file = discord.File("public/coin/heads.png", filename="coin.png")
        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="daily", description="Claim your daily reward.")
    async def daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if not await user_service.can_claim_daily(user_id):
                await interaction.response.send_message("❌ You have already claimed your daily reward. Try again later.", ephemeral=True)
                return

        amount = random.randint(100, 500)
        await user_service.claim_daily(user_id, amount)

        embed = discord.Embed(
            title="✨ Daily Reward",
            description=f"You have claimed your daily reward of **{amount}** Matrixx!",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url="attachment://coin.png")
        file = discord.File("public/coin/heads.png", filename="coin.png")
        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="balance", description="Check your or another user's balance.")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        user_data = await user_service.get_user(user.id)
        
        embed = discord.Embed(
            title=f"✨ {user.display_name}'s Balance",
            description=f"**Balance:** {user_data.balance} Matrixx",
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url="attachment://coin.png")
        file = discord.File("public/coin/heads.png", filename="coin.png")
        await interaction.response.send_message(embed=embed, file=file)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))