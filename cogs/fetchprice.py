import discord
from discord.ext import commands
import urllib.request
import json
import datetime as DT
import statistics
from difflib import SequenceMatcher
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import configparser


class FetchPrice(commands.Cog):
    """Cog that deals with all prices related stuffs.

    Commands:
        - prices
            Fetch current market prices from Data Project API.
            Also send plot of 7 days historical prices.
		- quick (part of prices)
			Same as prices command but without plots (faster).

    Functions:
        - item_match(item)
            Find closest matching item name/ID of input item.
            Uses Jaccard distance or difflib.
            Returns first 4 closest match.
        - grabHistory(item)
            Get item's 7 days historical prices for all cities.
            Plots them out to 'plot.png'.
    """

    def __init__(self, client):
        self.client = client

        # Load config.ini and get configs
        configs = configparser.ConfigParser()
        configs.read("./config.ini")

        debugChannel = int(configs["Channels"]["debugChannelID"])
        workChannel = [
            int(ID) for ID in configs["Channels"]["workChannelID"].split(", ")
        ]
        self.debugChannel = client.get_channel(debugChannel)
        self.workChannel = workChannel

        self.onlyWork = configs["General"].getboolean("onlyWork")
        self.debug = configs["General"].getboolean("debug")

        # API URLs
        self.apiURL = "https://www.albion-online-data.com/api/v2/stats/prices/"
        self.locationURL = (
            "?locations=Caerleon,Lymhurst,Martlock,Bridgewatch,FortSterling,Thetford"
        )
        self.iconURL = "https://gameinfo.albiononline.com/api/gameinfo/items/"
        self.historyURL = "https://www.albion-online-data.com/api/v1/stats/charts/"
        self.historyLocationURL = (
            "&locations=Thetford,Martlock,Caerleon,Lymhurst,Bridgewatch,FortSterling"
        )

        # Bot will search items through this list
        # There are also different localization names
        self.itemList = "item_data.json"

    @commands.command(
        aliases=[
            "Prices",
            "price",
            "Price",
            "PRICE",
            "PRICES",
            "quick",
            "Quick",
            "QUICK",
        ]
    )
    async def prices(self, ctx, *, item):
        """Fetch current prices from Data Project API.

        - Usage: <commandPrefix> price <item name>
        - Item name can also be its ID
        - Uses Jaccard edit distance/difflib for item name recognition.
        - Outputs as Discord Embed with thumbnail.
        - Plots 7 days historical prices.
        """

        # Get command (price or quick)
        command = ctx.message.content.split()[1]

        # Debug message
        if self.debug:
            await self.debugChannel.send(f"{ctx.author} -> {command} {item}")

        # Check if in workChannel
        if self.onlyWork:
            if ctx.channel.id not in self.workChannel:
                return

        await ctx.channel.trigger_typing()

        # Jaccard edit distance/difflib for input search
        itemNames, itemIDs = self.item_match(item)

        # Grab prices from full URL
        fullURL = self.apiURL + itemIDs[0] + self.locationURL
        with urllib.request.urlopen(fullURL) as url:
            data = json.loads(url.read().decode())

        # Create Discord embed
        em = discord.Embed(
            title=f"Current Prices for:\n**{itemNames[0]} ({itemIDs[0]})**"
        )

        # Extracting locations' timestamps and minimum sell order prices
        try:
            if data == []:
                raise Exception

            timeStringAll = []
            locationStringAll = []
            sellPriceMinStringAll = []

            for (i, indivData) in enumerate(data):

                # Convert timestamp to datetime format
                # And find how long ago is timestamp in seconds
                timestamp = DT.datetime.strptime(
                    indivData["sell_price_min_date"], "%Y-%m-%dT%H:%M:%S"
                )
                tdelta = DT.datetime.utcnow() - timestamp
                tdelta = DT.timedelta.total_seconds(tdelta)

                if tdelta >= 94608000:
                    timeString = "NIL"
                elif tdelta >= 3600:
                    timeString = str(round(tdelta / 3600, 1)) + " hours ago"
                elif tdelta >= 60:
                    timeString = str(round(tdelta / 60)) + " mins ago"
                else:
                    timeString = str(round(tdelta)) + " sec ago"

                timeStringAll.append(timeString)

                # Put quality beside location
                try:
                    if indivData["quality"] == 0 or indivData["quality"] == 1:
                        locationString = indivData["city"]
                    elif indivData["quality"] == 2:
                        locationString = indivData["city"] + " (Good)"
                    elif indivData["quality"] == 3:
                        locationString = indivData["city"] + " (Oustanding)"
                    elif indivData["quality"] == 4:
                        locationString = indivData["city"] + " (Excellent)"
                    elif indivData["quality"] == 5:
                        locationString = indivData["city"] + " (Masterpiece)"
                # Quality not given for items without quality
                except:
                    locationString = indivData["city"]

                locationStringAll.append(locationString)

                # Getting the minimum sell order prices
                sellPriceMinStringAll.append(indivData["sell_price_min"])

            # Express in embed format
            # Basically just output list as column
            embedLocationString = ""
            embedPriceString = ""
            embedTimeString = ""

            for (i, locationString) in enumerate(locationStringAll):
                embedLocationString += locationString + "\n"
                embedPriceString += str(sellPriceMinStringAll[i]) + "\n"
                embedTimeString += timeStringAll[i] + "\n"

            # Add the fields to Discord embed
            em.add_field(name="Locations", value=embedLocationString, inline=True)
            em.add_field(name="Min Sell Price", value=embedPriceString, inline=True)
            em.add_field(name="Last Updated", value=embedTimeString, inline=True)

        # If data is empty
        except:
            nodataString = "NO DATA"
            em.add_field(
                name=f"\n{nodataString:-^60}\n",
                value="There are no data for this item.",
                inline=True,
            )

        finally:
            # Next 3 closest item matches suggestions
            # Good for people if they don't remember item's name and type wrongly
            em.add_field(
                name="Suggestions:",
                value=f"{itemNames[1]} ({itemIDs[1]})\n{itemNames[2]} ({itemIDs[2]})\n{itemNames[3]} ({itemIDs[3]})",
                inline=False,
            )

            # Adding thumbnail
            # 'LEVEL1@1' itemID is 'LEVEL1' in item icon URL
            # So we remove the last 2 char
            if "@" in itemIDs[0]:
                iconFullURL = self.iconURL + itemIDs[0][:-2]
            else:
                iconFullURL = self.iconURL + itemIDs[0]

            em.set_thumbnail(url=iconFullURL)

            # \u274c is a red X
            em.set_footer(text="React with \u274c to delete this post.")

            try:
                # Skip plotting if command is quick
                if command.lower() == "quick":
                    raise Exception

                # Trigger typing again so that user know its still loading
                await ctx.channel.trigger_typing()

                # Grab past 7 days historical prices and plot them
                self.grabHistory(itemIDs[0], itemNames[0])

                plotFile = discord.File("./plot.png", filename="plot.png")

                # Finally send the embed
                msg = await ctx.send(embed=em, file=plotFile)

            # Just send embed without plot if command is quick
            except:
                msg = await ctx.send(embed=em)

            # Add delete reaction button
            await msg.add_reaction("\u274c")

            if self.debug:
                await self.debugChannel.send(
                    f"{ctx.author} -> {command} {item} | Matched -> {itemNames[0]} ({itemIDs[0]})"
                )

    # Error message of prices
    @prices.error
    async def prices_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify item.")

    def item_match(self, inputWord, option="difflib"):
        """Find closest matching item name and ID of input item.

        - Matches both item ID (UniqueName) and item name (LocalizedNames)
        - Uses Jaccard distance/difflib. (difflib by default)
        - I find difflib to be better.
        - Returns 4 closest match.
        """

        itemNames = []
        itemIDs = []
        jDists = []

        try:
            with open("item_data.json", "r", encoding="utf-8") as inFile:
                data = json.load(inFile)
        except Exception as e:
            print(e)

        # Loop through each item in item_data.json
        # Store distance and item index of each item
        for (i, indivData) in enumerate(data):

            # Calculate distance for item ID (UniqueName)
            try:
                w1 = inputWord.lower()
                w2 = indivData["UniqueName"].lower()

                # Use jaccard or difflib's SequenceMatcher
                if option == "jaccard":
                    # Jaccard distance = 1 - (|w1 ∩ w2|/|w1 ∪ w2|)
                    w1 = set(w1)
                    w2 = set(w2)
                    jDist = 1 - (len(w1.intersection(w2)) / len(w1.union(w2)))

                else:
                    jDist = 1 - SequenceMatcher(None, w1, w2).ratio()

                jDists.append([jDist, i])

            # If item has no 'UniqueName'
            except:
                # Max distance is 1
                jDists.append([1, i])

            # Calculate distance for item name (LocalizedNames)
            try:
                w1 = inputWord.lower()
                w2 = indivData["LocalizedNames"]["EN-US"].lower()

                # Use jaccard or difflib's SequenceMatcher
                if option == "jaccard":
                    # Jaccard distance = 1 - (|w1 ∩ w2|/|w1 ∪ w2|)
                    w1 = set(w1)
                    w2 = set(w2)
                    jDist = 1 - (len(w1.intersection(w2)) / len(w1.union(w2)))

                else:
                    jDist = 1 - SequenceMatcher(None, w1, w2).ratio()

                jDists.append([jDist, i])

            # If item has no 'LocalizedNames'
            except:
                jDists.append([1, i])

        # Sort JDists
        # Closest match has lowest distance
        jDists = sorted(jDists)

        # Get item names and IDs of first 4 closest match
        itemNames = [data[jDist[1]]["LocalizedNames"]["EN-US"] for jDist in jDists[:4]]
        itemIDs = [data[jDist[1]]["UniqueName"] for jDist in jDists[:4]]

        return itemNames, itemIDs

    def grabHistory(self, item, itemName):
        """Grab item's 7 days historical prices for all cities, and plots them.

        - Grabbed from Data Project API.
        - Plots timeseries to 'plot.png'.
        """

        # Outliers makes the plot useless, so we find and remove them
        # This function is not very effective though
        def reject_outliers(data):
            d = [abs(i - statistics.median(data)) for i in data]
            mdev = statistics.median(d)
            s = [i / mdev if mdev else 0 for i in d]
            m = 10
            indices = [i for (i, val) in enumerate(s) if val < m]

            newData = [data[i] for i in indices]

            return newData, indices

        # Find dates of past 7 days
        # historyURL requires dates in %m-%d-%Y format
        today = DT.datetime.utcnow()
        numDays = 7
        dates = [None] * numDays
        for i in range(1, 1 + numDays):
            dates[i - 1] = (today - DT.timedelta(days=i)).strftime("%m-%d-%Y")

        # List will have 6 different indices for 6 different cities
        # The indices corresponds to this ordering of cities (Alphabetical):
        # Bridgewatch, Caerleon, Fort Sterling, Lymhurst, Martlock, Thetford
        prices_minAll = [[], [], [], [], [], []]
        timestampsAll = [[], [], [], [], [], []]

        # Retrieve prices and timestamps of each city from each date
        for date in dates:

            # Raise exception if cannot get prices
            try:
                fullURL = (
                    self.historyURL + item + "?date=" + date + self.historyLocationURL
                )
                with urllib.request.urlopen(fullURL) as url:
                    prices = json.loads(url.read().decode())
            except Exception as e:
                print(e)
                return

            else:
                # Iterates over each city's prices
                # and extend data to their corresponding index
                for price in prices:
                    if price["location"] == "Bridgewatch":
                        prices_minAll[0].extend(price["data"]["prices_min"])
                        timestampsAll[0].extend(price["data"]["timestamps"])
                    elif price["location"] == "Caerleon":
                        prices_minAll[1].extend(price["data"]["prices_min"])
                        timestampsAll[1].extend(price["data"]["timestamps"])
                    elif price["location"] == "Fort Sterling":
                        prices_minAll[2].extend(price["data"]["prices_min"])
                        timestampsAll[2].extend(price["data"]["timestamps"])
                    elif price["location"] == "Lymhurst":
                        prices_minAll[3].extend(price["data"]["prices_min"])
                        timestampsAll[3].extend(price["data"]["timestamps"])
                    elif price["location"] == "Martlock":
                        prices_minAll[4].extend(price["data"]["prices_min"])
                        timestampsAll[4].extend(price["data"]["timestamps"])
                    elif price["location"] == "Thetford":
                        prices_minAll[5].extend(price["data"]["prices_min"])
                        timestampsAll[5].extend(price["data"]["timestamps"])

        # Convert timestamps from epochs to datetime format
        # Timestamp data are 1000 times larger for some reason
        # So they must be divided by 1000 to get the actual epoch
        for (i, timestamps) in enumerate(timestampsAll):
            timestampsAll[i] = [
                DT.datetime.fromtimestamp(timestamp / 1000) for timestamp in timestamps
            ]

        # Reject outliers from prices data as well as their corresponding timestamps
        for (i, prices) in enumerate(prices_minAll):
            try:
                prices_minAll[i], indices = reject_outliers(prices)
                timestampsAll[i] = [timestampsAll[i][j] for j in indices]
            # Pass if prices_minAll = []
            except:
                pass

        # Plot the data
        plt.style.use("seaborn")
        fig = plt.figure(figsize=(10, 5))

        # Plot labels and plot colors
        names = [
            "Bridgewatch",
            "Caerleon",
            "Fort Sterling",
            "Lymhurst",
            "Martlock",
            "Thetford",
        ]
        colors = ["orange", "black", "silver", "green", "blue", "brown"]

        # Settings for date xaxis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m/%d/%Y"))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator())

        # Iterate over all cities and plot each one
        for (i, timestamps) in enumerate(timestampsAll):
            try:
                # Sort data first in ascending timestamps
                x, y = [
                    list(x)
                    for x in zip(
                        *sorted(
                            zip(timestampsAll[i], prices_minAll[i]),
                            key=lambda pair: pair[0],
                        )
                    )
                ]

                plt.plot(x, y, ".-", label=names[i], color=colors[i])
            # Pass if prices_minAll = []
            except:
                pass

        plt.gcf().autofmt_xdate()
        plt.title(f"Historical Minimum Sell Order Prices for {itemName} ({item})")
        plt.xlabel("Dates")
        plt.ylabel("Silvers")
        plt.legend()
        fig.savefig("plot.png")

        return


def setup(client):
    client.add_cog(FetchPrice(client))
