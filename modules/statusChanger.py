import discord
import yaml
from discord.ext import commands, tasks


config = yaml.safe_load(open("config/statusChangerConfig.yml", 'r', encoding="utf-8"))
interval = config.get("change-interval")


class StatusUpdater(commands.Cog):
    """Shows multiple different data in the bots status"""
    def __init__(self, bot):
        self.bot = bot
        self.status = 0
        print("StatusChanger module ready!")


    @commands.Cog.listener()
    async def on_ready(self):
        if not self.update_status.is_running():
            self.update_status.start()

    @tasks.loop(seconds=interval)
    async def update_status(self):
        """Updates the bot status"""
        self.status += 1
        if self.status == len(config.get("status-list")):
            self.status = 0

        status_message = config.get("status-list")[self.status]

        await self.bot.change_presence(activity=discord.Game(name=status_message, type=3))

    @update_status.before_loop
    async def before_update_status(self):
        """Wait for bot to fully start before updating status"""
        await self.bot.wait_until_ready()
        print("Launching status updater!")


async def setup(bot):
    """Add the module to discord.py cogs"""
    await bot.add_cog(StatusUpdater(bot))
