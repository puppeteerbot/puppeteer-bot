from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import base64
from commondata import *
import discord
from thefckingkirkaapi import KirkaAPI  # linter: ignore
import json
import re
from unidecode import unidecode
import requests
from requests.utils import quote
import io
from io import BytesIO
import tradeParser
import datetime as dt

cached_prices = {}


def wrap_text(text, font, max_width, draw):
    """Wrap the text to fit within the max_width."""
    lines = []
    words = text.split(" ")
    current_line = words[0]

    for word in words[1:]:
        # Check the width of the current line with the new word
        width = draw.textlength(current_line + " " + word, font=font)
        if width <= max_width:
            current_line += " " + word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines


async def get_user_stats(short_id: str = None, ctx=None):
    try:
        if short_id is None and ctx:
            # Get the ID from the invoking user's server nickname
            nickname = unidecode(ctx.author.nick or ctx.author.name)
            match = re.search(r"#([A-Za-z0-9]{6})", nickname)
            if match:
                short_id = match.group(1)
            else:
                return "ID not found, either put your ID in your server nickname or put your ID as an argument."
        if short_id.startswith("#"):
            short_id = short_id[1:]
        if len(short_id) != 6:
            return "Invalid short ID. Please provide a valid short ID."
        short_id = short_id.upper()
        stats = requests.get(
            f"https://kirka.irrvlo.xyz/_next/data/Qj7Evkvz7SgKQYk1Q4HmZ/users/{short_id}.json"
        )
        print(stats.text)
        if stats.status_code == 404 or stats.json()["pageProps"]["error"]:
            return "User not found."
        data = stats.json()["pageProps"]["userData"]
        cosmetics = get_cosmetics(
            short_id, (data.get("clan", "") == "Reverie"), data["role"]
        )
        role = cosmetics.get("Role", data["role"])
        data["role"] = role
        userBadges = cosmetics.get("Badges", [])
        userBackground = cosmetics.get("Background")

        image = generate_profile_image(data, userBadges, userBackground)

        # Convert the image to bytes
        with io.BytesIO() as image_binary:
            image.save(image_binary, "PNG")
            image_binary.seek(0)
            file = discord.File(fp=image_binary, filename="profile.png")

        return file, f"Stats for #{short_id}:"
    except Exception as e:
        raise e


def get_cosmetics(shortId, inReverie, Role):  # cosmetics for profile command yahoo
    shortId = shortId.upper().strip("#")
    print(shortId)
    verified_guys = ["T57L43"]
    userBadges = {
        "B0TMFC": glitchyKirkaBadges,
        "ZSE1GS": glitchyKirkaBadges,
        "YUM43P": glitchyKirkaBadges,
        "985CBJ": [
            KirkaBadges["ReverieLeader"],
            KirkaBadges["Pdev"],
            KirkaBadges["poop"],
        ],
        "QYRPV0": [KirkaBadges["ReverieLeader"], "https://i.imgur.com/dOzdhiN.png"],
        "MZFCNO": [KirkaBadges["ReverieLeader"]],
        "FULOTV": [KirkaBadges["XX5"]],
    }
    userBackgrounds = {
        "B0TMFC": KirkaBackgrounds["Glitchedbg"],
        "T57L43": KirkaBackgrounds["Flow"],
        "ZSE1GS": KirkaBackgrounds["Glitchedbg"],
        "YUM43P": KirkaBackgrounds["Skynet"],
        "985CBJ": KirkaBackgrounds["TTV"],
        "MZFCNO": "https://i.imgur.com/8LVz09U.jpeg",
        "Y2OOB2": KirkaBackgrounds["ttvbro"],
    }
    bots = ["YUM43P", "Y2OOB2"]
    if shortId in bots:
        Role = "BOT"
    if shortId in verified_guys:
        Role = "VERIFIED"

    data_to_return = {
        "Badges": userBadges.get(
            shortId, [KirkaBadges["Reverie"]] if inReverie else []
        ),
        "Background": userBackgrounds.get(shortId, "https://i.imgur.com/XhbsxXM.jpeg"),
        "Role": Role,
    }
    print(data_to_return)
    return data_to_return



