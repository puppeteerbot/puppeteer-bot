import discord
from discord.ext import commands
from commondata import *


class MyHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return "`%s%s %s`  %s" % (
            self.context.clean_prefix,
            command.qualified_name,
            command.signature,
            command.description,
        )

    async def send_bot_help(self, mapping):
        cogs = [
            cog
            for cog in mapping.keys()
            if cog
            and cog.qualified_name
            not in [
                "No Category",
                "DontLook",
                "handlers",
                "Customhelp",
                "ErrorHandler",
                "Jokes",
            ]
        ]

        embed = discord.Embed(title="Cogs:", color=discord.Color.blurple())
        cog_list = "\n".join([cog.qualified_name for cog in cogs])
        embed.description = cog_list

        view = discord.ui.View()

        async def cog_callback(interaction: discord.Interaction, cog: commands.Cog):
            cog_embed = discord.Embed(
                title=f"{cog.qualified_name} Commands:", color=discord.Color.blurple()
            )
            filtered = await self.filter_commands(cog.get_commands(), sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered]
            cog_embed.description = "\n".join(command_signatures)
            await interaction.response.send_message(embed=cog_embed, ephemeral=True)

        for cog in cogs:
            view.add_item(
                discord.ui.Button(
                    label=cog.qualified_name,
                    style=discord.ButtonStyle.primary,
                    custom_id=cog.qualified_name,
                )
            )
            view.children[-1].callback = lambda i, c=cog: cog_callback(i, c)

        channel = self.get_destination()
        await channel.send(embed=embed, view=view)

    async def send_command_help(self, command):
        embed = discord.Embed(
            title=self.get_command_signature(command), color=discord.Color.random()
        )
        if command.help:
            embed.description = command.help
        if alias := command.aliases:
            embed.add_field(name="Aliases", value=", ".join(alias), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(
            title=self.get_command_signature(group),
            description=group.help,
            color=discord.Color.blurple(),
        )

        if filtered_commands := await self.filter_commands(group.commands):
            for command in filtered_commands:
                embed.add_field(
                    name=self.get_command_signature(command),
                    value=command.help or "No Help Message Found... ",
                )

        await self.get_destination().send(embed=embed)


class Customhelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owners = owners
        bot.help_command = MyHelp()


def setup(bot):
    bot.add_cog(Customhelp(bot))
