
#!-------------------------IMPORT MODULES--------------------#


import copy
import logging
import discord
import asyncio
import lavalink
from datetime import datetime
from discord.ext import commands
from discord import app_commands


#!--------------------CUSTOM VOICE PROTOCOL------------------#


class LavalinkVoiceClient(discord.VoiceClient):

    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        
        #** Setup Class Attributes **
        self.client = client
        self.channel = channel
        self.lavalink = self.client.lavalink


    async def on_voice_server_update(self, data):

        #** Transform Server Data & Hand It Down To Lavalink Voice Update Handler **
        lavalink_data = {
            't': 'VOICE_SERVER_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)
        
    
    async def on_voice_state_update(self, data):
        
        #** Transform Voice State Data & Hand It Down To Lavalink Voice Update Handler **
        lavalink_data = {
            't': 'VOICE_STATE_UPDATE',
            'd': data
        }
        await self.lavalink.voice_update_handler(lavalink_data)


    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False):
        
        #** Change Voice State To Channel Passed Into Voice Protocol**
        await self.channel.guild.change_voice_state(channel=self.channel)
        

    async def disconnect(self, *, force: bool = False):

        #** Get Player & Change Voice Channel To None **
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=None)

        #** Update ChannelID Of Player To None & Cleanup VoiceState **
        player.channel_id = None
        self.cleanup()


#!------------------------MUSIC COG-----------------------#


