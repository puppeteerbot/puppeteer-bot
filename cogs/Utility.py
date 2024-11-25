import discord
from discord.ext import commands
from discord.ext import tasks
from commondata import *
import asyncio
from PIL import Image
import aiohttp
import json
import math
import sympy
from sympy.printing.str import StrPrinter
import requests
from io import BytesIO
import random
import re
from bson import ObjectId
import datetime
from math import ceil


class HumanReadablePrinter(StrPrinter):
    def _print_Pow(self, expr):
        base, exp = expr.as_base_exp()
        if exp == -1:
            return f"1/({self._print(base)})"
        return f"{self._print(base)}^{self._print(exp)}"


def human_readable_str(expr):
    return HumanReadablePrinter().doprint(expr)


class TagPaginationView(discord.ui.View):
    def __init__(self, ctx, tag_names, per_page=25):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.tag_names = tag_names
        self.per_page = per_page
        self.total_pages = ceil(len(tag_names) / per_page)
        self.current_page = 1
        self.message = None

    def get_page_content(self, page):
        start = (page - 1) * self.per_page
        end = start + self.per_page
        return self.tag_names[start:end]

    async def update_embed(self, interaction):
        page_content = self.get_page_content(self.current_page)
        embed = discord.Embed(
            title=f"Available Tags (Page {self.current_page}/{self.total_pages})",
            color=0x00FF00,
        )
        tags = ""
        for tag in page_content:
            tags += f"`{tag}`\n"
        embed.add_field(name="\u200b", value=tags)
        embed.set_footer(text="Use the buttons below to navigate pages.")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(
        label="Previous", style=discord.ButtonStyle.secondary, disabled=True
    )
    async def previous_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "You cannot interact with this menu.", ephemeral=True
            )
            return

        self.current_page -= 1
        button.disabled = self.current_page == 1
        self.children[1].disabled = False  # Enable "Next" button
        await self.update_embed(interaction)

    @discord.ui.button(
        label="Next", style=discord.ButtonStyle.secondary, disabled=False
    )
    async def next_button(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message(
                "You cannot interact with this menu.", ephemeral=True
            )
            return

        self.current_page += 1
        button.disabled = self.current_page == self.total_pages
        self.children[0].disabled = False  # Enable "Previous" button
        await self.update_embed(interaction)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owners = owners
        self.todo_collection = self.bot.mongo_todo_stuff
        self.tags = bot.tags_db
        global todo_collection
        todo_collection = self.todo_collection

    @commands.command(
        description="Get a user's profile picture download link.", name="pfp"
    )
    async def pfp(self, ctx, user: discord.Member = None):
        """Get a user's profile picture download link."""
        user = user or ctx.author
        avatar_url = (
            str(user.avatar.url) if user.avatar else str(user.default_avatar.url)
        )
        if avatar_url:
            await ctx.reply(
                f"[Download link for {user.name}'s profile picture]({avatar_url})\n```{avatar_url}```"
            )
        else:
            await ctx.reply(f"{user.name} doesn't have a profile picture.")

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Get a user's profile picture download link.",
        name="pfp",
    )
    async def pfp_slash(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(
            discord.Member, "User to get profile picture for", required=False
        ) = None,
    ):
        user = user or ctx.author
        avatar_url = (
            str(user.avatar.url) if user.avatar else str(user.default_avatar.url)
        )
        if avatar_url:
            await ctx.respond(
                f"[Download link for {user.name}'s profile picture]({avatar_url})\n{avatar_url}"
            )
        else:
            await ctx.respond(f"{user.name} doesn't have a profile picture.")

    @commands.command(description="Flip a coin.", aliases=["cf"])
    async def coinflip(self, ctx):
        """Flip a coin."""
        import random

        result = random.choice(["Heads", "Tails"])
        if ctx.author.id == 1236667927944761396:
            result = "Tails"
        await ctx.reply(f"The coin landed on: **{result}**")

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Flip a coin.",
        name="coinflip",
    )
    async def coinflip_slash(self, ctx: discord.ApplicationContext):
        result = random.choice(["Heads", "Tails"])
        await ctx.respond(f"The coin landed on: **{result}**")

    @commands.command(
        description="Get a random number between two numbers. Defaults to 1-6. Includes endpoints.",
        aliases=["rand", "rng"],
    )
    async def random(self, ctx, start: int = 1, end: int = 6):
        """Get a random number between two numbers. Defaults to 1-6. Includes endpoints."""
        result = random.randint(start, end)
        await ctx.reply(f"Result: {result}")

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Get a random number between two numbers. Defaults to 1-6. Includes endpoints.",
        name="random",
    )
    async def random_slash(
        self,
        ctx: discord.ApplicationContext,
        start: discord.Option(int, "Start number", default=1),
        end: discord.Option(int, "End number", default=6),
    ):
        result = random.randint(start, end)
        await ctx.respond(f"Result: {result}")

    async def upload_images_to_imgur(self, images):
        clientid = Imgur_ClientID
        response = {"imagelinks": [], "failedToUpload": 0, "info": ""}

        for image in images:
            if isinstance(image, str):
                if image.startswith("http"):
                    response["imagelinks"].append(image)
                    continue

            if image.url.split("?")[0].endswith(".webp"):
                response["info"] = "You cannot upload webp files to imgur."
                response["failedToUpload"] += 1
                continue

            img_bytes = await image.read()
            responseimgur = requests.post(
                "https://api.imgur.com/3/image",
                headers={"Authorization": f"Client-ID {clientid}"},
                files={"image": BytesIO(img_bytes)},
            )

            if responseimgur.status_code == 200:
                img_url = responseimgur.json()["data"]["link"]
                response["imagelinks"].append(img_url)
            else:
                response["failedToUpload"] += 1

        return response

    @commands.command(
        description="Reply to an image with this command to upload it to imgur.",
        aliases=["imgur", "img"],
    )
    async def upload_to_imgur(self, ctx, *, links: str = None):
        """Reply to an image with this command to upload it to imgur."""
        try:
            images = []
            try:
                repliedmessage = ctx.message.reference.resolved
            except AttributeError:
                if ctx.message.attachments:
                    repliedmessage = ctx.message
                else:
                    if links:
                        images.extend(re.split(r"[\n ]", links))
                        repliedmessage = ctx.message
                    else:
                        await ctx.reply(
                            "Please reply to an image with this command to upload it to imgur."
                        )
                        return

            if isinstance(repliedmessage, discord.Message):
                if repliedmessage.attachments:
                    images.extend(repliedmessage.attachments)
                if repliedmessage.embeds:
                    for embed in repliedmessage.embeds:
                        if embed.image and embed.image.url:
                            images.append(embed.image.url)

            if not images:
                await ctx.reply(
                    "Please reply to an image with this command to upload it to imgur."
                )
                return

            response = await self.upload_images_to_imgur(images)

            message = "\n".join(response["imagelinks"])
            message += f'\n{response["info"]}'

            if response["failedToUpload"] > 0:
                message += f"\n-# :warning: {response['failedToUpload']} image(s) failed to upload"
            await ctx.reply(message)
        except Exception as e:
            raise e
            await ctx.reply("An error occurred while uploading the image to imgur.")

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Upload images to imgur.",
        name="upload_to_imgur",
    )
    async def upload_to_imgur_slash(
        self,
        ctx: discord.ApplicationContext,
        image: discord.Option(discord.Attachment, "Image to upload", required=True),
    ):
        try:
            await ctx.defer()
            response = await self.upload_images_to_imgur([image])

            message = "\n".join(response["imagelinks"])
            message += f'\n{response["info"]}'

            if response["failedToUpload"] > 0:
                message += f"\n-# :warning: {response['failedToUpload']} image(s) failed to upload"
            await ctx.respond(message)
        except Exception as e:
            raise e
            await ctx.respond("An error occurred while uploading the image to imgur.")

    async def convert_images(self, images, format):
        convertedimages = []
        for image in images:
            if isinstance(image, str):
                if image.startswith("http"):
                    continue
            img = Image.open(requests.get(image.url, stream=True).raw)
            imgbytes = BytesIO()
            img.save(imgbytes, format=format)
            convertedimages.append(imgbytes.getvalue())
        return [
            discord.File(BytesIO(img), filename=f"converted.{format.lower()}")
            for img in convertedimages
        ]

    @commands.command(description="Convert an image to png", aliases=["2png"])
    async def image_to_png(self, ctx, *, links: str = None):
        """Convert an image to png"""
        try:
            images = await self.get_images(ctx, links)
            if not images:
                await ctx.reply("Please choose an image to be converted!")
                return
            convertedimages = await self.convert_images(images, "PNG")
            await ctx.reply("Converted images:", files=convertedimages)
        except Exception as e:
            print(e)
            await ctx.reply("An error occurred while converting the image: " + str(e))
            raise e

    @commands.command(description="Convert an image to gif", aliases=["2gif"])
    async def image_to_gif(self, ctx, *, links: str = None):
        """Convert an image to gif"""
        try:
            images = await self.get_images(ctx, links)
            if not images:
                await ctx.reply("Please choose an image to be converted!")
                return
            convertedimages = await self.convert_images(images, "GIF")
            await ctx.reply("Converted images:", files=convertedimages)
        except Exception as e:
            print(e)
            await ctx.reply("An error occurred while converting the image: " + str(e))
            raise e

    @commands.command(description="Convert an image to jpg", aliases=["2jpg"])
    async def image_to_jpg(self, ctx, *, links: str = None):
        """Convert an image to JPEG"""
        try:
            images = await self.get_images(ctx, links)
            if not images:
                await ctx.reply("Please choose an image to be converted!")
                return
            convertedimages = await self.convert_images(images, "JPEG")
            await ctx.reply("Converted images:", files=convertedimages)
        except Exception as e:
            print(e)
            await ctx.reply("An error occurred while converting the image: " + str(e))
            raise e

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Convert an image to png",
        name="image_to_png",
    )
    async def image_to_png_slash(
        self,
        ctx: discord.ApplicationContext,
        image: discord.Option(discord.Attachment, "Image to convert", required=True),
    ):
        try:
            await ctx.defer()
            convertedimages = await self.convert_images([image], "PNG")
            await ctx.respond(content="Converted images:", files=convertedimages)
        except Exception as e:
            print(e)
            await ctx.respond("An error occurred while converting the image: " + str(e))
            raise e

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Convert an image to gif",
        name="image_to_gif",
    )
    async def image_to_gif_slash(
        self,
        ctx: discord.ApplicationContext,
        image: discord.Option(discord.Attachment, "Image to convert", required=True),
    ):
        try:
            await ctx.defer()
            convertedimages = await self.convert_images([image], "GIF")
            await ctx.respond(content="Converted images:", files=convertedimages)
        except Exception as e:
            print(e)
            await ctx.respond("An error occurred while converting the image: " + str(e))
            raise e

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Convert an image to jpg",
        name="image_to_jpg",
    )
    async def image_to_jpg_slash(
        self,
        ctx: discord.ApplicationContext,
        image: discord.Option(discord.Attachment, "Image to convert", required=True),
    ):
        try:
            await ctx.defer()
            convertedimages = await self.convert_images([image], "JPEG")
            await ctx.respond(content="Converted images:", files=convertedimages)
        except Exception as e:
            print(e)
            await ctx.respond("An error occurred while converting the image: " + str(e))
            raise e

    async def get_images(self, ctx, links):
        images = []
        try:
            repliedmessage = ctx.message.reference.resolved
        except AttributeError:
            if ctx.message.attachments:
                repliedmessage = ctx.message
            else:
                if links:
                    images.extend(re.split(r"[\n ]", links))
                    repliedmessage = ctx.message
                else:
                    await ctx.reply(
                        "Please reply to an image with this command to convert!"
                    )
                    return None

        if isinstance(repliedmessage, discord.Message):
            if repliedmessage.attachments:
                images.extend(repliedmessage.attachments)
            if repliedmessage.embeds:
                for embed in repliedmessage.embeds:
                    if embed.image and embed.image.url:
                        images.append(embed.image.url)
        return images

    async def get_httpcat_image(self, code):
        try:
            image = requests.get(f"https://http.cat/{code}.jpg")
            if image.status_code == 200:
                return BytesIO(image.content), None
            else:
                failimage = requests.get(f"https://http.cat/{image.status_code}.jpg")
                if failimage.status_code != 200:
                    print("huh" + str(image.status_code))
                    return None, f"Error: {image.status_code}"
                return BytesIO(failimage.content), f"Error: {image.status_code}"
        except Exception as e:
            return None, "Unknown error."

    @commands.command(
        description="get the http cat image for a http code", aliases=["hcat"]
    )
    async def httpcat(self, ctx, code):
        """Get the http cat image for a http code"""
        image_data, error_message = await self.get_httpcat_image(code)
        if image_data:
            await ctx.reply(
                file=discord.File(image_data, filename="httpcat.jpg"),
                content=error_message,
            )
        else:
            await ctx.reply(error_message)

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Get the http cat image for a http code",
        name="httpcat",
    )
    async def httpcat_slash(
        self,
        ctx: discord.ApplicationContext,
        code: discord.Option(str, "HTTP status code", required=True),
    ):
        await ctx.defer()
        image_data, error_message = await self.get_httpcat_image(code)
        if image_data:
            await ctx.respond(
                file=discord.File(image_data, filename="httpcat.jpg"),
                content=error_message,
            )
        else:
            await ctx.respond(error_message)

    @commands.command("setprefix", description="Obvious innit? (admin or dm only)")
    async def setprefix(self, ctx, new_prefix: str):
        """Sets a new prefix for the server or globally in DMs."""
        new_prefix = new_prefix.replace("<->", " ")
        if ctx.guild:  # In a server
            if not ctx.author.guild_permissions.administrator:
                await ctx.send(
                    "You need to be an administrator to change the server prefix."
                )
                return

            guild_id = str(ctx.guild.id)
            ctx.bot.mongo_prefixes.update_one(
                {"guild_id": guild_id}, {"$set": {"prefix": new_prefix}}, upsert=True
            )
            await ctx.send(f"Server prefix updated to: `{new_prefix}`")

        else:  # In DMs
            user_id = str(ctx.author.id)
            ctx.bot.mongo_prefixes.update_one(
                {"guild_id": f"user_{user_id}"},  # Use a unique key for users
                {"$set": {"prefix": new_prefix}},
                upsert=True,
            )
            await ctx.send(f"Global prefix for DMs updated to: `{new_prefix}`")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check for math calculations
        if message.content.startswith("="):
            try:
                # Remove the '=' prefix
                expression = message.content[1:]
                expression.replace(" ", "")
                expression.strip()
                # if the experssion is in a codeblock, extract it
                if message.content.startswith("```") and message.content.endswith(
                    "```"
                ):
                    expression = message.content[
                        message.content.find("\n") + 1 : message.content.rfind("```")
                    ]
                    expression.strip()
                # also for inline codeblock
                if message.content.startswith("`") and message.content.endswith("`"):
                    expression = message.content[
                        message.content.find("\n") + 1 : message.content.rfind("`")
                    ]
                    expression.strip()
                # Parse the expression with sympy
                parsed_expression = sympy.sympify(expression)
                # Evaluate the expression
                result = parsed_expression.evalf()
                pretty_result = human_readable_str(result)
                await message.reply(f"Result:\n```{pretty_result}```")
            except Exception as e:
                pass

    @commands.command(
        name="setnick",
        description="Set your nickname to our format",
        aliases=["stenick"],
    )
    async def setnick(
        self, ctx, user: discord.Member = None, shortId: str = None, clan: str = "RVR"
    ):
        """Set your nickname to our format"""
        if not ctx.author.guild_permissions.manage_nicknames:
            await ctx.reply("You do not have permission to set nicknames.")
            return
        usernameLengthLimit = 32
        username = f"[{clan}] {user.nick} | #{shortId}"
        if len(username) > usernameLengthLimit:
            username = f"{user.nick or user.display_name} #{shortId}"
            await ctx.reply("Had to truncate clan because of username length limit.")
        if len(username) > usernameLengthLimit:
            await ctx.reply("Still too big.")
            return
        await user.edit(nick=username)

    @commands.command(name="todo", description="Manage your todo list", aliases=["td"])
    async def todo(self, ctx, mode=None, *, arguments=None):
        """Manage your todo list"""
        mode, result = await todo_logic(ctx, mode, arguments=arguments)
        if mode == "text":
            await ctx.reply(result)
        elif mode == "embeds":
            for embed in result:
                await ctx.reply(embed=embed)
        else:
            raise ValueError("Invalid mode, glitchy get your ass here")

    @commands.message_command(
        name="Bookmark",
        description="Bookmark a message",
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
    )
    async def bookmark(self, ctx: discord.ApplicationContext, message: discord.Message):
        """Bookmark a message"""
        await ctx.defer()
        bookmark_db = self.bot.mongo_bookmarked_messages
        if not bookmark_db.find_one({"user_id": str(ctx.author.id)}):
            bookmark_db.update_one(
                {"user_id": ctx.author.id},
                {
                    "$set": {
                        f"bookmarks.{message.id}": {
                            "content": message.content,
                            "author": message.author.name,
                            "url": message.jump_url,
                            "timestamp": message.created_at.timestamp(),
                        }
                    }
                },
                upsert=True,
            )
            await ctx.respond("Bookmarked message.", ephemeral=True)
        else:
            await ctx.respond(
                "You already have that message bookmarked.", ephemeral=True
            )

    @commands.message_command(
        name="Unbookmark",
        description="Unbookmark a message",
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
    )
    async def unbookmark(
        self, ctx: discord.ApplicationContext, message: discord.Message
    ):
        """Unbookmark a message"""
        await ctx.defer()
        bookmark_db = self.bot.mongo_bookmarked_messages
        if bookmark_db.find_one({"user_id": ctx.author.id}):
            bookmark_db.update_one(
                {"user_id": ctx.author.id},
                {"$unset": {f"bookmarks.{message.id}": ""}},
                upsert=True,
            )
            await ctx.respond("Unbookmarked message.", ephemeral=True)
        else:
            await ctx.respond("You don't have that message bookmarked.", ephemeral=True)

    async def list_bookmarks_logic(self, user_id):
        bookmark_db = self.bot.mongo_bookmarked_messages
        bookmarks = bookmark_db.find({"user_id": user_id})
        embeds = []
        current_embed = discord.Embed(
            title="Bookmarked Messages", description="", color=0x00FF00
        )
        field_count = 0
        for bookmark in bookmarks:
            bookmark_data = bookmark["bookmarks"]
            for message_id, message_data in bookmark_data.items():
                content = message_data["content"]
                # Check if the content is too long to fit in a single field
                if len(content) > 200:
                    content = content[:200] + "..."
                # resolve mentions, i.e convert <@123456789012345678> to @user
                pings = []
                for match in re.finditer(r"<@!?(\d+)>", content):
                    print(match.group(1))
                    user_id = int(match.group(1))
                    user = await self.bot.fetch_user(user_id)
                    if user:
                        pings.append((user.id, user.name))
                for ping in pings:
                    content = content.replace(f"<@{ping[0]}>", f"`@{ping[1]}`")
                author = message_data["author"]
                url = message_data["url"]
                timestamp = message_data["timestamp"]
                timestamp = datetime.datetime.fromtimestamp(timestamp).strftime(
                    "%d-%m-%y %H:%M:%S"
                )
                current_embed.add_field(
                    name=f"{content}",
                    value=f"Author: {author}\nMessage ID: {message_id}\nURL: {url}\nTimestamp: {timestamp}",
                    inline=False,
                )
                field_count += 1
                if field_count >= 25:
                    embeds.append(current_embed)
                    current_embed = discord.Embed(
                        title="Bookmarked Messages", description="", color=0x00FF00
                    )
                    field_count = 0
        if current_embed.fields:
            embeds.append(current_embed)
        if not embeds:
            return "text", "You have no bookmarked messages."
        return "embeds", embeds

    @commands.command(
        name="bookmarks", description="List your bookmarked messages", aliases=["bms"]
    )
    async def list_bookmarks(self, ctx: discord.ApplicationContext):
        """List your bookmarked messages"""
        print(ctx)
        user_id = ctx.author.id
        bookmarks = await self.list_bookmarks_logic(user_id)
        if bookmarks[0] == "embeds":
            for embed in bookmarks[1]:
                await ctx.reply(embed=embed)
        elif bookmarks[0] == "text":
            await ctx.reply(bookmarks[1])
        else:
            await ctx.reply("huh")
            raise Exception(
                f"we should have gotten embeds, lets raise here. debug info: {bookmarks}"
            )

    @commands.slash_command(
        name="bookmarks",
        description="List your bookmarks",
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
    )
    async def list_bookmarks_slash(self, ctx: discord.ApplicationContext):
        """List your bookmarked messages"""
        user_id = ctx.author.id
        bookmarks = await self.list_bookmarks_logic(user_id)
        if bookmarks[0] == "embeds":
            for embed in bookmarks[1]:
                await ctx.respond(embed=embed, ephemeral=True)
        elif bookmarks[0] == "text":
            await ctx.respond(bookmarks[1], ephemeral=True)
        else:
            await ctx.respond("huh")
            raise Exception(
                f"we should have gotten embeds, lets raise here. debug info: {bookmarks}"
            )

    @commands.command(
        name="remove_bookmark", description="Remove a bookmark", aliases=["rmb"]
    )
    async def remove_bookmark(self, ctx, bookmark_id: int):
        """Remove a bookmark"""
        bookmark_db = self.bot.mongo_bookmarked_messages
        if bookmark_db.find_one({"user_id": ctx.author.id}):
            bookmark_db.update_one(
                {"user_id": ctx.author.id},
                {"$unset": {f"bookmarks.{bookmark_id}": ""}},
                upsert=True,
            )
            await ctx.reply("Removed bookmark.")
        else:
            await ctx.reply("You don't have that bookmark.")

    @commands.slash_command(
        name="remove_bookmark",
        description="Remove a bookmark",
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
    )
    async def remove_bookmark_slash(
        self, ctx: discord.ApplicationContext, bookmark_id: int
    ):
        """Remove a bookmark"""
        bookmark_db = self.bot.mongo_bookmarked_messages
        if bookmark_db.find_one({"user_id": ctx.author.id}):
            bookmark_db.update_one(
                {"user_id": ctx.author.id}, {"$unset": {f"bookmarks.{bookmark_id}": ""}}
            )
            await ctx.respond("Removed bookmark.", ephemeral=True)
        else:
            await ctx.respond("You don't have that bookmark.", ephemeral=True)

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx: commands.Context, *, name: str):
        """Retrieve a tag by name."""
        tag = self.tags.find_one({"name": name.lower()})
        if tag:
            content = tag["content"]
            embed = discord.Embed(title=f"Tag: {name}", color=discord.Color.random())
            embed.set_footer(text=f"Created by: {self.bot.get_user(tag['creator_id'])}")
            await ctx.send(content, embed=embed)
        else:
            await ctx.send("Tag not found.")

    @tag.command(name="create")
    async def create_tag(self, ctx, *, name: str):
        """Create a new tag."""
        name = name.lower()
        if name in ["list", "edit", "delete"]:
            await ctx.reply("you think you're clever huh?")
        if self.tags.find_one({"name": name}):
            await ctx.send("A tag with this name already exists.")
            return

        await ctx.send("Send the content of the tag in your next message.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            content_message = await self.bot.wait_for(
                "message", timeout=60.0, check=check
            )
            content = content_message.content
            self.tags.insert_one(
                {"name": name, "content": content, "creator_id": ctx.author.id}
            )
            await ctx.send(f"Tag `{name}` created successfully.")
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Tag creation canceled.")

    @tag.command(name="edit")
    async def edit_tag(self, ctx, *, name: str):
        """Edit an existing tag."""
        name = name.lower()
        tag = self.tags.find_one({"name": name})
        if not tag:
            await ctx.send("Tag not found.")
            return

        if tag["creator_id"] != ctx.author.id and ctx.author.id not in owners:
            await ctx.send("You don't have permission to edit this tag.")
            return

        await ctx.send("Send the new content of the tag in your next message.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            content_message = await self.bot.wait_for(
                "message", timeout=60.0, check=check
            )
            new_content = content_message.content
            self.tags.update_one({"name": name}, {"$set": {"content": new_content}})
            await ctx.send(f"Tag `{name}` updated successfully.")
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. Tag edit canceled.")

    @tag.command(name="delete")
    async def delete_tag(self, ctx, *, name: str):
        """Delete an existing tag."""
        name = name.lower()
        tag = self.tags.find_one({"name": name})
        if not tag:
            await ctx.send("Tag not found.")
            return

        if tag["creator_id"] != ctx.author.id and ctx.author.id not in owners:
            await ctx.send("You don't have permission to delete this tag.")
            return

        self.tags.delete_one({"name": name})
        await ctx.send(f"Tag `{name}` deleted successfully.")

    @tag.command(name="list")
    async def list_tags(self, ctx):
        """List all tags with pagination using buttons."""
        tags = list(self.tags.find())  # Retrieve all tags from the database
        tag_names = [tag["name"] for tag in tags]

        if not tag_names:
            await ctx.send("No tags available.")
            return

        # Initialize pagination view
        view = TagPaginationView(ctx, tag_names)
        embed = discord.Embed(title="Available Tags (Page 1)", color=0x00FF00)
        page_content = view.get_page_content(1)
        tags = ""
        for tag in page_content:
            tags += f"`{tag}`\n"
        embed.add_field(name="\u200b", value=tags)
        embed.set_footer(text="Use the buttons below to navigate pages.")

        # Send the initial embed and assign the message to the view
        view.message = await ctx.send(embed=embed, view=view)


