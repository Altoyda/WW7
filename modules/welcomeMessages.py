import discord
import yaml
from discord.ext import commands

config = yaml.safe_load(open("config/welcomeMessagesConfig.yml", 'r', encoding="utf-8"))


class WelcomeMessages(commands.Cog):
    """Class contains all module methods"""
    def __init__(self, bot):
        self.bot = bot
        print('WelcomeMessages module ready!')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Handles member join event, sends welcome message."""
        print(f"User {member.name} joined the server.")
        private_conf = config.get("private-welcome-message")
        if private_conf.get("send-private-message"):
            embed = discord.Embed(title=private_conf.get("embed-caption").replace("{user}", member.name),
                                  description=private_conf.get("embed-description").replace("{user}", member.name),
                                  colour=private_conf.get("embed-color"))
            embed.set_footer(text=private_conf.get("embed-footer"))
            for field in private_conf.get("embed-fields"):
                field_conf = private_conf.get("embed-fields").get(field)
                embed.add_field(name=field_conf.get("caption"),
                                value=field_conf.get("description"),
                                inline=field_conf.get("inline"))
            try:
                await member.send(embed=embed)
            except Exception:
                print(f"Couldn't send a welcome message to {member.name}.")
        public_conf = config.get("public-welcome-message")
        if public_conf.get("send-public-message"):
            embed = discord.Embed(title=public_conf.get("embed-caption").replace("{user}", member.name),
                                  description=public_conf.get("embed-description").replace("{user}", member.name),
                                  colour=public_conf.get("embed-color"))
            embed.set_footer(text=public_conf.get("embed-footer"))
            for field in public_conf.get("embed-fields"):
                field_conf = private_conf.get("embed-fields").get(field)
                embed.add_field(name=field_conf.get("caption"),
                                value=field_conf.get("description"),
                                inline=field_conf.get("inline"))
            try:
                channel = discord.utils.get(self.bot.get_all_channels(),
                                            id=public_conf.get("public-welcome-message-channel"))
                await channel.send(embed=embed)
            except Exception:
                print("Couldn't send a welcome message to the channel.")


async def setup(bot):
    """Add the module to discord.py cogs"""
    await bot.add_cog(WelcomeMessages(bot))
