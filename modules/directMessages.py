import discord
import yaml
from discord import app_commands
from discord.ext import commands
from discord.utils import get

from utils.utils import check_permissions

config = yaml.safe_load(open("config/directMessagesConfig.yml", 'r', encoding="utf-8"))


class DirectMessages(commands.Cog):
    """Class containing all module methods"""
    def __init__(self, bot):
        print('DirectMessages module ready!')
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages recieved by the bot in private messages"""
        if isinstance(message.channel, discord.channel.DMChannel):
            if message.author == self.bot.user:
                return  # Do not do anything if the sender is the bot
            channel = get(self.bot.get_all_channels(), id=config.get("dm-channel"))
            embed_conf = config.get("recieved-message-embed-format")
            embed_title = embed_conf.get("title").replace("{user}",
                                                          f"{message.author.name}#{message.author.discriminator}")
            await channel.send(embed=discord.Embed(title=embed_title,
                                                   description=message.content,
                                                   color=embed_conf.get("color")))

    @commands.hybrid_command(description="Sends a message to defined user")
    @app_commands.rename(arg_user='user')
    @app_commands.describe(arg_user='Recipient of the message (Format: Username#xxxx)')
    @app_commands.rename(arg_message='message')
    @app_commands.describe(arg_message='Message you want to send')
    async def sendmessage(self, ctx, arg_user=None, *, arg_message=None):
        """Handle -send command to send new private message via the bot"""
        if arg_user is None or arg_message is None:
            embed_conf = config.get("send-missing-args-embed")
            await ctx.reply(
                embed=discord.Embed(title=embed_conf.get("title"), description=embed_conf.get("description"),
                                    color=embed_conf.get("color")))
            return
        role_identificator = config.get("send-admin-role")
        if await check_permissions(ctx.author, role_identificator):
            recipient = discord.utils.get(self.bot.get_all_members(), name=arg_user[:-5], discriminator=arg_user[-4:])
            if recipient is None:
                embed_conf = config.get("invalid-recipient-embed")
                embed_desc = embed_conf.get("description").replace("{user}", arg_user)
                await ctx.reply(embed=discord.Embed(title=embed_conf.get("title"),
                                                           description=embed_desc,
                                                           color=embed_conf.get("color")))
            else:
                embed_conf = config.get("send-success-embed")
                await ctx.reply(
                    embed=discord.Embed(title=embed_conf.get("title"), description=embed_conf.get("description"),
                                        color=embed_conf.get("color")))
                await recipient.send(embed=discord.Embed(description=arg_message,
                                                         color=config.get("sending-message-embed-format").get("color")))

    @commands.hybrid_command(description="Sends a message to all server users")
    @app_commands.rename(arg_message='message')
    @app_commands.describe(arg_message='Message you want to send')
    async def sendall(self, ctx, *, arg_message=None):
        """Handle -sendall command to send new private message via the bot to all server users"""
        if arg_message is None:
            embed_conf = config.get("sendall-missing-args-embed")
            await ctx.reply(
                embed=discord.Embed(title=embed_conf.get("title"), description=embed_conf.get("description"),
                                    color=embed_conf.get("color")))
            return
        role_identificator = config.get("sendall-admin-role")
        if await check_permissions(ctx.author, role_identificator):
            send_count = 0
            for recipient in self.bot.get_all_members():
                try:
                    embed = discord.Embed(description=arg_message,
                                          color=config.get("sending-message-embed-format").get("color"))
                    await recipient.send(embed=embed)
                    send_count += 1
                except:
                    pass
            embed_conf = config.get("sendall-success-embed")
            embed_count = embed_conf.get("description").replace("{count}", str(send_count))
            await ctx.reply(embed=discord.Embed(title=embed_conf.get("title"),
                                                       description=embed_count,
                                                       color=embed_conf.get("color")))


async def setup(bot):
    """Add the module to discord.py cogs"""
    await bot.add_cog(DirectMessages(bot))