def generate_clan_image(data, page=0):
    # Create a blank image
    width, height = 800, 640
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)
    bgimage = "https://i.imgur.com/XhbsxXM.jpeg"
    # Define fonts
    title_font = load_font(36)
    text_font = load_font(20)
    # small_font = load_font(18) # unused
    subtext_font = load_font(14)

    # define colors
    # title_color = "white"
    # stroke_color = "black"
    # text_color = "white"
    # clan_color = hex_to_rgb("7a00ffff")
    # cyan_color = hex_to_rgb("01ffffff") # unused
    # prepare strings
    print(data)
    title_text = f"Clan: {data['name']}"
    leader = None
    for i in data["members"]:
        if i["role"] == "LEADER":
            leader = i
            print(i)
            break
    leader_text = f"Leader: {leader['user']['name']} ({leader['allScores']:,})"
    officers = []
    officers_score = 0
    for i in data["members"]:
        if i["role"] == "OFFICER":
            officers.append(i["user"])
            officers_score += i["allScores"]

    officers_text = f"{len(officers)} Officers, Score per officer (avg): {officers_score // len(officers) if len(officers) != 0 else 0:,}"
    members = sorted(
        [i for i in data["members"] if i["role"] == "NEWBIE"],
        key=lambda x: x["allScores"],
        reverse=True,
    )
    member_scores = sum(member["allScores"] for member in members)
    members_text = f"{len(members)} Members, Score per member (avg): {member_scores // len(members) if len(members) != 0 else 0:,}"
    all_members = []
    for i in data["members"]:
        all_members.append(i)

    all_members_text = [
        f"{i['role']} | {i['user']['name']} ({i['allScores']:,})"
        for i in sorted(all_members, key=lambda x: x["allScores"], reverse=True)
    ]

    misc_text = f"Discord: {data['discordLink'] if data.get('discordLink', {}) else None}\nCreated At: {data['createdAt'].split('T')[0]}\nTotal Score: {data['allScores']:,}\nAll members: {len(all_members)}"
    # and just because yes we're going to add customizability.
    settings = {
        "title": {"color": "white", "font": title_font, "x": 30, "y": 30},
        "leader": {"color": "red", "font": text_font, "x": 30, "y": 80},
        "officers": {"color": "turquoise", "font": text_font, "x": 30, "y": 110},
        "newbies": {"color": "lime", "font": text_font, "x": 30, "y": 140},
        "all_members": {"color": "white", "font": subtext_font, "x": 30, "y": 220},
        "misc": {"color": "white", "font": subtext_font, "x": 30, "y": 170},
        "description": {"color": "white", "font": subtext_font, "x": 30, "y": 570},
    }

    # first the background, because...
    if bgimage:
        headers = {"User-Agent": "this is a bot :3"}
        response = requests.get(bgimage, headers=headers)
        if response.status_code == 200:
            background = Image.open(BytesIO(response.content))
            background = background.resize((width, height))
            background = background.filter(ImageFilter.GaussianBlur(radius=5))
            image.paste(background, (0, 0))
        else:
            print(f"Failed to load background from {bgimage}: {response.status_code}")
    # draw them
    draw.text(
        (settings["title"]["x"], settings["title"]["y"]),
        title_text,
        font=settings["title"]["font"],
        fill=settings["title"]["color"],
    )
    draw.text(
        (settings["leader"]["x"], settings["leader"]["y"]),
        leader_text,
        font=settings["leader"]["font"],
        fill=settings["leader"]["color"],
    )
    draw.text(
        (settings["officers"]["x"], settings["officers"]["y"]),
        officers_text,
        font=settings["officers"]["font"],
        fill=settings["officers"]["color"],
    )
    draw.text(
        (settings["newbies"]["x"], settings["newbies"]["y"]),
        members_text,
        font=settings["newbies"]["font"],
        fill=settings["newbies"]["color"],
    )
    draw.text(
        (settings["misc"]["x"], settings["misc"]["y"]),
        misc_text,
        font=settings["misc"]["font"],
        fill=settings["misc"]["color"],
    )
    all_members_pages = []
    current_page = 0
    members_per_page = 10
    members_processed = 0
    left_column = []
    right_column = []
    for i in all_members_text:
        if members_processed % 2 == 0:
            left_column.append(i)
        else:
            right_column.append(i)
        members_processed += 1
        if len(left_column) == members_per_page:
            all_members_pages.append((left_column, right_column))
            left_column = []
            right_column = []
            current_page += 1
    try:
        originaly = settings["all_members"]["y"]
        for i in all_members_pages[page][0]:
            draw.text(
                (
                    settings["all_members"]["x"],
                    settings["all_members"]["y"] + (current_page * 35),
                ),
                i,
                font=settings["all_members"]["font"],
                fill=settings["all_members"]["color"],
            )
            print(f"left: {i}")
            settings["all_members"]["y"] += 25
        settings["all_members"]["y"] = originaly
        for i in all_members_pages[page][1]:
            draw.text(
                (
                    settings["all_members"]["x"] + 400,
                    settings["all_members"]["y"] + (current_page * 35),
                ),
                i,
                font=settings["all_members"]["font"],
                fill=settings["all_members"]["color"],
            )
            print(f"right: {i}")
            settings["all_members"]["y"] += 25
    except IndexError:
        draw.text(
            (30, 700),
            "Page not found!",
            font=settings["all_members"]["font"],
            fill=settings["all_members"]["color"],
        )

    # finalize
    imageBytes = BytesIO()
    image.save(imageBytes, "PNG")
    imageBytes.seek(0)
    return imageBytes


