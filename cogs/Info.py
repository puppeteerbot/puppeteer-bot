import discord
from discord.ext import commands
from commondatimport discord
from discord.ext import commands
from commondata import *
import requests


class subDescriptionView(discord.ui.View):
    functions = []
    for subDescription in DiscordBot_subdescriptions.keys():
        exec(
            f"""
@discord.ui.button(label="{subDescription}", style=discord.ButtonStyle.blurple)
async def button_callback_{len(functions)}(self, button, interaction):
    await interaction.response.send_message(DiscordBot_subdescriptions["{subDescription}"])
"""
        )
        functions.append(locals()[f"button_callback_{len(functions)}"])


def hex_to_rgb(hex_color, include_alpha=False):
    hex_color = hex_color.lstrip("0x").lstrip("#")

    if len(hex_color) == 6:  # RGB
        r, g, b = [hex_color[i : i + 2] for i in range(0, 6, 2)]
        a = "ff"  # default alpha to 255 (fully opaque)
    elif len(hex_color) == 8:  # RGBA
        r, g, b, a = [hex_color[i : i + 2] for i in range(0, 8, 2)]
    else:
        raise ValueError(
            "Hex color must be in RGB (6 characters) or RGBA (8 characters) format."
        )

    rgb_values = (int(r, 16), int(g, 16), int(b, 16))
    return rgb_values if not include_alpha else (*rgb_values, int(a, 16))


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx):
        embed = discord.Embed(
            title=DiscordBot_name,
            description=DiscordBot_description,
            color=discord.Color.blue(),
        )
        response = await ctx.send(embed=embed, view=subDescriptionView())

    @commands.command(description="List the rules.", hidden=True)
    async def rules(self, ctx, rule: int = None):
        """Rules info"""
        if ctx.guild.name != "Reverie":
            await ctx.reply(
                "Bot wasn't made for this server, this would just return the wrong rules. See #rules or whatever the channel is for you."
            )
            return
        print(f".{rule}")
        # we already have a list of rules so let's just first download those
        rulescontent = """\
            ```py
1: Common sense
2: No content intended to offend (i.e n-word, yes even soft R)
3: No NSFW content at all
4: No self-advertising without the permission of at least minor staff.
5: No impersonation.
6: No begging for roles.
7: Scamming in any part of kirka is forbidden, and will be met with a ban, length is at discretion of the moderator that bans.
8: No spamming except in ⁠spam
9: No harassing ANY member of this server
10: No walls of text, will be met with a harsher punishment if it also violates rule 8
10.1: Rule 10 does not apply in ⁠spam
11: No brainrot, brainrot is punishable by mute
12: No harassing staff.
13: Do not spam tickets or make tickets for no reason. If you do not include a message in your ticket it will be closed in 30 minutes. Repeated "ticket-ditching" will result in an inability to use tickets.
14: Yes this is an actual rule, if anyone says anything unfunny in a VC it is MANDATORY that everyone must go silent. The silence must last fifteen seconds. No coughing, no breathing, just pure silence. Make them feel bad.
15: No posting media in general. A pic here and there is allowed where relevant, but general is not #media.

Ignorance of rules is NOT an excuse, and no lighter punishments will be added just because you didn't read.

Also please, put your username in this format: [CLANTAG] DISPLAYNAME | #KIRKAID
If you joined from the linked discord in-game on the clan page, and you are in the clan, then you need to open up a ticket and get the role.
This is just to help us keep track of who is who, as requested above with the ID thing.
```
            """
        print(rulescontent)
        if rule is not None:
            # Split the rulescontent into lines and strip whitespace
            rules_lines = [
                line.strip() for line in rulescontent.split("\n") if line.strip()
            ]

            # Remove the code block markers
            rules_lines = rules_lines[1:-1]

            # Iterate through each line
            for line in rules_lines:
                if line.startswith(f"{rule}:"):
                    await ctx.reply(line)
                    return

            await ctx.reply("Rule not found.")
        else:
            # If no specific rule is requested, send all rules
            await ctx.send(rulescontent)

    @commands.slash_command(
        description="Get the link to add the bot",
        name="add_me",
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
    )
    async def add_me(self, ctx):
        await ctx.respond(
            f"Add me to your server with [this link!](https://discord.com/api/oauth2/authorize?client_id=1293863138785103963&permissions=8&integration_type=0&scope=bot+applications.commands)\n\
To install me as a user app, click [Here!](https://discord.com/oauth2/authorize?client_id=1293863138785103963&integration_type=1&scope=applications.commands)"
        )

    @commands.command(
        description="List the developers", name="devs", aliases=["dev", "creators"]
    )
    async def devs_command(self, ctx, dev=None):
        data_url = "https://juicepoopooumgood.github.io/Api-guy/Devs/index.json"
        data = requests.get(data_url).json()
        # data is structured like this: [
        #   {
        #     "User": "Glitchy",
        #     "ID": 1236667927944761396,
        #     "kirkaid": "B0TMFC",
        #     "Added": "Main developer of the bot",
        #     "Role": "Owner/Lead Dev"
        #   },
        devs_table = [
            {
                "Name": "Glitchy",
                "Matches": ["glitch", "glitchy", "err", "500"],
                "URL": "https://juicepoopooumgood.github.io/Api-guy/glitchy.json",
            },
            {
                "Name": "Poopoumgood",
                "Matches": ["ppg", "ppgyt", "poop", "ppug", "ppugyt"],
                "URL": "https://juicepoopooumgood.github.io/Api-guy/1169111190824308768/index.json",
            },
            {
                "Name": "Skywalk",
                "Matches": ["Sky", "Skywalk", "Walker", "skywalker", "Apiguy"],
                "URL": "https://juicepoopooumgood.github.io/Api-guy/Sky/index.json",
            },
        ]
        if dev:
            dev_table_entry = None
            for entry in devs_table:
                if dev.lower() in [match.lower() for match in entry["Matches"]]:
                    dev_table_entry = entry
            if not dev_table_entry:
                await ctx.reply(
                    "Contributor not found. Maybe they dont have a page registered."
                )
                return
            # dev table entry from URL is structured like this:
            #  {
            #     "User": "Glitch(y)",
            #     "ID": 1236667927944761396,
            #     "kirkaid": "B0TMFC",
            #     "Text0": ":D I'm glitchy, glitchy the dev :)",
            #     "img0": "https://yt3.googleusercontent.com/0NqzAGtea9hN3l5reUv2uL2XjOPn_JAG7nTXzsvIRaxBPodZoFFpInAJBN_947OgwXeolJFQfA=s160-c-k-c0x00ffffff-no-rj",
            #     "Descriptiontext": "description"
            # }
            dev_profile = requests.get(dev_table_entry["URL"]).json()
            if dev_profile["Color"] == "random":
                color = discord.Color.random()
            else:
                color = discord.Color.from_rgb(*hex_to_rgb(dev_profile["Color"]))
            embed = discord.Embed(
                color=color,
                title=dev_profile["User"],
            )
            print(dev_profile)
            embed.add_field(name="User:", value=f"<@{dev_profile['ID']}>")
            embed.add_field(name="Kirka ID:  ", value=dev_profile["kirkaid"])
            embed.set_footer(
                text=dev_profile["Descriptiontext"], icon_url=dev_profile["img0"]
            )
            for i in range(10):  # Adjust range if there could be more than 10 entries
                text_key = f"Text{i}"
                title_key = f"Title{i}"

                if text_key in dev_profile:  # Only add if the text key exists
                    field_title = (
                        dev_profile[title_key]
                        if title_key in dev_profile
                        else ("About:" if i == 0 else f"- -{i}")
                    )

                    embed.add_field(
                        name=field_title,
                        value=dev_profile[text_key],
                        inline=False,
                    )
            title_img, title_name = None, None
            if "title_img" in dev_profile:
                title_img = dev_profile["title_img"]
            if "title_name" in dev_profile:
                title_name = dev_profile["title_name"]
            embed.set_author(name=title_name, icon_url=title_img)

            await ctx.send(embed=embed)
            return

        embed = discord.Embed(color=discord.Color.random(), title="Developers")
        for i in data:
            embed.add_field(
                name=f"{i['User']} #{i['kirkaid']}",
                value=f"<@{i['ID']}>\nContribution: {i['Added']}\nRole: {i['Role']}",
            )
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
a import *
import requests


