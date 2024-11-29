from commondata import *
import discord
from discord.ext import commands
from datetime import datetime
import random
import typing

def has_higher_role(ctx, target_member):
    """
    Check if the author has a higher role than the target member.

    Args:
        ctx (commands.Context): The context of the command.
        target_member (discord.Member): The member to compare roles with.

    Returns:
        bool: True if the author has a higher role, False otherwise.
    """
    if ctx.author.id in owners:
        return True
    if target_member.id in owners:
        return False
    try:
        if target_member.id == ctx.guild.owner_id:
            return False
        return (
            ctx.author.id in owners
            or ctx.author.top_role > target_member.top_role
            or ctx.guild.owner_id == ctx.author.id
        )
    except Exception as e:
        raise e

async def create_muted_role(ctx):
        content = "Info: Creating muted role..."
        muted_role = await ctx.guild.create_role(
            name="🔇 | Muted", reason="Mute role creation"
        )
        categories = 0
        channels = 0
        permissions = {
            "send_messages": False,
            "send_messages_in_threads": False,
            "create_public_threads": False,
            "create_private_threads": False,
            "add_reactions": False,
            "connect": False,
            "request_to_speak": False,
            "speak": False
        }
        for category in ctx.guild.categories:
            await category.set_permissions(muted_role, **permissions)
            categories += 1
        for channel in ctx.guild.channels:
            channels += 1
            await channel.set_permissions(muted_role, **permissions)
        await muted_role.edit(permissions=permissions)

        content = f"\
        {content}\
        Modified {categories} categories and {channels} channels.\
        "
        response = Response(content)
        return response

