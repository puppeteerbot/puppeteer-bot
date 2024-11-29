from os.path import exists
from discord import Embed, File, Interaction
from discord.ext.commands import Context
from typing import Optional, List, Union
from discord.ext import commands as _8
from datetime import timedelta
from discord.commands.context import ApplicationContext


if exists("./.test_flag"):
    DiscordToken = "Unstable bot token"
else:
    DiscordToken = "Normal Bot Token"
owners = [1236667927944761396, 1018144363555069952, 1263441492882755635]
DiscordBot_name = "Puppeteer"
Imgur_ClientID = "f1d216554327a6d"
DiscordBot_description = """Heya, im puppeteer, a discord bot made by i_am_called_glitchy.
Originally just reverie's toy, this bot has been remade and coded to be useful for anyone to use, user or guild install :)"""
DiscordBot_subdescriptions = {
    "Engine": "Made with python 3.12.6 64-bit, pycord, irrvlo's API for some stuff, SherrifCarry's kirkajs (forked for python), lukeskywalk's api, and others...",
    "Legal Info": "This bot is not associated with kirka.io, irrvlo, or any other possibly implied party.\nThis bot has been made as a hobby project and all complaints should be directed to i_am_called_glitchy directly.\n-# dont bother with my email i dont check that.",
}
connectionString = "mongodb+srv://user:password@host"  # mongodb
glitchyKirkaBadges = [
    "https://i.imgur.com/JhMlisg.png",
    "https://i.imgur.com/PePV8tf.png",
    "https://i.imgur.com/hpqf68p.png",
    "https://i.imgur.com/QbyX7XV.png",
]
KirkaBadges = {
    "Reverie": "https://i.imgur.com/PePV8tf.png",
    "Glitchy": "https://i.imgur.com/JhMlisg.png",
    "ReverieLeader": "https://i.imgur.com/hpqf68p.png",
    "Pdev": "https://i.imgur.com/QbyX7XV.png",
    "poop": "https://cdn3.emoji.gg/emojis/9721-dnd-d20.png",
}
KirkaBackgrounds = {
    "Skynet": "https://i.imgur.com/NxItcCc.png",
    "Sniper": "https://irrvlo.xyz/snipergecko.png",
    "Glitchedbg": "https://i.imgur.com/IZ2tC5C.jpeg",
    # "TTV": "https://i.imgur.com/MJ13qJi.png"
    "TTV": "https://cdn.discordapp.com/avatars/1169111190824308768/5019045e780fd069aa2f36bddd72847c.png?size=1024",
    "ttvbro": "https://cdn.discordapp.com/avatars/1258173648989327361/ec62376e6a0c061f2c4ca5ab07c805ca.png?size=1024",
    "Puppeteer": "https://cdn.discordapp.com/avatars/1293863138785103963/e4441ab3e0454e6eecae6b590d594131.png?size=1024",
}
UserAgent = ":) this is a bot btw"


class DebugException(BaseException):
    def __init__(self, message, *args, **kwargs):
        self.message = message
        super().__init__(*args, **kwargs)



class Response:
    def __init__(
        self,
        content: Optional[str] = None,
        embeds: Optional[List[Embed]] = None,
        files: Optional[List[File]] = None,
        ephemeral: bool = False,
        mention_author: bool = True,
        meta: any = None,
    ):
        self.content: Optional[str] = content
        self.embeds: List[Embed] = embeds if embeds else []
        self.files: List[File] = files if files else []
        self.ephemeral: bool = ephemeral
        self.meta: any = meta
        self.reply_ping: bool = mention_author

    async def send(self, target):
        if isinstance(target, Context):  # Prefix command context
            await target.reply(
                content=self.content,
                embeds=self.embeds,
                files=self.files,
                mention_author=self.reply_ping,
            )
        elif isinstance(target, (Interaction, ApplicationContext)):  # Slash commands or button interactions
            if not target.response.is_done():
                await target.response.send_message(
                    content=self.content,
                    embeds=self.embeds,
                    files=self.files,
                    ephemeral=self.ephemeral,
                )
            else:
                await target.followup.send(
                    content=self.content,
                    embeds=self.embeds,
                    files=self.files,
                    ephemeral=self.ephemeral,
                )
        else:
            raise TypeError(f"Unsupported target type. Must be Context or Interaction, got {type(target)}.")

def is_owner_or_has_permissions(**perms):
    original_check = _8.has_permissions(**perms).predicate

    async def extended_check(ctx):
        if ctx.author.id in owners:
            return True
        return await original_check(ctx)

    return _8.check(extended_check)


def parse_duration(duration):
    """
    Parse a duration string into a timedelta object.

    Args:
        duration (str): A string representing a duration (e.g., "1w2d3h4m5s").

    Returns:
        timedelta: A timedelta object representing the parsed duration, or None if parsing fails.
    """

    units = {"w": "weeks", "d": "days", "h": "hours", "m": "minutes", "s": "seconds"}

    duration_dict = {}
    current_number = ""

    for char in duration:
        if char.isdigit():
            current_number += char
        elif char in units:
            if current_number:
                duration_dict[units[char]] = int(current_number)
                current_number = ""
        else:
            return None  # Invalid character found

    if current_number:  # If there's a trailing number without a unit
        return None

    try:
        return timedelta(**duration_dict)
    except (TypeError, ValueError): # oh god
        return None
# :D Welcome to puppeteer's development team!
