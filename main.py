import discord
from discord.ext import commands
import os
import logging
import configparser


# Load config.ini
currentPath = os.path.dirname(os.path.realpath(__file__))
configs = configparser.ConfigParser()
configs.read(currentPath + "/config.ini")

# adminUsers gets to load/unload/reload cogs
adminUsers = configs["General"]["adminUsers"].replace("'", "").split(", ")
commandPrefix = configs["General"]["commandPrefix"].replace("'", "").split(", ")

client = commands.AutoShardedBot(
    command_prefix=commands.when_mentioned_or(*commandPrefix), case_insensitive=True
)

# Set up logging to discord.log
logger = logging.getLogger("discord")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
)
logger.addHandler(handler)


@client.event
async def on_ready():
    """Things to do when bot is ready.

    - Load all cogs in folder /cogs.
    - Change activity to 'Ready'.
    - Login messages in console:
        Logged in username.
        List of joined guilds.
    """

    # Remove default help command (before loading of cogs)
    client.remove_command("help")

    # Load cogs in folder /cogs
    for filename in os.listdir(currentPath + "/cogs"):
        if filename.endswith(".py"):
            try:
                client.load_extension(f"cogs.{filename[:-3]}")
            except Exception as e:
                print(e)
                # reload again when load fails (no idea why this works)
                client.reload_extension(f"cogs.{filename[:-3]}")
                pass

    # Activity to 'Ready'
    await client.change_presence(activity=discord.Game("Ready"))

    # Login message in console
    print(f"Logged in as {client.user}.\nConnected to:")
    for (i, guild) in enumerate(client.guilds):

        # Only list up to 10 guilds
        print(guild.name)
        if i == 9:
            print(f"and {len(client.guilds) - 10} other guilds.")
            break


@client.command()
async def extension(ctx, option, extension):
    """Reload, load, or unload extensions.

    - Usage: <command-prefix> extension <option> <cog's name>
    - <option> : load, unload, reload
    - Only allowable if user is adminUser.
    """

    # Check if user is in adminUsers
    if str(ctx.author) not in adminUsers:
        await ctx.send(f"You do not have permission to {option} extensions.")
        return

    try:
        if option == "reload":
            client.reload_extension(f"cogs.{extension}")
        elif option == "load":
            client.load_extension(f"cogs.{extension}")
        elif option == "unload":
            client.unload_extension(f"cogs.{extension}")

        # Prompt usage method if option is wrong
        else:
            await ctx.send(
                f"Usage: `{commandPrefix[0]}extension <option> <extension>`\nOptions: `reload, load, unload`"
            )
            return

    except:
        await ctx.send(f"{extension} extension {option} FAILED.")
        return

    # Success message
    await ctx.send(f"{extension} extension {option.upper()}ED.")


# Copy from your Discord developer portal
token = configs["TOKEN"]["botToken"]
client.run(token)
