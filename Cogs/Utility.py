
#!-------------------------IMPORT MODULES--------------------#


import json
import discord
from datetime import datetime
from discord.ext import commands
from dateutil.relativedelta import relativedelta


#!--------------------------------STARTUP-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Utility")
print("Modules Imported: ✓\n")


#!------------------------UTILITY COG-----------------------#


class UtilityCog(commands.Cog, name="Utility"):

    def __init__(self, client):

        #** Assign Discord Bot Client As Class Object **
        self.client = client 

         #** Load Config File **
        with open('Config.json') as ConfigFile:
            Config = json.load(ConfigFile)
            ConfigFile.close()
            
        #** Setup Emojis **
        self.Emojis = Config['Variables']['Emojis']


    @commands.command(aliases=['pg'], description="Displays the bot's current ping to Discord in milliseconds.")
    async def ping(self, ctx):

        #** Return Client Latency in ms **
        await ctx.send("Pong! "+str(round(self.client.latency * 1000))+"ms")
    

    @commands.command(aliases=['up'], description="Displays the time since the bot last went down.")
    async def uptime(self, ctx):
        
        #** Calculate Time Difference Between DateTime Stored At Startup & Datetime Now **
        Uptime = relativedelta(datetime.strptime(datetime.now().strftime("%m-%d %H:%M"), "%m-%d %H:%M"), datetime.strptime(self.client.startup.strftime("%m-%d %H:%M"), "%m-%d %H:%M"))
        
        #** Format Into A Nice String & Return To User **
        await ctx.send("The bot has been online for:\n`"+str(Uptime.months)+" Months, "+str(Uptime.days)+" Days, "+str(Uptime.hours)+
                       " Hours & "+str(Uptime.minutes)+" Minutes`")


    @commands.command(aliases=['inv'], description="Displays the bot's Discord invite link.")
    async def invite(self, ctx):
        
        #** Create Embed With Invite Information **
        Invite = discord.Embed(
            title="Invite Flare To Your Discord Server!",
            colour=discord.Colour.orange(),
            description="A whole new way to listen to music awaits you:\n🎶 [Flare | Discord Music](https://discord.com/api/oauth2/authorize?client_id=803939964092940308&permissions=139921845328&scope=bot) 🎶")
        
        #** Send Embed To Discord **
        await ctx.send(embed=Invite)
        

#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(UtilityCog(client))