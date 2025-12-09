import os
import discord
import datetime
from discord import app_commands, ui
from discord.ext import commands

GUILD_ID = int(os.getenv('GUILD_ID'))

def is_owner():
    async def predicate(interaction: discord.Interaction) -> bool:
        return await interaction.client.is_owner(interaction.user)
    return app_commands.check(predicate)



class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    

    # --- Commands ---
    

    @app_commands.command(name="about", description="Shows information about the bot and its creator.")
    async def about(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 About Xirtam",
            description=(
                "Xirtam is a **multi-purpose Discord bot** built with "
                "`Python` and `discord.py`.\n\n"
                "It is designed to make your server **more fun, productive, and secure** 🎉"
            ),
            color=discord.Color.purple(),
            timestamp=datetime.datetime.utcnow()
        )

        embed.add_field(name="👨‍💻 Creator", value="**Utsav Lankapati**", inline=True)
        embed.add_field(name="🌐 Website", value="[Utsav Lankapati](https://utsav-lankapati.onrender.com)", inline=True)
        embed.add_field(name="📂 GitHub", value="[Matrixxboy/Xirtam](https://github.com/Matrixxboy/Xirtam)", inline=True)
        embed.add_field(name="⚙️ Version", value="`1.0.0`", inline=True)
        embed.add_field(name="📚 Library", value="`discord.py 2.x`", inline=True)
        embed.add_field(name="🌐 Language", value="`Python 3.11+`", inline=True)
        embed.add_field(name="💬 Support", value="[Join Discord](https://discord.gg/membBFG896)", inline=True)

        # Optional: set bot avatar as thumbnail
        if interaction.client.user.avatar:
            embed.set_thumbnail(url=interaction.client.user.avatar.url)

        embed.set_footer(text="Made with ❤️ by Utsav Lankapati")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Shows information about the server.")
    async def serverinfo(self, interaction: discord.Interaction):
        try:
            guild = interaction.guild
            
            # Fetch owner if not in cache
            owner = guild.owner
            if not owner:
                owner = await guild.fetch_member(guild.owner_id)

            embed = discord.Embed(
                title=f"Server Info: {guild.name}",
                color=discord.Color.green(),
                timestamp=datetime.datetime.utcnow()
            )
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            embed.add_field(name="Owner", value=owner.mention, inline=True)
            embed.add_field(name="Members", value=guild.member_count, inline=True)
            embed.add_field(name="Created At", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
            embed.add_field(name="Roles", value=len(guild.roles), inline=True)
            embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
            embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
            embed.set_footer(text=f"Server ID: {guild.id}")
            
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred while fetching server info: {e}", ephemeral=True)

    @app_commands.command(name="userinfo", description="Shows information about a user.")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(
            title=f"User Info: {member.display_name}",
            color=member.color,
            timestamp=datetime.datetime.utcnow()
        )
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Full Name", value=str(member), inline=True)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:D>", inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
        roles = [role.mention for role in member.roles[1:]] # Exclude @everyone
        embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles) if roles else "No roles", inline=False)
        embed.set_footer(text=f"User ID: {member.id}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sync", description="Sync slash commands (owner only)")
    @is_owner()
    async def sync(self, interaction: discord.Interaction):
        try:
            synced = await self.bot.tree.sync(guild=discord.Object(id=GUILD_ID))
            await interaction.response.send_message(f"✅ Synced {len(synced)} command(s) to the server.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to sync commands: {e}", ephemeral=True)

    # --- Events ---
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
            
        welcome_channel_name = "welcome"
        channel = discord.utils.get(member.guild.text_channels, name=welcome_channel_name)
        if channel:
            embed = discord.Embed(
                title=f"Welcome to {member.guild.name}!",
                description=f"Hello {member.mention}, we're glad to have you here! Please check out the server rules and select your roles.",
                color=discord.Color.purple(),
                timestamp=datetime.datetime.utcnow()
            )
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaDB6d2Q4eXN6c3B6d2w0b3RzZ3g3d2g3d2cifQ/hJqsdhTUKd5E4/giphy.gif") # Example GIF
            embed.set_footer(text="We hope you enjoy your stay!")
            await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))