
#!-------------------------IMPORT MODULES--------------------#


import json
import copy
import discord
import random
import asyncio
import lavalink
from datetime import datetime
from discord.ext import commands


#!------------------------------IMPORT CLASSES----------------------------------#


from Classes.Users import Users
from Classes.Database import UserData
from Classes.MusicUtils import Music
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
        self.Pagination = self.client.get_cog("EmbedPaginator")

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

        #** If Command Needs User To Be In VC, Check if Author is in Voice Channel **
        if not(ctx.command.name in ['queue', 'nowplaying']):
            if not(ctx.author.voice) or not(ctx.author.voice.channel):
                raise commands.CheckFailure(message="UserVoice")
        
        #** Return a Player If One Exists, Otherwise Create One **
        Player = self.client.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))

        #** Check If Bot If Is Connected & Needs to Connect to VC **
        if not(Player.is_connected):
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
                Player.store('Users', {})

                #** Join Voice Channel **
                await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
                
            #** If Bot Doesn't Need To Connect, Raise Error **
            elif ctx.command.name in ['stop', 'pause', 'skip', 'queue', 'seek', 'nowplaying', 'loop']:
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

            #** Save All Current Users Stored In Player To Database **
            UserDict = event.player.fetch('Users')
            for User in UserDict.values():
                await User.save()
            
        elif isinstance(event, lavalink.events.TrackStartEvent):
            
            #** Get Channel & Print Out Now Playing Information When New Track Starts **
            print("TrackStartEvent")
            Timestamp = datetime.now()
            Channel = self.client.get_channel(int(event.player.fetch("Channel")))
            print(event.track["title"], event.track["uri"])
            
            #** Create Now Playing Embed **
            NowPlaying = discord.Embed(title = "Now Playing:")

            #** Add Up Next To Footer Of Embed **
            if event.player.queue == []:
                NowPlaying.set_footer(text="Up Next: Nothing")
            else:
                NowPlaying.set_footer(text="Up Next: "+event.player.queue[0]["title"])

            #** If Not A Stream, Add Position Field & Source Of Music **
            if not(event.track.stream):
                NowPlaying.set_author(name="Playing From Soundcloud", icon_url="https://cdn.discordapp.com/emojis/897135141040832563.png?size=96&quality=lossless")
                NowPlaying.add_field(name="Position:", value = "0:00 / "+ Utils.format_time(event.track.duration))
                
                #** If Track Has Spotify Info, Format List of Artists **
                if event.track.extra['spotify'] != {}:
                    Artists = Utils.format_artists(event.track.extra['spotify']['artists'], event.track.extra['spotify']['artistID'])

                    #** Set Descrition and Thumbnail & Add By Field Above Position Field **
                    NowPlaying.description = self.Emojis['Soundcloud']+" ["+event.track["title"]+"]("+event.track["uri"]+")\n"+self.Emojis['Spotify']+" ["+event.track.extra['spotify']['name']+"]("+event.track.extra['spotify']['URI']+")"
                    NowPlaying.set_thumbnail(url=event.track.extra['spotify']['art'])
                    NowPlaying.insert_field_at(0, name="By:", value=Artists)

                #** If No Spotify Info, Create Basic Now Playing Embed **
                else:
                    #** Set Descrition and Thumbnail & Add By Field Above Position Field **
                    NowPlaying.description = self.Emojis['Soundcloud']+" ["+event.track["title"]+"]("+event.track["uri"]+")"
                    NowPlaying.insert_field_at(0, name="By:", value="["+event.track.author+"]("+event.track.extra["artistURI"]+")")
            
            #** If Track Is A Stream, Add Appropriate Information For A Stream **
            else:
                NowPlaying.set_author(name="Playing From "+event.track.extra['Source'].title()+" Stream")
                NowPlaying.description = "["+event.track['title']+"]("+event.track["uri"]+")"
                NowPlaying.add_field(name="By: ", value=event.track['author'])
                NowPlaying.add_field(name="Duration: ", value="N/A")

            #** Add Requester To Embed & Send Embed To Channel Where First Play Cmd Was Ran **
            NowPlaying.add_field(name="Requested By: ", value=str(event.track.requester), inline=False)
            Message = await Channel.send(embed=NowPlaying)

            #** Fetch Previous Now Playing Message & Store New Now Playing Message In Player **
            OldMessage = event.player.fetch('NowPlaying')
            event.player.store('NowPlaying', Message)

            #** Sleep Before Deleting Last Message If One Found **
            await asyncio.sleep(0.5)
            if OldMessage != None:
                await OldMessage.delete()

            #**-------------Add Listening History-------------**#

            #** Check If Track Should Be Added To History & Fetch Voice Channel**
            if not(event.track.extra['IgnoreHistory']):
                await asyncio.sleep(5)
                Voice = event.player.fetch("Voice")

                #** Get List Of Members In Voice Channel **
                UserIDs = []
                for Member in Voice.members:
                    if Member.id != 803939964092940308:
                        UserIDs.append(Member.id)

                #** Check Old Users Stored In Players Are Still Listening, If Not Teardown User Object **
                UserDict = event.player.fetch('Users')
                for DiscordID, User in UserDict.items():
                    if not(int(DiscordID) in UserIDs):
                        await User.save()
                        UserDict.remove(User)
                    else:
                        UserIDs.remove(int(DiscordID))
                
                #** Add New User Objects For Newly Joined Listeners & Store New User Dict Back In Player **
                for DiscordID in UserIDs:
                    UserDict[str(DiscordID)] = Users(self.client, DiscordID)
                event.player.store('Users', UserDict)

                #** Format Current Track Data Into Dict To Be Added To History **
                URI = event.track['identifier'].split("/")
                ID  = URI[4].split(":")[2]
                TrackData = {"ID": ID,
                             "ListenedAt": Timestamp,
                             "SpotifyID": None,
                             "Name": event.track['title'],
                             "Artists": [event.track['author']],
                             "URI": event.track['uri']}
                if event.track.extra['spotify'] != {}:
                    TrackData['SpotifyID'] = event.track.extra['spotify']['ID']
                    TrackData['Name'] = event.track.extra['spotify']['name']
                    TrackData['Artists'] = event.track.extra['spotify']['artists']
                    TrackData['ArtistIDs'] = event.track.extra['spotify']['artistID']
                    TrackData['Popularity'] = event.track.extra['spotify']['popularity']
                
                #** For All Current Listeners, Add New Song To Their Song History **
                for User in UserDict.values():
                    await User.incrementHistory(TrackData)


    @commands.guild_only()
    @commands.command(aliases=['p'], 
                      description="Allows you to play music through a Discord Voice Channel from a variety of sources.", 
                      usage="!play <song>", 
                      brief="You must be in a voice channel to use this command!",
                      help="`Possible Inputs For <song>:`\n- Text Search For Song\n- Soundcloud Track URL\n- Soundcloud Playlist URL\n- Spotify Track URL\n"+
                           "- Spotify Playlist URL**\* **\n- Spotify Album URL\n- HTTP Audio Stream URL\n**\* ** *Private playlists require linking Spotify to Discord using `!link` first!*")
    async def play(self, ctx, *, Query):

        #** Ensure Voice To Make Sure Client Is Good To Run **
        await self.ensure_voice(ctx)
    
        #** Get Guild Player from Cache & Remove "<>" Embed Characters from Query **
        Player = self.client.lavalink.player_manager.get(ctx.guild.id)
        Query = Query.strip('<>')

        #** Check If Query Is A Spotify URL **
        if Query.startswith("https://open.spotify.com/"):

            #** Strip ID From URL **
            SpotifyID = (Query.split("/"))[4].split("?")[0]
            if len(SpotifyID) != 22:
                raise commands.CheckFailure(message="SongNotFound")
            Cached = False

            #**------------INPUT: TRACK---------------**#

            if "track" in Query:

                #** Get Song From Cache & Check If It Is Cached **
                SongInfo = Database.SearchCache(SpotifyID)
                PlaylistInfo = None
                if SongInfo == None:

                    #** If Not Cached, Get Song Info **
                    SongInfo = SongData.GetSongInfo(SpotifyID)

                    #** Raise Error if No Song Found Otherwise Reformat Query With New Data **
                    if SongInfo == "SongNotFound":
                        raise commands.CheckFailure(message="SongNotFound")
                    elif SongInfo == "UnexpectedError":
                        raise commands.CheckFailure(message="UnexpectedError")
                
                else:
                    Cached = True

            #**------------INPUT: PLAYLIST---------------**#

            elif "playlist" in Query:

                #** Get Playlist Info From Spotify Web API **
                SongInfo = SongData.GetPlaylistSongs(SpotifyID)

                #** Raise Error If Playlist Not Found or Unexpected Error Occurs **
                if SongInfo == "PlaylistNotFound":
                    raise commands.CheckFailure(message="SongNotFound")
                elif SongInfo == "UnexpectedError":
                    raise commands.CheckFailure(message="UnexpectedError")

                #** Setup Playlist & Song Info; & Set Type **
                PlaylistInfo = SongInfo['PlaylistInfo']
                SongInfo = SongInfo['Tracks']
                Type = "Playlist"

            #**------------INPUT: ALBUM---------------**#

            elif "album" in Query:

                #** Get Album Info From Spotify Web API **
                SongInfo = SongData.GetAlbumInfo(SpotifyID)
                
                #** Raise Error If Album Not Found Or Unexpected Error **
                if SongInfo == "AlbumNotFound":
                    raise commands.CheckFailure(message="SongNotFound")
                elif SongInfo == "UnexpectedError":
                    raise commands.CheckFailure(message="UnexpectedError")

                #** Setup Playlist(Album) & Song Info; & Set Type **
                PlaylistInfo = SongInfo['PlaylistInfo']
                SongInfo = SongInfo['Tracks']
                Type = "Album"

            #**-----------QUEUE SONGS--------------**#
            
            #** Iterate Though List Of Spotify ID's **#
            for SpotifyID in list(SongInfo.keys()):
                
                #** Search SoundCloud For Track **
                Info = SongInfo[SpotifyID]
                Search = "scsearch:"+Info['Artists'][0]+" "+Info['Name']
                Results = await Player.node.get_tracks(Search)

                #** Create Track Object If Results Found **
                if len(Results) > 0:
                    ArtistURI = "/".join(Results['tracks'][0]['info']['uri'].split("/")[:4])
                    Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, IgnoreHistory=False, artistURI=ArtistURI,
                            spotify={'name': Info['Name'],
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
                
                #** Raise Song Not Found Error If Song Couldn't Be Found On Soundcloud **
                else:
                    raise commands.CheckFailure(message="SongNotFound")
                
                #** If Track Duration = 30000ms(30s), Inform It's Only A Preview **
                if Track.duration == 30000:
                    await ctx.send("**Sorry, we could only fetch a preview for `"+Info['Name']+"`!**")

                #** Format & Send Queued Embed If First Song In List To Queue **
                if list(SongInfo.keys()).index(SpotifyID) == 0:
                    if PlaylistInfo == None:
                        Artists = Utils.format_artists(Info['Artists'], Info['ArtistID'])
                        Queued = discord.Embed(
                            title = self.Emojis["Spotify"]+" Track Added To Queue!",
                            description = "["+Info['Name']+"]("+Query+") \nBy: "+Artists)
                    else:
                        Queued = discord.Embed(
                            title = self.Emojis["Spotify"]+" "+Type+" Added To Queue!",
                            description = "["+PlaylistInfo['Name']+"]("+Query+") - "+str(PlaylistInfo['Length'])+" Tracks")
                    Queued.set_footer(text="Requested By "+ctx.author.display_name+"#"+str(ctx.author.discriminator))
                    await ctx.send(embed=Queued)

                #**-----------------PLAY / ADD TO QUEUE--------------**#

                #** Add Song To Queue & Play if Not Already Playing **
                Player.add(requester=ctx.author.id, track=Track)
                if not(Player.is_playing):
                    await Player.play()

                #**-----------------ADD TO CACHE----------------**#

                #** Check If Data Needs To Be Cached **
                if not(Cached):
                    
                    #** Get SoundcloudID & Primary Colour Of Album Art **
                    URI = Track.identifier.split("/")
                    ID  = URI[4].split(":")[2]
                    RGB = Utils.get_colour(Info['Art'])
                    
                    #** Create Song Info Dict With Formatted Data & Send To Database **
                    ToCache = {'SpotifyID': SpotifyID, 'SoundcloudID': ID, 'SoundcloudURL': Track.uri, 'Colour': RGB}
                    ToCache.update(Info)
                    if ToCache['Explicit'] == 'N/A':
                        ToCache['Explicit'] = None
                    if ToCache['Popularity'] == 'N/A':
                        ToCache['Popularity'] = None
                    Database.AddFullSongCache(ToCache)
        
        #** If Query Is From Soundcloud Or Is A Plain Text Input **
        elif Query.startswith("https://soundcloud.com/") or not(Query.startswith("https://") or Query.startswith("http://")):

             #**------------INPUT: TEXT, TRACK OR PLAYLIST---------------**#

            #** Get Track(s) From Lavalink Player **
            if not(Query.startswith("https://")):
                Results = await Player.node.get_tracks("scsearch:"+Query)
                Results['tracks'] = [Results['tracks'][0]]
            else:
                Results = await Player.node.get_tracks(Query)

            #**---------------SEARCH CACHE------------**#

            #** Check If Results Found & Iterate Through Results **
            if len(Results['tracks']) > 0:
                for ResultTrack in Results['tracks']:
                    URI = ResultTrack['info']['identifier'].split("/")
                    ID  = URI[4].split(":")[2]
                    ArtistURI = "/".join(ResultTrack['info']['uri'].split("/")[:4])
                    Cached = False

                    #** Check If Song Is In Cache & Set Cache To True If Data Found **
                    Spotify = Database.SearchCache(ID)
                    if Spotify != None:
                        SpotifyID = list(Spotify.keys())[0]
                        Spotify = Spotify[SpotifyID]
                        if Spotify['PartialCache']:
                            Spotify = None
                        Cached = True
                    
                    #** Try To Get Spotify Info From Spotify Web API If None Found In Cache **
                    if Spotify == None:
                        Spotify = SongData.SearchSpotify(ResultTrack['info']['title'], ResultTrack['info']['author'])

                        #** Check Song Is Returned Correctly & If So, Get Spotify ID & Info Dict **
                        if Spotify in ["SongNotFound", "UnexpectedError"]:
                            Spotify = None
                        else:
                            SpotifyID = list(Spotify.keys())[0]
                            Spotify = Spotify[SpotifyID]
                            #** Set Cached To False If New Spotify Data Found For Partially/None Cached Song **
                            Cached = False
                    else:
                        Cached = True

                    #**-----------QUEUE SONGS--------------**#

                    #** Setup Track Objects For Track With Spotify Data If Available **
                    if Spotify != None:
                        Track = lavalink.models.AudioTrack(ResultTrack, ctx.author, recommended=True, IgnoreHistory=False, artistURI=ArtistURI,
                                spotify={'name': Spotify['Name'],
                                         'ID': SpotifyID,
                                         'artists': Spotify['Artists'],
                                         'artistID': Spotify['ArtistID'],
                                         'URI': "https://open.spotify.com/track/"+str(SpotifyID),
                                         'art': Spotify['Art'],
                                         'album': Spotify['Album'],
                                         'albumID': Spotify['AlbumID'],
                                         'release': Spotify['Release'],
                                         'popularity': Spotify['Popularity'],
                                         'explicit': Spotify['Explicit'],
                                         'preview': Spotify['Preview']})
                    else:
                        Track = lavalink.models.AudioTrack(ResultTrack, ctx.author, recommended=True, IgnoreHistory=False, artistURI=ArtistURI, spotify={})

                    #** If Track Duration = 30000ms(30s), Inform It's Only A Preview **
                    if Track.duration == 30000:
                        await ctx.send("We could only fetch a preview for `"+ResultTrack['info']['title']+"`!")

                    #** Format & Send Queued Embed If First Track In List **
                    if Results['tracks'].index(ResultTrack) == 0:
                        if Results['playlistInfo'] == {}:
                            Queued = discord.Embed(
                                title = self.Emojis["Soundcloud"]+" Track Added To Queue!",
                                description = "["+ResultTrack['info']['title']+"]("+ResultTrack['info']['uri']+") \nBy: ["+ResultTrack['info']['author']+"]("+ArtistURI+")")
                        else:
                            Queued = discord.Embed(
                                title = self.Emojis["Soundcloud"]+" Playlist Added To Queue!",
                                description = "["+Results['playlistInfo']['name']+"]("+Query+") - "+str(len(Results['tracks']))+" Tracks")
                        Queued.set_footer(text="Requested By "+ctx.author.display_name+"#"+str(ctx.author.discriminator))
                        await ctx.send(embed=Queued)

                    #**-----------------PLAY / ADD TO QUEUE--------------**#

                    #** Add Song To Queue & Play if Not Already Playing **
                    Player.add(requester=ctx.author.id, track=Track)
                    if not(Player.is_playing):
                        await Player.play()
                        
                    #**-----------------ADD TO CACHE----------------**#

                    #** Check If Data Needs To Be Cached **
                    if not(Cached):

                        #** If Spotify Data Available, Add Soundcloud Info & Get Colour **
                        if Spotify != None:
                            RGB = Utils.get_colour(Spotify['Art'])
                            ToCache = {'SpotifyID': SpotifyID, 'SoundcloudID': ID, 'SoundcloudURL': Track.uri, 'Colour': RGB}
                            ToCache.update(Spotify)

                            #** Format Explicit Column & Add Full Song Using Database Class **
                            if ToCache['Explicit'] == 'N/A':
                                ToCache['Explicit'] = None
                            Database.AddFullSongCache(ToCache)

                        #** Add Partial Class With Just Soundcloud Data If No Spotify Data Available **
                        else:
                            ToCache = {'SoundcloudID': ID, 'SoundcloudURL': Track.uri, 'Name': Track.title, 'Artists': [Track.author]}
                            Database.AddPartialSongCache(ToCache)
            
            #** Raise Bad Argument Error If No Tracks Found **
            else:
                raise commands.CheckFailure(message="SongNotFound")
        
        #** If Query Is A URL, Not From Spotify Or Soundcloud, And Not From Youtube Either **
        elif (Query.startswith("https://") or Query.startswith("http://")) and not(Query.startswith("https://www.youtube.com/")):

            #**--------------------INPUT: URL--------------------**#

            #** Get Results From Provided Input URL **
            Results = await Player.node.get_tracks(Query)

            #** If Track Loaded, Create Track Object From Stream **
            if Results["loadType"] == 'TRACK_LOADED':
                Track = lavalink.models.AudioTrack(Results['tracks'][0], ctx.author, recommended=True, IgnoreHistory=True, Source=Results['tracks'][0]['info']['sourceName'])

                #**-----------------PLAY / ADD TO QUEUE--------------**#

                #** Add Song To Queue & Play if Not Already Playing **
                Player.add(requester=ctx.author.id, track=Track)
                if not(Player.is_playing):
                    await Player.play()
            
            #** If URL Can't Be Loaded, Raise Error **
            else:
                raise commands.CheckFailure(message="SongNotFound")

        #** If Input Isn't One Of Above Possible Categories, Raise Bad Argument Error **
        else:
            raise commands.BadArgument(message="play")


    @commands.guild_only()
    @commands.command(aliases=['disconnect', 'dc'], 
                      description="Stops any currently playing audio in your voice channel.",
                      brief="You must be in a voice channel to use this command!")
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
            if OldMessage != None:
                await OldMessage.delete()
            Player.delete('NowPlaying')

            #** Save All Current Users Stored In Player To Database **
            UserDict = Player.fetch('Users')
            for User in UserDict.values():
                await User.save()
            
        #** If Music Not Playing, Raise Error **
        else:
            raise commands.CheckFailure(message="NotPlaying")


    @commands.guild_only()
    @commands.command(aliases=['v', 'loudness'], 
                      description="Adjusts the volume of the audio player between 0% and 100%.",
                      usage="!volume <percentage>",
                      brief="You must be in a voice channel to use this command!",
                      help="`Possible Inputs For <percentage>:`\n- Default: None *(shows current volume level)*\n- Integer value between 0 and 100")
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
    @commands.command(aliases=['unpause'], 
                      description="Pauses or unpauses the audio player.",
                      brief="You must be in a voice channel to use this command!")
    async def pause(self, ctx):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(ctx)
        
        #** Check If Player Is Actually Playing A Song **
        if not(Player.is_playing):
            raise commands.CheckFailure(message="NotPlaying")

        #** If Connected & Playing Skip Song & Confirm Track Skipped **
        else:
            await Player.set_pause(not(Player.paused))
            if Player.paused:
                await ctx.send("Player Paused!")
            else:
                await ctx.send("Player Unpaused!")

    
    @commands.guild_only()
    @commands.command(aliases=['s' ,'forceskip', 'fs', 'next'], 
                      description="Skips the currently playing song and plays the next song in the queue.",
                      brief="You must be in a voice channel to use this command!")
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
    @commands.command(aliases=['q', 'upnext'], 
                      description="Displays the server's current queue of songs.")
    async def queue(self, ctx):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(ctx)

        #** Format Queue List Into String To Set As Embed Description **
        if Player.queue != []:
            Queue = "__**NOW PLAYING:**__\n"

            #** Loop Through Queue **
            for i in range(-1, len(Player.queue)):

                #** -1 Indicates Currently Playing Song, Added First **
                if i == -1:

                    #** If Not Stream, Check If Has Spotify Data **
                    if not(Player.current.stream):
                        if Player.current.extra['spotify'] != {}:

                            #** Format Data For Spotify Else Format And Add Data For SoundCloud Instead **
                            Spotify = Player.current.extra['spotify']
                            Artists = Utils.format_artists(Spotify['artists'], Spotify['artistID'])
                            Queue += self.Emojis['Spotify']+"["+Spotify['name']+"]("+Spotify['URI']+")\nBy: "+Artists+"\n"
                        else:
                            Queue += self.Emojis['Soundcloud']+" ["+Player.current['title']+"]("+Player.current['uri']+")\nBy: "+Player.current['author']+"\n"
                    
                    #** If Stream, Format Data For Stream, And Add Up Next Seperator For Rest Of Queue **
                    else:
                        Queue += "["+Player.current['title']+"]("+Player.current['uri']+")\nBy: "+Player.current['author']+"\n"
                    Queue += "--------------------\n__**UP NEXT:**__\n"
                
                #** For i>=0, Work Though Index's In Queue **
                else:

                    #** If Track At Index Is Not Stream, Check If Song Has Spotify Data **
                    if not(Player.queue[i].stream):
                        if Player.queue[i].extra['spotify'] != {}:

                            #** Format Data For Spotify Else Format And Add Data For SoundCloud Instead **
                            Spotify = Player.queue[i].extra['spotify']
                            Artists = Utils.format_artists(Spotify['artists'], Spotify['artistID'])
                            Queue += self.Emojis['Spotify']+" **"+str(i+1)+": **["+Spotify['name']+"]("+Spotify['URI']+")\nBy: "+Artists+"\n"
                        else:
                            Queue += self.Emojis['Soundcloud']+" **"+str(i+1)+": **["+Player.queue[i]['title']+"]("+Player.queue[i]['uri']+")\nBy: ["+Player.queue[i]['author']+"]("+Player.queue[i].extra['artistURI']+")\n"
                    
                    #** If Stream, Format Data For Stream & Add To String **
                    else:
                        Queue += "**"+str(i+1)+": **["+Player.queue[i]['title']+"]("+Player.queue[i]['uri']+")\nBy: "+Player.queue[i]['author']+"\n"

            #** Format Queue Into Embed & Send Into Discord **
            UpNext = discord.Embed(
                title = "Queue For "+ctx.author.voice.channel.name+":",
                description = Queue,
                colour = discord.Colour.blue())
            UpNext.set_thumbnail(url=ctx.message.guild.icon_url)
            UpNext.set_footer(text="Shuffle: "+self.Emojis[str(Player.shuffle)]+"  Loop: "+self.Emojis[str(Player.repeat)])
            await ctx.send(embed=UpNext)
        
        #** If Queue Empty, Just Send Plain Text **
        else:
            await ctx.send("Queue Is Currently Empty!")


    @commands.guild_only()
    @commands.command(aliases=['m', 'mix', 'mixup'], 
                      description="Shuffles & un-shuffles the playback of songs in the queue.",
                      brief="You must be in a voice channel to use this command!")
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
    @commands.command(aliases=['repeat'], 
                      description="Loops the current song until the command is ran again.",
                      brief="You must be in a voice channel to use this command!")
    async def loop(self, ctx):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(ctx)

        #** If Current Track Not A Stream, Enable / Disable Repeat Mode **
        if not(Player.current.stream):
            Player.repeat = not(Player.repeat)
            if Player.repeat:
                await ctx.send("Current Track Now Looping!")
            else:
                await ctx.send("Track Loop Disabled!")
        
        #** If Current Track Is A Stream, Let User Know It Can't Be Looped **
        else:
            await ctx.send("Looping is not available for audio streams!")


    @commands.guild_only()
    @commands.command(aliases=['ts', 'timeskip'], 
                      description="Skips forward or backwards in time in the currently playing song.",
                      usage="!seek <time>",
                      brief="You must be in a voice channel to use this command!",
                      help="`Possible Inputs For <time>:`\n- Positive time in seconds less than remaining duration\n    *(skips forward specified time in song)*\n"+
                           "- Positive time in seconds greater than remaining duration\n    *(skips onto next song in queue)*\n"+
                           "- Negative time in seconds\n    *(skips backwards specified time in song/to start of song)*")
    async def seek(self, ctx, time):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(ctx)

        #** Check If Track Seeable **
        if Player.current.is_seekable:

            #** Check Specified Time Is Positive Or Negative & Check It Is A Decimal Value **
            Negative = False
            if time.startswith("-"):
                Negative = True
            time = time.replace("-", "").replace("+", "")
            if time.isdecimal():

                #** Check Integer Is Greater Than 0 (Skip Forwards) or Not **
                if not(Negative):

                    #** Check If Seek Time Is Within Current Track **
                    if (float(time) * 1000) < (Player.current.duration - Player.position):

                        #** Seek Forward Specified Time in ms **
                        await Player.seek(Player.position + (float(time) * 1000))

                        #** Let User Know How Much Time Has Been Skipped **
                        await ctx.send("Skipped Forwards "+time+" Seconds!")

                    #** Otherwise Skip Track**
                    else:
                        await Player.skip()

                        #** Let User Know Track Has Been Skipped **
                        await ctx.send("Current Track Skipped!")
                
                else:
                    #** If Time Is Less Than Start, seek back in song specified amount of time **
                    if (float(time) * 1000) < Player.position:

                        #** Seek Backwards Specified Time in ms **
                        await Player.seek(Player.position - (float(time) * 1000))

                        #** Let User Know How Much Time Has Been Skipped **
                        await ctx.send("Skipped Backwards "+time+" Seconds!")
                    
                    #** Seek back to start if greater than current position **
                    else:
                        await Player.seek(0)

                        #** Let User Know How Much Time Has Been Skipped **
                        await ctx.send("Skipped Back To Start Of Song!")

            #** Raise Bad Argument Error If Input Wasn't A Number **
            else:
                raise commands.BadArgument(message="info")

        #** Let User Know Audio Isn't Seekable **
        else:
            await ctx.send(Player.current['title']+" is not seekable!")
    

    @commands.guild_only()
    @commands.command(aliases=['np', 'now', 'currentsong', 'current'], 
                      description="Displays information about the currently playing song.")
    async def nowplaying(self, ctx):
        
        #** Ensure Cmd Is Good To Run & Get Player **
        Player = await self.ensure_voice(ctx)
        
        #** Create Now Playing Embed **
        NowPlaying = discord.Embed(title="Now Playing:")

        #** Add Up Next To Footer Of Embed **
        if Player.queue == []:
            NowPlaying.set_footer(text="Up Next: Nothing")
        else:
            NowPlaying.set_footer(text="Up Next: "+Player.queue[0]["title"])

        #** If Not A Stream, Add Position Field & Source Of Music **
        if not(Player.current.stream):
            NowPlaying.set_author(name="Playing From Soundcloud", icon_url="https://cdn.discordapp.com/emojis/897135141040832563.png?size=96&quality=lossless")
            NowPlaying.add_field(name="Position:", value = "0:00 / "+ Utils.format_time(Player.current.duration))
            
            #** If Track Has Spotify Info, Format List of Artists **
            if Player.current.extra['spotify'] != {}:
                Artists = Utils.format_artists(Player.current.extra['spotify']['artists'], Player.current.extra['spotify']['artistID'])

                #** Set Descrition and Thumbnail & Add By Field Above Position Field **
                NowPlaying.description = self.Emojis['Soundcloud']+" ["+Player.current["title"]+"]("+Player.current["uri"]+")\n"+self.Emojis['Spotify']+" ["+Player.current.extra['spotify']['name']+"]("+Player.current.extra['spotify']['URI']+")"
                NowPlaying.set_thumbnail(url=Player.current.extra['spotify']['art'])
                NowPlaying.insert_field_at(0, name="By:", value=Artists)

            #** If No Spotify Info, Create Basic Now Playing Embed **
            else:
                #** Set Descrition and Thumbnail & Add By Field Above Position Field **
                NowPlaying.description = self.Emojis['Soundcloud']+" ["+Player.current["title"]+"]("+Player.current["uri"]+")"
                NowPlaying.insert_field_at(0, name="By:", value="["+Player.current.author+"]("+Player.current.extra["artistURI"]+")")
        
        #** If Track Is A Stream, Add Appropriate Information For A Stream **
        else:
            NowPlaying.set_author(name="Playing From "+Player.current.extra['Source'].title()+" Stream")
            NowPlaying.description = "["+Player.current['title']+"]("+Player.current["uri"]+")"
            NowPlaying.add_field(name="By: ", value=Player.current['author'])
            NowPlaying.add_field(name="Duration: ", value="N/A")

        #** Add Requester To Embed & Send Embed To User **
        NowPlaying.add_field(name="Requested By: ", value=str(Player.current.requester), inline=False)
        await ctx.send(embed=NowPlaying)


    @commands.command(aliases=['i', 'song', 'songinfo'], 
                      description="Displays both basic and more in-depth information about a specified song.",
                      usage= "!info <spotifyURL>",
                      help="`Possible Inputs For <spotifyURL>:`\n- Spotify Track URL")
    async def info(self, ctx, SpotifyURL):

        #** Check If Input Is Spotify URL & Format Input Data, Else Raise Bad Argument Error **
        if SpotifyURL.startswith("https://open.spotify.com/track/"):
            SpotifyID = (SpotifyURL.split("/"))[4].split("?")[0]
        else:
            raise commands.BadArgument(message="info")

        #** Check ID Is A Valid Spotify ID **
        if len(SpotifyID) == 22:

            #** Get Song Details And Check If Song Is Found **
            SongInfo = SongData.GetSongDetails(SpotifyID)
            if not(SongData in ["SongNotFound", "UnexpectedError"]):

                #** Format Returned Data Ready To Be Put Into The Embeds **
                SongInfo = SongInfo[SpotifyID]
                Description = "**By: **" + Utils.format_artists(SongInfo['Artists'], SongInfo['ArtistID'])
                Links = self.Emojis['Spotify']+" Song: [Spotify]("+SpotifyURL+")\n"
                if SongInfo['Preview'] != None:
                    Links += self.Emojis['Preview']+" Song: [Preview]("+SongInfo['Preview']+")\n"
                if SongInfo['AlbumID'] != None:
                    Links += self.Emojis['Album']+" Album: ["+SongInfo['Album']+"](https://open.spotify.com/album/"+SongInfo['AlbumID']+")"
                else:
                    Links += self.Emojis['Album']+" Album: "+SongInfo['Album']
                
                #** Setup Embed With Advanced Song Information **
                BaseEmbed = discord.Embed(
                    title=SongInfo['Name'], 
                    description=Description)
                if SongInfo['Art'] != None:
                    BaseEmbed.set_thumbnail(url=SongInfo['Art'])
                BaseEmbed.set_footer(text="(2/2) React To See Basic Song Information!")
                BaseEmbed.add_field(name="Popularity:", value=SongInfo['Popularity'], inline=True)
                BaseEmbed.add_field(name="Explicit:", value=SongInfo['Explicit'], inline=True)
                BaseEmbed.add_field(name="Tempo:", value=SongInfo['Tempo'], inline=True)
                BaseEmbed.add_field(name="Key:", value=SongInfo['Key'], inline=True)
                BaseEmbed.add_field(name="Beats Per Bar:", value=SongInfo['BeatsPerBar'], inline=True)
                BaseEmbed.add_field(name="Mode:", value=SongInfo['Mode'], inline=True)
                Advanced = copy.deepcopy(BaseEmbed.to_dict())

                #** Setup Embed With Basic Song Information **
                BaseEmbed.clear_fields()
                BaseEmbed.set_footer(text="(1/2) React To See Advanced Song Information!")
                BaseEmbed.add_field(name="Length:", value=SongInfo['Duration'], inline=False)
                BaseEmbed.add_field(name="Released:", value=SongInfo['Release'], inline=True)
                BaseEmbed.add_field(name="Genre:", value=SongInfo['Genre'].title(), inline=True)
                BaseEmbed.add_field(name="Links:", value=Links, inline=False)
                Basic = BaseEmbed.to_dict()

                #** Send First Page & Setup Pagination Object **
                Page = await ctx.send(embed=BaseEmbed)
                await Page.add_reaction(self.Emojis['Back'])
                await Page.add_reaction(self.Emojis['Next'])
                await self.Pagination.add_pages(Page.id, [Basic, Advanced])
        
            #** Raise Check Failure Error If Track Can't Be Found **
            else:
                raise commands.CheckFailure(message="SongNotFound")
        else:
            raise commands.CheckFailure(message="SongNotFound")


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(MusicCog(client))