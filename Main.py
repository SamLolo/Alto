
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import string
import random
import asyncio
import discord
import mysql.connector
from datetime import datetime
from discord.utils import get
from discord.ext import commands


#!--------------------------------DATABASE CONNECTION-----------------------------------# 


#** Startup Sequence **
print("-----------------------STARTING UP----------------------")
print("Startup Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))

#** Get Connection Details **
Host = os.environ["DATABASE_HOST"]
User = os.environ["DATABASE_USER"]
Password = os.environ["DATABASE_PASS"]

#** Connect To Database **
connection = mysql.connector.connect(host = Host,
                                     database = "Melody",
                                     user = User,
                                     password = Password)

#** Setup Cursor and Output Successful Connection **                  
if connection.is_connected():
    cursor = connection.cursor()
    cursor.execute("SELECT database();")
    Record = cursor.fetchone()
    print("Connected To Database: "+Record[0].title()+"\n")

#** Delete Connection Details **
del Host
del User
del Password


#!-------------------------------FETCH CLASSES-----------------------------#


from Classes.Youtube import YoutubeAPI
from Classes.SpotifyUser import SpotifyUser
from Classes.Database import UserData
from Classes.Music import Music

Youtube = YoutubeAPI()
Database = UserData(cursor, connection)
SongData = Music()


#!--------------------------------DISCORD BOT-----------------------------------# 


#** Creating Bot Client **
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix = "!", case_insensitive=True, intents=intents)

#** Assigning Global Variables **
ActiveStates = {}
NextIcon = None
BackIcon = None
SpotifyIcon = None
AlbumIcon = None
PreviewIcon = None
Tick = None
Cross = None


#!--------------------------------DISCORD EVENTS-----------------------------------# 


@client.event
async def on_ready():
    print("Connection Established!")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=" Beta V1.03"))
    print("Preparing Internal Cache...")
    await client.wait_until_ready()
    print("Bot Is Now Online & Ready!\n")

    #** Import Global Variables **
    global NextIcon
    global BackIcon
    global SpotifyIcon
    global AlbumIcon
    global PreviewIcon
    global Tick
    global Cross

    #** Get Emojis **
    NextIcon = client.get_emoji(817548034732064799)
    BackIcon = client.get_emoji(817548165217386566)
    SpotifyIcon = client.get_emoji(738865749824897077)
    AlbumIcon = client.get_emoji(809904275739639849)
    PreviewIcon = client.get_emoji(810242525247045692)
    Tick = client.get_emoji(738865801964027904)
    Cross = client.get_emoji(738865828648189972)


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        Temp = await ctx.message.channel.send("**Command Not Found!**\nFor a full list of commands, run `!help`")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        Temp = await ctx.message.channel.send("**Missing Paramater `"+str(error.param)+"`!**\nFor a full list of commands & their parameters, run `!help`")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()
        return
    elif isinstance(error, commands.CheckFailure):
        print(error)
        if str(error) == "UserVoice":
            Temp = await ctx.message.channel.send("To use this command, please join a Voice Channel!")
        elif str(error) == "BotVoice":
            Temp = await ctx.message.channel.send("I'm Not Currently Connected!")
        elif str(error) == "SameVoice":
            Temp = await ctx.message.channel.send("You must be in my Voice Channel to use this!")
        elif str(error) == "NotPlaying":
            Temp = await ctx.message.channel.send("I'm Not Currently Playing Anything!")
        else:
            raise error
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()
        return
    else:
        raise error


#!--------------------------------DISCORD COMMANDS-----------------------------------# 


@client.command(aliases=['r', 'recommend', 'suggest', 'songideas'])
async def recommendations(ctx):

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
        Links = str(SpotifyIcon)+" Song: [Spotify]("+Data['external_urls']['spotify']+")\n"
        if Data['preview_url'] != None:
            Links += str(PreviewIcon)+" Song: [Preview]("+Data['preview_url']+")\n"
        Links += str(AlbumIcon)+" Album: ["+Data['album']['name']+"]("+Data['album']['external_urls']['spotify']+")"

        #** Setup Base Embed With Fields For First Song **
        BaseEmbed = discord.Embed(
            title = "Your Recommendations")
        BaseEmbed.set_thumbnail(url=Recommendations[0]['album']['images'][0]['url'])
        BaseEmbed.add_field(name="Song 1:", value=Song, inline=False)
        BaseEmbed.add_field(name="Links:", value=Links, inline=False)
        BaseEmbed.set_footer(text="(1/10) React To See More Recommendations!")

        #** Send First Embed To Discord And Add Reactions **
        Page = await ctx.send(embed=BaseEmbed)
        await Page.add_reaction(BackIcon)
        await Page.add_reaction(NextIcon)
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
                if Reaction.emoji == NextIcon or Reaction.emoji == BackIcon:
                    
                    #** Adjust Current Page Based On Reaction **
                    if CurrentPage == 9 and Reaction.emoji == NextIcon:
                        CurrentPage = 0
                    elif CurrentPage == 0 and Reaction.emoji == BackIcon:
                        CurrentPage = 9
                    else:
                        if Reaction.emoji == NextIcon:
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
                    Links = str(SpotifyIcon)+" Song: [Spotify]("+Data['external_urls']['spotify']+")\n"
                    if Data['preview_url'] != None:
                        Links += str(PreviewIcon)+" Song: [Preview]("+Data['preview_url']+")\n"
                    Links += str(AlbumIcon)+" Album: ["+Data['album']['name']+"]("+Data['album']['external_urls']['spotify']+")"
                    
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


@client.command()
async def reload(ctx, CogName):
    client.reload_extension("Cogs."+CogName)


#!-------------------------------ADD COGS-------------------------------#


client.load_extension('Cogs.Utility')
client.load_extension('Cogs.Music')


#!--------------------------------DISCORD LOOP-----------------------------------# 

#** Connecting To Discord **    
print("--------------------CONNECTING TO DISCORD--------------------")
client.run(os.environ["MUSICA_TOKEN"])