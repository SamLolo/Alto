
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


from Classes.SpotifyUser import SpotifyUser
from Classes.Database import UserData
from Classes.Music import Music
from Classes.Youtube import YoutubeAPI


#!--------------------------------STARTUP-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Account")
print("Modules Imported: ✓\n")


#!------------------------INITIALISE CLASSES-------------------#


Youtube = YoutubeAPI()
Database = UserData()
SongData = Music()


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


    @commands.command(aliases=['r', 'recommend', 'suggest', 'songideas'])
    async def recommendations(self, ctx):

        #** Add User To Database **
        User = SpotifyUser(ctx.author.id, cursor, connection)
        if User.Connected:
            print("User Found")
            
            #** Get User Playlists & Songs In Those Playlists **
            Playlists = User.GetUserPlaylists()
            print("Got Playlists")
            Songs = {}
            for PlaylistID in Playlists.keys():
                Songs.update(SongData.GetPlaylistSongs(PlaylistID)['Tracks'])
            print("Got Songs")
            
            #** Get Recommendations From Returned Songs **
            NewSongs = SongData.Recommend(Songs)
            print("Got Recomendations")
            
            #** Randomly Choose 10 Songs From 50 Recomendations **
            Recommendations = {}
            Description = ""
            for i in range(10):
                Song = random.choice(NewSongs)
                while Song in Recommendations.values():
                    Song = random.choice(NewSongs)
                Recommendations[i] = Song

            #** Prepare Data On Songs Ready To Be Displayed **
            Data = Recommendations[0]
            Song = Data['name']+"\nBy: "
            for i in range(len(Data['artists'])):
                if i == 0:
                    Song += "["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
                elif i != len(Data['artists'])-1:
                    Song += ", ["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
                else:
                    Song += " & ["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
            Links = self.Emojis['Spotify']+" Song: [Spotify]("+Data['external_urls']['spotify']+")\n"
            if Data['preview_url'] != None:
                Links += self.Emojis['Preview']+" Song: [Preview]("+Data['preview_url']+")\n"
            Links += self.Emojis['Album']+" Album: ["+Data['album']['name']+"]("+Data['album']['external_urls']['spotify']+")"

            #** Setup Base Embed With Fields For First Song **
            BaseEmbed = discord.Embed(
                title = "Your Recommendations")
            BaseEmbed.set_thumbnail(url=Recommendations[0]['album']['images'][0]['url'])
            BaseEmbed.add_field(name="Song 1:", value=Song, inline=False)
            BaseEmbed.add_field(name="Links:", value=Links, inline=False)
            BaseEmbed.set_footer(text="(1/10) React To See More Recommendations!")

            #** Send First Embed To Discord And Add Reactions **
            Page = await ctx.send(embed=BaseEmbed)
            await Page.add_reaction(self.Emojis['Back'])
            await Page.add_reaction(self.Emojis['Next'])
            CurrentPage = 0
            print("Sent!")

            #** Check Function To Be Called When Checking If Correct Reaction Has Taken Place **
            def ReactionAdd(Reaction):
                return (Reaction.message_id == Page.id) and (Reaction.user_id != 803939964092940308)

            #** Watches For Reactions, Checks Them And Then Acts Accordingly **
            while True:
                Reaction = await client.wait_for("raw_reaction_add", check=ReactionAdd)
                if Reaction.event_type == 'REACTION_ADD':
                    await Page.remove_reaction(Reaction.emoji, Reaction.member)
                    if Reaction.emoji == self.Emojis['Next'] or Reaction.emoji == self.Emojis['Back']:
                        
                        #** Adjust Current Page Based On Reaction **
                        if CurrentPage == 9 and Reaction.emoji == self.Emojis['Next']:
                            CurrentPage = 0
                        elif CurrentPage == 0 and Reaction.emoji == self.Emojis['Back']:
                            CurrentPage = 9
                        else:
                            if Reaction.emoji == self.Emojis['Next']:
                                CurrentPage += 1
                            else:
                                CurrentPage -= 1
                                
                        #** Prepare New Data For Next Song **
                        Data = Recommendations[CurrentPage]
                        Song = Data['name']+"\nBy: "
                        for i in range(len(Data['artists'])):
                            if i == 0:
                                Song += "["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
                            elif i != len(Data['artists'])-1:
                                Song += ", ["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
                            else:
                                Song += " & ["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
                        Links = self.Emojis['Spotify']+" Song: [Spotify]("+Data['external_urls']['spotify']+")\n"
                        if Data['preview_url'] != None:
                            Links += self.Emojis['Preview']+" Song: [Preview]("+Data['preview_url']+")\n"
                        Links += self.Emojis['Album']+" Album: ["+Data['album']['name']+"]("+Data['album']['external_urls']['spotify']+")"
                        
                        #** Format New Embed And Sent It Into Discord **
                        BaseEmbed.set_thumbnail(url=Recommendations[CurrentPage]['album']['images'][0]['url'])
                        BaseEmbed.clear_fields()
                        BaseEmbed.add_field(name="Song "+str(CurrentPage+1)+":", value=Song, inline=False)
                        BaseEmbed.add_field(name="Links:", value=Links, inline=False)
                        BaseEmbed.set_footer(text="("+str(CurrentPage+1)+"/10) React To See More Recommendations!")
                        await Page.edit(embed=BaseEmbed)
                        
        #** Let User Know If They've Not Connected Their Spotify **
        else:
            Temp = await ctx.send("**Spotify Not Connected!**\nTo run this command, first run `!link`")
            await asyncio.sleep(5)
            await ctx.message.delete()
            await Temp.delete()


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(AccountCog(client))