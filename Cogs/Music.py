
#!-------------------------IMPORT MODULES--------------------#


import os
import json
import discord
import random
import string
import asyncio
import mysql.connector
import lavalink
import requests
from PIL import Image
from io import BytesIO
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
print("Name: Cogs.Music")
print("Modules Imported: ✓")


#!------------------------INITIALISE CLASSES-------------------#


Youtube = YoutubeAPI()
Database = UserData()
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
            
        #** Setup Emojis **
        self.Emojis = Config['Variables']['Emojis']
        self.Emojis["True"] = "✅"
        self.Emojis["False"] = "❌"


    def cog_unload(self):
        
        #** Clear Event Hooks When Cog Unloaded **
        self.client.lavalink._event_hooks.clear()


    async def format_time(self, time):
        
        #** Parse Time Into Days, Hours, Minutes & Seconds **
        Time = lavalink.parse_time(time)
        
        #** Create Strings Of Time In 24 Hour Clock **
        if Time[1] == 0.0:
            return str(int(Time[2]))+":"+str(int(Time[3])).zfill(2)
        else:
            return str(int(Time[1]))+":"+str(int(Time[2])).zfill(2)+":"+str(int(Time[3])).zfill(2)
                

    async def format_artists(self, Artists, IDs):
        
        #** Prepare Empty String & Start Loop Through Artists **
        Formatted = ""
        for i in range(len(Artists)):
            
            #** If First Index, Add Artist & Link **
            if i == 0:
                Formatted += "["+Artists[i]+"](https://open.spotify.com/artist/"+IDs[i]+")"
                
            #** If Not Last Index, Add Comma Before Artist **
            elif i != len(Artists)-1:
                Formatted += ", ["+Artists[i]+"](https://open.spotify.com/artist/"+IDs[i]+")"
                
            #** If Last Index, add & Before Artist **
            else:
                Formatted += " & ["+Artists[i]+"](https://open.spotify.com/artist/"+IDs[i]+")"

        #** Returned Formatted String **
        return Formatted


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

                #** Join Voice Channel **
                await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
                
            #** If Bot Doesn't Need To Connect, Raise Error **
            elif ctx.command.name in ['stop', 'pause', 'skip', 'queue']:
                raise commands.CheckFailure("BotVoice")
                
        else:

            #** Check If Author Is In Same VC as Bot **
            if int(Player.channel_id) != ctx.author.voice.channel.id:
                raise commands.CheckFailure(message="SameVoice")
            
        #** Return Player Accociated With Guild **
        return Player


    async def track_hook(self, event):
        
        if isinstance(event, lavalink.events.QueueEndEvent):
            
            #** When Queue Empty, Disconnect From VC **
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
                    description = self.Emojis['Youtube']+" ["+event.track["title"]+"]("+event.track["uri"]+")\n"
                                +self.Emojis['Spotify']+" ["+event.track.extra['spotify']['name']+"]("+event.track.extra['spotify']['URI']+")")
                NowPlaying.set_thumbnail(url=event.track.extra['spotify']['thumbnail'])
                NowPlaying.add_field(name="By:", value=Artists)

            #** If No Spotify Info, Create Basic Now Playing Embed **
            else:
                NowPlaying = discord.Embed(
                    title = "Now Playing:",
                    description = self.Emojis['Youtube']+" ["+event.track["title"]+"]("+event.track["uri"]+")")

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

            #** Get UserData for Each Member In Database **
            for Member in Voice.members:
                if Member.id != 803939964092940308:
                    User = Database.GetUser(Member.id)

                    #** Add User If DiscordID Doesn't Exist **
                    if not(User):
                        User = Database.AddUser(Member.id)

                    print(User[2])
                    if event.track.extra['spotify'] != {}:
                        Database.AddSongHistory(User[2], "SP-"+event.track.extra['spotify']['ID'])
                    else:
                        ID = event.track.uri.split("=")[1]
                        Database.AddSongHistory(User[2], "YT-"+ID)


    @commands.guild_only()
    @commands.command(aliases=['p'])
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
            
            #** Check If User Input is URL and If Not Specify YT Search **
            if not(Query.startswith("https://") or Query.startswith("http://")):
                Query = "ytsearch:"+Query

                #** Get Track From Lavalink Player & Assign Song Data**
                Results = await Player.node.get_tracks(Query)
                Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, spotify={})
                Youtube.GetVideoInfo(Track)

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
                Search = "ytsearch:"+Song['Artists'][0]+" "+Song['Name']

                #** Get Track From Lavalink Player & Assign Track Data **
                Results = await Player.node.get_tracks(Search)
                Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, spotify={
                    'name': Song['Name'],
                    'ID': SpotifyID,
                    'artists': Song['Artists'],
                    'artistID': Song['ArtistID'],
                    'URI': Query,
                    'thumbnail': Song['Art']})

            #** If Query is Youtube or Soundcloud URL, Get Track From Lavalink Player & Assign Song Data **
            else:
                Results = await Player.node.get_tracks(Query)
                print(Results)
                Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, spotify={})
                Youtube.GetVideoInfo(Track)

            #** Check If Request Successful and Tracks Found **
            if not(Results):
                await ctx.send("**Unexpected Error!**\nIf this error persists, please contact Lolo#6699")
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
                    Search = "ytsearch:"+Song['Artists'][0]+" "+Song['Name']
                    Results = await Player.node.get_tracks(Search)
                    
                    #** Assign Track Data **
                    Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, spotify={
                        'name': Song['Name'],
                        'ID': SpotifyID,
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
                    Info = Youtube.GetVideoInfo(Track)
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
                                    'ID': SpotifyID,
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
    @commands.command(aliases=['disconnect', 'dc'])
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
            
        #** If Music Not Playing, Raise Error **
        else:
            raise commands.CheckFailure(message="NotPlaying")

    
    @commands.guild_only()
    @commands.command(aliases=['v', 'loudness'])
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
    @commands.command(aliases=['unpause'])
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
    @commands.command(aliases=['s' ,'forceskip', 'fs', 'next'])
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
    @commands.command(aliases=['q'])
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
    @commands.command(aliases=['m', 'mix', 'mixup'])
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
    @commands.command(aliases=['repeat'])
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
    @commands.command(aliases=['timeskip'])
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
    @commands.command(aliases=['np', 'now'])
    async def nowplaying(self, ctx):
        
        #** Ensure Cmd Is Good To Run & Get Player **
        Player = await self.ensure_voice(ctx)
        
        #** Create Now Playing Embed **
        NowPlaying = discord.Embed(title = "Now Playing:")
        
        #** Set Author & Footer and Add Position Field **
        NowPlaying.set_author(name="Requested By "+str(Player.current.requester)+"", icon_url=Player.current.requester.avatar_url)
        NowPlaying.add_field(name="Position:", value= await self.format_time(Player.position)+" / "+ await self.format_time(Player.current.duration))
        if Player.queue == []:
            NowPlaying.set_footer(text="Up Next: Nothing")
        else:
            NowPlaying.set_footer(text="Up Next: "+Player.queue[0]["title"])
        
        #** If Track Has Spotify Info, Format List of Artists **
        if Player.current.extra['spotify'] != {}:
            Artists = await self.format_artists(Player.current.extra['spotify']['artists'], Player.current.extra['spotify']['artistID'])

            #** Set Descrition and Thumbnail & Add By Field Above Position Field **
            NowPlaying.description = self.Emojis['Youtube']+" ["+Player.current["title"]+"]("+Player.current["uri"]+")\n"+self.Emojis['Spotify']+" ["+Player.current.extra['spotify']['name']+"]("+Player.current.extra['spotify']['URI']+")"
            NowPlaying.set_thumbnail(url=Player.current.extra['spotify']['thumbnail'])
            NowPlaying.insert_field_at(0, name="By:", value=Artists)

        #** If No Spotify Info, Create Basic Now Playing Embed **
        else:
            
            #** Get Info From Youtube URL **
            VideoID = Player.current.uri.split("=")[1]
            VideoInfo = Youtube.GetVideoInfo(Player.current)[VideoID]
            
            #** Set Descrition and Thumbnail & Add By Field Above Position Field **
            NowPlaying.description = self.Emojis['Youtube']+" ["+Player.current["title"]+"]("+Player.current["uri"]+")"
            NowPlaying.set_thumbnail(url=VideoInfo['Thumbnail'])
            NowPlaying.insert_field_at(0, name="By:", value="["+Player.current.author+"](https://www.youtube.com/channel/"+VideoInfo['ChannelID']+")")
            
        #** Send Embed To Channel Where First Play Cmd Was Ran & Add Reactions**
        Message = await ctx.send(embed=NowPlaying)
        for emoji in ['SkipBack', 'Play', 'Pause', 'SkipForwards']:
            await Message.add_reaction(self.Emojis[emoji])


    @commands.command(aliases=['words'])
    async def lyrics(self, ctx, *args):
        
        #** Get Lyrics For Requested Song **
        Lyrics = SongData.GetLyrics(" ".join(args))
        
        #** Get Most Dominant Colour In Album Art **
        RGB = SongData.GetColour(Lyrics['Meta']['Art'])
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


    @commands.command(aliases=['song', 'i', 'songinfo'])
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
                Description = "**By: **"
                for i in range(len(SongInfo['Artists'])):
                    if i == 0:
                        Description += "["+SongInfo['Artists'][i]+"](https://open.spotify.com/artist/"+SongInfo['ArtistID'][i]+")"
                    elif i != len(SongInfo['Artists'])-1:
                        Description += ", ["+SongInfo['Artists'][i]+"](https://open.spotify.com/artist/"+SongInfo['ArtistID'][i]+")"
                    else:
                        Description += " & ["+SongInfo['Artists'][i]+"](https://open.spotify.com/artist/"+SongInfo['ArtistID'][i]+")"
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
    
    
#!-----------------UNLOAD FUNCTION-------------------#
    
    
def teardown(bot):
    MusicCog.cog_unload()