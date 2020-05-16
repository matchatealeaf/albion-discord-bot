import discord
from discord.ext import commands, tasks
import pandas as pd
import datetime as DT
import urllib.request
import json
import pygsheets
import statistics


class Sheets(commands.Cog):
    """Cog that deals with all thing related to Google Sheets.

    Commands:
        - buyorder
            Calls sheetsFetch('buyorder') and send returned Discord embed.
        - sellorder
            Calls sheetsFetch('sellorder') and send returned Discord embed.
        - updateprices
            Update Google Sheets with weekly average prices.
		- refreshboard
			Restart the refresh task.

    Tasks:
        - refresh
            Refreshes buyorder and sellorder messages.
            Done by recalling sheetsFetch and editing message.

    Functions:
        - sheetsFetch(option)
            option: 'buyorder', 'sellorder'
            Fetch buy/sell orders Google Sheet CSV with pandas
            Returns embed with columns:
                Item Name (Item ID)
                Price Remaining/Quantity
    """

    def __init__(self, client):
        self.client = client

        # Set debug and market channel here
        self.debugChannel = client.get_channel(12345678)
        self.marketChannel = client.get_channel(12345678)

        self.adminUsers = ["username#1234"]

        # Spreadsheet URLs
        self.marketURL = "https://docs.google.com/spreadsheets/d/..."
        self.buyorderURL = (
            "https://docs.google.com/spreadsheets/d/.../export?format=csv&id=..."
        )
        self.sellorderURL = (
            "https://docs.google.com/spreadsheets/d/.../export?format=csv&id=..."
        )

        # API URL
        self.apiURL = "https://www.albion-online-data.com/api/v1/stats/charts/"

        # Spreadsheets
        self.spreadsheet = "The Pangolin Trading Company Buy-Order Reference Sheet"
        self.worksheet = "Guild Buy Orders"

        # The auth file that allows bot to edit google sheet (refer to google sheet's API)
        self.serviceFile = "editor_servicefile.json"

        # Start refresh task
        self.refresh.start()

    @commands.command()
    async def buyorder(self, ctx):
        """Retrieve buy orders details from Google Sheets into a Discord embed."""

        # Debug message
        await self.debugChannel.send(f"{ctx.author} -> buyorder")
        if str(ctx.author) not in self.adminUsers:
            return
        await ctx.channel.trigger_typing()

        # Call sheetsFetch and send embed
        em = self.sheetsFetch("buyorder")
        msg = await ctx.send(embed=em)
        await msg.add_reaction("\u274c")  # Delete reaction button

        # Only add refresh 'flag' if in self.marketChannel channel
        if ctx.channel == self.marketChannel:
            await msg.add_reaction("\U0001f504")

    @commands.command()
    async def sellorder(self, ctx):
        """Retreive sell orders details from Google Sheets into a Discord embed."""

        # Debug message
        await self.debugChannel.send(f"{ctx.author} -> sellorder")
        if str(ctx.author) not in self.adminUsers:
            return
        await ctx.channel.trigger_typing()

        # Call sheetsFetch and send embed
        em = self.sheetsFetch("sellorder")
        msg = await ctx.send(embed=em)
        await msg.add_reaction("\u274c")  # Delete reaction button

        # Only add refresh 'flag' if in self.marketChannel channel
        if ctx.channel == self.marketChannel:
            await msg.add_reaction("\U0001f504")

    @commands.command(aliases=["Updateprices", "UpdatePrices"])
    async def updateprices(self, ctx):
        """Update Google Sheets with weekly average prices.

        - Average of all 5 cities except Caerleon and Black Market.
        - Reject outliers.
        - Only self.adminUsers can run this command.
        """

        # Debug message
        await self.debugChannel.send(f"{ctx.author} -> updateprices")
        if str(ctx.author) not in self.adminUsers:
            return

        def reject_outliers(data):
            d = [abs(i - statistics.median(data)) for i in data]
            mdev = statistics.median(d)
            s = [i / mdev if mdev else 0 for i in d]
            m = 10
            indices = [i for (i, val) in enumerate(s) if val < m]

            newData = [data[i] for i in indices]
            return newData, indices

        await ctx.send("Updating weekly average prices. This might take awhile.")

        # Connect to Google Sheets
        gc = pygsheets.authorize(service_account_file=self.serviceFile)
        sh = gc.open(self.spreadsheet)
        wks = sh.worksheet_by_title(self.worksheet)

        # Get list of item IDs from Google Sheets and get their _id from MongoDB
        itemIDs = wks.get_values("A4", "A196")

        # Get dates of past 7 days
        now = DT.datetime.utcnow()
        dates = [None] * 7
        for i in range(1, 8):
            dates[i - 1] = (now - DT.timedelta(days=i)).strftime("%m-%d-%Y")

        avgPrices = []
        # Iterate over all items
        for (i, itemID) in enumerate(itemIDs):

            itemPrices = []
            # Iterate over all 7 days
            for date in dates:

                # Retrieve the prices of each day for each item
                try:
                    fullURL = (
                        self.apiURL
                        + itemID[0]
                        + "?date="
                        + date
                        + "&locations=Thetford,Martlock,Lymhurst,Bridgewatch,FortSterling"
                    )
                    with urllib.request.urlopen(fullURL) as url:
                        prices = json.loads(url.read().decode())

                    for price in prices:
                        # Do not include Caerleon
                        if price["location"] != "Caerleon":
                            itemPrices.extend(price["data"]["prices_min"])
                # Pass if no data on that day
                except:
                    pass

            try:
                # Reject outliers
                itemPrices, indices = reject_outliers(itemPrices)

                # Find average and append it to avgPrices
                # Each element in avgPrices need to be in a list (Google Sheets requirement)
                average = int(statistics.mean(itemPrices))
                avgPrices.append([average])

            # If itemPrices is []
            except:
                avgPrices.append([0])

        # Send avgPrices to Google Sheets
        wks.update_values(crange="C4:C196", values=avgPrices)

        await ctx.send("Weekly prices updated.")
        await self.debugChannel.send("Weekly prices updated.")

    @tasks.loop(seconds=900)
    async def refresh(self):
        """Refresh buyorder and sellorder messages.

        - Only refreshes if messages are in the self.marketChannel channel.
        - Only refreshes if message has \U0001f504 reaction by the bot.
        - Scans through self.marketChannel history to find the messages.
        - Refreshes by recalling sheetsFetch and edit message.
        """

        messages = await self.marketChannel.history(limit=50).flatten()
        for message in messages:
            # Use try as some messages does not have reaction
            try:
                for reaction in message.reactions:
                    # If reaction has '\U0001f504' reaction by the bot
                    if reaction.emoji == "\U0001f504" and reaction.me:

                        # If message is buy order
                        if "BUY ORDERS" in message.embeds[0].title:
                            em = self.sheetsFetch("buyorder")
                            await message.edit(embed=em)

                        # If message is sell order
                        elif "SELL ORDERS" in message.embeds[0].title:
                            em = self.sheetsFetch("sellorder")
                            await message.edit(embed=em)
            except Exception as e:
                if e[0:2] != "400":
                    await self.debugChannel.send(e)

    @commands.command(aliases=["RefreshBoard", "Refreshboard"])
    async def refreshboard(self, ctx):
        """Restart self.refresh tasks.

        - Only self.adminUsers can run this command.
        """

        # Debug message
        await self.debugChannel.send(f"{ctx.author} -> refresh")
        if str(ctx.author) not in self.adminUsers:
            return

        else:
            self.refresh.restart()
            await self.debugChannel.send("Market blackboard refreshed.")

    def sheetsFetch(self, option):
        """Returns buy/sell orders Google Sheets as Discord embed.

        - Returns embed with columns:
            Item Name (Item ID)
            Price
            Remaining/Quantity
        - For buy orders, only return rows with 'Remaining' > 0.
        """

        # 'buyorder' and 'sellorder' options
        if option == "buyorder":
            URL = self.buyorderURL
            title = (
                "Pangolin Guild Market            :moneybag: **BUY ORDERS** :moneybag:"
            )
            quantity = "Remaining"

        elif option == "sellorder":
            URL = self.sellorderURL
            title = (
                "Pangolin Guild Market            :moneybag: **SELL ORDERS** :moneybag:"
            )
            quantity = "Quantity"

        # Read CSV with pandas
        df = pd.read_csv(URL, header=2)

        # Drop 0 Remaining and nan values
        if option == "buyorder":
            df = df[df["Remaining"] > 0]
            color = 0x3194FF
            footer = pd.read_csv(URL).iloc[0, 1]
        elif option == "sellorder":
            color = 0xF05A57
            footer = pd.read_csv(URL).iloc[0, 0]

        # Discord embed
        em = discord.Embed(title=title, description=self.marketURL, colour=color)

        # Tier and enchantment names to remove
        tierNames = [
            "Beginner's",
            "Novice's",
            "Journeyman's",
            "Adept's",
            "Expert's",
            "Master's",
            "Grandmaster's",
            "Elder's",
            "Beginner",
            "Novice",
            "Journeyman",
            "Adept",
            "Expert",
            "Master",
            "Grandmaster",
            "Elder",
            "Stonestream",
            "Rushwater",
            "Thunderfall",
        ]
        enchantNames = ["Uncommon", "Rare", "Exceptional"]

        # Enchantment labels at end of item ID to know if item has enchantment
        enchantNumbers = ["@1", "@2", "@3"]

        # Express data in columns for Discord embed
        embedItemString = ""
        embedPriceString = ""
        embedQuantityString = ""
        for (i, row) in df.iterrows():

            tier = df["Item ID"][i][:2]
            name = df["Item Name"][i]

            # Only sell order df has quality
            try:
                # Show quality as (G), (O), (E), or (M) if quality not Normal
                if df["Quality"][i] in [
                    "Good",
                    "Outstanding",
                    "Excellent",
                    "Masterpiece",
                ]:
                    quality = f"({df['Quality'][i][0]})"
                else:
                    quality = ""
            except:
                quality = ""

            # Remove tier names and enchantment names if exist
            if name.split()[0] in tierNames or name.split()[0] in enchantNames:
                name = " ".join(name.split()[1:])

            # Add enchantment label to tier if exist
            if df["Item ID"][i][-2:] in enchantNumbers:
                tier += "." + df["Item ID"][i][-1]

            # Only add tier in front if it is a tier
            if tier[0] == "T":
                fieldString = f"{tier} {name} {quality}"
            else:
                fieldString = f"{name} {quality}"

            # Break if field's char length exceeds 1024 (Discord limitation)
            if len(embedItemString) + len(fieldString) > 1024:
                break

            embedItemString += fieldString + "\n"
            embedPriceString += f"{int(df['Price'][i])}\n"
            embedQuantityString += f"{int(df[quantity][i])}\n"

        # Discord embed fields, 3 inline columns
        em.add_field(name="Item", value=embedItemString, inline=True)
        em.add_field(name="Price", value=embedPriceString, inline=True)
        em.add_field(name=quantity, value=embedQuantityString, inline=True)

        em.set_footer(text=f"Updated on: {footer}")
        return em


def setup(client):
    client.add_cog(Sheets(client))
