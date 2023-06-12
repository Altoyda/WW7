import discord
import yaml
from discord import app_commands
from discord.ext import commands
from discord.utils import get
from database.database import Database
from utils.utils import remove_command_message, check_permissions

db = Database(False)
config = yaml.safe_load(open("config/reactionRolesConfig.yml", 'r', encoding="utf-8"))


class RoleSelect(discord.ui.Select):
    """The fancy select interaction thingy"""

    def __init__(self, select_options, menu_placeholder, selector_name, only_one_role):
        options = []
        for option in select_options:
            option_conf = select_options.get(option)
            options.append(discord.SelectOption(label=option_conf.get("name"),
                                                description=option_conf.get("description"),
                                                emoji=option_conf.get("emoji"),
                                                value=option))
        max = len(options)
        if only_one_role:
            max = 1
        super().__init__(placeholder=menu_placeholder, min_values=0, max_values=max, options=options,
                         custom_id="role_select"+selector_name)


class ReactionRoles(commands.Cog):
    """Class containing all module methods"""

    def __init__(self, bot):
        db.check_create_table("reactionRoles",
                              "id INT AUTO_INCREMENT PRIMARY KEY, message_id VARCHAR(64),"
                              "selector VARCHAR(64), is_active BOOL DEFAULT 1")
        print('ReactionRoles module ready!')
        self.bot = bot

    @commands.hybrid_command(description="Creates new role selector")
    @app_commands.rename(arg='selector_name')
    @app_commands.describe(arg='Selector name defined in config')
    async def reactionroles(self, ctx, arg):
        """Handles -reactionroles command"""
        if not await check_permissions(ctx.author, config.get("selector-creation-admin-role")):
            return  # Exit if user doesn't have enough perms
        for selector in config.get("selectors"):
            if selector == arg:
                selector_config = config.get("selectors").get(selector)
                embed = discord.Embed(title=selector_config.get("embed-title"),
                                      description=selector_config.get("embed-description"),
                                      colour=selector_config.get("embed-color"))
                embed.set_footer(text=selector_config.get("embed-footer"))
                if selector_config.get("type") == "menu":
                    view = discord.ui.View()
                    view.add_item(RoleSelect(selector_config.get("options"), selector_config.get("select-menu-title"), selector, selector_config.get("only-one-role")))
                    reply_message = await ctx.reply("...")
                    await ctx.channel.send(embed=embed, view=view)
                    await reply_message.delete()
                else:
                    reply_message = await ctx.reply("...")
                    message = await ctx.channel.send(embed=embed)
                    await reply_message.delete()
                    db.insert("reactionRoles", "message_id, selector", f"{str(message.id)}, '{str(selector)}'")
                    for role_option in selector_config.get("options"):
                        emoji = selector_config.get("options").get(role_option).get("emoji")
                        await message.add_reaction(emoji)
                return
        error_embed = discord.Embed(title="Selector not found!",
                                    description="The requested selector was not found in the configuration.",
                                    colour=0xff0000)
        await ctx.reply(embed=error_embed)
        await remove_command_message(ctx.message)

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        """Handles role select menu interactions"""
        custom_id = interaction.data.get("custom_id")
        if custom_id is None or not custom_id.startswith("role_select"):
            return
        await interaction.response.defer(thinking=False)
        user = interaction.user
        selector = custom_id.split("role_select")[1]
        selector_conf = config.get("selectors").get(selector)
        values = interaction.data.get("values")
        for option in selector_conf.get("options"):
            option_conf = selector_conf.get("options").get(option)
            role_identificator = option_conf.get("role")
            role = await self.get_role(role_identificator, interaction.guild)
            if role is None:
                continue
            if option in values:    # Roles to add
                required_role = option_conf.get("required-role")
                if required_role is not None:
                    required_r = await self.get_role(required_role, interaction.guild)
                    if required_r is None:
                        return
                    if required_r not in user.roles:
                        embed_conf = config.get("another-role-required-embed")
                        embed = discord.Embed(
                            title=embed_conf.get("embed-title").replace("{user}", user.name),
                            description=embed_conf.get("embed-description").replace("{required_role}",
                                                                                    required_r.name),
                            color=embed_conf.get("embed-color"))
                        embed.set_footer(text=embed_conf.get("embed-footer"))
                        if str.lower(embed_conf.get("send-to")) == "dm":
                            await user.send(embed=embed)
                        elif str.lower(embed_conf.get("send-to")) == "channel":
                            msg = await interaction.response.send_message(embed=embed, ephemeral=True)
                            await msg.delete(delay=10)
                        return
                if not role in user.roles:
                    await self.add_user_role(role, interaction.channel, user)

            else:  # Roles to remove
                if role in user.roles:
                    await self.remove_user_role(role, interaction.channel, user)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handles reaction add event"""
        await self.check_change_state(payload, True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handles reaction remove event"""
        await self.check_change_state(payload, False)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        """Handles deletion of role selector"""
        if db.check_contains("reactionRoles", "message_id", str(payload.message_id)):
            db.update_data("reactionRoles", "is_active", "0", f"message_id={payload.message_id}")
            print("Selector message deleted, database status updated!")

    async def check_change_state(self, payload, added):
        """Checks current user role status when reaction is added/removed."""
        user = get(self.bot.get_all_members(), id=payload.user_id)
        if user.bot:
            return
        message_id = payload.message_id
        if db.check_contains("reactionRoles", "message_id", str(message_id)):
            selector = db.get_value_general("reactionRoles", "selector", f"message_id like '{str(message_id)}'")
            selector_conf = config.get("selectors").get(selector)
            try:
                channel = get(self.bot.get_guild(payload.guild_id).channels, id=payload.channel_id)
                message = await self.bot.get_channel(payload.channel_id).fetch_message(message_id)
                for option in selector_conf.get("options"):
                    option_config = selector_conf.get("options").get(option)
                    role_identificator = option_config.get("role")
                    role = await self.get_role(role_identificator, self.bot.get_guild(payload.guild_id))
                    if role is None:
                        print(f"Role {role_identificator} was not found on your server,"
                              f" please, check your configuration!")
                        return
                    option_emoji = option_config.get("emoji")
                    if option_emoji == str(payload.emoji):
                        if added:
                            required_role = option_config.get("required-role")
                            if required_role is not None:
                                req_role = await self.get_role(required_role, self.bot.get_guild(payload.guild_id))
                                if req_role is None:
                                    print(f"There is a problem with your configuration,"
                                          f" required role {required_role} in option {option}"
                                          f" was not found on the server!")
                                    return
                                # If user does not have the role required for acquiring new one
                                if req_role not in user.roles:
                                    await message.remove_reaction(str(payload.emoji), user)
                                    embed_conf = config.get("another-role-required-embed")
                                    embed = discord.Embed(
                                        title=embed_conf.get("embed-title").replace("{user}", user.name),
                                        description=embed_conf.get("embed-description").replace("{required_role}",
                                                                                                req_role.name),
                                        color=embed_conf.get("embed-color"))
                                    embed.set_footer(text=embed_conf.get("embed-footer"))
                                    if str.lower(embed_conf.get("send-to")) == "dm":
                                        await user.send(embed=embed)
                                    elif str.lower(embed_conf.get("send-to")) == "channel":
                                        msg = await channel.send(embed=embed)
                                        await msg.delete(delay=10)
                                    return

                            await self.add_user_role(role, channel, user)
                        else:
                            await self.remove_user_role(role, channel, user)
                    else:
                        if selector_conf.get("only-one-role") and added and role in user.roles:
                            await message.remove_reaction(option_emoji, user)
                            # No need to remove the role here since the remove_reaction also fires reaction remove event

            except Exception as exc:
                print(
                    "Something went wrong when trying to assing new role using ReactionRoles."
                    " Please, check your configuration.")
                print(exc)

    async def get_role(self, role_identificator, guild):
        """Returns role by its identificator"""
        if isinstance(role_identificator, int):
            role = discord.utils.get(guild.roles, id=role_identificator)
        else:
            role = discord.utils.get(guild.roles, name=role_identificator)
        if role is None:
            print(f"Role {role_identificator} was not found on your server,"
                  f" please, check your configuration!")
            return None
        return role

    async def remove_user_role(self, role, channel, user):
        """Removes role from the user if he has it."""
        if role in user.roles:
            # User has the role, remove it
            await user.remove_roles(role)
            print(f"Removed role {role.name} from {user.name}")
            # Send player removed role embed
            await self.send_removed_role_embed(role, channel, user)

    async def add_user_role(self, role, channel, user):
        """Adds role to the user if he doesn't have it yet."""
        if role not in user.roles:
            # Add the role to the user since he doesn't have it
            await user.add_roles(role)
            print(f"Added role {role.name} to {user.name}")
            # Send player got role embed
            await self.send_added_role_embed(role, channel, user)

    @staticmethod
    async def send_added_role_embed(role, channel, user):
        """Sends embed message with info about a role being added to users account"""
        embed_conf = config.get("role-added-embed")
        if not embed_conf.get("enabled"):
            return
        embed_title = embed_conf.get("embed-title").replace("{role}", role.name).replace("{user}", user.name)
        embed_desc = embed_conf.get("embed-description").replace("{role}", role.name).replace("{user}", user.mention)
        embed = discord.Embed(title=embed_title,
                              description=embed_desc,
                              colour=embed_conf.get("embed-color"))
        embed.set_footer(text=embed_conf.get("embed-footer"))
        if embed_conf.get("send-to") == "dm":
            await user.send(embed=embed)
        else:
            msg = await channel.send(embed=embed)
            await msg.delete(delay=10)

    @staticmethod
    async def send_removed_role_embed(role, channel, user):
        """Sends embed message with info about a role being removed from users account"""
        embed_conf = config.get("role-removed-embed")
        if not embed_conf.get("enabled"):
            return
        embed_title = embed_conf.get("embed-title").replace("{role}", role.name).replace("{user}", user.name)
        embed_desc = embed_conf.get("embed-description").replace("{role}", role.name).replace("{user}", user.mention)
        embed = discord.Embed(title=embed_title,
                              description=embed_desc,
                              colour=embed_conf.get("embed-color"))
        embed.set_footer(text=embed_conf.get("embed-footer"))
        if embed_conf.get("send-to") == "dm":
            await user.send(embed=embed)
        else:
            msg = await channel.send(embed=embed)
            await msg.delete(delay=10)


async def setup(bot):
    """Add the module to discord.py cogs"""
    await bot.add_cog(ReactionRoles(bot))
