
#!-------------------------IMPORT MODULES--------------------#


import os
import json
import discord
import random
import string
import asyncio
import mysql.connector
import lavalink
from datetime import datetime
from discord.ext import commands


#!------------------------------IMPORT CLASSES----------------------------------#


from Classes.SpotifyUser import SpotifyUser
from Classes.Database import UserData
from Classes.Music import Music
from Classes.Youtube import YoutubeAPI


#!--------------------------------DATABASE CONNECTION-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Music")
print("Modules Imported: ✓")

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
    print("Database Connected: ✓")

#** Delete Connection Details **
del Host
del User
del Password


#!------------------------INITIALISE CLASSES-------------------#


Youtube = YoutubeAPI()
Database = UserData(cursor, connection)
SongData = Music()


#!------------------------MUSIC COG-----------------------#


class MusicCog(commands.Cog):

    def __init__(self, client):

        #** Assign Discord Bot Client As Class Object **
        self.client = client 

        #** Create Client If One Doesn't Already Exist **
        if not hasattr(client, 'lavalink'):
            client.lavalink = lavalink.Client(803939964092940308)
            client.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'eu', 'default-node')
            client.add_listener(client.lavalink.voice_update_handler, 'on_socket_response')

        #** Add Event Hook **
        lavalink.add_event_hook(self.track_hook)
        print("Lavalink Started: ✓\n")
        
        #** Load Config File **
        with open('Config.json') as ConfigFile:
            Config = json.load(ConfigFile)
            ConfigFile.close()
        self.Emojis = Config['Variables']['Emojis']


    def cog_unload(self):
        
        #** Clear Event Hooks When Cog Unloaded **
        self.client.lavalink._event_hooks.clear()


    async def ensure_voice(self, ctx):
        
        #** Return a Player If One Exists, Otherwise Create One **
        Player = self.client.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))

        #** Check if Author is in Voice Channel **
        if not(ctx.author.voice) or not(ctx.author.voice.channel):
            raise commands.CheckFailure(message="UserVoice")

        #** Check If Bot If Is Connected & Needs to Connect to VC **
        if not Player.is_connected:
            if ctx.command.name in ['play']:

                #** Check If Bot Has Permission To Speak and Raise Error **
                Permissions = ctx.author.voice.channel.permissions_for(ctx.me)
                if not Permissions.connect or not Permissions.speak:
                    raise commands.BotMissingPermissions(["Connect", "Speak"])

                #** Store Channel ID as Value In Player **
                Player.store('Channel', ctx.channel.id)

                #** Join Voice Channel **
                await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
        else:

            #** Check If Author Is In Same VC as Bot **
            if int(Player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CheckFailure(message="BotVoice")


    async def track_hook(self, event):
        
        if isinstance(event, lavalink.events.QueueEndEvent):
            
            #** When Queue Empty, Disconnect From VC **
            Guild = self.client.get_guild(int(event.player.guild_id))
            await Guild.change_voice_state(channel=None)
            
        elif isinstance(event, lavalink.events.TrackStartEvent):
            
            #** Print Out Now Playing Information When New Track Starts **
            Channel = self.client.get_channel(int(event.player.fetch("Channel")))
            print(event.track["title"], event.track["uri"])
            NowPlaying = discord.Embed(
                title = "Now Playing:",
                description = "["+event.track["title"]+"]("+event.track["uri"]+")")
            await Channel.send(embed=NowPlaying)


    @commands.guild_only()
    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query: str):
        
        #** Ensure Voice To Make Sure Client Is Good To Run **
        await self.ensure_voice(ctx)
    
        #** Get Guild Player from Cache & Remove "<>" Embed Characters from Query **
        Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        Query = query.strip('<>')

        #** Check if Input Is A Playlist / Album **
        if not(Query.startswith("https://open.spotify.com/playlist/") or Query.startswith("https://open.spotify.com/album/") or (Query.startswith("https://www.youtube.com/watch?") and "&list=" in Query)):
            
            #? ---------- LOAD TRACK ---------- ?#
            
            #** Check If User Input is URL and If Not Specify YT Search **
            if not(Query.startswith("https://") or Query.startswith("http://")):
                Query = "ytsearch:"+Query

            #** Check If User Input Is A Correct Spotify Track URL & Get Song Data **
            elif Query.startswith("https://open.spotify.com/track/"):
                SpotifyID = (Query.split("/"))[4].split("?")[0]
                if len(SpotifyID) != 22:
                    raise commands.UserInputError(message="Bad URL")
                Song = SongData.GetSongInfo(SpotifyID)

                #** Raise Error if No Song Found Otherwise Reformat Query With New Data **
                if Song == "SongNotFound":
                    raise commands.UserInputError(message="Bad URL")
                Song = Song[SpotifyID]          
                Query = "ytsearch:"+Song['Artists'][0]+" "+Song['Name']

            #** Get Track From Lavalink Player **
            Results = await Player.node.get_tracks(Query)

            #** Check If Request Successful and Tracks Found **
            if not(Results):
                await ctx.send("**Unexpected Error!**\nIf this error persists, please contact Lolo#6699")
            elif Results['tracks'] == []:
                await ctx.send("**No Songs Found!**\nPlease Check Your Query & Try Again")
            else:
                
                #** Add Track To Queue & Confirm Track Added If Track Currently Playing **
                TrackQueued = discord.Embed(
                    title = "Track Added To Queue!",
                    description = "["+Results['tracks'][0]["info"]["title"]+"]("+Results['tracks'][0]["info"]["uri"]+")")
                Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author.id, recommended=True)
                Player.add(requester=ctx.author.id, track=Track)
                if Player.is_playing:
                    await ctx.send(embed=TrackQueued)

                #** Play if Player Not Concurrently Playing **
                if not(Player.is_playing):
                    await Player.play()
        
        else:
            
            #? ---------- lOAD PLAYLIST / ALBUM ---------- ?#
            
            #** Check If User Input Is A Correct Spotify Playlist URL & Get Playlist Data **
            if Query.startswith("https://open.spotify.com/playlist/"):
                PlaylistID = (Query.split("/"))[4].split("?")[0]
                if len(PlaylistID) != 22:
                    raise commands.UserInputError(message="Bad URL")
                Playlist = SongData.GetPlaylistSongs(PlaylistID)

                #** Reformat Query & Get Youtube Result For Song **
                if Playlist == "PlaylistNotFound":
                    raise commands.UserInputError(message="Bad URL")
                ID, Song = Playlist['Tracks'].items()[0]
                Query = "ytsearch:"+Song['Artists'][0]+" "+Song['Name']
                Results = await Player.node.get_tracks(Query)
                
                #** Set Playlist Info **
                Type = "Spotify"
                PlaylistName = Playlist['PlaylistInfo']['Name']
                Length = Playlist['PlaylistInfo']['Length']
                
            #** If Youtube Playlist, Get Youtube Result**
            elif Query.startswith("https://www.youtube.com/watch?"):
                Results = await Player.node.get_tracks(Query)
                
                #** Set Playlist Info **
                Type = "Youtube"
                PlaylistName = Results['playlistInfo']['name']
                Length = len(Results['tracks'])
                
            #** Add First Song To Queue & Play if Not Already Playing **
            Player.add(requester=ctx.author.id, track=Results['tracks'][0])
            PlaylistQueued = discord.Embed(
                title = self.Emojis[Type]+" Playlist Added To Queue!",
                description = PlaylistName+" - "+str(Length)+" Tracks")
            await ctx.send(embed=PlaylistQueued)
            if not(Player.is_playing):
                await Player.play()

