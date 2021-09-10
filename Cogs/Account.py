
#!-------------------------IMPORT MODULES--------------------#


import os
import discord
import random
import string
import asyncio
import json
import mysql.connector
from datetime import datetime
from discord.ext import commands


#!------------------------------IMPORT CLASSES----------------------------------#


from Classes.Users import Users
from Classes.Database import UserData
from Classes.Music import Music
from Classes.Utils import Utility


#!--------------------------------STARTUP-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Account")
print("Modules Imported: ✓\n")


#!------------------------INITIALISE CLASSES-------------------#


Database = UserData()
SongData = Music()
Utils = Utility()


#!------------------------UTILITY COG-----------------------#


class AccountCog(commands.Cog):

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

        #** Get Pagination Cog **
        self.Pagination = self.client.get_cog("EmbedPaginator")
        print(self.Pagination)


    @commands.command(aliases=['r', 'recommend', 'suggest', 'songideas'])
    async def recommendations(self, ctx):

        #** Add User To Database **
        User = Users(ctx.author.id)
        if User.Connected:
            print("User Found")

            #** Send Initial Waiting Message To User **
            Page = await ctx.send("**Analysing Your Spotify History...**")
            
            #** Get User Playlists & Songs In Those Playlists **
            Playlists = User.GetUserPlaylists()
            print("Got Playlists")
            Songs = {}
            for PlaylistID in Playlists.keys():
                Songs.update(SongData.GetPlaylistSongs(PlaylistID)['Tracks'])
            print("Got Songs")
            
            #** Update User On Progress **
            await Page.edit(content="**Adding The Finishing Touches...**")

            #** Get Recommendations From Returned Songs **
            NewSongs = SongData.Recommend(Songs)
            print("Got Recomendations")
            
            #** Randomly Choose 10 Songs From 50 Recomendations **
            Recommendations = []
            Description = ""
            for i in range(10):
                Song = random.choice(NewSongs)
                while Song in Recommendations:
                    Song = random.choice(NewSongs)
                Recommendations.append(Song)

            #** Loop Through Data & Create Dictionary Of Embed Pages **
            Data = {}
            for i in range(len(Recommendations)):

                #** Format Embed Sections **
                Song = Recommendations[i]['name']+"\nBy: "
                for j in range(len(Recommendations[i]['artists'])):
                    if j == 0:
                        Song += "["+Recommendations[i]['artists'][j]['name']+"]("+Recommendations[i]['artists'][j]['external_urls']['spotify']+")"
                    elif j != len(Recommendations[i]['artists'])-1:
                        Song += ", ["+Recommendations[i]['artists'][j]['name']+"]("+Recommendations[i]['artists'][j]['external_urls']['spotify']+")"
                    else:
                        Song += " & ["+Recommendations[i]['artists'][j]['name']+"]("+Recommendations[i]['artists'][j]['external_urls']['spotify']+")"
                Links = self.Emojis['Spotify']+" Song: [Spotify]("+Recommendations[i]['external_urls']['spotify']+")\n"
                if Recommendations[i]['preview_url'] != None:
                    Links += self.Emojis['Preview']+" Song: [Preview]("+Recommendations[i]['preview_url']+")\n"
                Links += self.Emojis['Album']+" Album: ["+Recommendations[i]['album']['name']+"]("+Recommendations[i]['album']['external_urls']['spotify']+")"

                #** Create New Embed **
                NewPage = discord.Embed(
                    title = "Your Recommendations")
                NewPage.set_thumbnail(url=Recommendations[i]['album']['images'][0]['url'])
                NewPage.add_field(name="Song "+str(i+1)+":", value=Song, inline=False)
                NewPage.add_field(name="Links:", value=Links, inline=False)
                NewPage.set_footer(text="("+str(i+1)+"/10) React To See More Recommendations!")

                #** Display First Recomendation To User **
                if i == 0:
                    await Page.edit(content=None, embed=NewPage)
                    await Page.add_reaction(self.Emojis['Back'])
                    await Page.add_reaction(self.Emojis['Next'])
                    print("Sent!")

                #** Convert Embed To Dictionary and Add To Data Dictionary **
                Data[str(i)] = NewPage.to_dict()

            #** Add Embed To Active Pages In Pagination Cog **
            await self.Pagination.add_page(Page.id, Data)
            print("All Pages Created!")
                        
        #** Let User Know If They've Not Connected Their Spotify **
        else:
            Temp = await ctx.send("**Spotify Not Connected!**\nTo run this command, first run `!link`")
            await asyncio.sleep(5)
            await ctx.message.delete()
            await Temp.delete()


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(AccountCog(client))