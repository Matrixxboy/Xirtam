import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Shows the help message.")
    async def help(self, interaction: discord.Interaction):
        cogs = [cog for cog in self.bot.cogs.values() if cog.get_app_commands()]
        
        embed = discord.Embed(
            title="Help",
            description="Click a button to see the commands for that category.",
            color=discord.Color.purple()
        )
        
        view = discord.ui.View()
        for cog in cogs:
            button = discord.ui.Button(style=discord.ButtonStyle.secondary, label=cog.qualified_name)
            button.callback = self.create_cog_callback(cog)
            view.add_item(button)
            
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    def create_cog_callback(self, cog: commands.Cog):
        async def callback(interaction: discord.Interaction):
            embed = discord.Embed(
                title=f"{cog.qualified_name} Commands",
                color=discord.Color.purple()
            )
            for command in cog.get_app_commands():
                embed.add_field(name=f"/{command.name}", value=command.description or "No description", inline=False)
            
            view = discord.ui.View()
            home_button = discord.ui.Button(style=discord.ButtonStyle.primary, label="Home")
            home_button.callback = self.create_home_callback()
            view.add_item(home_button)
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        return callback

    def create_home_callback(self):
        async def callback(interaction: discord.Interaction):
            cogs = [cog for cog in self.bot.cogs.values() if cog.get_app_commands()]
            
            embed = discord.Embed(
                title="Help",
                description="Click a button to see the commands for that category.",
                color=discord.Color.purple()
            )
            
            view = discord.ui.View()
            for cog in cogs:
                button = discord.ui.Button(style=discord.ButtonStyle.secondary, label=cog.qualified_name)
                button.callback = self.create_cog_callback(cog)
                view.add_item(button)
            
            await interaction.response.edit_message(embed=embed, view=view)
            
        return callback

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))