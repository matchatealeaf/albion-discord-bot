import discord
from discord.ext import commands
import urllib.request
import json
import datetime as DT
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import configparser
import os


class FetchGold(commands.Cog):
    """Cog that deals with all gold prices related stuffs.

    Commands:
        - gold
            Fetch and plot gold prices.
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
        self.goldURL = "https://www.albion-online-data.com/api/v2/stats/gold?date="

    @commands.command()
    async def gold(self, ctx, *, days):

        # Debug message
        if self.debug:
            await self.debugChannel.send(f"{ctx.message.content}")

        # Check if in workChannel
        if self.onlyWork:
            if ctx.channel.id not in self.workChannel:
                return

        await ctx.channel.trigger_typing()

        # Check if input is number
        try:
            numDays = int(days)
        except:
            await ctx.send("Please enter a single number.")


        # Get date of past numDays
        today = DT.datetime.utcnow()
        date = (today - DT.timedelta(days=numDays)).strftime("%m-%d-%Y")
        fullURL = self.goldURL + date

        with urllib.request.urlopen(fullURL) as url:
            data = json.loads(url.read().decode())

        # Create Discord embed
        em = discord.Embed(
            title=":moneybag: Gold Prices for the Past 6 Hours :moneybag:",
            colour=discord.Colour.gold(),
        )

        # Extracting latest gold prices and timestamps
        try:
            if data == []:
                raise Exception

            # Get data in a list
            goldPrices = []
            timeStamps = []
            for (i, price) in enumerate(data):
                goldPrices.append(price["price"])
                timeStamp = DT.datetime.strptime(
                    price["timestamp"], "%Y-%m-%dT%H:%M:%S"
                )
                timeStamps.append(timeStamp)

            # Format data for Discord embed for past 6 hours data
            embedGoldPriceString = ""
            embedTimestampString = ""

            for i in range(1, 7):
                embedGoldPriceString += format(goldPrices[-i], ',d') + "\n"
                embedTimestampString += str(timeStamps[-i]) + "\n"

            # Add the fields to Discord embed
            em.add_field(name="Gold Prices", value=embedGoldPriceString, inline=True)
            em.add_field(name="Time", value=embedTimestampString, inline=True)

        # If data is empty
        except:
            nodataString = "NO DATA"
            em.add_field(
                name=f"\n{nodataString:-^60}\n",
                value="There are no gold data.",
                inline=True,
            )

        finally:
            # Plot the data
            plt.style.use("seaborn")
            plt.figure(figsize=(9, 5))

            # Settings for date xaxis
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m/%d/%Y"))
            plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())

            plt.plot(timeStamps, goldPrices, ".-", color="goldenrod")

            plt.gcf().autofmt_xdate()
            plt.title(f"Past {numDays} Days Gold Prices")
            plt.xlabel("Dates")
            plt.ylabel("Prices")
            plt.savefig("goldplot.png", bbox_inches="tight")
            plt.close("all")

            # \u274c is a red X
            em.set_footer(text="React with \u274c to delete this post.")
            plotFile = discord.File("./goldplot.png", filename="goldplot.png")

            msg = await ctx.send(embed=em, file=plotFile)

            # Add delete reaction button
            await msg.add_reaction("\u274c")

            if self.debug:
                await self.debugChannel.send(
                    f"{ctx.message.content} | Gold Matched"
                )

    # Error message of gold
    @gold.error
    async def gold_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify number of days to plot.")


def setup(client):
    client.add_cog(FetchGold(client))
