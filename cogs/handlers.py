import discord
from discord.ext import commands
from commondata import *


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send(
                f"Oops! You're missing a required argument: {error.param.name}. "
                f"Please check the command usage and try again."
            )
        # permission error
        elif isinstance(error, commands.errors.MissingPermissions):
            await ctx.send(
                f"Oops! You don't have permission to use this command.\n "
                f"Please check your permissions and try again."
            )
        # fucked arguments
        elif isinstance(error, commands.errors.BadArgument):
            await ctx.send(
                f"Oops! You've entered an invalid argument: {error}. \n \
                           Please check the command usage and try again."
            )
        # command not found
        elif isinstance(error, commands.errors.CommandNotFound):
            pass
        # not owner
        elif isinstance(error, commands.errors.NotOwner):
            # dm glitchy
            message = f"someone decided to use a restricted command, he's {ctx.author.mention} and the command was {ctx.command.name}."
            print(message)
        # guild only command
        elif isinstance(error, commands.errors.NoPrivateMessage):
            await ctx.reply("Sorry, this command can only be used in servers!")
        # member not found
        elif isinstance(error, commands.errors.MemberNotFound):
            await ctx.send(
                f"Oops! The member you're trying to mention doesn't exist. "
                f"Please check the member's name and try again."
            )
        # debug exception in a command, we ignore this so we dont get duplicate errors
        elif (
            isinstance(error, commands.errors.CommandInvokeError)
            and error.original == DebugException
        ):
            ...
        # other errors
        else:
            await ctx.send(
                f"Oops! Something went wrong. Please try again later. {error.original}"
            )
            raise error.original  # notify the devs


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