#!           if Type == "Spotify":
#!               for i in range(len(Query)-1):
#!                    Results = await Player.node.get_tracks(Query[i+1])
#!                    Player.add(requester=ctx.author.id, track=Results['tracks'][0])


    @commands.guild_only()
    @commands.command(aliases=['s', 'disconnect', 'dc'])
    async def stop(self, ctx):

        #** Ensure Voice To Make Sure Client Is Good To Run **
        await self.ensure_voice(ctx)
        
        #** Get Guild Player & Check If Connected **
        player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not(player.is_connected):
            await ctx.send("I'm not currently connected!")

        #** Check If Command Author is in same VC as Music Bot **
        elif not(ctx.author.voice) or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            await ctx.send("Please join a voice channel to use this command!")

        #** Clear Queue & Stop Playing Music **
        else:
            player.queue.clear()
            await player.stop()
            
            #** Disconnect From VC & Send Message Accordingly **
            await ctx.guild.change_voice_state(channel=None)
            await ctx.send("Disconnected!")

    
    @commands.guild_only()
    @commands.command(aliases=['v'])
    async def volume(self, ctx, Volume):

        #** Check Volume is Integer Between 0 -> 100 & Ensure Voice To Make Sure Client Is Good To Run **
        if Volume.isdecimal():
            if int(Volume) < 100 and int(Volume) > 0:
                await self.ensure_voice(ctx)
        
                #** Get Guild Player & Check If Connected **
                Player = self.client.lavalink.player_manager.get(ctx.guild.id)
                if not(Player.is_connected):
                    await ctx.send("I'm not currently connected!")

                #** If Connected Set Volume & Confirm Volume Change **
                else:
                    await Player.set_volume(int(Volume))
                    await ctx.send("Volume Set To "+str(Volume))

            #** If Issue With Input, Let User Know About The Issue **
            else:
                await ctx.send("Volume must be between 0 & 100!")
        else:
            await ctx.send("Volume must be an integer!")


    @commands.guild_only()
    @commands.command()
    async def skip(self, ctx):
        
        #** Ensure Voice Before Allowing Command To Run **
        await self.ensure_voice(ctx)
        
        #** Get Guild Player & Check If Connected **
        Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not(Player.is_connected):
            await ctx.send("I'm not currently connected!")
        
        #** Check If Player Is Actually Playing A Song **
        elif not(Player.is_playing):
            await ctx.send("I'm not currently playing anything!")

        #** If Connected & Playing Skip Song & Confirm Track Skipped **
        else:
            await Player.skip()
            await ctx.send("Track Skipped!")

    
    @commands.guild_only()
    @commands.command(aliases=['unpause'])
    async def pause(self, ctx):
        
        #** Ensure Voice Before Allowing Command To Run **
        await self.ensure_voice(ctx)
        
        #** Get Guild Player & Check If Connected **
        Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not(Player.is_connected):
            await ctx.send("I'm not currently connected!")
        
        #** Check If Player Is Actually Playing A Song **
        elif not(Player.is_playing) and not(Player.paused):
            await ctx.send("I'm not currently playing anything!")

        #** If Connected & Playing Skip Song & Confirm Track Skipped **
        else:
            if Player.paused:
                await Player.set_pause(False)
                await ctx.send("Player Unpaused!")
            else:
                await Player.set_pause(True)
                await ctx.send("Player Paused!")

    
    @commands.guild_only()
    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        
        #** Ensure Voice Before Allowing Command To Run **
        await self.ensure_voice(ctx)
        
        #** Get Guild Player & Check If Connected **
        Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        if not(Player.is_connected):
            await ctx.send("I'm not currently connected!")

        #** Format Queue List Into String **
        else:
            Queue = ""
            for i in range(len(Player.queue)):
                Queue += str(i+1)+") ["+Player.queue[i]["title"]+"]("+Player.queue[i]["uri"]+")\n"

            #** Format Queue Into Embed & Send Into Discord **
            UpNext = discord.Embed(
                title="Up Next:",
                description = Queue)
            await ctx.send(embed=UpNext)


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(MusicCog(client))
    
    
#!-----------------UNLOAD FUNCTION-------------------#
    
    
def teardown(bot):
    MusicCog.cog_unload()