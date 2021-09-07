
#!-------------------------IMPORT MODULES--------------------#


import os
import json
import discord
import random
import string
import asyncio
import mysql.connector
from datetime import datetime
from discord.ext import commands


#!------------------------------IMPORT CLASSES----------------------------------#


from Classes.SpotifyUser import SpotifyUser
from Classes.Database import UserData
from Classes.Music import Music
from Classes.Youtube import YoutubeAPI


#!--------------------------------STARTUP-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Utility")
print("Modules Imported: ✓\n")


#!------------------------INITIALISE CLASSES-------------------#


Youtube = YoutubeAPI()
Database = UserData()
SongData = Music()


#!------------------------UTILITY COG-----------------------#


class UtilityCog(commands.Cog):

    def __init__(self, client):

        #** Assign Discord Bot Client As Class Object **
        self.client = client 

        #** Assign Other Class Objects **
        self.ActiveStates = {}

         #** Load Config File **
        with open('Config.json') as ConfigFile:
            Config = json.load(ConfigFile)
            ConfigFile.close()
            
        #** Setup Emojis **
        self.Emojis = Config['Variables']['Emojis']
        self.Emojis["True"] = "✅"
        self.Emojis["False"] = "❌"


    @commands.command(aliases=['l', 'connect'])
    async def link(self, ctx):
    
        #** Check if User Already Has A Linked Account **
        Error = False
        Spotify = SpotifyUser(ctx.author.id)
        if Spotify.Connected == False:

            #** Add User To Database **
            User = Database.GetUser(ctx.author.id)
            if User == None:
                User = Database.AddUser()

            #** Generate Random State and Make Sure It Isn't Active **
            while True:
                State = []
                for i in range(10):
                    State.append(random.choice(string.ascii_letters))
                State = "".join(State)
                if not(State in self.ActiveStates.keys()):
                    self.ActiveStates[State] = ctx.author.id
                    break

            #** Send Embed With Auth URL Into User's DMs And Notify User **
            AuthURL = "https://accounts.spotify.com/authorize?client_id=710b5d6211ee479bb370e289ed1cda3d&response_type=code&redirect_uri=http%3A%2F%2F82.22.157.214:5000%2F&scope=playlist-read-private%20playlist-read-collaborative&state="+State
            Embed = discord.Embed(
                title = "Link Your Spotify Account!",
                description = "To link your spotify account, [Click Here]("+AuthURL+")!\nOnce authorised, you'll receive a confirmation underneath!",
                colour = discord.Colour.dark_green())
            Embed.set_footer(text="Authentication Will Time Out After 10 Minutes")
            DMChannel = await ctx.message.author.create_dm()
            try:
                AuthEmbed = await DMChannel.send(embed=Embed)
                await ctx.send("I've sent you a DM!")
            except :
                Error = True

            #** Check For User Details In Database Every 5 Seconds For 10 Mins **
            if not(Error):
                print(State)
                await asyncio.sleep(10)
                connection, cursor = Database.return_connection()
                cursor.execute("SELECT * FROM spotify WHERE State = '"+str(State)+"';")
                Spotify = cursor.fetchone()
                connection.commit()
                print(Spotify)
                for Count in range(118):
                    if Spotify != None:
                        break
                    await asyncio.sleep(5)
                    cursor.execute("SELECT * FROM spotify WHERE State = '"+str(State)+"';")
                    Spotify = cursor.fetchone()
                    connection.commit()
                    print(Spotify)
                self.ActiveStates.pop(State)

                #** Update Users To Include Spotify Table ID **
                if Spotify != None:
                    cursor.execute("UPDATE users SET Spotify = '"+str(Spotify[0])+"' WHERE DiscordID = '"+str(ctx.author.id)+"';")
                    connection.commit()
                
                    #** Let User Know They're Connected **
                    Embed = discord.Embed(
                        title = "Account Connected!",
                        colour = discord.Colour.dark_green())
                    Embed.set_thumbnail(url=Spotify[5])
                    Embed.add_field(name="Username", value="["+Spotify[3]+"](https://open.spotify.com/user/"+Spotify[4]+")")
                    await AuthEmbed.edit(embed=Embed)

                #** Let User Know If Authentication Times Out **
                else:
                    await AuthEmbed.edit(content="Authentication Timed Out!\nTo restart the linking process, re-run `!link`!")
                
        else:
            #** Send Embed Asking User If They'd Like To Unlink Into DMs **
            UnlinkEmbed = discord.Embed(
                title = "Your Spotify Is Already Linked!",
                description = "**Account:**\n["+Spotify.Name+"](https://open.spotify.com/user/"+Spotify.ID+")\n\nIf You'd Like To Unlink Your Account, Please:\n`React To The Tick Below`",
                colour = discord.Colour.dark_green())
            DMChannel = await ctx.message.author.create_dm()
            try:
                Unlink = await DMChannel.send(embed=UnlinkEmbed)
                await ctx.send("I've sent you a DM!")
            except :
                Error = True
                
            if not(Error):
                await Unlink.add_reaction(self.Emojis['Tick'])
                
                #** Check Function To Be Called When Checking If Correct Reaction Has Taken Place **
                def ReactionAdd(Reaction):
                    return (Reaction.message_id == Unlink.id) and (Reaction.user_id != 803939964092940308)

                #** Watches For Reactions, Checks Them And Then Acts Accordingly **
                while True:
                    Reaction = await self.client.wait_for("raw_reaction_add", check=ReactionAdd)
                    if Reaction.event_type == 'REACTION_ADD':
                        print(Reaction.emoji)
                        if Reaction.emoji == self.Tick:
                            Database.RemoveSpotify(ctx.author.id)
                            await DMChannel.send("**Spotify Account Unlinked!**\nIf you need to relink at any time, simply run `!link`.")
                            
        #** If Error, Tell User To Open Their DMs With The Bot **
        if Error == True:
            Temp = await ctx.message.channel.send("**DM Failed!**\nPlease turn on `Allow Server Direct Messages` in Discord settings in order to link your account")
            await asyncio.sleep(5)
            await ctx.message.delete()
            await Temp.delete()


    @commands.command(aliases=['pg'])
    async def ping(self, ctx):

        #** Return Client Latency in ms **
        await ctx.send("Pong! "+str(round(self.client.latency * 1000))+"ms")
    

    @commands.command(aliases=['up'])
    async def uptime(self, ctx):
        print("N/A")


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(UtilityCog(client))