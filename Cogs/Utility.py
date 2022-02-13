
#!-------------------------IMPORT MODULES--------------------#


import json
import discord
import random
import string
import asyncio
from datetime import datetime
from discord.ext import commands
from dateutil.relativedelta import relativedelta


#!------------------------------IMPORT CLASSES----------------------------------#


from Classes.Users import Users
from Classes.Database import UserData


#!--------------------------------STARTUP-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Utility")
print("Modules Imported: ✓\n")


#!------------------------INITIALISE CLASSES-------------------#


Database = UserData()


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
        self.Emojis["True"] = "✅"
        self.Emojis["False"] = "❌"


    @commands.command(aliases=['l', 'connect'], description="Allows you to link your spotify with your account on the bot.")
    async def link(self, ctx):
    
        #** Check if User Already Has A Linked Account **
        User = Users(self.client, ctx.author.id)
        if User.SpotifyConnected == False:

            #{ Add DiscordID To Spotify Table In Database }

            #** Send Embed With Auth URL Into User's DMs And Notify User **
            AuthURL = "http://82.22.157.214:5000/link?discord="+str(ctx.author.id)
            Embed = discord.Embed(
                title = "Link Your Spotify Account!",
                description = "To link your spotify account, [Click Here]("+AuthURL+")!\nYou will be redirected to Spotify & asked to grant access to the bot.\nOnce authorised, you'll receive a confirmation on the webpage.\nYou will also get a DM confirmation up to 5 mins afterwards!",
                colour = discord.Colour.dark_green())
            Embed.set_footer(text="Authentication Will Time Out After 10 Minutes")

            #** Create DM & Try To Send Embed To User **
            DMChannel = await ctx.message.author.create_dm()
            try:
                await DMChannel.send(embed=Embed)
                await ctx.send("I've sent you a DM!")

            #** Raise Error If Can't Send Messages To DM Channel **
            except :
                raise commands.CheckFailure(message="DM")
                
        else:
            #** Send Embed Asking User If They'd Like To Unlink Into DMs **
            UnlinkEmbed = discord.Embed(
                title = "Your Spotify Is Already Linked!",
                description = "**Account:**\n["+User.SpotifyData['name']+"](https://open.spotify.com/user/"+User.SpotifyData['spotifyID']+")\n\nIf You'd Like To Unlink Your Account, Please:\n`React To The Tick Below`",
                colour = discord.Colour.dark_green())

            #** Create DM & Try To Send Embed To User **
            DMChannel = await ctx.message.author.create_dm()
            try:
                Unlink = await DMChannel.send(embed=UnlinkEmbed)
                await ctx.send("I've sent you a DM!")
            
            #** Raise Error If Can't Send Messages To DM Channel **
            except :
                raise commands.CheckFailure(message="DM")
            
            #** Check Function To Be Called When Checking If Correct Reaction Has Taken Place **
            def ReactionAdd(Reaction):
                return (Reaction.message_id == Unlink.id) and (Reaction.user_id != 803939964092940308)

            #** Watches For Reactions, Checks Them And Then Acts Accordingly **
            await Unlink.add_reaction(self.Emojis['Tick'])
            while True:
                Reaction = await self.client.wait_for("raw_reaction_add", check=ReactionAdd)
                if Reaction.event_type == 'REACTION_ADD':
                    if Reaction.emoji == self.Tick:
                        Database.RemoveSpotify(ctx.author.id)
                        await DMChannel.send("**Spotify Account Unlinked!**\nIf you need to relink at any time, simply run `!link`.")


    @commands.command(aliases=['pg'], description="Displays the bot's current ping to Discord in milliseconds.")
    async def ping(self, ctx):

        #** Return Client Latency in ms **
        await ctx.send("Pong! "+str(round(self.client.latency * 1000))+"ms")
    

    @commands.command(aliases=['up'], description="Displays the time since the bot last went down.")
    async def uptime(self, ctx):
        
        Uptime = relativedelta(datetime.strptime(datetime.now().strftime("%m-%d %H:%M"), "%m-%d %H:%M"), datetime.strptime(self.client.startup.strftime("%m-%d %H:%M"), "%m-%d %H:%M"))
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