class subDescriptionView(discord.ui.View):
    functions = []
    for subDescription in DiscordBot_subdescriptions.keys():
        exec(
            f"""
@discord.ui.button(label="{subDescription}", style=discord.ButtonStyle.blurple)
async def button_callback_{len(functions)}(self, button, interaction):
    await interaction.response.send_message(DiscordBot_subdescriptions["{subDescription}"])
"""
        )
        functions.append(locals()[f"button_callback_{len(functions)}"])


def hex_to_rgb(hex_color, include_alpha=False):
    hex_color = hex_color.lstrip("0x").lstrip("#")

    if len(hex_color) == 6:  # RGB
        r, g, b = [hex_color[i : i + 2] for i in range(0, 6, 2)]
        a = "ff"  # default alpha to 255 (fully opaque)
    elif len(hex_color) == 8:  # RGBA
        r, g, b, a = [hex_color[i : i + 2] for i in range(0, 8, 2)]
    else:
        raise ValueError(
            "Hex color must be in RGB (6 characters) or RGBA (8 characters) format."
        )

    rgb_values = (int(r, 16), int(g, 16), int(b, 16))
    return rgb_values if not include_alpha else (*rgb_values, int(a, 16))


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx):
        embed = discord.Embed(
            title=DiscordBot_name,
            description=DiscordBot_description,
            color=discord.Color.blue(),
        )
        response = await ctx.send(embed=embed, view=subDescriptionView())

    @commands.command(description="List the rules.", hidden=True)
    async def rules(self, ctx, rule: int = None):
        """Rules info"""
        if ctx.guild.name != "Reverie":
            await ctx.reply(
                "Bot wasn't made for this server, this would just return the wrong rules. See #rules or whatever the channel is for you."
            )
            return
        print(f".{rule}")
        # we already have a list of rules so let's just first download those
        rulescontent = """\
            ```py
1: Common sense
2: No content intended to offend (i.e n-word, yes even soft R)
3: No NSFW content at all
4: No self-advertising without the permission of at least minor staff.
5: No impersonation.
6: No begging for roles.
7: Scamming in any part of kirka is forbidden, and will be met with a ban, length is at discretion of the moderator that bans.
8: No spamming except in ⁠spam
9: No harassing ANY member of this server
10: No walls of text, will be met with a harsher punishment if it also violates rule 8
10.1: Rule 10 does not apply in ⁠spam
11: No brainrot, brainrot is punishable by mute
12: No harassing staff.
13: Do not spam tickets or make tickets for no reason. If you do not include a message in your ticket it will be closed in 30 minutes. Repeated "ticket-ditching" will result in an inability to use tickets.
14: Yes this is an actual rule, if anyone says anything unfunny in a VC it is MANDATORY that everyone must go silent. The silence must last fifteen seconds. No coughing, no breathing, just pure silence. Make them feel bad.
15: No posting media in general. A pic here and there is allowed where relevant, but general is not #media.

Ignorance of rules is NOT an excuse, and no lighter punishments will be added just because you didn't read.

Also please, put your username in this format: [CLANTAG] DISPLAYNAME | #KIRKAID
If you joined from the linked discord in-game on the clan page, and you are in the clan, then you need to open up a ticket and get the role.
This is just to help us keep track of who is who, as requested above with the ID thing.
```
            """
        print(rulescontent)
        if rule is not None:
            # Split the rulescontent into lines and strip whitespace
            rules_lines = [
                line.strip() for line in rulescontent.split("\n") if line.strip()
            ]

            # Remove the code block markers
            rules_lines = rules_lines[1:-1]

            # Iterate through each line
            for line in rules_lines:
                if line.startswith(f"{rule}:"):
                    await ctx.reply(line)
                    return

            await ctx.reply("Rule not found.")
        else:
            # If no specific rule is requested, send all rules
            await ctx.send(rulescontent)

    @commands.slash_command(
        description="Get the link to add the bot",
        name="add_me",
        integration_types={
            discord.IntegrationType.user_install,
            discord.IntegrationType.guild_install,
        },
    )
    async def add_me(self, ctx):
        await ctx.respond(
            f"Add me to your server with [this link!](https://discord.com/api/oauth2/authorize?client_id=1293863138785103963&permissions=8&integration_type=0&scope=bot+applications.commands)\n\
To install me as a user app, click [Here!](https://discord.com/oauth2/authorize?client_id=1293863138785103963&integration_type=1&scope=applications.commands)"
        )

    @commands.command(
        description="List the developers", name="devs", aliases=["dev", "creators"]
    )
    async def devs_command(self, ctx, dev=None):
        data_url = "https://juicepoopooumgood.github.io/Api-guy/Devs/index.json"
        data = requests.get(data_url).json()
        # data is structured like this: [
        #   {
        #     "User": "Glitchy",
        #     "ID": 1236667927944761396,
        #     "kirkaid": "B0TMFC",
        #     "Added": "Main developer of the bot",
        #     "Role": "Owner/Lead Dev"
        #   },
        devs_table = [
            {
                "Name": "Glitchy",
                "Matches": ["glitch", "glitchy", "err", "500"],
                "URL": "https://juicepoopooumgood.github.io/Api-guy/glitchy.json",
            },
            {
                "Name": "Poopoumgood",
                "Matches": ["ppg", "ppgyt", "poop", "ppug", "ppugyt"],
                "URL": "https://juicepoopooumgood.github.io/Api-guy/1169111190824308768/index.json",
            },
            {
                "Name": "Skywalk",
                "Matches": ["Sky", "Skywalk", "Walker", "skywalker", "Apiguy"],
                "URL": "https://juicepoopooumgood.github.io/Api-guy/Sky/index.json",
            },
        ]
        if dev:
            dev_table_entry = None
            for entry in devs_table:
                if dev.lower() in [match.lower() for match in entry["Matches"]]:
                    dev_table_entry = entry
            if not dev_table_entry:
                await ctx.reply(
                    "Contributor not found. Maybe they dont have a page registered."
                )
                return
            # dev table entry from URL is structured like this:
            #  {
            #     "User": "Glitch(y)",
            #     "ID": 1236667927944761396,
            #     "kirkaid": "B0TMFC",
            #     "Text0": ":D I'm glitchy, glitchy the dev :)",
            #     "img0": "https://yt3.googleusercontent.com/0NqzAGtea9hN3l5reUv2uL2XjOPn_JAG7nTXzsvIRaxBPodZoFFpInAJBN_947OgwXeolJFQfA=s160-c-k-c0x00ffffff-no-rj",
            #     "Descriptiontext": "description"
            # }
            dev_profile = requests.get(dev_table_entry["URL"]).json()
            if dev_profile["Color"] == "random":
                color = discord.Color.random()
            else:
                color = discord.Color.from_rgb(*hex_to_rgb(dev_profile["Color"]))
            embed = discord.Embed(
                color=color,
                title=dev_profile["User"],
            )
            print(dev_profile)
            embed.add_field(name="User:", value=f"<@{dev_profile['ID']}>")
            embed.add_field(name="Kirka ID:  ", value=dev_profile["kirkaid"])
            embed.set_footer(
                text=dev_profile["Descriptiontext"], icon_url=dev_profile["img0"]
            )
            for i in range(10):  # Adjust range if there could be more than 10 entries
                text_key = f"Text{i}"
                title_key = f"Title{i}"

                if text_key in dev_profile:  # Only add if the text key exists
                    field_title = (
                        dev_profile[title_key]
                        if title_key in dev_profile
                        else ("About:" if i == 0 else f"- -{i}")
                    )

                    embed.add_field(
                        name=field_title,
                        value=dev_profile[text_key],
                        inline=False,
                    )
            title_img, title_name = None, None
            if "title_img" in dev_profile:
                title_img = dev_profile["title_img"]
            if "title_name" in dev_profile:
                title_name = dev_profile["title_name"]
            embed.set_author(name=title_name, icon_url=title_img)

            await ctx.send(embed=embed)
            return

        embed = discord.Embed(color=discord.Color.random(), title="Developers")
        for i in data:
            embed.add_field(
                name=f"{i['User']} #{i['kirkaid']}",
                value=f"<@{i['ID']}>\nContribution: {i['Added']}\nRole: {i['Role']}",
            )
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Info(bot))
