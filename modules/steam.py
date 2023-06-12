import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import re
from database.database import Database

db = Database(False)

class Steam(commands.Cog):
    """Class containing all methods related to the Steam module"""
    def __init__(self, bot):
        self.bot = bot
        db.check_create_table("Steam", "discord_id INTEGER PRIMARY KEY, steam_id INTEGER, player_name TEXT, avatar_url TEXT, profile_url TEXT, country TEXT, gbl_status TEXT")

        print('Steam module ready!')

    async def retrieve_steam_profile(self, steam_id):
        api_key = "ADD YOUR STEAM API KEY"
        api_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                data = await response.json()
                profile = data.get("response", {}).get("players", [{}])[0]
                return profile

    async def display_steam_profile(self, ctx, steam_id):
        """Display the Steam profile of a user"""
        profile = await self.retrieve_steam_profile(steam_id)
        if not profile:
            await ctx.send("Failed to retrieve the Steam profile.")
            return

        embed = discord.Embed(title="Steam Profile", color=discord.Color.blue())
        embed.add_field(name="Steam ID", value=f"[{steam_id}](https://www.steamidfinder.com/lookup/{steam_id})", inline=False)
        embed.add_field(name="Player Name", value=profile.get("personaname", "N/A"), inline=False)
        embed.add_field(name="Profile URL", value=f"[Steam Profile](https://steamcommunity.com/profiles/{steam_id})", inline=False)
        embed.add_field(name="Country", value=profile.get("loccountrycode", "N/A"), inline=False)
        embed.add_field(name="GBL Status", value=f"[Check Status](https://vaclist.net/account/{steam_id})", inline=False)
        embed.set_thumbnail(url=profile.get("avatarfull", "N/A"))

        await ctx.send(embed=embed)

    @commands.group(name="steam", descripton="Lookup Steam ID", invoke_without_command=True)
    async def steam_group(self, ctx, *, steam=None):
        """Steam profile commands"""
        if steam and steam.isdigit():
            await self.display_steam_profile(ctx, steam)
        else:
            profile = db.get_steam_profile(ctx.author.id)
            if profile:
                await self.display_steam_profile(ctx, profile[1])
            else:
                await ctx.send("Steam profile not found. Add your profile using `-steam addprofile <steam_id>`.")
    
    @steam_group.command(name="addprofile", description="Add your Steam profile")
    async def add_profile(self, ctx, steam_id: str):
        """Add your Steam profile"""
        steam_id_pattern = r"^\d{17}$"  # Regex pattern to validate Steam ID (17 digits)

        if not re.match(steam_id_pattern, steam_id):
            await ctx.send("Invalid Steam ID format. Please provide a valid Steam ID.")
            return

        steam_id = int(steam_id)
        profile = await self.retrieve_steam_profile(steam_id)

        if profile:
            db.add_steam_profile(ctx.author.id, steam_id, profile["personaname"], profile["avatarfull"], profile["profileurl"], profile["loccountrycode"], profile["personastate"])
            await ctx.send("Steam profile added successfully.")
        else:
            await ctx.send("Failed to add Steam profile.")
            

    def cog_unload(self):
        db.close_connection()

async def setup(bot):
    """Add the module to discord.py cogs"""
    await bot.add_cog(Steam(bot))
