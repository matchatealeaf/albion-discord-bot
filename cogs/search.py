import discord
from discord.ext import commands
import urllib.request
import json
import datetime as DT
import configparser
import os


class Search(commands.Cog):
    """Cog that deals with official API database.

    API Databases: Player, Guild

    Commands:
        - search
            Search and returns player/guild/item details.
			Options: player, guild
            Item search is not implemented yet.
            Probably can list recipes.
    """

    def __init__(self, client):
        self.client = client

        # Load config.ini and get configs
        currentPath = os.path.dirname(os.path.realpath(__file__))
        configs = configparser.ConfigParser()
        configs.read(os.path.dirname(currentPath) + "/config.ini")

        debugChannel = int(configs["Channels"]["debugChannelID"])
        workChannel = [
            int(ID) for ID in configs["Channels"]["workChannelID"].split(", ")
        ]
        self.debugChannel = client.get_channel(debugChannel)
        self.workChannel = workChannel

        self.onlyWork = configs["General"].getboolean("onlyWork")
        self.debug = configs["General"].getboolean("debug")

        # API URLs
        self.allianceURL = (
            "https://gameinfo.albiononline.com/api/gameinfo/alliances/"  # + ID
        )
        self.guildURL = (
            "https://gameinfo.albiononline.com/api/gameinfo/guilds/"  # + ID + /members
        )
        self.playerURL = (
            "https://gameinfo.albiononline.com/api/gameinfo/players/"  # + ID
        )
        self.searchURL = (
            "https://gameinfo.albiononline.com/api/gameinfo/search?q="  # + name
        )

        # Item search is not implemented
        # API can provide recipe
        self.itemURL = "https://gameinfo.albiononline.com/api/gameinfo/items/"  # + item name + /data

    @commands.command()
    async def search(self, ctx, option, *, name):
        """Search and retrieve details for players and guilds."""

        # Debug message
        if self.debug:
            await self.debugChannel.send(f"{ctx.message.content}")

        # Check if in workChannel
        if self.onlyWork:
            if ctx.channel.id not in self.workChannel:
                return

        await ctx.channel.trigger_typing()

        # URL spaces are replaced with '%20'
        name = name.replace(" ", "%20")

        # Search for player/guild ID using search API
        fullURL = self.searchURL + name
        with urllib.request.urlopen(fullURL) as url:
            data = json.loads(url.read().decode())

        try:
            # Player
            if option.lower() == "player" or option.lower() == "players":

                # Get from player API using player's ID
                fullURL = self.playerURL + data["players"][0]["Id"]
                with urllib.request.urlopen(fullURL) as url:
                    data = json.loads(url.read().decode())

                # Get player details
                name = data["Name"]
                guild = data["GuildName"]
                alliance = data["AllianceName"]
                pve = data["LifetimeStatistics"]["PvE"]["Total"]
                pvp = data["KillFame"]
                gathering = data["LifetimeStatistics"]["Gathering"]["All"]["Total"]
                fiber = data["LifetimeStatistics"]["Gathering"]["Fiber"]["Total"]
                hide = data["LifetimeStatistics"]["Gathering"]["Hide"]["Total"]
                ore = data["LifetimeStatistics"]["Gathering"]["Ore"]["Total"]
                rock = data["LifetimeStatistics"]["Gathering"]["Rock"]["Total"]
                wood = data["LifetimeStatistics"]["Gathering"]["Wood"]["Total"]
                crafting = data["LifetimeStatistics"]["Crafting"]["Total"]
                totalFame = pve + pvp + gathering + crafting

                timestamp = data["LifetimeStatistics"]["Timestamp"]
                timestamp2 = DT.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                timestamp2 = timestamp2.strftime("%I:%M%p UTC %d %b %y")

                # Change empty string to None
                # Discord embed doesn't print empty string
                if alliance == "":
                    alliance = None
                if guild == "":
                    guild = None

                # Create Discord embed
                em = discord.Embed(title=f":crossed_swords:**{name}**:crossed_swords:")

                # First row
                em.add_field(name="Guild", value=str(guild), inline=True)
                em.add_field(name="Alliance", value=str(alliance), inline=True)

                # Second row
                em.add_field(name="Total Fame", value=f"{totalFame:,}", inline=False)

                # Third row
                em.add_field(name="PvE Fame", value=f"{pve:,}", inline=True)
                em.add_field(name="PvP Fame", value=f"{pvp:,}", inline=True)
                # Extra empty column
                em.add_field(name="\u200b", value="\u200b", inline=True)

                # Fourth row
                em.add_field(name="Gathering Fame", value=f"{gathering:,}", inline=True)
                em.add_field(name="Crafting Fame", value=f"{crafting:,}", inline=True)
                em.add_field(name="\u200b", value="\u200b", inline=True)

                # Fifth row
                em.add_field(
                    name="Gathering Resources",
                    value="Fiber\nHide\nOre\nRock\nWood",
                    inline=True,
                )
                em.add_field(
                    name="Fame",
                    value=f"{fiber:,}\n{hide:,}\n{ore:,}\n{rock:,}\n{wood:,}",
                    inline=True,
                )
                em.add_field(name="\u200b", value="\u200b", inline=True)

                # Sixth row
                em.add_field(name="Last Updated On:", value=timestamp2, inline=False)

                em.set_footer(text="React with \u274c to delete this post.")

                msg = await ctx.send(embed=em)
                await msg.add_reaction("\u274c")  # Delete reaction button

                # Debug message
                if self.debug:
                    await self.debugChannel.send(
                        f"{ctx.message.content} | Matched -> {name}"
                    )

            # Guild
            elif option.lower() == "guild" or option.lower() == "guilds":

                # Get from guild API using guild's ID
                guildID = data["guilds"][0]["Id"]
                fullURL = self.guildURL + guildID
                with urllib.request.urlopen(fullURL) as url:
                    data = json.loads(url.read().decode())

                # Get guild details
                guild = data["Name"]
                allianceID = data["AllianceId"]
                founder = data["FounderName"]
                foundedOn = data["Founded"]
                foundedOn = DT.datetime.strptime(foundedOn, "%Y-%m-%dT%H:%M:%S.%fZ")
                foundedOn = foundedOn.strftime("%d %b %y")
                pvp = data["killFame"]
                memberCount = data["MemberCount"]

                # Set alliance based on allianceID
                # If allianceID exists, set alliance as alliance tag
                if allianceID == "" or allianceID == None:
                    alliance = None
                else:
                    fullURL = self.allianceURL + allianceID
                    with urllib.request.urlopen(fullURL) as url:
                        data = json.loads(url.read().decode())
                    alliance = data["AllianceTag"]

                # Get guild members list
                fullURL = self.guildURL + guildID + "/members"
                with urllib.request.urlopen(fullURL) as url:
                    data = json.loads(url.read().decode())

                # Get guild fame details
                members = []
                fames = []
                pvpFames = 0
                pveFames = 0
                gatheringFames = 0
                craftingFames = 0
                for (i, member) in enumerate(data):
                    members.append(member["Name"])
                    pvpFame = member["KillFame"]
                    pveFame = member["LifetimeStatistics"]["PvE"]["Total"]
                    gatheringFame = member["LifetimeStatistics"]["Gathering"]["All"][
                        "Total"
                    ]
                    craftingFame = member["LifetimeStatistics"]["Crafting"]["Total"]

                    # Each member's fame
                    fames.append(pvpFame + pveFame + gatheringFame + craftingFame)

                    # Guild total individual fames (sum of member's fame)
                    pvpFames += pvpFame
                    pveFames += pveFame
                    gatheringFames += gatheringFame
                    craftingFames += craftingFame

                totalFame = sum(fames)  # Guild total overall fames

                # Sort members based on descending fame
                sortedMembers = [
                    x for _, x in sorted(zip(fames, members), reverse=True)
                ]
                sortedFames = sorted(fames, reverse=True)

                # Display only 10 members max
                if len(sortedMembers) > 10:
                    membersLength = 10
                else:
                    membersLength = len(sortedMembers)

                # Put sorted members and fames in column format for Discord embed
                memberString = ""
                fameString = ""
                for i in range(membersLength):
                    memberString += f"{sortedMembers[i]}\n"
                    fameString += f"{sortedFames[i]:,}\n"

                # Create Discord embed
                em = discord.Embed(title=f":crossed_swords:**{guild}**:crossed_swords:")

                # First row
                em.add_field(name="Guild Master", value=founder, inline=True)
                em.add_field(name="Alliance", value=str(alliance), inline=True)
                em.add_field(name="Founded On", value=foundedOn, inline=True)

                # Second row
                em.add_field(name="Total Fame", value=f"{totalFame:,}", inline=True)
                em.add_field(name="Members", value=memberCount, inline=True)
                em.add_field(name="\u200b", value="\u200b", inline=True)

                # Third row
                em.add_field(name="PvE Fame", value=f"{pveFames:,}", inline=True)
                em.add_field(name="PvP Fame", value=f"{pvpFames:,}", inline=True)
                em.add_field(name="\u200b", value="\u200b", inline=True)

                # Fourth row
                em.add_field(
                    name="Gathering Fame", value=f"{gatheringFames:,}", inline=True,
                )
                em.add_field(
                    name="Crafting Fame", value=f"{craftingFames:,}", inline=True,
                )
                em.add_field(name="\u200b", value="\u200b", inline=True)

                # Fifth row
                em.add_field(
                    name=f"Top {membersLength} Members",
                    value=memberString,
                    inline=True,
                )
                em.add_field(name="Fame", value=fameString, inline=True)

                em.set_footer(text="React with \u274c to delete this post.")

                msg = await ctx.send(embed=em)
                await msg.add_reaction("\u274c")  # Delete reaction button

                # Debug message
                if self.debug:
                    await self.debugChannel.send(
                        f"{ctx.message.content} | Matched -> {guild}"
                    )

            else:
                await ctx.send(
                    f"Please specify a valid option.\nUsage: `search <option> <name>`\nOptions: `player` or `guild`."
                )

                # Debug message
                if self.debug:
                    await self.debugChannel.send(
                        f"{ctx.message.content} | Invalid option."
                    )

        except:
            await ctx.send(f"{option} {name} not found.")

            # Debug message
            if self.debug:
                await self.debugChannel.send(f"{ctx.message.content} | Not found.")

    # Error message of search
    @search.error
    async def search_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f"Please specify a valid option.\nUsage: `search <option> <name>`\nOptions: `player` or `guild`."
            )


def setup(client):
    client.add_cog(Search(client))
