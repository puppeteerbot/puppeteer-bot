from commondata import *
from discord.ext import commands
from discord import Interaction
from discord.errors import ApplicationCommandInvokeError

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            response = Response(
                content=f"Oops! You're missing a required argument: `{error.param.name}`. "
                        "Please check the command usage and try again."
            )
            await response.send(ctx)

        elif isinstance(error, commands.errors.MissingPermissions):
            response = Response(
                content="Oops! You don't have permission to use this command.\n"
                        "Please check your permissions and try again."
            )
            await response.send(ctx)

        elif isinstance(error, commands.errors.BadArgument):
            response = Response(
                content=f"Oops! You've entered an invalid argument: `{error}`.\n"
                        "Please check the command usage and try again."
            )
            await response.send(ctx)

        elif isinstance(error, commands.errors.CommandNotFound):
            pass

        elif isinstance(error, commands.errors.NotOwner):
            message = (
                f"Someone tried to use a restricted command. "
                f"User: {ctx.author.mention}, Command: `{ctx.command.name}`."
            )
            print(message)

        elif isinstance(error, commands.errors.NoPrivateMessage):
            response = Response(content="Sorry, this command can only be used in servers!")
            await response.send(ctx)

        elif isinstance(error, commands.errors.MemberNotFound):
            response = Response(
                content="Oops! The member you're trying to mention doesn't exist. "
                        "Please check the member's name and try again."
            )
            await response.send(ctx)

        elif (
            isinstance(error, commands.errors.CommandInvokeError)
            and error.original == DebugException
        ):
            ...

        else:
            response = Response(
                content=f"Oops! Something went wrong. Please try again later.\n"
                        f"Error: `{error.original}`"
            )
            await response.send(ctx)
            raise error.original

    @commands.Cog.listener()
    async def on_application_command_error(self, interaction: Interaction, error):
        if isinstance(error, ApplicationCommandInvokeError):
            response = Response(
                content=f"Oops! Something went wrong while executing the command.\n"
                        f"Error: `{error.original}`",
                ephemeral=True  # Send error privately
            )
            await response.send(interaction)
            raise error
        elif isinstance(error, commands.errors.MissingPermissions):
            response = Response(
                content="Oops! You don't have permission to use this command.\n"
                        "Please check your permissions and try again.",
                ephemeral=True
            )
            await response.send(interaction)
        elif isinstance(error, commands.errors.MissingRequiredArgument):
            response = Response(
                content="A required argument is missing for this command.\n"
                        "Please check the command usage and try again.",
                ephemeral=True
            )
            await response.send(interaction)
        else:
            response = Response(
                content="An unexpected error occurred. Please try again later.",
                ephemeral=True
            )
            await response.send(interaction)
            raise error


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