def generate_profile_image(data, badges=None, bgimage=None):
    # Create a blank image
    print(data)
    width, height = 800, 550
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)
    # put in the background image, none if not specified
    if not bgimage:
        bgimage = "https://i.imgur.com/XhbsxXM.jpeg"
    if bgimage:
        headers = {"User-Agent": "this is a bot :3"}
        response = requests.get(bgimage, headers=headers)
        if response.status_code == 200:
            background = Image.open(BytesIO(response.content))
            background = background.resize((width, height))
            background = background.filter(ImageFilter.GaussianBlur(radius=5))
            image.paste(background, (0, 0))
        else:
            print(f"Failed to load background from {bgimage}: {response.status_code}")

    # Define fonts
    title_font = load_font(36)
    text_font = load_font(20)
    # small_font = load_font(18) # unused
    subtext_font = load_font(16)

    # define colors
    # title_color = "white" # unused
    text_color = "white"
    stroke_color = "black"
    bio_color = (30, 30, 30)
    clan_color = hex_to_rgb("7a00ffff")
    cyan_color = hex_to_rgb("01ffffff")

    # Draw title
    title = f"[{data['level']}] {data['name']}#{data['shortId']}"
    print(title)
    draw.text(
        (30, 30),
        title,
        font=title_font,
        fill=0xFFFFFF,
        stroke_width=2,
        stroke_fill=stroke_color,
    )
    clan = data["clan"]
    clantextlength = draw.textlength(f"Clan: {clan}", font=subtext_font)
    draw.text(
        (30, 80),
        f"Clan: {clan}",
        font=subtext_font,
        fill=clan_color if data["clan"] != "Reverie" else cyan_color,
    )
    # Draw bio
    bio = data["bio"]
    # draw a nice rounded box around it and pack it using both x and y space
    if bio:
        bio_x = 50 + clantextlength + 20  # Add some padding between clan and bio
        # draw.rounded_rectangle((bio_x, 80, bio_x + text_length + 20, 80 + 25), fill=0x101010, radius=5)
        draw.text(
            (bio_x + 5, 80),
            f"Bio: {bio}",
            font=text_font,
            fill=bio_color,
            stroke_width=1,
            stroke_fill="white",
        )

    # Draw kills, deaths, wins, total games, losses, wlr, kdr, score per kill, kills per game, deaths per game, score per game
    kills = data["stats"]["kills"]
    deaths = data["stats"]["deaths"]
    wins = data["stats"]["wins"]
    games = data["stats"]["games"]
    score = data["stats"]["scores"]
    losses = games - wins
    wlr = wins / losses if losses != 0 else 0
    kdr = kills / deaths if deaths != 0 else 0
    score_per_kill = score / kills if kills != 0 else 0
    kills_per_game = kills / games if games != 0 else 0
    deaths_per_game = deaths / games if games != 0 else 0
    score_per_game = score / games if games != 0 else 0

    textstuff = [
        f"Kills: {kills:,}",
        f"Deaths: {deaths:,}",
        f"Wins: {wins}",
        f"Losses: {losses}",
        f"WLR: {wlr:.2f}",
        f"KDR: {kdr:.2f}",
        f"Games: {games}",
        f"Score per kill: {score_per_kill:.2f}",
        f"Kills per game: {kills_per_game:.2f}",
        f"Deaths per game: {deaths_per_game:.2f}",
        f"Score per game: {score_per_game:.2f}",
        f"Role: {data['role']}",
        f"Scores: {score:,}",
        f"Created: {dt.datetime.strptime(data['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")}",
        f"Coins: {data['coins']}",
        f"Diamonds: {data['diamonds']}",
    ]
    for i in textstuff:
        # draw a nice rounded box around it and pack it using both x and y space
        box_x = 30 if textstuff.index(i) % 2 == 0 else 340
        box_y = 120 + (textstuff.index(i) // 2) * 35
        text_length = draw.textlength(i, font=text_font)
        draw.rounded_rectangle(
            (box_x, box_y, box_x + text_length + 20, box_y + 25),
            fill=0x222222,
            radius=5,
        )
        draw.text((box_x + 10, box_y), i, font=text_font, fill=text_color)

    # Draw badges
    badge_x = 30
    badge_y = 400
    badge_size = 48
    print(data["role"])
    if data["role"] in ["VERIFIED", "ADMIN", "MODERATOR"]:
        if not badges:
            badges = []
        badges.append("https://i.imgur.com/ZVug92R.png")
    if data["role"] in ["BOT"]:
        if not badges:
            badges = []
        badges.append("https://cdn3.emoji.gg/emojis/68882-bot.png")
    if badges:
        for badge_url in badges:
            try:
                if badge_url.startswith("data:image/"):
                    # Parse the base64 data
                    image_data = badge_url.split(",")[1]
                    badge = Image.open(BytesIO(base64.b64decode(image_data))).resize( # FIXME: linter screams at me will fix later
                        (badge_size, badge_size)
                    )
                else:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    }
                    response = requests.get(badge_url, headers=headers)
                    if response.status_code == 200:
                        badge = Image.open(BytesIO(response.content)).resize(
                            (badge_size, badge_size)
                        )
                    else:
                        print(
                            f"Failed to load badge from {badge_url}: {response.status_code}"
                        )
                        continue
                image.paste(badge, (badge_x, badge_y), badge)
                badge_x += badge_size + 10  # Adjust spacing between badges
            except Exception as e:
                print(f"Failed to load badge from {badge_url}: {e}")
                raise e

    x = 25
    y = 450
    xp_bar_width = 370
    xp_bar_height = 48
    xp_bar_border = 5
    xp_bar_fill_color = (30, 30, 30)
    xp_bar_progress_color = "red"

    print(f"DEBUG: Drawing XP bar for user {data['name']}#{data['shortId']}")
    draw.rectangle((x, y, x + xp_bar_width, y + xp_bar_height), fill=xp_bar_fill_color)
    xpSinceLastLevel = data["xpSinceLastLevel"]
    xpUntilNextLevel = data["xpUntilNextLevel"]
    scale = xpSinceLastLevel / xpUntilNextLevel
    print(f"DEBUG: XP scale: {scale}")
    # draw.rectangle((x + xp_bar_border, y + xp_bar_border, x + xp_bar_width - xp_bar_border, y + xp_bar_height - xp_bar_border), fill=xp_bar_progress_color, outline=xp_bar_progress_outline_color)
    draw.rectangle(
        (
            x + xp_bar_border,
            y + xp_bar_border,
            x + xp_bar_border + (xp_bar_width - 2 * xp_bar_border) * scale,
            y + xp_bar_height - xp_bar_border,
        ),
        fill=xp_bar_progress_color,
    )
    print(f"DEBUG: XP bar drawn")
    draw.text(
        (x + xp_bar_border - 150, y + xp_bar_border + xp_bar_height),
        f"Progress: {int(scale*100)}%, Xp until next: {xpUntilNextLevel - xpSinceLastLevel:,}",
        font=text_font,
        fill=text_color,
        stroke_width=2,
        stroke_fill="black",
    )
    draw.text(
        (410, 464),
        f"Estimated Playtime: {data['estimatedTimePlayed']}",
        font=text_font,
        fill=text_color,
    )

    # Save the image
    return image


