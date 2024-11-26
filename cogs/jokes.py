import discord
from discord.ext import commands
from commondata import *


class Jokes(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.ext.commands.Bot = bot
        self.owners = owners
        self.dmed = False

    @commands.command(aliases=["walk", "work", "walk_dog"])
    async def touch_grass(self, ctx):
        if not ctx.author.id in self.owners:
            await ctx.reply(
                "Go touch some grass t.t, maybe get a life like in actual irl."
            )
        else:
            await ctx.reply("You found 10 coins on the street on your way!")

    @commands.Cog.listener()
    async def on_message(self, message):
        # handle jokes
        if message.author.bot:
            return
        if message.author.id in self.owners:
            if "glockchy" in message.content.lower():
                await message.reply("https://i.imgur.com/ibFoVrV.jpeg")
        if message.author.id == 1267481067842175191:
            await message.add_reaction("👍")
        if "goat" in message.content.lower():
            await message.reply(":goat:")
        if "puppeteer" in message.content.lower() and message.author.id in self.owners:
            await message.add_reaction("<:dev:1301925243459211305>")


def setup(bot):
    bot.add_cog(Jokes(bot))
