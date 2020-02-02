import discord
from discord.ext import commands
import configparser
import os


class Utils(commands.Cog):
    """Cog for utility commands.

    - These commands are only available for users in self.adminUsers.
    - You don't want people to have access to exec, as it can be used to execute
        any Python code, and can be used to spam or kick members.
    - eval might be used for accessing information that the bot has:
        - List all members
        - List all servers bot is in etc.
    - exec might be used to perform simple programming tasks:
        - List all members who joined before a date or has a certain role
        - Randomly pick a member
        - Group members into different teams
        - Anything that you can program really
    - This cog will also contain extra utility or background stuffs that the bot does
        - e.g. implement the delete reaction button '\u274c' (red X)

    Commands:
        - ping
            Return latency.
        - exec
            Execute Python codes with exec function.
        - eval
            Eval Python values with eval function.

    Listens:
        - Delete reaction button (on_raw_reaction_add)
            Deletes a bot message when reacted with '\u274c' (red X).
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

        self.adminUsers = configs["General"]["adminUsers"].replace("'", "").split(", ")

    @commands.command()
    async def ping(self, ctx):
        """Returns latency of bot."""

        # Debug message
        if self.debug:
            await self.debugChannel.send(f"{ctx.author} -> ping")

        # Check if in workChannel
        if self.onlyWork:
            if ctx.channel.id not in self.workChannel:
                return

        # Checks if admin
        if str(ctx.author) not in self.adminUsers:
            return

        await ctx.send(f"Pong! {round(self.client.latency * 1000)}ms")

    @commands.command(aliases=["python"])
    async def exec(self, ctx, *, codes):
        """Execute Python codes with exec function

        - Resolves ```python and ``` at start and end of code block.
        - Any Python code can be executed. (becareful!)
        - Only allows adminUser to execute codes.
        """

        # Debug message
        if self.debug:
            await self.debugChannel.send(f"{ctx.author} -> exec {codes}")

        # Check if in workChannel
        if self.onlyWork:
            if ctx.channel.id not in self.workChannel:
                return

        # Check if admin
        if str(ctx.author) not in self.adminUsers:
            return

        await ctx.channel.trigger_typing()

        # Strip ```python and ``` if exists
        if codes[:9] == "```python":
            codes = codes[9:]
            codes = codes[:-3]
        elif codes[:3] == "```":
            codes = codes[3:]
            codes = codes[:-3]

        # Execute code
        # Send exception with bot if exception raised
        # Can reassign self.msg in exec codes to get bot to send messages
        self.msg = "Code executed."
        try:
            exec(f"{codes}")
            await ctx.send(self.msg)
        except Exception as e:
            await ctx.send(e)

    @commands.command()
    async def eval(self, ctx, *, codes):
        """Evalute Python variables with eval function.

        - Resolves ```python and ``` at start and end of code block.
        - eval function can only evalulate variables.
        """

        # Debug message
        if self.debug:
            await self.debugChannel.send(f"{ctx.author} -> eval {codes}")

        # Check if in workChannel
        if self.onlyWork:
            if ctx.channel.id not in self.workChannel:
                return

        # Check if admin
        if str(ctx.author) not in self.adminUsers:
            return

        await ctx.channel.trigger_typing()

        # Strip ```python and ``` if exists
        if codes[:9] == "```python":
            codes = codes[9:]
            codes = codes[:-3]
        elif codes[:3] == "```":
            codes = codes[3:]
            codes = codes[:-3]

        # Evalulate with eval and send exception if raised
        try:
            msg = eval(f"{codes}")
            await ctx.send(msg)
        except Exception as e:
            await ctx.send(e)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, rawReaction):
        """Delete bot's message by reaction.

        - Reaction to delete message is \u274c (red X).
        - Make sure that it is bot's message,
        - and that reaction is not by the bot itself.
        """

        # Get reacted message
        channel = await self.client.fetch_channel(rawReaction.channel_id)
        msg = await channel.fetch_message(rawReaction.message_id)

        # Get user who reacted and the reaction emoji
        user = self.client.get_user(rawReaction.user_id)
        emoji = rawReaction.emoji

        # Only delete message if:
        # it is bot's message,
        # reaction is not by bot (bot adds reaction after each message)
        # reaction emoji is \u274c (the :x: emoji)
        if (
            msg.author == self.client.user
            and user != self.client.user
            and str(emoji) == "\u274c"
        ):
            await msg.delete()


def setup(client):
    client.add_cog(Utils(client))