# Load font
def load_font(size):
    try:
        return ImageFont.truetype("./cc.ttf", size)
    except IOError:
        return ImageFont.load_default(size)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("0x")
    # split the hex string into 4 parts, RGBA
    r, g, b, a = [hex_color[i : i + 2] for i in range(0, len(hex_color), 2)]
    print(r, g, b, a)
    return tuple(int(x, 16) for x in (r, g, b, a))


class KirkaInfo(commands.Cog):
    class ClanView(discord.ui.View):
        def __init__(self, clan_data, page):
            super().__init__()
            page = page - 1  # account for user friendliness
            if page <= 0:
                page = 0  # ah yes minified python
            self.clan_data = clan_data
            self.clan_members = clan_data["members"]
            self.current_page = page
            self.members_per_page = 20
            self.total_pages = (
                len(self.clan_members) + self.members_per_page - 1
            ) // self.members_per_page
            self.members_split_into_pages = []
            # sort the clan members by score
            self.clan_members = sorted(
                self.clan_members, key=lambda x: x["allScores"], reverse=True
            )
            temp = []
            for i in self.clan_members:
                temp.append(i)
                if len(temp) == self.members_per_page:
                    self.members_split_into_pages.append(temp)
                    temp = []

            self.init_menu()

        def init_menu(self):
            self.clear_items()
            self.add_item(
                discord.ui.Button(
                    label="Previous",
                    style=discord.ButtonStyle.primary,
                    disabled=self.current_page <= 0,
                    custom_id="back",
                )
            )
            self.add_item(
                discord.ui.Button(
                    label="Next",
                    style=discord.ButtonStyle.primary,
                    disabled=self.current_page == self.total_pages,
                    custom_id="next",
                )
            )
            try:
                self.add_item(
                    discord.ui.Select(
                        placeholder="Select a member to display profile",
                        options=[
                            discord.SelectOption(
                                label=f"{member['user']['name']}", value=str(index)
                            )
                            for index, member in enumerate(
                                self.members_split_into_pages[self.current_page]
                            )
                        ],
                        min_values=1,
                        max_values=1,
                        custom_id="member_select",
                        row=1,
                    )
                )
            except IndexError:
                self.add_item(
                    discord.ui.Select(
                        placeholder="Error fetching member list.",
                        options=[],
                        min_values=1,
                        max_values=1,
                        custom_id="member_select",
                        row=1,
                    )
                )

        async def previous_page(self, interaction: discord.Interaction):
            self.current_page -= 1
            self.init_menu()
            imageBytes = generate_clan_image(self.clan_data, self.current_page)
            file = discord.File(imageBytes, filename="clan.png")
            await interaction.response.edit_message(attachments=[])
            await interaction.edit_original_response(
                content=f"Page {self.current_page+1} of {self.total_pages}",
                file=file,
                view=self,
            )

        async def next_page(self, interaction: discord.Interaction):
            self.current_page += 1
            self.init_menu()
            imageBytes = generate_clan_image(self.clan_data, self.current_page)
            file = discord.File(imageBytes, filename="clan.png")
            await interaction.response.edit_message(attachments=[])
            await interaction.edit_original_response(
                content=f"Page {self.current_page+1} of {self.total_pages}",
                file=file,
                view=self,
            )

        async def message_select(self, interaction: discord.Interaction):
            print("DEBUG: Entering message_select method")
            # first we need to get what member was selected
            print(interaction.data)
            selected_member_index = int(dict(interaction.data)["values"][0])
            print(f"DEBUG: Selected member index: {selected_member_index}")
            selected_member = self.members_split_into_pages[self.current_page][
                selected_member_index
            ]
            print(f"DEBUG: Selected member: {selected_member['user']['name']}")
            # then we get the id of the member
            member_id = selected_member["user"]["id"]
            print(f"DEBUG: Member ID: {member_id}")
            # fetch the data
            try:
                member_data = requests.get(
                    f"https://kirka.irrvlo.xyz/_next/data/Qj7Evkvz7SgKQYk1Q4HmZ/users/{member_id}.json"
                ).json()["pageProps"]["userData"]
            except KeyError as e:
                await interaction.respond(
                    "Sorry, could not load user profile. This is a bug!", ephemeral=True
                )
                raise e
            # generate the image
            image = generate_profile_image(member_data)
            imageBytes = BytesIO()
            image.save(imageBytes, "PNG")
            imageBytes.seek(0)
            print("DEBUG: Profile image generated")
            file = discord.File(imageBytes, filename="profile.png")
            print("DEBUG: Discord file created")
            await interaction.response.edit_message(attachments=[])
            await interaction.edit_original_response(content=f"", file=file, view=self)
            print("DEBUG: Message edited")

        # register the callbacks now
        async def interaction_check(self, interaction: discord.Interaction):
            print("DEBUG: Entering interaction_check method")
            if interaction.custom_id == "back":
                await self.previous_page(interaction)
            elif interaction.custom_id == "next":
                await self.next_page(interaction)
            elif interaction.custom_id == "member_select":
                await self.message_select(interaction)
            return True

    def __init__(self, bot):
        print("DEBUG: Initializing KirkaInfo cog")
        self.bot = bot
        self.owners = owners
        self.KirkaAPI = KirkaAPI()
        self.clancommandfucked = False
        self.debug = True

    @commands.command(
        description="Get info about a clan", name="claninfo", aliases=["clan"]
    )
    async def claninfo(self, ctx, *, clan_name: str = "Reverie", page: int = 0):
        if page != 0:
            page += 1
        clan_data = await self.KirkaAPI.getClan(clan_name)
        clan_data = dict(clan_data)

        if not clan_data.get("name", False):
            await ctx.send(f"Clan '{clan_name}' not found.")
            return
        if clan_name == "Staff":
            await ctx.reply(
                f"For some reason staff clan breaks half the code... Why? If you're willing to dive deep, take this: ```{json.dumps(clan_data)}```"
            )
            return

        image = generate_clan_image(clan_data)
        file = discord.File(image, filename="clan.png")
        try:
            await ctx.reply(
                f"Clan {clan_name} info:\nDiscord link: <{clan_data['discordLink'] if clan_data.get('discordLink') else 'None'}>\nDescription: {clan_data['description']}",
                file=file,
                view=self.ClanView(clan_data, page),
            )
        except Exception as e:
            raise e

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Get info about a clan",
        name="clan",
    )
    async def claninfo_slash(
        self, ctx: discord.ApplicationContext, clan_name: str = "Reverie", page: int = 0
    ):
        if page != 0:
            page += 1
        clan_data = await self.KirkaAPI.getClan(clan_name)
        clan_data = dict(clan_data)
        if not clan_data:
            await ctx.respond(f"Clan '{clan_name}' not found.")
            return
        if clan_name == "Staff":
            await ctx.respond(
                f"For some reason staff clan breaks half the code... Why? If you're willing to dive deep, take this: ```{json.dumps(clan_data)}```"
            )
            return
        image = generate_clan_image(clan_data)
        file = discord.File(image, filename="clan.png")
        try:
            await ctx.respond(
                f"Clan {clan_name} info:\nDiscord link: <{clan_data['discordLink'] if clan_data.get('discordLink') else 'None'}>\nDescription: {clan_data['description']}",
                file=file,
                view=self.ClanView(clan_data, page),
            )
        except Exception as e:
            raise e

    @commands.command(
        name="get_stats",
        description="Get stats for a user (Short ID, example is '#B0TMFC')",
        aliases=["profile", "p"],
    )
    async def get_stats(self, ctx, short_id: str = None):
        result = await get_user_stats(short_id, ctx)
        if isinstance(result, str):
            await ctx.send(result)
        else:
            file, message = result
            await ctx.reply(message, file=file)

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Get stats for a user (Short ID, example is '#B0TMFC')",
        name="get_stats",
    )
    async def get_stats_slash(
        self, ctx: discord.ApplicationContext, short_id: str = None
    ):
        await ctx.defer()
        result = await get_user_stats(short_id, ctx)
        if isinstance(result, str):
            await ctx.respond(result)
        else:
            file, message = result
            await ctx.respond(message, file=file)

    async def get_render_core(_, item_name: str):
        try:
            item_name = quote(item_name.lower())
            response = requests.get(
                f"https://kirka.irrvlo.xyz/_next/data/Qj7Evkvz7SgKQYk1Q4HmZ/items/{item_name}.json"
            )
            if response.status_code == 200:
                data = response.json()
                if data["pageProps"]["error"]:
                    return None
                try:
                    item_data = data["pageProps"]["itemData"]
                except:
                    return None
                item_name = item_data["name"]
                item_rarity = item_data["rarity"]
                item_type = item_data["type"]
                item_rarity_color = {
                    "Common": 0x00FF00,
                    "Uncommon": 0x00FF00,
                    "Rare": 0x0000FF,
                    "Epic": 0x800080,
                    "Legendary": 0xFFA500,
                    "Mythical": 0xFF0000,
                    "Unreleased": 0x000000,
                    "Default": 0x8F8F8F,
                    "Glitched": 0x00FFFF,
                }
                item_price_bvl = item_data["price"]
                item_image = item_data["img"]
                item_image = item_image[:62] + quote(item_image[62:])
                owners = item_data["units"].split("/")[1]

                embed = discord.Embed(
                    title=f"{item_name} ({item_rarity})",
                    color=item_rarity_color[item_rarity],
                )
                embed.add_field(name="Type", value=item_type, inline=True)
                embed.add_field(name="Rarity", value=item_rarity, inline=True)
                embed.add_field(
                    name="Image", value=f"[Click here](<{item_image}>)", inline=True
                )
                embed.add_field(name="Price (bvl)", value=item_price_bvl, inline=True)
                embed.add_field(name="Owners", value=owners, inline=True)
                embed.set_image(url=item_image)

                return embed
            else:
                print(
                    f"Debug: API request failed with status code {response.status_code}"
                )
                return None
        except Exception as e:
            print(f"Debug: An error occurred in get_render_core: {str(e)}")
            return None

    @commands.command(
        name="get_render",
        aliases=["r", "show"],
        description="Get the render for an item",
    )
    async def get_render(self, ctx, *, item_name: str):
        embed = await self.get_render_core(item_name)
        if embed:
            await ctx.send(embed=embed)
        else:
            await ctx.send("Failed to fetch item data. Please try again later.")

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Get the render for an item",
        name="get_render",
    )
    async def get_render_slash(self, ctx: discord.ApplicationContext, item_name: str):
        embed = await self.get_render_core(item_name)
        if embed:
            await ctx.respond(embed=embed)
        else:
            await ctx.respond("Failed to fetch item data. Please try again later.")

    async def get_texture_core(_, item_name: str):
        try:
            item_name = quote(item_name.lower())
            response = requests.get(
                f"https://kirka.irrvlo.xyz/_next/data/Qj7Evkvz7SgKQYk1Q4HmZ/items/{item_name}.json"
            )
            if response.status_code == 200:
                data = response.json()
                if data["pageProps"]["error"]:
                    return None
                try:
                    item_data = data["pageProps"]["itemData"]
                except:
                    return None
                item_render = item_data["img"]
                item_texture = item_render.replace("render", "texture")
                imgbytes = requests.get(item_texture).content
                return imgbytes, item_name
            else:
                print(
                    f"Debug: API request failed with status code {response.status_code}"
                )
                return None
        except Exception as e:
            print(f"Debug: An error occurred in get_texture_core: {str(e)}")
            return None

    @commands.command(description="Get the texture of an item.", aliases=["txt"])
    async def get_texture(self, ctx, *, item_name: str):
        result = await self.get_texture_core(item_name)
        if result:
            imgbytes, item_name = result
            file = discord.File(
                io.BytesIO(imgbytes), filename=f"{item_name}_texture.png"
            )
            await ctx.reply(f"{item_name} Texture:", file=file)
        else:
            await ctx.reply("Failed to fetch item texture. Please try again later.")

    @commands.slash_command(
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
        description="Get the texture of an item",
        name="get_texture",
    )
    async def get_texture_slash(self, ctx: discord.ApplicationContext, item_name: str):
        result = await self.get_texture_core(item_name)
        if result:
            imgbytes, item_name = result
            file = discord.File(
                io.BytesIO(imgbytes), filename=f"{item_name}_texture.png"
            )
            await ctx.respond(f"{item_name} Texture:", file=file)
        else:
            await ctx.respond("Failed to fetch item texture. Please try again later.")

    @commands.command(description="Compare a trade.", aliases=["cmp"])
    async def compare_trade(self, ctx, *, trade: str):
        value_lists = [
            {
                "url": "https://opensheet.elk.sh/1tzHjKpu2gYlHoCePjp6bFbKBGvZpwDjiRzT9ZUfNwbY/Alphabetical",
                "info": {
                    "ValueColumn": "Price",
                    "ItemNameColumn": "Skin Name",
                    "Name": "BVL",
                },
            },
            {
                "url": "https://opensheet.elk.sh/1VqX9kwJx0WlHWKCJNGyIQe33APdUSXz0hEFk6x2-3bU/Sorted+View",
                "info": {
                    "ValueColumn": "Base Value",
                    "ItemNameColumn": "Name",
                    "Name": "Yzz",
                },
            },
            {
                "url": "https://opensheet.elk.sh/1a6ZUrMt89EgMgl_HzM7zHG6vaQIs5W9_e4tlIadjBrM/1",
                "info": {
                    "ValueColumn": "Static Value",
                    "ItemNameColumn": "Item",
                    "Name": "rev",
                },
            },
        ]

        message = ""
        analyzer = tradeParser.TradeAnalyzer(value_lists)
        result = analyzer.analyze_trade(trade)
        message += "My totals:\n"
        for value_list_name, total in result["my_totals"].items():
            message += f"{total:,} ({value_list_name})  "
        message += "\nYour totals:\n"
        for value_list_name, total in result["your_totals"].items():
            message += f"{total:,} ({value_list_name})  "
        message += "\nTrade differences:\n"
        for value_list_name, difference in result["trade_differences"].items():
            message += f"{difference:,} ({value_list_name})  "

        await ctx.reply(message)

    @commands.command("clanwar", description="Get the clan war leaderboard")
    @commands.cooldown(1, 5)
    async def clanwar(self, ctx):
        response = requests.get("https://api.kirka.io/api/leaderboard/clanChampionship")
        data = response.json()
        embed = discord.Embed(title="Clan War Leaderboard")
        for i, clan in enumerate(data["results"][:25]):
            embed.add_field(
                name=f"{i+1}. {'Gold' if i<3 else 'Epic' if i<8 else 'Wood'} | {clan['name']}",
                value=f"Members: {clan['membersCount']}, Scores: {clan['scores']:,}",
                inline=True,
            )
        formatted_date = dt.datetime.fromtimestamp(data["remainingTime"]).strftime(
            "%d/%m/%y %H:%M:%S"
        )
        embed.set_footer(text=f"CW ends at {formatted_date}")
        await ctx.reply(embed=embed)

    @commands.command("sololb", description="Get the leaderboard of players")
    async def sololb(self, ctx):
        response = requests.get("https://api.kirka.io/api/leaderboard/solo")
        data = response.json()
        embed = discord.Embed(title="Solo leaderboard")
        for i, player in enumerate(data["results"][:25]):
            embed.add_field(
                name=f"{i+1}. {'Gold' if i<3 else 'Epic' if i<8 else 'Wood'} | {player['name']}",
                value=f"Scores: {player['scores']:,}",
                inline=True,
            )
        await ctx.reply(embed=embed)

    @commands.command(
        "cwrewards",
        description="Get the clan war rewards.",
        aliases=["cwr", "clanwarrewards", "clanwarewards"],
    )
    async def clanwar_rewards(self, ctx):
        await ctx.reply("Click the buttons!", view=self.cw_rewards_view())

    class cw_rewards_view(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.response = requests.get(
                "https://juicepoopooumgood.github.io/Api-guy/Cw/Main/"
            )
            self.data = self.response.json()
            self.buttons = []
            for entry in self.data:
                button = discord.ui.Button(
                    label=entry["Date"],
                    style=discord.ButtonStyle.primary,
                    custom_id=entry["Location"],
                )
                button.callback = self.button_callback
                self.buttons.append(button)
            for button in self.buttons:
                self.add_item(button)

        async def button_callback(self, interaction: discord.Interaction):
            print(interaction.data)
            url = interaction.data["custom_id"]
            response = requests.get(url)
            data = response.json()
            embed = discord.Embed(title="Clan War Rewards")
            for item in data:
                embed.add_field(
                    name=f"{item['Name']} ({item['Rarity']})",
                    value=f"Image: [Click here](<{item['Tinyimg']}>)\nWeapon: {item['Type']}",
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        global cached_prices
        if message.author.bot:
            return
        if message.guild:
            if message.guild.id in [
                1296584026454360174
            ]:  # we do it like this because Message does not have .get() and we dont want attr errors
                return

        item_names = re.findall(r"\[(.*?)]", message.content)
        if not item_names:
            return
        if cached_prices is None:
            cached_prices = {}

        response = []
        prices = []

        operation = None
        if message.content.upper().startswith("SUM"):
            operation = "SUM"
        elif message.content.upper().startswith("AVG"):
            operation = "AVG"

        for item_name in item_names:
            if item_name in cached_prices:
                bvl_price = cached_prices[f"{item_name}|BVL"]
                yzz_price = cached_prices[f"{item_name}|YZZ"]
                rev_price = cached_prices[f"{item_name}|REV"]
            else:
                try:
                    bvl_price = await self.KirkaAPI.pricebvl(item_name)
                    if bvl_price == 0 or isinstance(bvl_price, ValueError):
                        bvl_price = None
                    cached_prices[f"{item_name}|BVL"] = bvl_price
                except Exception:
                    bvl_price = None

                try:
                    yzz_price = await self.KirkaAPI.priceyzzzmtz(item_name)
                    if yzz_price == 0 or isinstance(yzz_price, ValueError):
                        yzz_price = None
                    cached_prices[f"{item_name}|YZZ"] = yzz_price
                except Exception:
                    yzz_price = None

                try:
                    rev_price = await self.KirkaAPI.pricecustom(
                        item_name,
                        "Item",
                        "Static Value",
                        "https://opensheet.elk.sh/1a6ZUrMt89EgMgl_HzM7zHG6vaQIs5W9_e4tlIadjBrM/1",
                    )
                    if rev_price == 0 or isinstance(rev_price, ValueError):
                        rev_price = None
                    cached_prices[f"{item_name}|REV"] = rev_price
                except Exception:
                    rev_price = None

                bvl_formatted = (
                    f"{bvl_price:,.0f}" if bvl_price is not None else "Unknown"
                )
                yzz_formatted = (
                    f"{yzz_price:,.0f}" if yzz_price is not None else "Unknown"
                )
                rev_formatted = (
                    f"{rev_price:,.0f}" if rev_price is not None else "Unknown"
                )

            if (
                bvl_formatted != "Unknown" # V
                or yzz_formatted != "Unknown" # i can ignore these, right?
                or rev_formatted != "Unknown" # ^
            ):
                response.append(
                    f"{item_name} price: {bvl_formatted} (bvl), {yzz_formatted} (yzz), {rev_formatted} (rev)"
                )
                valid_prices = [
                    p for p in [bvl_price, yzz_price, rev_price] if p is not None
                ]
                if valid_prices:
                    prices.append(sum(valid_prices) / len(valid_prices))

        if operation:
            if operation == "SUM":
                result = sum(prices)
                response.append(f"Sum of average prices: {result:,.2f}")
            elif operation == "AVG":
                result = sum(prices) / len(prices) if prices else 0
                response.append(f"Average of average prices: {result:,.2f}")

        if response:
            await message.reply("\n".join(response), mention_author=False)

        if self.debug:
            print(f"Message processed: {message.content}")
            print(f"Item names found: {item_names}")
            print(f"Response: {response}")

    @commands.command(
        name="trades", description="Get trades from lukeskywalk's API"
    )
    async def trades(self, ctx, trade_id: int):
        try:
            response = requests.get("https://kirka.lukeskywalk.com/trades.json")
            data = response.json()
            if response.status_code == 200:
                trades = []
                for trade in data:
                    if trade_id is None or trade["tradeId"] == trade_id:
                        offered = ", ".join(
                            [
                                f"{item['i']} x{item['q']} ({item['r']})"
                                for item in trade["offered"]
                            ]
                        )
                        wanted = ", ".join(
                            [
                                f"{item['i']} x{item['q']} ({item['r']})"
                                for item in trade["wanted"]
                            ]
                        )
                        trades.append(
                            f"Trade ID: {trade['tradeId']}\nUser: {trade['userAndTag']}\nOffered: {offered}\nWanted: {wanted}"
                        )
                if trades:
                    await ctx.reply("\n\n".join(trades))
                else:
                    await ctx.reply("No trades found with the specified ID.")
            else:
                await ctx.reply("Failed to fetch trades. Please try again later.")
        except Exception as e:
            await ctx.reply("An error occurred: " + str(e))

    async def level_rewards_core(self, level):
        response = requests.get(
            "https://opensheet.elk.sh/1g9hNBnFQ37alV93ON2PI42yZwWrprQ9FpuOsugAspKQ/1"
        )
        response.raise_for_status()
        data = response.json()

        if "-" in level:  # Range handling
            try:
                start, end = map(int, level.split("-"))
                if start > end:
                    return (
                        "string",
                        "Invalid range! Start level must be less than or equal to end level.",
                    )
            except ValueError:
                return (
                    "string",
                    "Invalid range format! Use 'start-end' with integers only.",
                )

            total_score = 0
            rewards = []
            if len(range(start, end + 1)) > 25:
                return (
                    "string",
                    "You can only get the range of up to 25 levels at a time!",
                )
            embed = discord.Embed(
                title=f"Level rewards from lvl {start} to {end}:",
                color=discord.Color.random(),
            )
            found_reward = False
            for lvl in range(start, end + 1):
                lvl_str = str(lvl)
                try:
                    level_data = data[int(lvl_str)]
                except IndexError:
                    print(f"Level {lvl} got IndexError")
                    continue
                score_needed = int(level_data["Score needed"])
                total_score += score_needed
                embed.add_field(
                    name=f"Level {lvl}:",
                    value=f"{level_data['Reward']}\nScore needed: {score_needed:,} | Total score needed so far: {total_score:,}",
                    inline=False,
                )
                found_reward = True

            if not found_reward:
                return ("string", "No levels found in the specified range.")
            return ("embed", embed)
        try:
            int(level)
        except ValueError:
            return (
                "string",
                "Invalid level! Must be an integer or a range (e.g., '14-83').",
            )

        embed = discord.Embed(
            title=f"Level rewards for lvl {level}:", color=discord.Color.random()
        )
        try:
            level_data = data[int(level)]
        except IndexError:
            level_data = None
        if not level_data:
            return ("string", "Level does not exist!")

        score_needed = int(level_data["Score needed"])
        reward = level_data["Reward"]
        embed.add_field(
            name="Reward Details",
            value=f"Level {level}: {reward} | Score needed: {score_needed:,}",
            inline=False,
        )
        embed.set_footer(text="Level reward information")
        return ("embed", embed)

    @commands.command(
        "lvlreward",
        aliases=["lvl", "lvr"],
        description="Get the rewards of a level, or a range of levels",
    )
    async def lvlreward_cmmd(self, ctx, level):
        result_type, result_data = await self.level_rewards_core(level)

        if result_type == "string":
            await ctx.send(result_data)
        elif result_type == "embed":
            await ctx.send(embed=result_data)

    @discord.slash_command(
        name="lvlreward",
        description="Get the rewards of a level, or a range of levels",
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
    )
    async def lvlreward_slash(self, ctx, level: str):
        await ctx.defer()
        result_type, result_data = await self.level_rewards_core(level)

        if result_type == "string":
            await ctx.respond(result_data)
        elif result_type == "embed":
            await ctx.respond(embed=result_data)


def setup(bot):
    bot.add_cog(KirkaInfo(bot))
