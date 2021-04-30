
#!-------------------------IMPORT MODULES--------------------#


import os
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

        #** Check If User Input is URL and Get Tracks **
        if not(Query.startswith("https://") or Query.startswith("http://")):
            Query = "ytsearch:"+Query
        Results = await Player.node.get_tracks(Query)

        #** Check If Request Successful and Tracks Found **
        if not(Results):
            await ctx.send("**Unexpected Error!**\nIf this error persists, please contact Lolo#6699")
        elif Results['tracks'] == []:
            await ctx.send("**No Songs Found!**\nPlease Check Your Query & Try Again")
        else:

            #** If Result = Playlist, Add All Tracks To Queue **
            if Results['loadType'] == 'PLAYLIST_LOADED':
                for Track in Results['tracks']:
                    Player.add(requester=ctx.author.id, track=Track)
                PlaylistQueued = discord.Embed(
                    title = "Playlist Added To Queue!",
                    description = Results["playlistInfo"]["name"]+" - "+str(len(Results['tracks']))+" Tracks")
                await ctx.send(PlaylistQueued)
            
            #** If Result = Track, Add Track To Queue **
            else:
                print(Results['tracks'][0])
                TrackQueued = discord.Embed(
                    title = "Track Added To Queue!",
                    description = "["+Results['tracks'][0]["info"]["title"]+"]("+Results['tracks'][0]["info"]["uri"]+")")
                Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author.id, recommended=True)
                Player.add(requester=ctx.author.id, track=Track)
                if not(Player.is_playing):
                    await ctx.send(TrackQueued)

            #** Send Embed To Discord, And Play if Player Not Concurrently Playing **
            if not(Player.is_playing):
                await Player.play()


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

        #** Check Volume is Integer & Ensure Voice To Make Sure Client Is Good To Run **
        if Volume.isdecimal():
            if int(Volume) > 100 or int(Volume) < 0:
                await self.ensure_voice(ctx)
        
                #** Get Guild Player & Check If Connected **
                player = self.client.lavalink.player_manager.get(ctx.guild.id)
                if not(player.is_connected):
                    await ctx.send("I'm not currently connected!")

                else:
                    player.set_volume(int(Volume))
                    await ctx.send("Volume Set To "+str(Volume))
            else:
                await ctx.send("Volume must be between 0 & 100!")
        else:
            await ctx.send("Volume must be an integer!")


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(MusicCog(client))
    
    
#!-----------------UNLOAD FUNCTION-------------------#
    
    
def teardown(bot):
    MusicCog.cog_unload()