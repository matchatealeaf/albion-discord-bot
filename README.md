# Albion Online Discord Assistant Bot

## Meet The Assistant

![](Images/eg_price.png)

Thanks to the [Albion Online Data Project](https://www.albion-online-data.com/), and the many players that download and run the Data Project [client](https://github.com/BroderickHyman/albiondata-client/releases) while playing the game, market price data are collected and shared freely with all Albion players. Perhaps the most popular tool that utilized these data is [AlbionOnline2D](https://www.albiononline2d.com/en/item).

The Discord bot fetches the latest minimum sell order prices (same as AlbionOnline2D), and plots the past 7 days historical prices, for the item that you asked. (Notice the typo 'lether' instead of 'leather'). The assistant will find the closest match to your query and also provides item suggestions in case you forgot how to spell. What a sweet assistant.

## How do I get the Assistant?

Unfortunately I am unable to host the bot right now. So you would have to **host it yourself**.

### Getting Started

#### Create a Discord bot account

1. First go to Discord's [developer portal](https://discordapp.com/developers/applications/).
2. Create an application by clicking on **New Application**.
3. Click on your newly created application, and on the left panel click on **Bot**.
4. Build a bot by clicking on **Add Bot**.
5. You have now created a bot account.

#### Run the Assistant as your bot account

1. Download all the files in this repository, and the requirements. (Look at **Requirements** below)
2. In your bot page in Discord's developer portal, copy the bot's **TOKEN**.
3. Edit **main.py**, at the very bottom change `token = 'abcdefghijklmnopqrstuvwxyz'` to `token = 'your copied token'`. This is to tell the program to use your bot account.
4. Open **cmd** or your **terminal** in the directory where you downloaded the files. Run `python main.py`.
5. Your bot should now be hosted on your computer and you should see the message:
```
Logged in as Bot_Username#1234.
Connected to:
```

#### Invite your Assistant bot

1. In your application page in Discord's developer portal, click on **OAuth2**.
2. Under **Scopes** tick the **bot** box.
3. Choose the **Bot Permissions** below as you like.
4. Copy the link under **Scopes** once done, and open in your browser.
5. Choose your server and go through annoying reCaptcha and you are done.
6. Everytime you start the bot, the message will now say:
```
Logged in as Bot_Username#1234
Connected to:
Your server name
```

#### Extra for people who knows discord.py and Python 

1. Inside **main.py** you can change or append:
```python
adminUsers = ['username#1234']
commandPrefix = ['emilie ', 'Emilie' ]
```
  + Being an admin user allows you to load/unload/reload cogs.
  + commandPrefix is how the bot should be called.
2. Inside **cogs/utils.py** you can change or append:
```python
self.adminUsers = ['username#1234']
```
  + The **utils.py** cog contain powerful commands that should only be callable by admin users.
  + Such commands can be abused to spam the server or to kick members. (Refer to **Features** below)
3. Some other settings for the other cogs.
  + Set and enable debug channel, for bot to send commands log to said debug channel.
  + Set and enable work channels, for bot to only works on said work channels.

### Requirements

+ Python 3.6 or higher
+ [discord.py](https://github.com/Rapptz/discord.py)
  + The bot is written with discord.py, an async API.
+ [flask](https://flask.palletsprojects.com/en/1.1.x/)
  + flask is a micro web framework to host your bot.
+ [matplotlib](https://matplotlib.org/)
  + matplotlib is required to plot the 7 days historical prices.
  
  To install the required Python libraries, run the command:
  ```
  pip install discord.py flask matplotlib
  ```
  Or if you have `conda` installed:
  ```
  conda install discord.py flask matplotlib
  ```

## Features

```
emilie price <item name>
```
+ Returns latest minimum sell order prices as Discord embed, and plots 7 days historical prices. (First screenshot)
```
emilie quick <item name>
```
+ Same as previous command, but no plotting of 7 days historical prices (faster).
```
emilie search <option> <player/guild name>
```
+ `<option>` can be `player` or `guild`.
+ Search and returns details about a player/guild.
+ [Screenshot: Searching for player](Images/eg_player.png)
+ [Screenshot: Searching for guild](Images/eg_guild.png)

Admin commands:
```
emilie extension <option> <cogs filenames>
```
+ `<option>` can be `load`, `unload`, `reload`.
+ Load/Unload/Reload cogs in the cogs folder, e.g. if you want to remove or add certain features.
```
emilie eval <python variables/generators>
```
+ eval is simply the Python function [eval](https://docs.python.org/3.5/library/functions.html#eval).
+ Allows you to check stuffs that the bot knows, i.e. list of members, servers the bot is in etc.
+ [Screenshot: Listing all users with the role 'Member'](Images/eg_member.png)
```
emilie exec <python codes>
```
+ exec is the Python function [exec](https://docs.python.org/3.5/library/functions.html#exec).
+ This is a powerful command and care must be taken when using it.
+ This command allows you to run any Python code, thus it can be abused to spam or perform tasks that breaks the bot.
+ [Screenshot: Finding the first 300 primes](Images/eg_primes.png) (I know this is arbitrary... but just to show you what it can do.)

The eval and the exec commands are there because I got tired of adding features to the bot.

I don't have to implement anything if I can simply run arbitrary codes.

*- Famous last words before breaking everything*

## Future Works

+ Allow different localizations for item search.
  + This is possible but not implemented yet.
  + Items are searched via the `item_data.json` file, which already have different localizations.
+ Item data search to show recipes etc.
  + This is also possible but not implemented yet.
  + The item API is already included in the the cog **cogs/search.py**, but nothing is done with it yet.
+ Host a bot myself so people can use the bot without having to host their own.

## Extra Background

This is a stripped-down version of a bot I made for my guild, Pangolin Trading Company. As I haven't been on Albion for quite a while, I am releasing the source codes of the bot so that the community can improve upon or implement their own bots. The stripped functions are those that were specific to the guild. For example:

+ Fetch data from guild's Google Sheets
+ Edit data in guild's Google Sheets
+ Send guild's server welcome messages
+ Send direct messages to guild members

The cogs of these features are in the '**Unused cogs**' folder, so you can refer to them if you want to implement these features yourself.

## License
See the [LICENSE](LICENSE) file for license rights and limitations.

