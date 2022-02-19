
#!-------------------------IMPORT MODULES--------------------#


import math
import discord
import random
import asyncio
import json
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


class AccountCog(commands.Cog, name="Account"):

    def __init__(self, client):

        #** Assign Discord Bot Client As Class Object & Get Pagination Cog**
        self.client = client
        self.Pagination = self.client.get_cog("EmbedPaginator")

        #** Load Config File **
        with open('Config.json') as ConfigFile:
            Config = json.load(ConfigFile)
            ConfigFile.close()
            
        #** Setup Emojis **
        self.Emojis = Config['Variables']['Emojis']
        self.Emojis["True"] = "✅"
        self.Emojis["False"] = "❌"
        
    
    @commands.command(aliases=['account', 'a'], 
                      description="Displays information about your alto profile.")
    async def profile(self, ctx):
        
        ProfileEmbed = discord.Embed(title=ctx.author.display_name+"'s Profile",
                                     colour=ctx.author.colour)
        ProfileEmbed.set_thumbnail(url=ctx.author.avatar_url)
        
        await ctx.send(embed=ProfileEmbed)


    @commands.command(aliases=['h', 'lastlistened'], 
                      description="Displays your 50 last listened to songs through the bot.")
    async def history(self, ctx):
        
        # { !!!NEEDS TESTING!!! } #
        
        HistoryEmbed = discord.Embed(title=ctx.author.display_name+"'s Listening History",
                                     colour=ctx.author.colour)
        HistoryEmbed.set_thumbnail(url=ctx.author.avatar_url)
        
        CurrentUser = Users(self.client, ctx.author.id)
        if len(CurrentUser.array) > 0:
            History = iter(CurrentUser.array)
            Description = ""
            Pages = []
            
            for Count in range(math.ceil(len(CurrentUser.array) / 10)):
                for i in range(10):
                    NextSong = next(History, None)
                    if NextSong == None:
                        break
                    Values = CurrentUser.History[NextSong]
                    if Values['SpotifyID'] is not None:
                        FormattedArtists = Utils.format_artists(Values['Artists'], Values['ArtistIDs'])
                        Description += self.Emojis['Spotify']+"**"+Values['Name']+"**\n"+FormattedArtists+"\n"
                    else:
                        Description += self.Emojis['Soundcloud']+"**"+Values['Name']+"**\n"+Values['Artists'][0]+"\n"
                
                HistoryEmbed.description = Description
                Description = ""
                if math.ceil(len(CurrentUser.array) / 10) > 1:
                    HistoryEmbed.set_footer(text="Page "+str(Count+1)+"/"+str(math.ceil(len(CurrentUser.array) / 10)))
                
                if Count == 0:
                    Page = await ctx.send(embed=HistoryEmbed)
            
            if math.ceil(len(CurrentUser.array) / 10) > 1:
                await Page.add_reaction(self.Emojis['Back'])
                await Page.add_reaction(self.Emojis['Next'])
                await self.Pagination.add_fields(Page.id, Pages)
        
        else:
            await ctx.send("**You do not have any history to display!**\nGet listening today by joining a vc and running `!play`!")
    

    @commands.command(aliases=['r', 'recommend', 'suggestions'], 
                      description="Displays 10 random song recommendations based on your listening history.",
                      usage="!recommendations <type>",
                      brief="Requires you to have some listening history or a connected Spotify account!",
                      help="`Possible Inputs For <type>:`\n- Default: None *(uses listening history)*\n- History *(uses listening history)*\n"+
                           "- Spotify *(uses Spotify playlists)*")
    async def recommendations(self, ctx, *args):
        
        #** Check Input Is Valid & If So Get User **
        Input = "".join(args)
        if Input.lower() in ["", "history", "spotify"]:
            User = Users(self.client, ctx.author.id)
            
            #** Check If User Has Requested Recommendations From Their History **
            if Input.lower() in ["", "history"]:
                
                #** Check User Actually Has Listening History To Analyse & If Not Raise Error **
                if len(User.array) > 0:

                    #** Send Processing Message To User & Get Recommendations From Spotify API Through User Class**
                    Page = await ctx.send("**Analysing Your Listening History...**")
                    Tracks = User.getRecommendations()
                
                else:
                    raise commands.CheckFailure(message="History")

            #** Check If User Has Requested To Use Spotify & Make Sure User Has Spotify Connected **
            elif Input.lower() == "spotify":    
                if User.SpotifyConnected:
                    print("User Found")

                    #** Send Initial Waiting Message To User **
                    Page = await ctx.send("**Collecting Your Spotify History...**")
                    
                    #** Get User Playlists & Songs In Those Playlists **
                    Playlists = User.GetUserPlaylists()
                    print("Got Playlists")
                    Songs = {}
                    for PlaylistID in Playlists.keys():
                        Songs.update(SongData.GetPlaylistSongs(PlaylistID)['Tracks'])
                    print("Got Songs")
                    
                    #** Update User On Progress **
                    await Page.edit(content="**Analysing Your Spotify History...**")

                    #** Get Recommendations From Returned Songs **
                    Tracks = SongData.Recommend(Songs)
                    print("Got Recomendations")
                                
                #** Let User Know If They've Not Connected Their Spotify **
                else:
                    raise commands.CheckFailure(message="Spotify")

            #** Check Tracks We're Fetched Correctly From Spotify API **
            print(Tracks)
            if not(Tracks in ["RecommendationsNotFound", "UnexpectedError"]):

                #** Randomly Choose 10 Songs From 50 Recomendations **
                Recommendations = {}
                for i in range(10):
                    SpotifyID = random.choice(list(Tracks.keys()))
                    while SpotifyID in Recommendations.keys():
                        SpotifyID = random.choice(list(Tracks.keys()))
                    Recommendations.update({SpotifyID: Tracks[SpotifyID]})

                #** Loop Through Data & Create Dictionary Of Embed Pages **
                Pages = []
                Count = 0
                for SpotifyID, Data in Recommendations.items():

                    #** Format Embed Sections **
                    Song = Data['Name']+"\nBy: "+Utils.format_artists(Data['Artists'], Data['ArtistID'])
                    Links = self.Emojis['Spotify']+" Song: [Spotify](https://open.spotify.com/track/"+SpotifyID+")\n"
                    if Data['Preview'] != None:
                        Links += self.Emojis['Preview']+" Song: [Preview]("+Data['Preview']+")\n"
                    Links += self.Emojis['Album']+" Album: ["+Data['Album']+"](https://open.spotify.com/album/"+Data['AlbumID']+")"

                    #** Create New Embed **
                    NewPage = discord.Embed(
                        title = ctx.author.display_name+"'s Recommendations")
                    NewPage.set_thumbnail(url=Data['Art'])
                    NewPage.add_field(name="Song "+str(Count+1)+":", value=Song, inline=False)
                    NewPage.add_field(name="Links:", value=Links, inline=False)
                    NewPage.set_footer(text="("+str(Count+1)+"/10) React To See More Recommendations!")

                    #** Display First Recomendation To User **
                    if Count == 0:
                        await Page.edit(content=None, embed=NewPage)
                        await Page.add_reaction(self.Emojis['Back'])
                        await Page.add_reaction(self.Emojis['Next'])
                        print("Sent!")

                    #** Convert Embed To Dictionary and Add To Data Dictionary & Increment Counter **
                    Pages.append(NewPage.to_dict())
                    Count += 1

                #** Add Embed To Active Pages In Pagination Cog **
                await self.Pagination.add_pages(Page.id, Pages)
                print("All Pages Created!")
            
            #** Return Error To User If Failed To Get Recommendations **
            else:
                await Page.edit(content="**An Error Occurred Whilst Fetching Recommendations**!\nIf this error persists, contact Lolo#6699.")
                await asyncio.sleep(5)
                await ctx.message.delete()
                await Page.delete()

        #** Raise Error If Command Doesn't Have A Valid Input **
        else:
            raise commands.BadArgument(message="recommendations")


    @commands.command(aliases=['l', 'connect'], 
                      description="Allows you to link your spotify with your account on the bot.")
    async def link(self, ctx):
    
        #** Check if User Already Has A Linked Account **
        User = Users(self.client, ctx.author.id)
        if User.SpotifyConnected == False:

            #** Add DiscordID To Spotify Table In Database **
            Database.PrepareLink(ctx.author.id)

            #** Send Embed With Auth URL Into User's DMs And Notify User **
            AuthURL = "http://82.22.157.214:5000/link?discord="+str(ctx.author.id)
            LinkEmbed = discord.Embed(
                title = "Connect Your Spotify With Discord!",
                description = "To link your spotify account, [Click Here]("+AuthURL+")!",
                colour = discord.Colour.blue())
            LinkEmbed.set_thumbnail(url="https://i.imgur.com/mUNosuh.png")
            LinkEmbed.add_field(name="What To Do Now:", value="\n**1)** *Visit the link above, and after a few seconds, you will be redirected to Spotify and asked to grant access to the bot.*"
                                                                       +"\n**2)** *Once authorised, you'll be redirected again and should receive a confirmation on the webpage if successful.*"
                                                                       +"\n**3)** *You will also get a DM confirmation below here in Discord up to 2 minutes afterwards!*")
            LinkEmbed.set_footer(text="Authentication Will Time Out After 10 Minutes")

            #** Create DM Channel With User If One Doesn't Already Exist **
            if ctx.message.author.dm_channel == None:
                await ctx.message.author.create_dm()
            
            #** Try To Send Embed To User **
            try:
                await ctx.message.author.dm_channel.send(embed=LinkEmbed)
                await ctx.send("I've sent you a DM!")

            #** Raise Error If Can't Send Messages To DM Channel **
            except :
                raise commands.CheckFailure(message="DM")
                
        else:
            #** Send Embed Asking User If They'd Like To Unlink Into DMs **
            UnlinkEmbed = discord.Embed(
                title = "Your Spotify Is Already Linked!",
                description = "**Account:**\n["+User.SpotifyData['name']+"](https://open.spotify.com/user/"+User.SpotifyData['spotifyID']+")\n\nIf You'd Like To Unlink Your Account, Please:\n`React To The Tick Below`",
                colour = discord.Colour.blue())
            UnlinkEmbed.set_thumbnail(url="https://i.imgur.com/mUNosuh.png")

            #** Create DM Channel With User If One Doesn't Already Exist **
            if ctx.message.author.dm_channel == None:
                await ctx.message.author.create_dm()
            
            #** Try To Send Embed To User **
            try:
                Unlink = await ctx.message.author.dm_channel.send(embed=UnlinkEmbed)
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
                    if str(Reaction.emoji) == self.Emojis['Tick']:
                        Database.RemoveSpotify(ctx.author.id)
                        await ctx.message.author.dm_channel.send("**Spotify Account Unlinked!**\nIf you need to relink at any time, simply run `!link`.")


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(AccountCog(client))