class MusicCog(commands.Cog, name="Music"):

    def __init__(self, client: discord.Client):

        #** Assign Discord Bot Client As Class Object & Setup Logging **
        self.client = client 
        self.Pagination = self.client.get_cog("EmbedPaginator")
        self.logger = logging.getLogger('lavalink')

        #** Create Client If One Doesn't Already Exist **
        if not hasattr(client, 'lavalink'):
            self.logger.info("No Previous Lavalink Client Found. Creating New Connection")
            client.lavalink = lavalink.Client(client.user.id)
            client.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'eu', name='default-node')
            client.add_listener(client.lavalink.voice_update_handler, 'on_socket_response')
            client.logger.debug("Lavalink listener added")
            self.logger.info("New Client Registered")
        else:
            self.logger.info("Found Previous Lavalink Connection")

        #** Add Event Hook **
        lavalink.add_event_hook(self.track_hook)
        self.logger.debug("Event hooks added")


    def cog_unload(self):
        
        #** Clear Event Hooks When Cog Unloaded **
        self.client.lavalink._event_hooks.clear()
        self.logger.debug("Cleared event hooks")


    async def ensure_voice(self, interaction):

        #** If Command Needs User To Be In VC, Check if Author is in Voice Channel **
        if not(interaction.command.name in ['queue', 'nowplaying']):
            if not(interaction.user.voice) or not(interaction.user.voice.channel):
                raise app_commands.CheckFailure("UserVoice")
        
        #** Return a Player If One Exists, Otherwise Create One **
        Player = self.client.lavalink.player_manager.create(interaction.guild_id)

        #** Check If Voice Client Already Exists **
        if not(Player.is_connected):
            if interaction.command.name in ['play']:

                #** Join Voice Channel If Not Already In One **
                await interaction.user.voice.channel.connect(cls=LavalinkVoiceClient)

                #** Store Key, Value Pairs In Player & Set Default Volume To 25% **
                Player.store('Channel', interaction.channel_id)
                Player.store('Voice', interaction.user.voice.channel)
                Player.store('Users', {})
                await Player.set_volume(25)
                
            #** If Bot Doesn't Need To Connect, Raise Error **
            elif interaction.command.name in ['stop', 'pause', 'skip', 'queue', 'seek', 'nowplaying', 'loop']:
                raise app_commands.CheckFailure("BotVoice")
                
        else:

            #** Check If Author Is In Same VC as Bot **
            if int(Player.channel_id) != interaction.user.voice.channel.id:
                raise app_commands.CheckFailure("SameVoice")
            
        #** Return Player Associated With Guild **
        return Player


    async def track_hook(self, event):
        
        if isinstance(event, lavalink.events.TrackEndEvent):
            
            #** If Queue Empty, Save User Data & Disconnect From VC **
            if event.player.queue == []:
            
                #** If Player Connected, Get Guild Object & Disconnect From VC **
                if event.player.is_connected:
                    Guild = self.client.get_guild(int(event.player.guild_id))
                    await Guild.voice_client.disconnect()
                    
                    #** Remove Old Now Playing Message & Delete Stored Value **
                    OldMessage = event.player.fetch('NowPlaying')
                    await OldMessage.delete()
                    event.player.delete('NowPlaying')

                    #** Save All Current Users Stored In Player To Database **
                    UserDict = event.player.fetch('Users')
                    for User in UserDict.values():
                        await User.save()
                    print("All User Data Saved!")
            
        elif isinstance(event, lavalink.events.TrackStartEvent):
            
            #** Get Channel & Print Out Now Playing Information When New Track Starts **
            Timestamp = datetime.now()
            Channel = self.client.get_channel(int(event.player.fetch("Channel")))
            
            #** Create Now Playing Embed **
            NowPlaying = discord.Embed(title = "Now Playing:")

            #** Add Up Next To Footer Of Embed **
            if event.player.queue == []:
                NowPlaying.set_footer(text="Up Next: Nothing")
            else:
                NowPlaying.set_footer(text="Up Next: "+event.player.queue[0]["title"])

            #** If Not A Stream, Add Duration Field & Source Of Music **
            if not(event.track.stream):
                NowPlaying.set_author(name="Playing From Soundcloud", icon_url="https://cdn.discordapp.com/emojis/897135141040832563.png?size=96&quality=lossless")
                NowPlaying.add_field(name="Duration:", value = self.client.utils.format_time(event.track.duration))
                
                #** If Track Has Spotify Info, Format List of Artists **
                if event.track.extra['spotify'] != {}:
                    Artists = self.client.utils.format_artists(event.track.extra['spotify']['artists'], event.track.extra['spotify']['artistID'])

                    #** Set Descrition and Thumbnail & Add By Field Above Duration Field **
                    NowPlaying.description = f"{self.client.utils.get_emoji('Soundcloud')} [{event.track['title']}]({event.track['uri']})\n{self.client.utils.get_emoji('Spotify')} [{event.track.extra['spotify']['name']}]({event.track.extra['spotify']['URI']})"
                    NowPlaying.set_thumbnail(url=event.track.extra['spotify']['art'])
                    NowPlaying.insert_field_at(0, name="By:", value=Artists)

                #** If No Spotify Info, Create Basic Now Playing Embed **
                else:
                    #** Set Descrition and Thumbnail & Add By Field Above Position Field **
                    NowPlaying.description = f"{self.client.utils.get_emoji('Soundcloud')} [{event.track['title']}]({event.track['uri']})"
                    NowPlaying.insert_field_at(0, name="By:", value="["+event.track.author+"]("+event.track.extra["artistURI"]+")")
            
            #** If Track Is A Stream, Add Appropriate Information For A Stream & N/A For Duration As It Is Endless **
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
                        UserDict.pop(DiscordID)
                    else:
                        UserIDs.remove(int(DiscordID))
                
                #** Add New User Objects For Newly Joined Listeners & Store New User Dict Back In Player **
                for DiscordID in UserIDs:
                    UserDict[str(DiscordID)] = self.client.userClass.User(self.client, DiscordID)
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


    @app_commands.guild_only()
    @app_commands.command(description="Allows you to play music through a Discord Voice Channel from a variety of sources.")
    @app_commands.describe(spotify="A Spotify Link For A Track, Album Or Playlist",
                           search="Text To Use To Search Soundcloud",
                           soundcloud="A Soundcloud Link For A Track Or Playlist",
                           website="Any Link To A Website Which Has An Audio Stream")
    async def play(self, interaction: discord.Interaction, search: str = None, spotify: str = None, soundcloud: str = None, website: str = None):

        #** Ensure Voice To Make Sure Client Is Good To Run & Get Player In Process **
        Player = await self.ensure_voice(interaction)
    
        #** Remove "<>" Embed Characters from Inputs **
        for input in [search, spotify, soundcloud, website]:
            if input is not None:
                Query = input.strip('<>')

        #** Check If Query Is A Spotify URL **
        if Query.startswith("https://open.spotify.com/"):

            #** Strip ID From URL **
            SpotifyID = (Query.split("/"))[4].split("?")[0]
            if len(SpotifyID) != 22:
                raise app_commands.CheckFailure("SongNotFound")
            Cached = False

            #**------------INPUT: TRACK---------------**#

            if "track" in Query:

                #** Get Song From Cache & Check If It Is Cached **
                SongInfo = self.client.database.SearchCache(SpotifyID)
                PlaylistInfo = None
                if SongInfo == None:

                    #** If Not Cached, Get Song Info **
                    SongInfo = self.client.music.GetSongInfo(SpotifyID)

                    #** Raise Error if No Song Found Otherwise Reformat Query With New Data **
                    if SongInfo == "SongNotFound":
                        raise app_commands.CheckFailure("SongNotFound")
                    elif SongInfo == "UnexpectedError":
                        raise app_commands.CheckFailure("UnexpectedError")
                
                else:
                    Cached = True

            #**------------INPUT: PLAYLIST---------------**#

            elif "playlist" in Query:

                #** Get Playlist Info From Spotify Web API **
                SongInfo = self.client.music.GetPlaylistSongs(SpotifyID)

                #** Raise Error If Playlist Not Found or Unexpected Error Occurs **
                if SongInfo == "PlaylistNotFound":
                    raise app_commands.CheckFailure("SongNotFound")
                elif SongInfo == "UnexpectedError":
                    raise app_commands.CheckFailure("UnexpectedError")

                #** Setup Playlist & Song Info; & Set Type **
                PlaylistInfo = SongInfo['PlaylistInfo']
                SongInfo = SongInfo['Tracks']
                Type = "Playlist"

            #**------------INPUT: ALBUM---------------**#

            elif "album" in Query:

                #** Get Album Info From Spotify Web API **
                SongInfo = self.client.music.GetAlbumInfo(SpotifyID)
                
                #** Raise Error If Album Not Found Or Unexpected Error **
                if SongInfo == "AlbumNotFound":
                    raise app_commands.CheckFailure("SongNotFound")
                elif SongInfo == "UnexpectedError":
                    raise app_commands.CheckFailure("UnexpectedError")

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
                if len(Results.tracks) > 0:
                    ArtistURI = "/".join(Results['tracks'][0]['info']['uri'].split("/")[:4])
                    Track = lavalink.models.AudioTrack(Results['tracks'][0], interaction.user, recommended=True, IgnoreHistory=False, artistURI=ArtistURI,
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
                    raise app_commands.CheckFailure("SongNotFound")
                
                #** If Track Duration = 30000ms(30s), Inform It's Only A Preview **
                if Track.duration == 30000:
                    await interaction.channel.send("**Sorry, we could only fetch a preview for `"+Info['Name']+"`!**")

                #** Format & Send Queued Embed If First Song In List To Queue **
                if list(SongInfo.keys()).index(SpotifyID) == 0:
                    if PlaylistInfo == None:
                        Artists = self.client.utils.format_artists(Info['Artists'], Info['ArtistID'])
                        Queued = discord.Embed(
                            title = f"{self.client.utils.get_emoji('Spotify')} Track Added To Queue!",
                            description = "["+Info['Name']+"]("+Query+") \nBy: "+Artists)
                    else:
                        Queued = discord.Embed(
                            title = f"{self.client.utils.get_emoji('Spotify')} {Type} Added To Queue!",
                            description = "["+PlaylistInfo['Name']+"]("+Query+") - "+str(PlaylistInfo['Length'])+" Tracks")
                    Queued.set_footer(text="Requested By "+interaction.user.display_name+"#"+str(interaction.user.discriminator))
                    await interaction.response.send_message(embed=Queued)

                #**-----------------PLAY / ADD TO QUEUE--------------**#

                #** Add Song To Queue & Play if Not Already Playing **
                Player.add(requester=interaction.user.id, track=Track)
                if not(Player.is_playing):
                    await Player.play()

                #**-----------------ADD TO CACHE----------------**#

                #** Check If Data Needs To Be Cached **
                if not(Cached):
                    
                    #** Get SoundcloudID & Primary Colour Of Album Art **
                    URI = Track.identifier.split("/")
                    ID  = URI[4].split(":")[2]
                    RGB = self.client.utils.get_colour(Info['Art'])
                    
                    #** Create Song Info Dict With Formatted Data & Send To Database **
                    ToCache = {'SpotifyID': SpotifyID, 'SoundcloudID': ID, 'SoundcloudURL': Track.uri, 'Colour': RGB}
                    ToCache.update(Info)
                    if ToCache['Explicit'] == 'N/A':
                        ToCache['Explicit'] = None
                    if ToCache['Popularity'] == 'N/A':
                        ToCache['Popularity'] = None
                    self.client.database.AddFullSongCache(ToCache)
        
        #** If Query Is From Soundcloud Or Is A Plain Text Input **
        elif Query.startswith("https://soundcloud.com/") or not(Query.startswith("https://") or Query.startswith("http://")):

             #**------------INPUT: TEXT, TRACK OR PLAYLIST---------------**#

            #** Get Track(s) From Lavalink Player **
            if not(Query.startswith("https://")):
                Results = await Player.node.get_tracks("scsearch:"+Query)
                print(Results)
                print(Results['tracks'])
                Results.tracks = [Results['tracks'][0]]
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
                    Spotify = self.client.database.SearchCache(ID)
                    if Spotify != None:
                        SpotifyID = list(Spotify.keys())[0]
                        Spotify = Spotify[SpotifyID]
                        if Spotify['PartialCache']:
                            Spotify = None
                        Cached = True
                    
                    #** Try To Get Spotify Info From Spotify Web API If None Found In Cache **
                    if Spotify == None:
                        Spotify = self.client.music.SearchSpotify(ResultTrack['info']['title'], ResultTrack['info']['author'])

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
                        Track = lavalink.models.AudioTrack(ResultTrack, interaction.user, IgnoreHistory=False, artistURI=ArtistURI, 
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
                        Track = lavalink.models.AudioTrack(ResultTrack, interaction.user, IgnoreHistory=False, artistURI=ArtistURI, spotify={})

                    #** If Track Duration = 30000ms(30s), Inform It's Only A Preview **
                    if Track.duration == 30000:
                        await interaction.channel.send("We could only fetch a preview for `"+ResultTrack['info']['title']+"`!")

                    #** Format & Send Queued Embed If First Track In List **
                    if Results['tracks'].index(ResultTrack) == 0:
                        if Results['playlist_info']['name'] == None:
                            Queued = discord.Embed(
                                title = f"{self.client.utils.get_emoji('Soundcloud')} Track Added To Queue!",
                                description = "["+ResultTrack['info']['title']+"]("+ResultTrack['info']['uri']+") \nBy: ["+ResultTrack['info']['author']+"]("+ArtistURI+")")
                        else:
                            Queued = discord.Embed(
                                title = f"{self.client.utils.get_emoji('Soundcloud')} Playlist Added To Queue!",
                                description = "["+Results['playlist_info']['name']+"]("+Query+") - "+str(len(Results['tracks']))+" Tracks")
                        Queued.set_footer(text="Requested By "+interaction.user.display_name+"#"+str(interaction.user.discriminator))
                        await interaction.response.send_message(embed=Queued)

                    #**-----------------PLAY / ADD TO QUEUE--------------**#

                    #** Add Song To Queue & Play if Not Already Playing **
                    Player.add(requester=interaction.user.id, track=Track)
                    if not(Player.is_playing):
                        await Player.play()
                        
                    #**-----------------ADD TO CACHE----------------**#

                    #** Check If Data Needs To Be Cached **
                    if not(Cached):

                        #** If Spotify Data Available, Add Soundcloud Info & Get Colour **
                        if Spotify != None:
                            RGB = self.client.utils.get_colour(Spotify['Art'])
                            ToCache = {'SpotifyID': SpotifyID, 'SoundcloudID': ID, 'SoundcloudURL': Track.uri, 'Colour': RGB}
                            ToCache.update(Spotify)

                            #** Format Explicit Column & Add Full Song Using Database Class **
                            if ToCache['Explicit'] == 'N/A':
                                ToCache['Explicit'] = None
                            self.client.database.AddFullSongCache(ToCache)

                        #** Add Partial Class With Just Soundcloud Data If No Spotify Data Available **
                        else:
                            ToCache = {'SoundcloudID': ID, 'SoundcloudURL': Track.uri, 'Name': Track.title, 'Artists': [Track.author]}
                            self.client.database.AddPartialSongCache(ToCache)
            
            #** Raise Bad Argument Error If No Tracks Found **
            else:
                raise app_commands.CheckFailure("SongNotFound")
        
        #** If Query Is A URL, Not From Spotify Or Soundcloud, And Not From Youtube Either **
        elif (Query.startswith("https://") or Query.startswith("http://")) and not(Query.startswith("https://www.youtube.com/")):

            #**--------------------INPUT: URL--------------------**#

            #** Get Results From Provided Input URL **
            Results = await Player.node.get_tracks(Query)

            #** If Track Loaded, Create Track Object From Stream **
            if Results["loadType"] == 'TRACK_LOADED':
                Track = lavalink.models.AudioTrack(Results['tracks'][0], interaction.user, recommended=True, IgnoreHistory=True, Source=Results['tracks'][0]['info']['sourceName'])

                #**-----------------PLAY / ADD TO QUEUE--------------**#

                #** Add Song To Queue & Play if Not Already Playing **
                Player.add(requester=interaction.user.id, track=Track)
                if not(Player.is_playing):
                    await Player.play()
            
            #** If URL Can't Be Loaded, Raise Error **
            else:
                raise app_commands.CheckFailure("SongNotFound")

        #** If Input Isn't One Of Above Possible Categories, Raise Bad Argument Error **
        else:
            raise commands.BadArgument(message="play")


    @app_commands.guild_only()
    @app_commands.command(description="Stops music, clears queue and disconnects the bot!")
    async def disconnect(self, interaction: discord.Interaction):

        #** Ensure Voice To Make Sure Client Is Good To Run & Get Guild Player**
        Player = await self.ensure_voice(interaction)

        #** Clear Queue & Stop Playing Music If Music Playing**
        if Player.is_playing or Player.is_connected:
            if Player.is_playing:
                Player.queue.clear()
                await Player.stop()
            
            #** Disconnect From VC & Send Message Accordingly **
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("Disconnected!")

            #** Remove Old Now Playing Message & Delete Stored Value **
            OldMessage = Player.fetch('NowPlaying')
            if OldMessage != None:
                await OldMessage.delete()
            Player.delete('NowPlaying')

            #** Save All Current Users Stored In Player To Database **
            UserDict = Player.fetch('Users')
            for User in UserDict.values():
                await User.save()
            
        #** If Not Connected, Raise Error **
        else:
            raise app_commands.CheckFailure("BotVoice")


    @app_commands.guild_only()
    @app_commands.command(description="Adjusts the volume of the audio player between 0% and 100%.")
    async def volume(self, interaction: discord.Interaction, percentage: app_commands.Range[int, 0, 100] = None):

        #** Ensure Voice To Make Sure Client Is Good To Run & Get Player **
        Player = await self.ensure_voice(interaction)
        
        #** If No Volume Change, Return Current Volume **
        if percentage is None:
            await interaction.response.send_message(f"**Current Volume:** {Player.volume}%")

        else: 

            #** If Connected Set Volume & Confirm Volume Change **
            await Player.set_volume(percentage)
            await interaction.response.send_message(f"Volume Set To {percentage}%")

    
    @app_commands.guild_only()
    @app_commands.command(description="Pauses or unpauses the audio player.")
    async def pause(self, interaction: discord.Interaction):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(interaction)
        
        #** Check If Player Is Actually Playing A Song **
        if not(Player.is_playing):
            raise app_commands.CheckFailure("NotPlaying")

        #** If Connected & Playing Skip Song & Confirm Track Skipped **
        else:
            await Player.set_pause(not(Player.paused))
            if Player.paused:
                await interaction.response.send_message("Player Paused!")
            else:
                await interaction.response.send_message("Player Unpaused!")

    
    @app_commands.guild_only()
    @app_commands.command(description="Skips the currently playing song and plays the next song in the queue.")
    async def skip(self, interaction: discord.Interaction):

        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(interaction)
        
        #** Check If Player Is Actually Playing A Song **
        if not(Player.is_playing):
            raise app_commands.CheckFailure("NotPlaying")

        #** If Connected & Playing Skip Song & Confirm Track Skipped **
        else:
            await interaction.response.send_message(f"**Skipped Track:** {Player.current['title']}")
            await Player.skip()
    
    
    @app_commands.guild_only()
    @app_commands.command(description="Displays the server's current queue of songs.")
    async def queue(self, interaction: discord.Interaction):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(interaction)

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
                            Artists = self.client.utils.format_artists(Spotify['artists'], Spotify['artistID'])
                            Queue += f"{self.client.utils.get_emoji('Spotify')} [{Spotify['name']}]({Spotify['URI']})\nBy: {Artists}\n"
                        else:
                            Queue += f"{self.client.utils.get_emoji('Soundcloud')} [{Player.current['title']}]({Player.current['uri']})\nBy: {Player.current['author']}\n"
                    
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
                            Artists = self.client.utils.format_artists(Spotify['artists'], Spotify['artistID'])
                            Queue += f"{self.client.utils.get_emoji('Spotify')} **{str(i+1)}: **[{Spotify['name']}]({Spotify['URI']})\nBy: {Artists}\n"
                        else:
                            Queue += f"{self.client.utils.get_emoji('Soundcloud')} **{str(i+1)}: **[{Player.queue[i]['title']}]({Player.queue[i]['uri']})\nBy: [{Player.queue[i]['author']}]({Player.queue[i].extra['artistURI']})\n"
                    
                    #** If Stream, Format Data For Stream & Add To String **
                    else:
                        Queue += "**"+str(i+1)+": **["+Player.queue[i]['title']+"]("+Player.queue[i]['uri']+")\nBy: "+Player.queue[i]['author']+"\n"

            #** Format Queue Into Embed & Send Into Discord **
            UpNext = discord.Embed(
                title = "Queue For "+interaction.user.voice.channel.name+":",
                description = Queue,
                colour = discord.Colour.blue())
            UpNext.set_thumbnail(url=interaction.guild.icon.url)
            
            #** Format Footer Based On Whether Shuffle & Repeat Are Active **
            if Player.shuffle:
                footer = "Shuffle: ✅  "
            else:
                footer = "Shuffle: ❌  "
            
            if Player.repeat:
                footer += "Loop: ✅"
            else:
                footer += "Loop: ❌"
            
            #** Set Footer & Sent Embed To Discord **
            UpNext.set_footer(text=footer)
            await interaction.response.send_message(embed=UpNext)
        
        #** If Queue Empty, Just Send Plain Text **
        else:
            await interaction.response.send_message("Queue Is Currently Empty!")


    @app_commands.guild_only()
    @app_commands.command(description="Shuffles & un-shuffles the playback of songs in the queue.")
    async def shuffle(self, interaction: discord.Interaction):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(interaction)

        #** Enable / Disable Shuffle Mode **
        Player.shuffle = not(Player.shuffle)
        if Player.shuffle:
            await interaction.response.send_message("Player Shuffled!")
        else:
            await interaction.response.send_message("Player No Longer Shuffled!")


    @app_commands.guild_only()
    @app_commands.command(description="Loops the current song or queue until the command is ran again.")
    @app_commands.choices(state=[app_commands.Choice(name="Off", value=0),
                                 app_commands.Choice(name="Current Track", value=1),
                                 app_commands.Choice(name="Current Queue", value=2)])
    async def loop(self, interaction: discord.Interaction, state: app_commands.Choice[int]):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(interaction)

        #** If Current Track Not A Stream, Set Loop Based On Input **
        if not(Player.current.stream):
            Player.set_loop(state.value)
            await interaction.response.send_message(f"Track Looping Set To {state.name}")
        
        #** If Current Track Is A Stream, Let User Know It Can't Be Looped **
        else:
            await interaction.response.send_message("Looping is not available for audio streams!")


    @app_commands.guild_only()
    @app_commands.command(description="Skips seconds forward or backwards in time in the currently playing song.")
    async def seek(self, interaction: discord.Interaction, forward: int = None, backward: int = None):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(interaction)

        #** Check If Track Seeable **
        if Player.current.is_seekable:

            #** Check Integer Is Greater Than 0 (Skip Forwards) or Not **
            if forward is not None:

                #** Check If Seek Time Is Within Current Track **
                if (forward * 1000) < (Player.current.duration - Player.position):

                    #** Seek Forward Specified Time in ms **
                    await Player.seek(Player.position + (forward * 1000))

                    #** Let User Know How Much Time Has Been Skipped **
                    await interaction.response.send_message(f"Skipped Forwards {forward * 1000} Seconds!")

                #** Otherwise Skip Track**
                else:
                    await Player.skip()

                    #** Let User Know Track Has Been Skipped **
                    await interaction.response.send_message("Current Track Skipped!")
            
            elif backward is not None:
                #** If Time Is Less Than Start, seek back in song specified amount of time **
                if (backward * 1000) < Player.position:

                    #** Seek Backwards Specified Time in ms **
                    await Player.seek(Player.position - (backward * 1000))

                    #** Let User Know How Much Time Has Been Skipped **
                    await interaction.response.send_message(f"Skipped Backwards {backward * 1000} Seconds!")
                
                #** Seek back to start if greater than current position **
                else:
                    await Player.seek(0)

                    #** Let User Know How Much Time Has Been Skipped **
                    await interaction.response.send_message("Skipped Back To Start Of Song!")
            
            #** Let User They Need To Enter Forward Or Backwards Time For Command To Work **
            else:
                await interaction.response.send_message(f"To Seek, Please Enter A Time In Seconds!", ephemeral=True)

        #** Let User Know Audio Isn't Seekable **
        else:
            await interaction.response.send_message(f"{Player.current['title']} is not seekable!", ephemeral=True)
    

    @app_commands.guild_only()
    @app_commands.command(description="Displays information about the currently playing song.")
    async def nowplaying(self, interaction: discord.Interaction):
        
        #** Ensure Cmd Is Good To Run & Get Player **
        Player = await self.ensure_voice(interaction)
        
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
            NowPlaying.add_field(name="Position:", value = self.client.utils.format_time(Player.position)+" / "+ self.client.utils.format_time(Player.current.duration))
            
            #** If Track Has Spotify Info, Format List of Artists **
            if Player.current.extra['spotify'] != {}:
                Artists = self.client.utils.format_artists(Player.current.extra['spotify']['artists'], Player.current.extra['spotify']['artistID'])

                #** Set Descrition and Thumbnail & Add By Field Above Position Field **
                NowPlaying.description = f"{self.client.utils.get_emoji('Soundcloud')} [{Player.current['title']}]({Player.current['uri']})\n{self.client.utils.get_emoji('Spotify')} [{Player.current.extra['spotify']['name']}]({Player.current.extra['spotify']['URI']})"
                NowPlaying.set_thumbnail(url=Player.current.extra['spotify']['art'])
                NowPlaying.insert_field_at(0, name="By:", value=Artists)

            #** If No Spotify Info, Create Basic Now Playing Embed **
            else:
                #** Set Descrition and Thumbnail & Add By Field Above Position Field **
                NowPlaying.description = f"{self.client.utils.get_emoji('Soundcloud')} [{Player.current['title']}]({Player.current['uri']})"
                NowPlaying.insert_field_at(0, name="By:", value="["+Player.current.author+"]("+Player.current.extra["artistURI"]+")")
        
        #** If Track Is A Stream, Add Appropriate Information For A Stream **
        else:
            NowPlaying.set_author(name="Playing From "+Player.current.extra['Source'].title()+" Stream")
            NowPlaying.description = "["+Player.current['title']+"]("+Player.current["uri"]+")"
            NowPlaying.add_field(name="By: ", value=Player.current['author'])
            NowPlaying.add_field(name="Position: ", value="N/A")

        #** Add Requester To Embed & Send Embed To User **
        NowPlaying.add_field(name="Requested By: ", value=str(Player.current.requester), inline=False)
        await interaction.response.send_message(embed=NowPlaying)


    @app_commands.command(description="Displays both basic and more in-depth information about a specified song.")
    async def info(self, interaction: discord.Interaction, spotify: str):

        #** Check If Input Is Spotify URL & Format Input Data, Else Raise Bad Argument Error **
        if spotify.startswith("https://open.spotify.com/track/"):
            SpotifyID = (spotify.split("/"))[4].split("?")[0]
        else:
            await interaction.response.send_message("Please enter a valid Spotify Track Link!", ephemeral=True)

        #** Check ID Is A Valid Spotify ID **
        if len(SpotifyID) == 22:

            #** Get Song Details And Check If Song Is Found **
            SongInfo = self.client.music.GetSongDetails(SpotifyID)
            if not(self.client.music in ["SongNotFound", "UnexpectedError"]):

                #** Format Returned Data Ready To Be Put Into The Embeds **
                SongInfo = SongInfo[SpotifyID]
                Description = "**By: **" + self.client.utils.format_artists(SongInfo['Artists'], SongInfo['ArtistID'])
                Links = f"{self.client.utils.get_emoji('Spotify')} Song: [Spotify]({spotify})\n"
                if SongInfo['Preview'] != None:
                    Links += f"{self.client.utils.get_emoji('Preview')} Song: [Preview]({SongInfo['Preview']})\n"
                if SongInfo['AlbumID'] != None:
                    Links += f"{self.client.utils.get_emoji('Album')} Album: [{SongInfo['Album']}](https://open.spotify.com/album/{SongInfo['AlbumID']})"
                else:
                    Links += f"{self.client.utils.get_emoji('Album')} Album: {SongInfo['Album']}"
                
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
                Page = await interaction.response.send_message(embed=BaseEmbed)
                await Page.add_reaction(self.client.utils.get_emoji('Back'))
                await Page.add_reaction(self.client.utils.get_emoji('Next'))
                await self.Pagination.add_pages(Page.id, [Basic, Advanced])
        
            #** Raise Check Failure Error If Track Can't Be Found **
            else:
                raise app_commands.CheckFailure("SongNotFound")
        else:
            raise app_commands.CheckFailure("SongNotFound")


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(MusicCog(client))