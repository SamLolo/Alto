
#!-------------------------IMPORT MODULES--------------------#


import discord
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from dateutil.relativedelta import relativedelta


#!------------------------UTILITY COG-----------------------#


class UtilityCog(commands.Cog, name="Utility"):

    def __init__(self, client: discord.Client):

        #** Assign Discord Bot Client As Class Object **
        self.client = client 
        
    
    @app_commands.command(description="Displays the bot's latency to Discord in milliseconds.")
    async def ping(self, interaction: discord.Interaction):
        
        #** Return Client Latency in ms **
        await interaction.response.send_message(f'**Pong!** `{round(self.client.latency * 1000)} ms`')


    @app_commands.command(description="Displays the time since the bot came online.")
    async def uptime(self, interaction: discord.Interaction):
        
        #** Calculate Time Difference Between DateTime Stored At Startup & Datetime Now **
        Uptime = relativedelta(datetime.strptime(datetime.now().strftime("%m-%d %H:%M"), "%m-%d %H:%M"), datetime.strptime(self.client.startup.strftime("%m-%d %H:%M"), "%m-%d %H:%M"))
        
        #** Format Into A Nice String & Return To User **
        await interaction.response.send_message(f'*The bot has been online for:*\n`{Uptime.months} Months, {Uptime.days} Days, {Uptime.hours} Hours & {Uptime.minutes} Minutes`')


    @app_commands.command(description="Displays the bot's Discord invite link.")
    async def invite(self, interaction: discord.Interaction):
        
        #** Create Embed With Invite Information **
        Invite = discord.Embed(
            title="Invite Alto To Your Discord Server!",
            colour=discord.Colour.blue(),
            description="A whole new way to listen to music awaits you:\n🎶 [Alto | Discord Music](https://discord.com/oauth2/authorize?client_id=803939964092940308&permissions=3632192&scope=bot) 🎶")
        Invite.set_thumbnail(url=self.client.application.icon)

        #** Send Embed To Discord **
        await interaction.response.send_message(embed=Invite)
        

#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(UtilityCog(client))