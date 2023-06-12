import discord
import yaml
from discord.ext import commands
from discord.utils import get
from database.database import Database
from utils.utils import check_permissions

database = Database(False)
config = yaml.safe_load(open("config/suggestionsModuleConfig.yml", 'r', encoding="utf-8"))



class Suggestions(commands.Cog):
    """Class that handles all suggestion module things"""
    def __init__(self, bot):
        """Initialize the module"""
        self.bot = bot
        self.database = Database()  # Instantiate the Database class
        self.database.check_create_table("suggestions", "message_id TEXT PRIMARY KEY, channel_id TEXT NOT NULL")
        print('Suggestions module ready!')

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handles reaction add event"""
        if message.author.bot:
            return
        channel = message.channel
        for sug_channel in config.get("suggestion-channels"):
            sug_conf = config.get("suggestion-channels").get(sug_channel)
            if channel.id == sug_conf.get("channel-id"):
                # Handle the suggestion
                embed = discord.Embed(title=sug_conf.get("embed-title").replace("{user}", message.author.name),
                                      description=message.content,
                                      color=sug_conf.get("new-color"))
                embed.set_footer(text=sug_conf.get("embed-footer"))
                suggestion = await channel.send(embed=embed)
                database.insert("suggestions", "message_id, channel_id", f"{str(suggestion.id)}, {str(channel.id)}")
                try:
                    await suggestion.add_reaction(config.get("like-emoji"))
                    await suggestion.add_reaction(config.get("accept-emoji"))
                    await suggestion.add_reaction(config.get("deny-emoji"))
                except Exception as exc:
                    print("Unable to add reactions to suggestion, check your configuration! (full error below)")
                    print(exc)
                await message.delete()
                return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handles reaction add event"""
        if payload.member.bot:
            return

        message_id = payload.message_id

        if database.check_contains("suggestions", "message_id", str(message_id)):
            emoji = str(payload.emoji)

            if emoji == config.get("accept-emoji") or emoji == config.get("deny-emoji"):
                for sug_chan in config.get("suggestion-channels"):
                    sug_conf = config.get("suggestion-channels").get(sug_chan)

                    if payload.channel_id == payload.channel_id:
                        # Check permissions
                        channel = get(self.bot.get_guild(payload.guild_id).channels, id=payload.channel_id)
                        message = await self.bot.get_channel(payload.channel_id).fetch_message(message_id)
                        role_identificator = sug_conf.get("accept-role")
                        role = discord.utils.get(channel.guild.roles, name=role_identificator)

                        if role is None:
                            msg = await channel.send(embed=self.missing_role_embed(role_identificator))
                            await msg.delete(delay=10)
                            await message.remove_reaction(str(payload.emoji), payload.member)
                            return

                        if not await check_permissions(payload.member, role_identificator):
                            msg = await channel.send(embed=self.missing_role_embed(role))
                            await msg.delete(delay=10)
                            await message.remove_reaction(str(payload.emoji), payload.member)
                            return

                        # Set the role as accepted / denied
                        embed = message.embeds[0]

                        if emoji == config.get("accept-emoji"):
                            embed.color = sug_conf.get("accept-color")
                            embed.title = f"{sug_conf.get('accepted-prefix')} {embed.title}"
                        else:
                            embed.color = sug_conf.get("deny-color")
                            embed.title = f"{sug_conf.get('denied-prefix')} {embed.title}"

                        await message.edit(embed=embed)
                        await message.clear_reactions()

                        # The suggestion is not needed in the database anymore
                        database.delete_value_general("suggestions", f"message_id like '{message_id}'")
                        return


    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        """Removes unneeded suggestion data when suggestion message is removed"""
        database.delete_value_general("suggestions", f"message_id like '{payload.message_id}'")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Removes unneeded suggestion data from the database when suggestions channel is deleted."""
        database.delete_value_general("suggestions", f"channel_id like '{channel.id}'")

    @staticmethod
    def missing_role_embed(role):
        embed_conf = config.get("missing-role-embed")
        embed = discord.Embed(title=embed_conf.get("title"),
                              description=embed_conf.get("description").replace("{role}", role.name),
                              color=embed_conf.get("color"))
        embed.set_footer(text=embed_conf.get("footer"))
        return embed


async def setup(bot):
    """Add the module to discord.py cogs"""
    await bot.add_cog(Suggestions(bot))
