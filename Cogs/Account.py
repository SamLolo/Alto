
#!-------------------------IMPORT MODULES--------------------#


import copy
import math
import json
import random
import asyncio
import discord
from datetime import datetime
from discord.ext import commands
from dateutil.relativedelta import relativedelta


#!------------------------------IMPORT CLASSES----------------------------------#


from Classes.Users import Users
from Classes.Database import UserData
from Classes.MusicUtils import Music
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
        
        #** Setup Base Profile Embed With Title & User's Colour **
        ProfileEmbed = discord.Embed(title=ctx.author.display_name+"'s Profile",
                                     colour=ctx.author.colour)

        #** If User Not In VC, Create New User Object **
        if not(ctx.author.voice) or not(ctx.author.voice.channel):
            CurrentUser = Users(self.client, ctx.author.id)
        
        #** If In VC, Check If Player Active & If Not, Create New User Object **
        else:
            Player = self.client.lavalink.player_manager.get(ctx.author.voice.channel.guild.id)
            if Player == None:
                CurrentUser = Users(self.client, ctx.author.id)
            
            #** If Player Active, Fetch Users Dict & Check If User In Dictionary Otherwise Create New User Object **
            else:
                UserDict = Player.fetch('Users')
                try:
                    CurrentUser = UserDict[str(ctx.author.id)]
                except:
                    CurrentUser = Users(self.client, ctx.author.id)

        #** Get Last Song's Data if Listening History Isn't Empty **
        if len(CurrentUser.array) > 0:
            LastSongData = CurrentUser.History[len(CurrentUser.array) - 1]

            #** Format Data For Song & Add Last Listened To Song To Embed As Field **
            FormattedSong = Utils.format_song(LastSongData)
            ProfileEmbed.add_field(name="Last Listened To:", value=FormattedSong, inline=False)

            #** Calculate Time Difference And Check What To Display **
            TimeDiff = relativedelta(datetime.now(), LastSongData['ListenedAt'])
            if TimeDiff.years > 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value="Over "+str(TimeDiff.years)+" years ago")
            elif TimeDiff.years == 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value="Over a year ago")
            elif TimeDiff.months > 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value="Over "+str(TimeDiff.months)+" months ago")
            elif TimeDiff.months == 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value="Over a month ago")
            elif TimeDiff.days > 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value=str(TimeDiff.days)+" days ago")
            elif TimeDiff.days == 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value="A day ago")
            elif TimeDiff.hours > 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value=str(TimeDiff.hours)+" hours ago")
            elif TimeDiff.hours == 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value="An hour ago")
            else:
                ProfileEmbed.add_field(name="Last Listening Session:", value="Less than an hour ago")
        
        #** Add Blank Fields If Listening History Empty **
        else:
            ProfileEmbed.add_field(name="Last Listened To:", value="No Listening History")
            ProfileEmbed.add_field(name="Last Listening Session:", value="N/A")

        #** Calculate Total Song Count & Add As Field To Embed **
        SongTotal = int(CurrentUser.user['data']['songs']) + len(CurrentUser.array)
        ProfileEmbed.add_field(name="Lifetime Song Count:", value=str(SongTotal)+" Songs")
        
        #** Send Profile Embed To User **
        await ctx.send(embed=ProfileEmbed)


    @commands.command(aliases=['h', 'lastlistened'], 
                      description="Displays your 20 last listened to songs through the bot.")
    async def history(self, ctx):
        
        #** Setup Base History Embed With Title, User's Colour & Profile Picture **
        HistoryEmbed = discord.Embed(title=ctx.author.display_name+"'s Listening History",
                                     colour=ctx.author.colour)
        HistoryEmbed.set_thumbnail(url=ctx.author.avatar_url)
        
        #** If User Not In VC, Create New User Object **
        if not(ctx.author.voice) or not(ctx.author.voice.channel):
            CurrentUser = Users(self.client, ctx.author.id)
        
        #** If In VC, Check If Player Active & If Not, Create New User Object **
        else:
            Player = self.client.lavalink.player_manager.get(ctx.author.voice.channel.guild.id)
            if Player == None:
                CurrentUser = Users(self.client, ctx.author.id)
            
            #** If Player Active, Fetch Users Dict & Check If User In Dictionary Otherwise Create New User Object **
            else:
                UserDict = Player.fetch('Users')
                try:
                    CurrentUser = UserDict[str(ctx.author.id)]
                except:
                    CurrentUser = Users(self.client, ctx.author.id)

        #** Check User Has Listened To Some Songs **
        if len(CurrentUser.array) > 0:

            #** Organise Song History Queue Into New Array Sorted With Newest First Song First **
            OrganisedArray = []
            for i in range(CurrentUser.inpointer-1, (-1*len(CurrentUser.array)+(CurrentUser.inpointer-1)), -1):
                OrganisedArray.append(CurrentUser.History[i])

            #** Create Iteration Object Through History List **
            History = iter(OrganisedArray)
            Pages = []
            
            #** For Upper Bound Of Length Of History Divided By 5 Representing The Amount Of Pages Needed **
            for Count in range(math.ceil(len(CurrentUser.array) / 5)):

                #** Set Empty Description String & Get Next SongData Dict In History. If Returns None, Break Loop As Run Out Of Songs **
                Description = ""
                for i in range(5):
                    NextSong = next(History, None)
                    if NextSong == None:
                        break

                    #** Format Song & Add Listened To Stat & Divisor **
                    Description += Utils.format_song(NextSong)
                    Description += "\n*Listened on "+NextSong['ListenedAt'].strftime('%d/%m/%y')+" at "+NextSong['ListenedAt'].strftime('%H:%M')+"*"
                    Description += "\n--------------------\n"
                
                #** Set Embed Description To String Created Above **
                HistoryEmbed.description = Description

                #** Set Page Number If More Than One Page Needed **
                if math.ceil(len(CurrentUser.array) / 5) > 1:
                    HistoryEmbed.set_footer(text="Page "+str(Count+1)+"/"+str(math.ceil(len(CurrentUser.array) / 5)))
                    PageDict = copy.deepcopy(HistoryEmbed.to_dict())
                    Pages.append(PageDict)
                
                #** Send First Embed Page On First Loop Through Count **
                if Count == 0:
                    Page = await ctx.send(embed=HistoryEmbed)
            
            #** If More Than One Page Being Displayed, Add Back And Next Reactions & Add To Global Pagination System **
            if math.ceil(len(CurrentUser.array) / 5) > 1:
                await Page.add_reaction(self.Emojis['Back'])
                await Page.add_reaction(self.Emojis['Next'])
                await self.Pagination.add_pages(Page.id, Pages)
        
        #** Let User Know If They Have No Listening History To Display **
        else:
            await ctx.send("**You do not have any history to display!**\nGet listening today by joining a vc and running `/play`!")
    

    @commands.command(aliases=['r', 'recommend', 'suggestions'], 
                      description="Displays 10 random song recommendations based on your listening history.",
                      brief="Requires you to have some listening history!")
    async def recommendations(self, ctx, *args):
        
        #** Check Input Is Valid & If So Get User **
        Input = "".join(args)
        User = Users(self.client, ctx.author.id)
        
        #** Check User Actually Has Listening History To Analyse & If Not Raise Error **
        if len(User.array) > 0:

            #** Send Processing Message To User & Get Recommendations From Spotify API Through User Class**
            Page = await ctx.send("**Analysing Your Listening History...**")
            Tracks = User.getRecommendations()
            print("Got Recommendations")
        
        else:
            raise commands.CheckFailure(message="History")

        #** Check Tracks We're Fetched Correctly From Spotify API **
        if not(Tracks in ["RecommendationsNotFound", "UnexpectedError"]):

            #** Randomly Choose 10 Songs From 50 Recomendations **
            print(Tracks)
            Recommendations = {}
            for i in range(10):
                SpotifyID = random.choice(list(Tracks.keys()))
                while SpotifyID in Recommendations.keys():
                    SpotifyID = random.choice(list(Tracks.keys()))
                Recommendations.update({SpotifyID: Tracks[SpotifyID]})
            print(Recommendations)

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
            print("All Pages Created!\n")
        
        #** Return Error To User If Failed To Get Recommendations **
        else:
            await Page.edit(content="**An Error Occurred Whilst Fetching Recommendations**!\nIf this error persists, open a ticket in our Discord server:* `/discord`.")
            await asyncio.sleep(5)
            await ctx.message.delete()
            await Page.delete()


    @commands.command(aliases=['remove', 'clear'],
                      description="Deletes your user data where requested from our database.",
                      usage="/delete <data>",
                      help="`Possible Inputs For <data>:`\n- all: *deletes all traces of your data*\n- history: *clears your stored listening history*\n"+
                           "- user: *deletes all user data including your listening history*")
    async def delete(self, ctx, data):
        
        #** Generate Message To Send To User & The Table That Would Need To Be Deleted **
        if data == "all":
            Message = "All stored data will be deleted and lost forever!\nYou may lose access to certain bot features temporarily after this process!"
            Tables = ['users', 'spotify', 'history', 'recommendations']
        elif data in ["history", "listening history"]:
            Message = "All listening history will be deleted, including data used to generate recommendations! This action is irriversable!"
            Tables = ['history']
        elif data == "user":
            Message = "All listening history and user data, besides spotify data, will be deleted and lost forever!\nYou may lose access to certain bot features temporarily after this process!"
            Tables = ['users', 'history', 'recommendations']
        
        #** If Invalid Input, Raise Bad Argument Error **
        else:
            raise commands.BadArgument(message="delete")

        #** Create Warning Embed & Check User Is Sure They Want To Delete Their Data **
        WarningEmbed = discord.Embed(title="Are you sure you want to remove your data?",
                                     description=Message,
                                     colour=discord.Colour.gold())
        WarningEmbed.set_footer(text="If you continue using the bot, new data will be stored!")

        #** Create DM Channel With User If One Doesn't Already Exist **
        if ctx.message.author.dm_channel == None:
            await ctx.message.author.create_dm()
        
        #** Try To Send Embed To User & Add Reaction If Successful**
        try:
            SentWarning = await ctx.message.author.dm_channel.send(embed=WarningEmbed)
            await ctx.send("Please check your DMs!")
            await SentWarning.add_reaction(self.Emojis['Tick'])

        #** Raise Error If Can't Send Messages To DM Channel **
        except :
            raise commands.CheckFailure(message="DM")

        #** Check Function To Be Called When Checking If Correct Reaction Has Taken Place **
        def ReactionAdd(Reaction):
            return (Reaction.message_id == SentWarning.id) and (Reaction.user_id != 803939964092940308)

        #** Wait For User To React To Tick & Remove Data When Done So **
        while True:
                Reaction = await self.client.wait_for("raw_reaction_add", check=ReactionAdd)
                if Reaction.event_type == 'REACTION_ADD':
                    if str(Reaction.emoji) == self.Emojis['Tick']:
                        Database.RemoveData(ctx.author.id, Tables)
                        await ctx.message.author.dm_channel.send("All requested data successfully removed!")


#!-------------------SETUP FUNCTION-------------------#


async def setup(client):
    await client.add_cog(AccountCog(client))