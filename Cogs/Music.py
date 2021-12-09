
#!-------------------------IMPORT MODULES--------------------#


import os
import json
import discord
import random
import asyncio
import lavalink
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
print("Name: Cogs.Music")
print("Modules Imported: ✓")


#!------------------------INITIALISE CLASSES-------------------#


Database = UserData()
SongData = Music()
Utils = Utility()


#!------------------------MUSIC COG-----------------------#


class MusicCog(commands.Cog, name="Music"):

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
            
        #** Setup Emojis **
        self.Emojis = Config['Variables']['Emojis']
        self.Emojis["True"] = "✅"
        self.Emojis["False"] = "❌"


    def cog_unload(self):
        
        #** Clear Event Hooks When Cog Unloaded **
        self.client.lavalink._event_hooks.clear()
        print("Music Cog Unloaded!")


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
                if not(Permissions.connect) or not(Permissions.speak):
                    raise commands.BotMissingPermissions(["Connect", "Speak"])

                #** Store Channel ID as Value In Player **
                Player.store('Channel', ctx.channel.id)

                #** Store Voice Channel Bot Is Connecting To **
                Player.store('Voice', ctx.author.voice.channel)

                #** Create Empty Users List **
                Player.store('Users', [])

                #** Join Voice Channel **
                await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
                
            #** If Bot Doesn't Need To Connect, Raise Error **
            elif ctx.command.name in ['stop', 'pause', 'skip', 'queue']:
                raise commands.CheckFailure("BotVoice")
                
        else:

            #** Check If Author Is In Same VC as Bot **
            if int(Player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CheckFailure(message="SameVoice")
            
        #** Return Player Associated With Guild **
        return Player


    async def track_hook(self, event):
        
        if isinstance(event, lavalink.events.QueueEndEvent):
            
            #** When Queue Empty, Disconnect From VC **
            print("QueueEndEvent")
            Guild = self.client.get_guild(int(event.player.guild_id))
            await Guild.change_voice_state(channel=None)
            
            #** Remove Old Now Playing Message & Delete Stored Value **
            OldMessage = event.player.fetch('NowPlaying')
            await OldMessage.delete()
            event.player.delete('NowPlaying')
            
        elif isinstance(event, lavalink.events.TrackStartEvent):
            
            #** Get Channel & Print Out Now Playing Information When New Track Starts **
            Channel = self.client.get_channel(int(event.player.fetch("Channel")))
            print(event.track["title"], event.track["uri"])
            
            #** If Track Has Spotify Info, Configure List of Artists **
            if event.track.extra['spotify'] != {}:
                Artists = ""
                for i in range(len(event.track.extra['spotify']['artists'])):
                    if i == 0:
                        Artists += "["+event.track.extra['spotify']['artists'][i]+"](https://open.spotify.com/artist/"+event.track.extra['spotify']['artistID'][i]+")"
                    elif i != len(event.track.extra['spotify']['artists'])-1:
                        Artists += ", ["+event.track.extra['spotify']['artists'][i]+"](https://open.spotify.com/artist/"+event.track.extra['spotify']['artistID'][i]+")"
                    else:
                        Artists += " & ["+event.track.extra['spotify']['artists'][i]+"](https://open.spotify.com/artist/"+event.track.extra['spotify']['artistID'][i]+")"
                
                #** Create Now Playing Embed **
                NowPlaying = discord.Embed(
                    title = "Now Playing:",
                    description = self.Emojis['Soundcloud']+" ["+event.track["title"]+"]("+event.track["uri"]+")\n"
                                +self.Emojis['Spotify']+" ["+event.track.extra['spotify']['name']+"]("+event.track.extra['spotify']['URI']+")")
                NowPlaying.set_thumbnail(url=event.track.extra['spotify']['art'])
                NowPlaying.add_field(name="By:", value=Artists)

            #** If No Spotify Info, Create Basic Now Playing Embed **
            else:
                NowPlaying = discord.Embed(
                    title = "Now Playing:",
                    description = self.Emojis['Soundcloud']+" ["+event.track["title"]+"]("+event.track["uri"]+")")

            #** Fetch Previous Now Playing Message & Check If Exists **
            OldMessage = event.player.fetch('NowPlaying')

            #** Send Embed To Channel Where First Play Cmd Was Ran & Add Reactions**
            Message = await Channel.send(embed=NowPlaying)
            await Message.add_reaction(self.Emojis['SkipBack'])
            await Message.add_reaction(self.Emojis['Play'])
            await Message.add_reaction(self.Emojis['Pause'])
            await Message.add_reaction(self.Emojis['SkipForwards'])

            #** Store Now Playing Message In Player **
            event.player.store('NowPlaying', Message)

            #** Sleep Before Deleting Last Message **
            await asyncio.sleep(0.5)
            if OldMessage is not None:
                
                #** Delete Previous Message If One Found **
                await OldMessage.delete()


            # { Add Track To Listening History For All In VC } #


            #** Wait 5 Seconds & Get Voice Channel **
            await asyncio.sleep(5)
            Voice = event.player.fetch("Voice")

            #** Get List Of Members In Voice Channel **
            UserIDs = []
            for Member in Voice.members:
                if Member.id != 803939964092940308:
                    UserIDs.append(Member.id)
            print(UserIDs)

            #** Check Old Users Stored In Players Are Still Listening, If Not Teardown User Object **
            UserList = event.player.fetch('Users')
            print(UserList)
            for User in UserList:
                print(type(User.userData['discordID']))
                if not(int(User.userData['discordID']) in UserIDs):
                    print(UserIDs)
                    print(User.userData['discordID'])
                    await User.save()
                    UserList.remove(User)
                else:
                    UserIDs.remove(int(User.userData['discordID']))
            
            #** Add New User Objects For Newly Joined Listeners & Store New User List Back In Player **
            for DiscordID in UserIDs:
                UserList.append(Users(self.client, DiscordID))
            event.player.store('Users', UserList)

            #** For All Current Listeners, Add New Song To Their Song History **
            for User in UserList:
                if event.track.extra['spotify'] != {}:
                    await User.incrementHistory("SP-"+event.track.extra['spotify']['ID'])
                else:
                    ID = event.track.uri.split("/")[4]
                    await User.incrementHistory("SC-"+ID)


    @commands.guild_only()
    @commands.command(aliases=['p'], description="Allows you to play music through a Discord Voice Channel from a variety of sources.")
    async def play(self, ctx, *, Query):
        
        MusicVid = 0  # { For Test Purposes }
        
        #** Ensure Voice To Make Sure Client Is Good To Run **
        await self.ensure_voice(ctx)
    
        #** Get Guild Player from Cache & Remove "<>" Embed Characters from Query **
        Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        Query = Query.strip('<>')

        #** Check if Input Is A Playlist / Album **
        if not(Query.startswith("https://open.spotify.com/playlist/") or Query.startswith("https://open.spotify.com/album/") or (Query.startswith("https://www.youtube.com/watch?") and "&list=" in Query)):
            
            #? ---------- LOAD TRACK ---------- ?#
            
            #** Check If User Input is URL and If Not Specify SC Search **
            if not(Query.startswith("https://") or Query.startswith("http://")):
                Query = "scsearch:"+Query

                #** Get Track From Lavalink Player **
                Results = await Player.node.get_tracks(Query)
                print(Results['tracks'][0])
                if len(Results) > 0:
                    URI = Results['tracks'][0]['info']['identifier'].split("/")
                    ID  = URI[4].split(":")[2]
                    print(ID)

                    #** Check If Song Is In Cache **
                    Song = Database.SearchCache('Soundcloud', ID)
                    if Song == None:

                        Songs = SongData.SearchSpotify(Results['tracks'][0]['info']['title'], Results['tracks'][0]['info']['author'])
                        if Songs == "UnexpectedError":
                            Results = None
                        elif Songs == "SongNotFound":
                            Results = []
                        else:

                            print(Songs)

                    Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, spotify={})

            #** Check If User Input Is A Correct Spotify Track URL**
            elif Query.startswith("https://open.spotify.com/track/"):
                SpotifyID = (Query.split("/"))[4].split("?")[0]
                if len(SpotifyID) != 22:
                    raise commands.UserInputError(message="Bad URL")

                #** Get Song From Cache & Check If It Is Cached **
                Song = Database.SearchCache('Spotify', SpotifyID)
                Cached = True
                if Song == None:

                    #** If Not Cached, Get Song Info **
                    Cached = False
                    Song = SongData.GetSongInfo(SpotifyID)

                    #** Raise Error if No Song Found Otherwise Reformat Query With New Data **
                    if Song == "SongNotFound":
                        raise commands.UserInputError(message="Bad URL")
                    Song = Song[SpotifyID]          
                
                #** Format Query With New Data & Get Tracks From Query **
                Search = "scsearch:"+Song['Artists'][0]+" "+Song['Name']
                print(Search)
                Results = await Player.node.get_tracks(Search)

                #** Create Track Object **
                if len(Results) > 0:
                    Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, spotify={
                        'name': Song['Name'],
                        'ID': SpotifyID,
                        'artists': Song['Artists'],
                        'artistID': Song['ArtistID'],
                        'URI': Query,
                        'art': Song['Art'],
                        'album': Song['Album'],
                        'albumID': Song['AlbumID'],
                        'release': Song['Release'],
                        'popularity': Song['Popularity'],
                        'explicit': Song['Explicit'],
                        'preview': Song['Preview']})
                    print(Track)
                    print(Track.duration)

                    #** If Not Cached, Add New Data To Song Cache **
                    if not(Cached):
                        URI = Track.identifier.split("/")
                        ID  = URI[4].split(":")[2]
                        print(ID)
                        Database.AddSongCache(SpotifyID, ID, Song)

            #** If Query is Youtube or Soundcloud URL, Get Track From Lavalink Player & Assign Song Data **
            else:
                Results = await Player.node.get_tracks(Query)
                Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, spotify={})
                print(Track)
                #Youtube.GetVideoInfo(Track)
                UserData.GetSoundcloudTrack(Track.id)

            #** Check If Request Successful and Tracks Found **
            if not(Results):
                await ctx.send("**Unexpected Error!**\nPlease check ur Query & Try Again. If this error persists, contact Lolo#6699")
            elif Results['tracks'] == []:
                await ctx.send("**No Songs Found!**\nPlease Check Your Query & Try Again")
            else:
                
                #** Add Track To Queue & Confirm Track Added If Track Currently Playing **
                Player.add(requester=ctx.author.id, track=Track)
                TrackQueued = discord.Embed(
                    title = "Track Added To Queue!",
                    description = "["+Results['tracks'][0]["info"]["title"]+"]("+Results['tracks'][0]["info"]["uri"]+")")
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
                
                #** Set Playlist Info **
                Type = "Spotify"
                PlaylistName = Playlist['PlaylistInfo']['Name']
                Length = Playlist['PlaylistInfo']['Length']
                
                #**Create Track Iter Object **
                Tracks = iter(Playlist['Tracks'].items())

            #** Check If User Input Is A Correct Spotify Album URL & Get Album Data **
            elif Query.startswith("https://open.spotify.com/album/"):
                AlbumID = (Query.split("/"))[4].split("?")[0]
                if len(AlbumID) != 22:
                    raise commands.UserInputError(message="Bad URL")
                Album = SongData.GetAlbumInfo(AlbumID)

                #** Reformat Query & Get Youtube Result For Song **
                if Album == "PlaylistNotFound":
                    raise commands.UserInputError(message="Bad URL")
                
                #** Set Playlist Info **
                Type = "Spotify"
                PlaylistName = Album['PlaylistInfo']['Name']
                Length = Album['PlaylistInfo']['Length']
                
                #**Create Track Iter Object **
                Tracks = iter(Album['Tracks'].items())
                
            #** If Youtube Playlist, Get Youtube Result**
            elif Query.startswith("https://www.youtube.com/watch?"):
                Results = await Player.node.get_tracks(Query)
                
                #** Set Playlist Info **
                Type = "Youtube"
                PlaylistName = Results['playlistInfo']['name']
                Length = len(Results['tracks'])
                
                #**Create Track Iter Object **
                Tracks = iter(Results['tracks'])
            
            #** For Length Of Playlist, Loop Through Adding Songs **
            Message = True
            while True:
                
                #** If Spotify URL, Get Youtube Track For Song **
                if Query.startswith("https://open.spotify.com/"):
                    ID, Song = next(Tracks, '-1')
                    if str(ID)+str(Song) == '-1':
                        print("Playlist/Album Queued!")
                        break
                    Search = "scsearch:"+Song['Artists'][0]+" "+Song['Name']
                    Results = await Player.node.get_tracks(Search)
                    
                    #** Assign Track Data **
                    Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, spotify={
                        'name': Song['Name'],
                        'ID': ID,
                        'artists': Song['Artists'],
                        'artistID': Song['ArtistID'],
                        'URI': "https://open.spotify.com/track/"+ID,
                        'thumbnail': Song['Art']})
                    
                #** If Youtube Playlist, Get Spotify Info For First Song**
                elif Query.startswith("https://www.youtube.com/watch?"):
                    
                    #** Get Track & Check If All Tracked Queued **
                    Track = next(Tracks, '-1')
                    if str(Track) == '-1':
                        print("Playlist Queued!")
                        break
                    
                    #** Get Video ID From URI **
                    VideoID = Track['info']['uri'].split("=")[1]
                    
                    #** Get Youtube Track Info & Check If Music Video Detected **
                    Info = SongData.GetVideoInfo(Track)
                    if Info[VideoID]['Music']:
                        
                        #** If Music Video Detected, Search For Song On Spotify **
                        SpotifyInfo = SongData.SearchSpotify(Info[VideoID]['Title'], Info[VideoID]['Artist'])
                        

                        if SpotifyInfo == "SongNotFound":
                            print(Info)
                            Track = lavalink.models.AudioTrack(Track, ctx.author, recommended=True, spotify={}, youtube={})
                            
                        #** Get ID of Song From Dictionary **
                        else:
                            for Keys in SpotifyInfo.keys():
                                ID = Keys
                            
                            #** Assign Track Data **
                            SpotifyInfo = SpotifyInfo[ID]
                            Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, 
                                spotify={
                                    'name': SpotifyInfo['Name'],
                                    'ID': ID,
                                    'artists': SpotifyInfo['Artists'],
                                    'artistID': SpotifyInfo['ArtistID'],
                                    'URI': "https://open.spotify.com/track/"+ID,
                                    'thumbnail': SpotifyInfo['Art']},
                                youtube={})

                    #** Assign Track Data **  
                    else:
                        Track = lavalink.models.AudioTrack(Track, ctx.author, recommended=True, spotify={})
                    
                #** Add Song To Queue & Play if Not Already Playing **
                Player.add(requester=ctx.author.id, track=Track)
                if not(Player.is_playing):
                    await Player.play()
                    
                #** Send Embed On First Song Queued **
                if Message == True:
                    PlaylistQueued = discord.Embed(
                        title = self.Emojis[Type]+" Playlist Added To Queue!",
                        description = "["+PlaylistName+"]("+Query+") - "+str(Length)+" Tracks")
                    Message = await ctx.send(embed=PlaylistQueued)

            print(MusicVid) # { For Test Purposes }


    @commands.guild_only()
    @commands.command(aliases=['t'], description="Allows you to play music through a Discord Voice Channel from a variety of sources.")
    async def test(self, ctx, *, Query):

        #** Ensure Voice To Make Sure Client Is Good To Run **
        await self.ensure_voice(ctx)
    
        #** Get Guild Player from Cache & Remove "<>" Embed Characters from Query **
        Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        Query = Query.strip('<>')

        if Query.startswith("https://open.spotify.com/"):

            #** Strip ID From URL **
            SpotifyID = (Query.split("/"))[4].split("?")[0]
            if len(SpotifyID) != 22:
                raise commands.UserInputError(message="Bad URL")
            Cached = False

            #**------------INPUT: TRACK---------------**#

            if "track" in Query:

                #** Get Song From Cache & Check If It Is Cached **
                SongInfo = Database.SearchCache('Spotify', SpotifyID)
                if SongInfo == None:

                    #** If Not Cached, Get Song Info **
                    SongInfo = SongData.GetSongInfo(SpotifyID)
                    PlaylistInfo = None

                    #** Raise Error if No Song Found Otherwise Reformat Query With New Data **
                    if SongInfo == "SongNotFound":
                        raise commands.UserInputError(message="Bad URL")
                
                else:
                    Cached = True

            #**------------INPUT: PLAYLIST---------------**#

            elif "playlist" in Query:

                #** Get Playlist Info From Spotify Web API **
                SongInfo = SongData.GetPlaylistSongs(SpotifyID)
                if SongInfo == "PlaylistNotFound":
                    raise commands.UserInputError(message="Bad URL")

                PlaylistInfo = SongInfo[SpotifyID]
                SongInfo = SongInfo['Tracks']
                Type = "Playlist"

            #**------------INPUT: ALBUM---------------**#

            elif "album" in Query:

                #** Get Album Info From Spotify Web API **
                SongInfo = SongData.GetAlbumInfo(SpotifyID)
                if SongInfo == "PlaylistNotFound":
                    raise commands.UserInputError(message="Bad URL")

                PlaylistInfo = SongInfo[SpotifyID]
                SongInfo = SongInfo['Tracks']
                Type = "Album"

            #**-----------QUEUE SONGS--------------**#
            
            #** Iterate Though List Of Spotify ID's **#
            for SpotifyID in list(SongInfo.keys()):
                
                #** Search SoundCloud For Track **
                Info = SongInfo[SpotifyID]
                Search = "scsearch:"+Info['Artists'][0]+" "+Info['Name']
                Results = await Player.node.get_tracks(Search)

                #** Create Track Object **
                if len(Results) > 0:
                    Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, spotify={
                        'name': Info['Name'],
                        'ID': SpotifyID,
                        'artists': Info['Artists'],
                        'artistID': Info['ArtistID'],
                        'URI': Query,
                        'art': Info['Art'],
                        'album': Info['Album'],
                        'albumID': Info['AlbumID'],
                        'release': Info['Release'],
                        'popularity': Info['Popularity'],
                        'explicit': Info['Explicit'],
                        'preview': Info['Preview']})
                    print(Track)
                    print(Track.duration)
                
                #** If Track Duration = 30s, Inform It's Only A Preview **
                if Track.duration == 3000:
                    await ctx.send("We could only fetch a preview for the requested song!")

                #** Send Queued Embed **
                if list(SongInfo.keys()).index(SpotifyID) == 0:
                    if PlaylistInfo == None:
                        if len(Info['Artists']) > 1:
                            Artists = Utils.format_artists(Info['Artists'], Info['ArtistID'])
                        Queued = discord.Embed(
                            title = self.Emojis["Spotify"]+" Track Added To Queue!",
                            description = "["+Info['Name']+"]("+Query+") \nBy: "+Artists)
                    else:
                        Queued = discord.Embed(
                            title = self.Emojis["Spotify"]+" "+Type+" Added To Queue!",
                            description = "["+PlaylistInfo['Name']+"]("+Query+") - "+str(PlaylistInfo['Length'])+" Tracks")
                    await ctx.send(embed=Queued)

                #**-----------------ADD TO CACHE----------------**#

                if not(Cached):
                    
                    #** Create Song Info Dict & Send To Database **
                    URI = Track.identifier.split("/")
                    ID  = URI[4].split(":")[2]
                    RGB = Utils.get_colour(Info['Art'])
                    ToCache = {'SpotifyID': SpotifyID, 'SoundcloudID': ID, 'SoundcloudURL': Track.uri, 'Colour': RGB}
                    ToCache = ToCache.update(Info)
                    Database.AddFullSongCache(ToCache)

                #**-----------------PLAY / ADD TO QUEUE--------------**#

                #** Add Song To Queue & Play if Not Already Playing **
                Player.add(requester=ctx.author.id, track=Track)
                if not(Player.is_playing):
                    await Player.play()


    @commands.guild_only()
    @commands.command(aliases=['disconnect', 'dc'], description="Stops any currently playing audio in your voice channel.")
    async def stop(self, ctx):

        #** Ensure Voice To Make Sure Client Is Good To Run & Get Guild Player**
        Player = await self.ensure_voice(ctx)

        #** Clear Queue & Stop Playing Music If Music Playing**
        if Player.is_playing:
            Player.queue.clear()
            await Player.stop()
            
            #** Disconnect From VC & Send Message Accordingly **
            await ctx.guild.change_voice_state(channel=None)
            await ctx.send("Disconnected!")

            #** Remove Old Now Playing Message & Delete Stored Value **
            OldMessage = Player.fetch('NowPlaying')
            await OldMessage.delete()
            Player.delete('NowPlaying')

            #** Save All Current Users Stored In Player To Database **
            UserList = Player.fetch('Users')
            for User in UserList:
                await User.save()

            #** Remove Player From Cache **
            self.client.lavalink.player_manager.remove(ctx.guild.id)
            
        #** If Music Not Playing, Raise Error **
        else:
            raise commands.CheckFailure(message="NotPlaying")


    @commands.guild_only()
    @commands.command(aliases=['v', 'loudness'], description="Adjusts the volume of the audio player between 0% and 100%.")
    async def volume(self, ctx, *args):

        #** Ensure Voice To Make Sure Client Is Good To Run & Get Player **
        Player = await self.ensure_voice(ctx)
        
        #** If No Volume Change, Return Current Volume **
        if not(args):
            await ctx.send("**Current Volume:** "+str(Player.volume)+"%")

        #** Get New Volume From Args **
        else:
            Volume = args[0]
            
            #** Check Volume is Integer Between 0 -> 100 **
            if Volume.isdecimal():
                if int(Volume) <= 100 and int(Volume) > 0:

                    #** If Connected Set Volume & Confirm Volume Change **
                    await Player.set_volume(int(Volume))
                    await ctx.send("Volume Set To "+str(Volume)+"%")

                #** If Issue With Input, Let User Know About The Issue **
                else:
                    await ctx.send("Volume must be between 1 & 100!")
            else:
                await ctx.send("Volume must be an integer!")


        @commands.guild_only()
        @commands.command(aliases=['s' ,'forceskip', 'fs', 'next'])
        async def skip(self, ctx):
            
            #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
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
                await ctx.send("Skipped Track: "+Player.current["title"])
                await Player.skip()

    
    @commands.guild_only()
    @commands.command(aliases=['unpause'], description="Pauses or unpauses the audio player.")
    async def pause(self, ctx):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(ctx)
        
        #** Check If Player Is Actually Playing A Song **
        if not(Player.is_playing):
            raise commands.CheckFailure(message="NotPlaying")

        #** If Connected & Playing Skip Song & Confirm Track Skipped **
        else:
            print(Player.paused)
            await Player.set_pause(not(Player.paused))
            if Player.paused:
                await ctx.send("Player Paused!")
            else:
                await ctx.send("Player Unpaused!")

    
    @commands.guild_only()
    @commands.command(aliases=['s' ,'forceskip', 'fs', 'next'], description="Skips the currently playing song and plays the next song in th queue.")
    async def skip(self, ctx):

        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(ctx)
        
        #** Check If Player Is Actually Playing A Song **
        if not(Player.is_playing):
            raise commands.CheckFailure(message="NotPlaying")

        #** If Connected & Playing Skip Song & Confirm Track Skipped **
        else:
            await ctx.send("**Skipped Track:** "+Player.current["title"])
            await Player.skip()
    
    
    @commands.guild_only()
    @commands.command(aliases=['q'], description="Displays the bots current queue of songs.")
    async def queue(self, ctx):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(ctx)

        #** Format Queue List Into String **
        if Player.queue != []:
            Queue = ""
            for i in range(len(Player.queue)):
                Queue += str(i+1)+") ["+Player.queue[i]["title"]+"]("+Player.queue[i]["uri"]+")\n"

            #** Format Queue Into Embed & Send Into Discord **
            UpNext = discord.Embed(
                title = "Up Next:",
                description = Queue)
            UpNext.set_footer(text="Shuffle: "+self.Emojis[str(Player.shuffle)]+"  Loop: "+self.Emojis[str(Player.repeat)])
            await ctx.send(embed=UpNext)
        
        #** If Queue Empty, Just Send Plain Text **
        else:
            await ctx.send("Queue Is Currently Empty!")


    @commands.guild_only()
    @commands.command(aliases=['m', 'mix', 'mixup'], description="Shuffles the playback of songs in the queue.")
    async def shuffle(self, ctx):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(ctx)

        #** Enable / Disable Shuffle Mode **
        Player.shuffle = not(Player.shuffle)
        if Player.shuffle:
            await ctx.send("Player Shuffled!")
        else:
            await ctx.send("Player No Longer Shuffled!")


    @commands.guild_only()
    @commands.command(aliases=['repeat'], description="Loops the current song until the command is ran again.")
    async def loop(self, ctx):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(ctx)

        #** Enable / Disable Repeat Mode **
        Player.repeat = not(Player.repeat)
        if Player.repeat:
            await ctx.send("Current Track Now Looping!")
        else:
            await ctx.send("Track Loop Disabled!")


    @commands.guild_only()
    @commands.command(aliases=['timeskip'], description="Skips forward or backwards in time in the currently playing song.")
    async def seek(self, ctx, time):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(ctx)

        #** Check If Track Seeable **
        if Player.current.is_seekable:

            #** Check If Seek Time Is Within Current Track **
            if int(time)*1000 < int(Player.current.duration - Player.position):

                #** Seek Forward Specified Time in ms **
                await Player.seek(Player.position + float(int(time)*1000))

                #** Let User Know How Much Time Has Been Skipped **
                await ctx.send("Skipped Forwards "+time+" Seconds!")

            #** Otherwise Skip Track**
            else:
                await Player.skip()

                #** Let User Know Track Has Been Skipped **
                await ctx.send("Current Track Skipped!")

        #** Let User Know Audio Isn't Seekable **
        else:
            await ctx.send(Player.current['title']+" is not seekable!")
    

    @commands.guild_only()
    @commands.command(aliases=['np', 'now'], description="Displays information about the currently playing song.")
    async def nowplaying(self, ctx):
        
        #** Ensure Cmd Is Good To Run & Get Player **
        Player = await self.ensure_voice(ctx)
        
        #** Create Now Playing Embed **
        NowPlaying = discord.Embed(title = "Now Playing:")
        
        #** Set Author & Footer and Add Position Field **
        NowPlaying.set_author(name="Requested By "+str(Player.current.requester)+"", icon_url=Player.current.requester.avatar_url)
        NowPlaying.add_field(name="Position:", value= await Utils.format_time(Player.position)+" / "+ await Utils.format_time(Player.current.duration))
        if Player.queue == []:
            NowPlaying.set_footer(text="Up Next: Nothing")
        else:
            NowPlaying.set_footer(text="Up Next: "+Player.queue[0]["title"])
        
        #** If Track Has Spotify Info, Format List of Artists **
        if Player.current.extra['spotify'] != {}:
            Artists = await Utils.format_artists(Player.current.extra['spotify']['artists'], Player.current.extra['spotify']['artistID'])

            #** Set Descrition and Thumbnail & Add By Field Above Position Field **
            NowPlaying.description = self.Emojis['Soundcloud']+" ["+Player.current["title"]+"]("+Player.current["uri"]+")\n"+self.Emojis['Spotify']+" ["+Player.current.extra['spotify']['name']+"]("+Player.current.extra['spotify']['URI']+")"
            NowPlaying.set_thumbnail(url=Player.current.extra['spotify']['art'])
            NowPlaying.insert_field_at(0, name="By:", value=Artists)

        #** If No Spotify Info, Create Basic Now Playing Embed **
        else:
            
            #** Get Info From Youtube URL **
            VideoID = Player.current.uri.split("=")[1]
            VideoInfo = SongData.GetVideoInfo(Player.current)[VideoID]
            
            #** Set Descrition and Thumbnail & Add By Field Above Position Field **
            NowPlaying.description = self.Emojis['Soundcloud']+" ["+Player.current["title"]+"]("+Player.current["uri"]+")"
            NowPlaying.set_thumbnail(url=VideoInfo['Thumbnail'])
            NowPlaying.insert_field_at(0, name="By:", value="["+Player.current.author+"](https://www.youtube.com/channel/"+VideoInfo['ChannelID']+")")
            
        #** Send Embed To Channel Where First Play Cmd Was Ran & Add Reactions**
        Message = await ctx.send(embed=NowPlaying)
        for emoji in ['SkipBack', 'Play', 'Pause', 'SkipForwards']:
            await Message.add_reaction(self.Emojis[emoji])


    @commands.command(aliases=['words'], description="Displays a specified songs lyrics.")
    async def lyrics(self, ctx, *args):
        
        #** Get Lyrics For Requested Song **
        Lyrics = SongData.GetLyrics(" ".join(args))
        
        #** Get Most Dominant Colour In Album Art **
        RGB = Utils.GetColour(Lyrics['Meta']['Art'])
        Colour = discord.Colour.from_rgb(RGB[0], RGB[1], RGB[2])
        
        #** Create Lyric Embed **
        LyricEmbed = discord.Embed(
            title = Lyrics['Meta']['Title'],
            description = "**By: **["+Lyrics['Meta']['Artist']+"](https://open.spotify.com/track/"+Lyrics['Spotify']['ArtistID'][0]+")\n\n"+Lyrics['Lyrics'],
            colour = Colour)
        LyricEmbed.set_thumbnail(url=Lyrics['Meta']['Art'])
        
        #** Get Embed Length (Max 6000) For Test Purposes **
        print(len(LyricEmbed))
        
        #** Return Lyrics To User **
        await ctx.send(embed=LyricEmbed)


    @commands.command(aliases=['song', 'i', 'songinfo'], description="Displays both basic and more indepth information about a specified song.")
    async def info(self, ctx, SpotifyID):

        #** Format Input Data and Check To Make Sure It's A Valid ID **
        print(ctx.author.name)
        print(SpotifyID)
        Error = False
        if SpotifyID.startswith("https://open.spotify.com/track/"):
            SpotifyID = (SpotifyID.split("/"))[4].split("?")[0]
        if len(SpotifyID) == 22:

            #** Get Song Details And Check If Song Is Found **
            SongInfo = SongData.GetSongDetails(SpotifyID)
            if SongInfo != "SongNotFound":

                #** Format Returned Data Ready To Be Put Into The Embeds **
                SongInfo = SongInfo[SpotifyID]
                Description = "**By: **" + Utils.format_artists(SongInfo['Artists'], SongInfo['ArtistID'])
                Links = self.Emojis['Spotify']+" Song: [Spotify](https://open.spotify.com/track/"+SpotifyID+")\n"
                if SongInfo['Preview'] != None:
                    Links += self.Emojis['Preview']+" Song: [Preview]("+SongInfo['Preview']+")\n"
                if SongInfo['AlbumID'] != None:
                    Links += self.Emojis['Album']+" Album: ["+SongInfo['Album']+"](https://open.spotify.com/album/"+SongInfo['AlbumID']+")"
                else:
                    Links += self.Emojis['Album']+" Album: "+SongInfo['Album']
                
                #** Setup Embed With Basic Song Information **
                Basic = discord.Embed(
                    title=SongInfo['Name'], 
                    description=Description)
                if SongInfo['Art'] != None:
                    Basic.set_thumbnail(url=SongInfo['Art'])
                Basic.set_footer(text="(1/2) React To See Advanced Song Information!")
                Basic.add_field(name="Length:", value=SongInfo['Duration'], inline=False)
                Basic.add_field(name="Released:", value=SongInfo['Release'], inline=True)
                Basic.add_field(name="Genre:", value=SongInfo['Genre'].title(), inline=True)
                Basic.add_field(name="Links:", value=Links, inline=False)
                
                #** Setup Embed With Advanced Song Information **
                Advanced = discord.Embed(
                    title=SongInfo['Name'], 
                    description=Description)
                if SongInfo['Art'] != None:
                    Advanced.set_thumbnail(url=SongInfo['Art'])
                Advanced.set_footer(text="(2/2) React To See Basic Song Information!")
                Advanced.add_field(name="Popularity:", value=SongInfo['Popularity'], inline=True)
                Advanced.add_field(name="Explicit:", value=SongInfo['Explicit'], inline=True)
                Advanced.add_field(name="Tempo:", value=SongInfo['Tempo'], inline=True)
                Advanced.add_field(name="Key:", value=SongInfo['Key'], inline=True)
                Advanced.add_field(name="Beats Per Bar:", value=SongInfo['BeatsPerBar'], inline=True)
                Advanced.add_field(name="Mode:", value=SongInfo['Mode'], inline=True)

                #** Send First Embed To Discord And Add Reactions **
                Page = await ctx.send(embed=Basic)
                await Page.add_reaction(self.Emojis['Back'])
                await Page.add_reaction(self.Emojis['Next'])
                CurrentPage = 1

                #** Check Function To Be Called When Checking If Correct Reaction Has Taken Place **
                def ReactionAdd(Reaction):
                    return (Reaction.message_id == Page.id) and (Reaction.user_id != 803939964092940308)

                #** Watches For Reactions, Checks Them And Then Acts Accordingly **
                while True:
                    Reaction = await self.client.wait_for("raw_reaction_add", check=ReactionAdd)
                    if Reaction.event_type == 'REACTION_ADD':
                        if str(Reaction.emoji) == self.Emojis['Next'] or str(Reaction.emoji) == self.Emojis['Back']:
                            await Page.remove_reaction(Reaction.emoji, Reaction.member)
                            if CurrentPage == 1:
                                await Page.edit(embed=Advanced)
                                CurrentPage = 2
                            else:
                                await Page.edit(embed=Basic)
                                CurrentPage = 1
                        else:
                            await Page.remove_reaction(Reaction.emoji, Reaction.member)
        
            #** Output Song Not Found If Music.GetSongDetails() Returns Song Not Found **
            else:
                Error = True
        else:
            Error = True

        #** Output Error To User **
        if Error == True:
            Temp = await ctx.send("**Invalid SongID!**\nFor help with this command, run `!help info`")
            await asyncio.sleep(5)
            await ctx.message.delete()
            await Temp.delete()


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(MusicCog(client))