
#!-------------------------IMPORT MODULES--------------------#


import discord
from discord.ext import commands
from discord import app_commands
from dateutil.relativedelta import relativedelta


#!------------------------UTILITY COG-----------------------#


class UtilityCog(commands.Cog, name="Utility"):

    def __init__(self, client: discord.Client):
        """
        Instanciates the Utility extension, creating required attributes for functions within the class
        
        Parameters:
        client (discord.Client): the discord client the extension has been loaded with
        
        Returns:
        None
        """
        self.client = client
        
    
    @app_commands.command()
    async def ping(self, interaction: discord.Interaction):
        """
        Displays the bot's latency to Discord in milliseconds.
        
        Parameters:
        interaction (discord.Interaction): the discord interaction that triggered the command
        
        Returns:
        None
        """
        await interaction.response.send_message(f'**Pong!** `{round(self.client.latency * 1000)} ms`')


    @app_commands.command()
    async def uptime(self, interaction: discord.Interaction):
        """
        Displays the time since the bot last went offline.
        
        Parameters:
        interaction (discord.Interaction): the discord interaction that triggered the command
        
        Returns:
        None
        """
        #** Calculate Time Difference Between DateTime Stored At Startup & Datetime Now
        uptime = relativedelta(discord.utils.utcnow(), self.client.startup)
        if uptime.years == 0:
            await interaction.response.send_message(f'*The bot has been online for:*\n`{uptime.months} Months, {uptime.days} Days, {uptime.hours} Hours & {uptime.minutes} Minutes`')
        elif uptime.years == 1:
            await interaction.response.send_message(f'*The bot has been online for:*\n`{uptime.years} Year, {uptime.months} Months, {uptime.days} Days, {uptime.hours} Hours & {uptime.minutes} Minutes`')
        else:
            await interaction.response.send_message(f'*The bot has been online for:*\n`{uptime.years} Years, {uptime.months} Months, {uptime.days} Days, {uptime.hours} Hours & {uptime.minutes} Minutes`')


    @app_commands.command()
    async def invite(self, interaction: discord.Interaction):
        """
        Displays the bot's Discord invite link.
        
        Parameters:
        interaction (discord.Interaction): the discord interaction that triggered the command
        
        Returns:
        None
        """
        #** Create Embed With Invite Information **
        invite = discord.Embed(title="Invite Alto To Your Discord Server!",
                               colour=discord.Colour.blue(),
                               description="A whole new way to listen to music awaits you:\n🎶 [Alto | Discord Music](https://discord.com/api/oauth2/authorize?client_id=803939964092940308&permissions=414836976704&scope=bot) 🎶")
        invite.set_thumbnail(url=self.client.application.icon)
        await interaction.response.send_message(embed=invite)
        

#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    """
    Adds the Utility extension to the clients list of cogs
    
    Parameters:
    client (discord.Client): the discord client to use
    
    Returns:
    None
    """
    await client.add_cog(UtilityCog(client))