todo_commands = discord.SlashCommandGroup("todo", "Manage your todo list")


async def todo_logic(ctx, mode=None, *, arguments=None):
    user_id = ctx.author.id
    if mode == "list":
        embeds = []
        current_embed = discord.Embed(title="Todo List", description="", color=0x00FF00)
        field_count = 0
        user_todos = todo_collection.find({"user_id": user_id}).to_list(length=None)
        for todo_item in user_todos:
            if field_count >= 20:
                embeds.append(current_embed)
                current_embed = discord.Embed(
                    title="Todo List (Continued)", description="", color=0x00FF00
                )
                field_count = 0
            current_embed.add_field(
                name=f"Item {todo_item['_id']}",
                value=f"{todo_item['name']} (Added: {todo_item['timeadded']})",
                inline=False,
            )
            field_count += 1
        embeds.append(current_embed)
        return "embeds", embeds
    elif mode == "add":
        result = todo_collection.insert_one(
            {
                "user_id": user_id,
                "name": arguments,
                "timeadded": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        return "text", f"Added '{arguments}' to todo list with ID {result.inserted_id}."
    elif mode == "remove":
        if not ObjectId.is_valid(arguments):
            return "text", "Please provide a valid todo item ID to remove."
        todo_id = ObjectId(arguments)
        result = todo_collection.delete_one({"_id": todo_id, "user_id": user_id})
        if result.deleted_count > 0:
            return "text", f"Removed todo item with ID {todo_id} from your list."
        else:
            return "text", f"No todo item found with ID {todo_id} in your list."
    else:
        return "text", "Invalid mode. Please use 'list', 'add', or 'remove'."


@todo_commands.command(
    name="list",
    description="List your todo items",
    integration_types={
        discord.IntegrationType.user_install,
        discord.IntegrationType.guild_install,
    },
)
async def todo_slash_list(ctx):
    """List your todo items"""
    result = await todo_logic(ctx, mode="list")
    if result[0] == "embeds":
        count = 1
        for embed in result[1]:
            if count == 1:
                await ctx.respond(embed=embed)
            else:
                await ctx.followup.send(embed=embed)
            count += 1
    else:
        await ctx.respond(result[1])


@todo_commands.command(
    name="add",
    description="Add a todo item",
    integration_types={
        discord.IntegrationType.user_install,
        discord.IntegrationType.guild_install,
    },
)
async def todo_slash_add(
    ctx,
    *,
    arguments: discord.Option(
        name="arguments", description="The todo item to add", type=str
    ),
):
    """Add a todo item"""
    result = await todo_logic(ctx, mode="add", arguments=arguments)
    if result[0] == "text":
        await ctx.respond(result[1])
    else:
        raise ValueError("Invalid mode, glitchy get your ass here")


@todo_commands.command(
    name="remove",
    description="Remove a todo item",
    integration_types={
        discord.IntegrationType.user_install,
        discord.IntegrationType.guild_install,
    },
)
async def todo_slash_remove(
    ctx,
    arguments: discord.Option(
        name="arguments", description="The ID of the todo item to remove", type=str
    ),
):
    """Remove a todo item"""
    result = await todo_logic(ctx, mode="remove", arguments=arguments)
    if result[0] == "text":
        await ctx.respond(result[1])


def setup(bot):
    bot.add_application_command(todo_commands)
    bot.add_cog(Utility(bot))