class ReportView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.report_channels_db = bot.mongo_report_channels

    @discord.ui.button(
        label="Report", style=discord.ButtonStyle.red, custom_id="report"
    )
    async def report_button(self, _button, interaction):
        # check if we're even running in a guild
        if interaction.guild is None:
            await interaction.respond(
                f"You're doing it wron- wait, what what the FUCK *are* you even doing? DebugException raised."
            )
            raise DebugException(
                f"{interaction.user.id} managed to call the report button even though it's not supposed to be spawned."
            )
        if not self.report_channels_db.find_one({"_id": interaction.guild.id}):
            await interaction.respond(
                f"Sorry, {interaction.guild.name} does not have a report channel configured!",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(ReportModal(self.bot))


class ReportModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Report")
        self.report_reason = discord.ui.InputText(
            label="Report Reason",
            placeholder="Please enter the reason for the report",
            required=True,
            max_length=100,
            min_length=10,
        )
        self.report_description = discord.ui.InputText(
            label="Report Description",
            placeholder="Please enter a description of the report",
            max_length=500,
            min_length=10,
        )
        self.reported_user = discord.ui.InputText(
            label="Reported user",
            placeholder="i_am_called_glitchy",
            max_length=35,
            min_length=3,
        )
        self.add_item(self.report_reason)
        self.add_item(self.report_description)
        self.add_item(self.reported_user)
        self.report_channels_db = bot.mongo_report_channels

    async def callback(self, interaction: discord.Interaction):
        reason = self.report_reason.value
        description = self.report_description.value
        reported_user = self.reported_user.value
        # check if we're even running in a guild
        if interaction.guild is None:
            await interaction.respond(
                f"You're doing it wron- wait, what what the FUCK *are* you even doing? DebugException raised."
            )
            raise DebugException(
                f"{interaction.user.id} managed to call the report button even though it's not supposed to be spawned oustide guild contexts."
            )
        # check if we even have a report channel
        if not self.report_channels_db.find_one({"_id": interaction.guild.id}):
            await interaction.respond(
                f"Sorry, {interaction.guild.name} does not have a report channel configured!",
                ephemeral=True,
            )
            return
        channel_id = self.report_channels_db.find_one({"_id": interaction.guild.id})[
            "channel_id"
        ]
        report_channel = interaction.guild.get_channel(channel_id)
        if not report_channel:
            await interaction.respond(
                "Sorry, the report channel was not found. This usually means that it was deleted.",
                ephemeral=True,
            )
            return
        try:
            await report_channel.send(
                f"**Report from {interaction.user.mention} ({interaction.user.name})**:```\n- Report reason: {reason}\n- Description: {description}\n- Reported user: {reported_user}```"
            )
        except discord.Forbidden:
            await interaction.respond(
                "Sorry, i cannot send messages in the specified channel. This is a permission error.",
                ephemeral=True,
            )
            return
        except Exception as e:
            await interaction.respond("An unknown error happened.")
            raise e

        await interaction.respond(
            f"Report submitted: {reason} - {description}", ephemeral=True
        )


class Moderation(commands.Cog):
    """A cog for moderation commands."""

    def __init__(self, bot):
        self.bot = bot
        # using self.bot.mongo_db, get the warned_users collection, create if not existing
        self.warned_users_collection = self.bot.mongo_warned_users
        self.report_channels_collection = self.bot.mongo_report_channels

    @commands.guild_only()
    @commands.command(description="Compare role hierarchy")
    async def who_is_higher(
        self, ctx, member1: discord.Member, member2: discord.Member = None
    ):
        """
        Check who is higher on the role hierarchy.

        Usage:
            .who_is_higher @member1 @member2
            .who_is_higher @member

        Arguments:
            member1: The first member to compare.
            member2: The second member to compare. If not provided, compares with you.
        """
        try:
            if member2 is None:
                result = "You" if has_higher_role(ctx, member1) else "They"
            else:
                result = (
                    "First member"
                    if member1.top_role > member2.top_role
                    else "Second member"
                )
                if member1.top_role == member2.top_role:
                    result = "They have the same role"
                if member1.id == ctx.guild.owner_id:
                    result = "First member (Owner)"
                if member2.id == ctx.guild.owner_id:
                    result = "Second member (Owner)"
            response = Response(result)
            await response.send(ctx)
        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")

    @commands.guild_only()
    @commands.command(description="Kick a member.")
    @is_owner_or_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, softban="no", *, reason=None):
        """
        Kick a member from the server.

        Usage:
            !kick @member [reason]

        Arguments:
            member: The member to kick.
            softban: If "softban" is second argument, the member will be softbanned (who knew?)
            reason: The reason for kicking the member (optional).
        """
        doSoftban = False
        if softban.lower() == "softban":
            doSoftban = True
        else:
            # just to make sure the reason is set correctly
            reason = f"{softban} {reason}"
        if not has_higher_role(ctx, member):
            await ctx.send("You don't have permission to kick this member.")
            return
        try:
            await member.send(
                f'You have been {"softbanned" if doSoftban else "kicked"} from {ctx.guild.name} by {ctx.author}. Reason: {reason if reason else "No reason provided"}'
            )
        except (discord.errors.Forbidden, discord.errors.HTTPException):
            await ctx.send("Unable to DM the user about their kick.")

        if not doSoftban:
            await member.kick(reason=reason)
            await ctx.send(f"{member.mention} has been kicked by {ctx.author.mention}.")
        else:
            await member.ban(reason=reason, delete_message_seconds=99999999)
            await ctx.send(
                f"{member.mention} has been softbanned by {ctx.author.mention}."
            )
            await member.unban()

    @commands.command(description="Ban a member.")
    @is_owner_or_has_permissions(ban_members=True)
    async def ban(self, ctx, member: typing.Union[discord.User, discord.Member] , *, reason=None):
        """
        Ban a member from the server.

        Usage:
            !ban @member [reason]

        Arguments:
            member: The member to ban.
            reason: The reason for banning the member (optional).
        """
        if not has_higher_role(ctx, member):
            await ctx.send("You don't have permission to ban this member.")
            return
        try:
            await member.send(
                f'You have been banned from {ctx.guild.name} by {ctx.author}. Reason: {reason if reason else "No reason provided"}'
            )
        except (discord.errors.Forbidden, discord.errors.HTTPException):
            await ctx.send("Unable to DM the user about their ban.")
        await ctx.guild.ban(member)
        await ctx.send(f"{member.mention} has been banned by {ctx.author.mention}.")

    @commands.command(description="Unban a member.")
    @is_owner_or_has_permissions(ban_members=True)
    async def unban(self, ctx, *, member: discord.User|str):
        """
        Unban a member from the server.

        Usage:
            !unban <user_id> or <username#discriminator>

        Arguments:
            member: The member to unban (user ID or username#discriminator).
        """
        try:
            banned_users = [ban_entry async for ban_entry in ctx.guild.bans()]
            if member.isdigit():
                user = discord.Object(id=int(member))
                await ctx.guild.unban(user)
                await ctx.send(
                    f"User with ID {member} has been unbanned by {ctx.author.mention}."
                )
            else:
                name, discriminator = member.split("#")
                for ban_entry in banned_users:
                    user = ban_entry.user
                    if (user.name, user.discriminator) == (name, discriminator):
                        await ctx.guild.unban(user)
                        await ctx.send(
                            f"{user.mention} has been unbanned by {ctx.author.mention}."
                        )
                        return
                await ctx.send(f"User {member} not found in the ban list.")
        except ValueError:
            await ctx.send(
                "Invalid format. Please use either a user ID or username#discriminator."
            )
        except discord.errors.NotFound:
            await ctx.send("User not found in the ban list.")
        except discord.errors.Forbidden:
            await ctx.send("I don't have permission to unban members.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            raise e

    @commands.command(aliases=["purge"], description="Bulk-delete messages.")
    @is_owner_or_has_permissions(manage_messages=True)
    async def clear(
        self,
        ctx: commands.Context,
        amount: int,
        user: discord.Member | discord.User = None,
    ):
        """
        Clear a specified number of messages from the channel.

        Usage:
            !clear <amount>

        Arguments:
            amount: The number of messages to clear.
        """
        await ctx.channel.purge(
            limit=amount + 1,
            check=lambda m: m.author == user if user else lambda msg: True
        )
        await ctx.send(
            f"{amount} messages have been cleared by {ctx.author.mention}.",
            delete_after=5,
        )

    @commands.command(description="Mute a member.")
    @is_owner_or_has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration: str, *, reason=None):
        """
        Mute a member for a specified duration.

        Usage:
            !mute @member <duration> [reason]

        Arguments:
            member: The member to mute.
            duration: The duration of the mute (e.g., "1h30m").
            reason: The reason for muting the member (optional).
        """
        try:
            if not has_higher_role(ctx, member):
                await ctx.send("You don't have permission to mute this member.")
                return

            muted_role = discord.utils.get(ctx.guild.roles, name=lambda name: "Muted" in name)
            if muted_role is None:
                await create_muted_role(ctx)

            mute_duration = parse_duration(duration)

            if mute_duration is not None:
                try:
                    await member.timeout_for(mute_duration, reason=reason)
                except (discord.errors.Forbidden, discord.errors.HTTPException):
                    await ctx.send(
                        "Permission error! User is admin? Use indefinite mute."
                    )
                    return
                await ctx.send(
                    f"{member.mention} has been timed out for {duration} by {ctx.author.mention}."
                )
                try:
                    await member.send(
                        f'You have been timed out in {ctx.guild.name} for {duration} by {ctx.author}. Reason: {reason if reason else "No reason provided"}'
                    )
                except (discord.errors.Forbidden, discord.errors.HTTPException):
                    await ctx.send("Unable to DM the user about their mute/unmute.")
                except Exception as e:
                    await ctx.send(f"Error occurred during mute process: {str(e)}")
                    raise e
            else:
                try:
                    await member.add_roles(muted_role, reason=reason)
                except (discord.errors.Forbidden, discord.errors.HTTPException):
                    await ctx.send(f"Bot does not have permission to mute!")
                try:
                    await ctx.send(
                        f"{member.mention} has been muted indefinitely by {ctx.author.mention}."
                    )
                    await member.send(
                        f'You have been muted indefinitely in {ctx.guild.name} by {ctx.author}. Reason: {reason if reason else "No reason provided"}'
                    )
                except (discord.errors.Forbidden, discord.errors.HTTPException):
                    await ctx.send("Unable to DM the user about their mute.")
                except Exception as e:
                    await ctx.send(
                        f"Error occurred while sending mute message: {str(e)}"
                    )
        except Exception as e:
            raise e

    @commands.command(description="Unmute a member.")
    @is_owner_or_has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """
        Unmute a member.

        Usage:
            !unmute @member

        Arguments:
            member: The member to unmute.
        """
        if not has_higher_role(ctx, member):
            await ctx.send("You don't have permission to unmute this member.")
            return
        muted_role = discord.utils.get(ctx.guild.roles, name=lambda name: "Muted" in name)
        if muted_role is None:
            await create_muted_role(ctx)
        was_muted = False
        if muted_role in member.roles:
            await member.remove_roles(muted_role)
            was_muted = True
        if member.communication_disabled_until is not None:
            await member.remove_timeout()
            was_muted = True
        if was_muted:
            await ctx.send(
                f"{member.mention} has been unmuted by {ctx.author.mention}."
            )
            try:
                await member.send(
                    f"You have been unmuted in {ctx.guild.name} by {ctx.author}."
                )
            except (discord.errors.Forbidden, discord.errors.HTTPException):
                await ctx.send("Unable to DM the user about their unmute.")
        else:
            await ctx.reply(f"{member.mention} was not muted.")


    @commands.command(
        description="Warn a user verbally, don't save.", aliases=["vwarn", "vw"]
    )
    @is_owner_or_has_permissions(manage_messages=True)
    async def verbal_warn(self, ctx, user: discord.User, *, reason: str):
        """
        Warn a user verbally.
        """
        if isinstance(user, discord.Member) and not has_higher_role(ctx, user):
            await ctx.send("You don't have permission to warn this member.")
            return
        try:
            await user.send(
                f"You have been verbally warned in {ctx.guild.name} for {reason}.\n-# Responsible moderator: {ctx.author.mention}"
            )
            await ctx.message.add_reaction("✅")
        except (discord.errors.Forbidden, discord.errors.HTTPException):
            await ctx.reply("Unable to DM the user.")
            await ctx.send(
                f"{user.mention} you have been verbally warned for {reason}.\n-# Responsible moderator: {ctx.author.mention}"
            )

    @commands.command(description="Warn a user.", aliases=["w"])
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def warn(self, ctx, user: discord.Member, *, reason: str):
        """
        Warn a user.
        """
        if not has_higher_role(ctx, user):
            await ctx.send("You don't have permission to warn this member.")
            return

        try:
            await user.send(
                f"You have been warned in {ctx.guild.name} for: {reason}.\n- Responsible moderator: {ctx.author.mention}"
            )
            await ctx.message.add_reaction("✅")
        except (discord.errors.Forbidden, discord.errors.HTTPException):
            await ctx.reply("Unable to DM the user.")
            await ctx.send(
                f"{user.mention} you have been warned for: {reason}.\n- Responsible moderator: {ctx.author.mention}"
            )

        warn_id = f"{ctx.guild.id}-{random.randint(1000, 9999)}"
        warning = {
            "reason": reason,
            "moderator": ctx.author.mention,
            "time": datetime.now().isoformat(),
            "id": warn_id,
            "guild": ctx.guild.id,
        }

        self.warned_users_collection.update_one(
            {"_id": str(user.id)},
            {"$push": {f"guilds.{ctx.guild.id}.warnings": warning}},
            upsert=True,
        )

    @commands.command(description="Revoke a warning by warn ID.", aliases=["rw"])
    @commands.has_permissions(moderate_members=True)
    async def revoke_warn(self, ctx, warn_id: str):
        """
        Revoke a warning by warn ID.
        """
        guild_id, warn_suffix = warn_id.split("-")
        if str(ctx.guild.id) != guild_id:
            await ctx.send("Invalid warn ID for this guild.")
            return

        user_with_warning = self.warned_users_collection.find_one(
            {f"guilds.{ctx.guild.id}.warnings.id": warn_id}
        )
        if not user_with_warning:
            await ctx.send("Warning ID not found.")
            return

        member_id = user_with_warning["_id"]
        member = ctx.guild.get_member(int(member_id))
        if not has_higher_role(ctx, member):
            await ctx.send("You don't have permission to revoke this warning.")
            return

        self.warned_users_collection.update_one(
            {"_id": member_id},
            {"$pull": {f"guilds.{ctx.guild.id}.warnings": {"id": warn_id}}},
        )
        await ctx.send(f"Warning with ID {warn_id} has been revoked.")

    @commands.command(description="Get warns for a user or the top warns in the guild.", aliases=["ws"])
    @commands.guild_only()
    async def warns(self, ctx, user: discord.User = None):
        """
        Get warns for a user or the top warned users in the current guild.
        """
        if user is None:
            pipeline = [
                {"$match": {f"guilds.{ctx.guild.id}": {"$exists": True}}},
                {"$project": {
                    "_id": 1,
                    "warn_count": {"$size": f"$guilds.{ctx.guild.id}.warnings"},
                }},
                {"$sort": {"warn_count": -1}},
                {"$limit": 5},
            ]
            top_warned_users = self.warned_users_collection.aggregate(pipeline)

            embed = Embed(
                title=f"Top 5 Warned Users in {ctx.guild.name}",
                color=discord.Color.red(),
            )
            for user_data in top_warned_users:
                user_obj = await self.bot.get_or_fetch_user(int(user_data["_id"]))
                if user_obj:
                    embed.add_field(
                        name=f"{user_obj.name}",
                        value=f"Warns: {user_data['warn_count']}",
                        inline=False,
                    )
            await ctx.send(embed=embed)
        else:
            user_data = self.warned_users_collection.find_one(
                {"_id": str(user.id), f"guilds.{ctx.guild.id}": {"$exists": True}}
            )
            if not user_data or not user_data["guilds"][str(ctx.guild.id)]["warnings"]:
                await ctx.send(f"{user.name} has no warns in {ctx.guild.name}.")
            else:
                embed = Embed(
                    title=f"Warns for {user.name}#{user.discriminator} in {ctx.guild.name}",
                    color=discord.Color.red(),
                )
                warnings = sorted(
                    user_data["guilds"][str(ctx.guild.id)]["warnings"],
                    key=lambda x: x["time"],
                    reverse=True,
                )
                for counter, warn in enumerate(warnings, 1):
                    embed.add_field(
                        name=f"Case #{counter}:",
                        value=(
                            f"Reason: {warn['reason']}\n"
                            f"Moderator: {warn['moderator']}\n"
                            f"Time: {warn['time']}\n"
                            f"Warn ID: {warn['id']}"
                        ),
                        inline=True,
                    )
                await ctx.send(embed=embed)

    # we dont bother with aliases because this is a one-time command
    @commands.command(description="Setup the report channel.")
    async def setup_report(self, ctx, channel: discord.TextChannel):
        channel_id = channel.id
        # check if we already have it in the db
        if self.report_channels_collection.find_one({"_id": channel_id}):
            await ctx.send(
                f"Report channel already set to {channel.mention}. Overwriting..."
            )
        # format is {guild_id:  channel_id}
        self.report_channels_collection.update_one(
            {"_id": ctx.guild.id}, {"$set": {"channel_id": channel_id}}, upsert=True
        )
        await ctx.reply("Done :)\nBe sure to test things!")

    @commands.command(description="Report a user")
    @commands.guild_only()
    async def report(self, ctx):
        await ctx.reply("Fill in this information:", view=ReportView(self.bot))


def setup(bot):
    # huh it's blind ig
    # noinspection PyTypeChecker
    bot.add_view(ReportView(bot))
    bot.add_cog(Moderation(bot))
