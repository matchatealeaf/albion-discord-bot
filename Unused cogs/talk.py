import discord
from discord.ext import commands


class Talk(commands.Cog):
    """Cog that deals with bot 'talking'.

    - Commands only callable by self.adminUsers

    Listens:
        - Welcome message (on_member_join)
            Sends a welcome message to self.generalChannel.
            Referenced self.rulesChannel and self.faqChannel in message.
        - Member leave notification (on_member_remove)
            Sends a notification of member leaving to self.debugChannel.
        - Member welcome message (on_member_update)
            Sends a direct message to member who received Member role.

    Commands:
        - send_info_to
            Sends a welcome message to specific user. (Uses user ID)
        - send_info_all
            Sends a welcome message to existing member who have self.memberRoles role.

    Functions:
        - welcome_message
            - Returns the welcome message for members.
    """

    def __init__(self, client):
        self.client = client

        # Set debug channel and admin user here
        self.debugChannel = client.get_channel(12345678)
        self.adminUsers = ["username#1234"]

        self.memberRoles = ["Member"]

        # The channel to send welcome message
        self.generalChannel = client.get_channel(12345678)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Send a welcome message on self.generalChannel when someone joined."""

        """Enable/Disable debug message here
        await self.debugChannel.send(
            f'{member.name} joined {member.guild.name}')
        """

        message = f"{member.mention}\nWelcome to the the guild!"
        await self.generalChannel.send(message)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Send a message to self.debugChannel when someone left the server."""

        # Enable/Disable debug message here
        # await self.debugChannel.send(f'{member.name} left {member.guild.name}')

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Send a message to self.debugChannel and send direct message to users who joined the server as a member."""

        # Get list of before and after roles
        beforeRoles = [str(role) for role in before.roles]
        afterRoles = [str(role) for role in after.roles]

        # Check if user became a member
        if not (set(beforeRoles) & set(self.memberRoles)) and (set(afterRoles) & set(self.memberRoles)):

            """Enable/Disable debug message here
            await self.debugChannel.send(
                f'{before.name} became a member!')
            """

            # Get direct messages
            message = self.welcome_message()

            try:
                await before.send(message)
                # Enable/Disable debug message here
                # await self.debugChannel.send(f'Welcome messages sent to {before.name}')
            except:
                # Enable/Disable debug message here
                # await self.debugChannel.send(f'Welcome messages failed to send to {before.name}')
                pass

    @commands.command()
    async def send_info_to(self, ctx, userID):
        """Send direct message to specific user."""

        # Enable/Disable debug message here
        # await self.debugChannel.send(f'{ctx.author} -> send_info_to {userID}')

        # Only callable for admins
        if str(ctx.author) not in self.adminUsers:
            return

        # Get direct messages
        message = self.welcome_message()

        # Get user
        user = await self.client.fetch_user(userID)

        # Send messages to user
        try:
            await user.send(message)
        except:
            errorUsers = user.name

            # Enable/Disable debug message here
            # await self.debugChannel.send(f'Welcome message not sent to {errorUsers}')

            pass

        # Enable/Disable debug message here
        # await self.debugChannel.send(f'Welcome messages sent to {user.name}')

    @commands.command()
    async def send_info_all(self, ctx):
        """Send direct message to all members."""

        # Enable/Disable debug message here
        # await self.debugChannel.send(f'{ctx.author} -> send_info')

        # Only callable for admins
        if str(ctx.author) not in self.adminUsers:
            return

        # Get direct messages
        message = self.welcome_message()

        sentto = ""
        errorUsers = ""

        # Only send to members who have Member role
        for member in self.client.guilds[0].members:
            roles = [str(role) for role in member.roles]
            if set(roles) & set(self.memberRoles):
                try:
                    await member.send(message)
                    sentto += str(member.name) + ", "
                except:
                    errorUsers += str(member.name) + ", "

        """Enable/Disable debug message here
        await self.debugChannel.send(f'Welcome messages sent to {sentto}')
        await self.debugChannel.send(
            f'Welcome messages failed to send to {errorUsers}')
        """

    def welcome_message(self):

        # Message to send
        message = "Well hello there!"

        return message


def setup(client):
    client.add_cog(Talk(client))
