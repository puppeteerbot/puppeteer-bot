import discord
from discord.ext import commands, tasks
import asyncio
import os
import subprocess
import sys
from commondata import owners, DiscordToken, connectionString

# import mongodb
from pymongo import MongoClient
from flask import Flask, request
from threading import Thread

app = Flask(__name__)


@app.route("/")
def home():
    return "Puppeteer is up :D"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()


class App(commands.Bot):
    def __init__(self, DiscordToken, *args, **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=".", intents=intents, *args, **kwargs)
        self.mongo_client = MongoClient(connectionString)
        self.mongo_db = self.mongo_client["puppeteer_bot"]
        self.mongo_warned_users = self.mongo_db["warned_users"]
        self.mongo_todo_stuff = self.mongo_db["todo_stuff"]
        self.mongo_snake_game = self.mongo_db["snake_game"]
        self.mongo_bookmarked_messages = self.mongo_db["bookmarked_messages"]
        self.mongo_report_channels = self.mongo_db["report_channels"]
        self.mongo_prefixes = self.mongo_db["prefixes"]
        self.tags_db = self.mongo_db["tags"]
        self.DiscordToken = DiscordToken
        self.DiscordPrefix = "."
        self.DiscordBot_owners = owners
        self.fail_notified = False

    async def setup_hook(self):
        for cog in os.listdir("cogs"):
            if cog.endswith(".py"):
                try:
                    if cog == "cogs.commondata.py":
                        continue
                    self.load_extension(f"cogs.{cog[:-3]}")
                    print(f"Loaded cog: {cog[:-3]}")
                except Exception as e:
                    print(f"Failed to load cog {cog}: {e}")
                    raise e

    async def get_member_count(self):
        print("Getting member count...")
        admin_servers = [
            guild for guild in self.guilds if guild.me.guild_permissions.administrator
        ]
        print(f"Found {len(admin_servers)} admin servers")
        unique_members = set()
        for guild in admin_servers:
            print(f"Processing guild: {guild.name}")
            for member in guild.members:
                print(f"Added {member.name}")
                unique_members.add(member.id)
        print(f"Found {len(unique_members)} unique members")
        return len(unique_members)

    async def on_ready(self):
        member_count = await self.get_member_count()
        await self.sync_commands(force=True)
        await self.change_presence(
            activity=discord.Game(name=f"with {member_count} members...")
        )
        print(f"Discord bot ready, logged in as {self.user}")

    async def get_dynamic_prefix(self, message):
        """Get dynamic prefix based on server or user (DM)"""
        if message.guild:  # In a server
            guild_id = str(message.guild.id)
            prefix_data = self.mongo_prefixes.find_one({"guild_id": guild_id})
        else:  # In DMs
            user_id = str(message.author.id)
            prefix_data = self.mongo_prefixes.find_one({"guild_id": f"user_{user_id}"})

        # Return the custom prefix or fallback to the default
        return (
            prefix_data["prefix"]
            if prefix_data and "prefix" in prefix_data
            else self.DiscordPrefix
        )

    @tasks.loop(minutes=1)
    async def update_status(self):
        member_count = await self.get_member_count()
        await self.change_presence(
            activity=discord.Game(name=f"with {member_count} members...")
        )

    async def on_message(self, message):
        if message.author.bot:
            return  # Ignore bot messages
            # Get the dynamic prefix
        dynamic_prefix = await self.get_dynamic_prefix(message)

        # Check if the message starts with the dynamic prefix
        if message.content.startswith(dynamic_prefix):
            # Replace the dynamic prefix with the bot's default prefix for processing
            message.content = message.content.replace(
                dynamic_prefix, self.DiscordPrefix, 1
            )
        # Manually process the command
        await self.process_commands(message)


async def main():
    bot = App(DiscordToken=DiscordToken)
    await bot.setup_hook()
    await bot.start(DiscordToken)


if __name__ == "__main__":
    # keep_alive() # we use this when we need to
    asyncio.run(main())
