
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
from Classes.Music import Music
from Classes.Utils import Utility


#!--------------------------------STARTUP-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Music")
print("Modules Imported: ✓", end="")


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
        
        #** Return a Player If One Exists, Otherwise Create One **
        Player = self.client.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))

        #** Check if Author is in Voice Channel **
        if not(ctx.author.voice) or not(ctx.author.voice.channel):
            raise commands.CheckFailure(message="UserVoice")

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

            #** Save All Current Users Stored In Player To Database **
            UserList = event.player.fetch('Users')
            for User in UserList:
                await User.save()

            #** Remove Player From Cache **
            self.client.lavalink.player_manager.remove(Guild.id)
            
        elif isinstance(event, lavalink.events.TrackStartEvent):
            
            #** Get Channel & Print Out Now Playing Information When New Track Starts **
            Timestamp = datetime.now()
            Channel = self.client.get_channel(int(event.player.fetch("Channel")))
            print(event.track["title"], event.track["uri"])
            
            #** Create Now Playing Embed **
            NowPlaying = discord.Embed(title = "Now Playing:")
            
            #** Set Author & Footer and Add Position Field **
            NowPlaying.set_author(name="Requested By "+str(event.track.requester)+"", icon_url=event.track.requester.avatar_url)
            NowPlaying.add_field(name="Position:", value = Utils.format_time(event.player.position)+" / "+ Utils.format_time(event.track.duration))
            if event.player.queue == []:
                NowPlaying.set_footer(text="Up Next: Nothing")
            else:
                NowPlaying.set_footer(text="Up Next: "+event.player.queue[0]["title"])
            
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

            #** Send Embed To Channel Where First Play Cmd Was Ran & Add Reactions**
            Message = await Channel.send(embed=NowPlaying)
            await Message.add_reaction(self.Emojis['SkipBack'])
            await Message.add_reaction(self.Emojis['Play'])
            await Message.add_reaction(self.Emojis['Pause'])
            await Message.add_reaction(self.Emojis['SkipForwards'])

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
                UserList = event.player.fetch('Users')
                for User in UserList:
                    if not(int(User.userData['discordID']) in UserIDs):
                        await User.save()
                        UserList.remove(User)
                    else:
                        UserIDs.remove(int(User.userData['discordID']))
                
                #** Add New User Objects For Newly Joined Listeners & Store New User List Back In Player **
                for DiscordID in UserIDs:
                    UserList.append(Users(self.client, DiscordID))
                event.player.store('Users', UserList)

                #** For All Current Listeners, Add New Song To Their Song History **
                URI = event.track['identifier'].split("/")
                ID  = URI[4].split(":")[2]
                TrackData = {ID: {"ListenedAt": Timestamp,
                                "SpotifyID": None,
                                "Name": event.track['title'],
                                "Artists": event.track['author']}}
                for User in UserList:
                    if event.track.extra['spotify'] != {}:
                        TrackData[ID]['SpotifyID'] = event.track.extra['spotify']['ID']
                        TrackData[ID]['Name'] = event.track.extra['spotify']['name']
                        TrackData[ID]['Artists'] = event.track.extra['spotify']['artists']
                    await User.incrementHistory(TrackData)


    @commands.guild_only()
    @commands.command(aliases=['p'], description="Allows you to play music through a Discord Voice Channel from a variety of sources.")
    async def play(self, ctx, *, Query):

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
                SongInfo = Database.SearchCache(SpotifyID)
                print(SongInfo)
                PlaylistInfo = None
                if SongInfo == None:

                    #** If Not Cached, Get Song Info **
                    SongInfo = SongData.GetSongInfo(SpotifyID)

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

                PlaylistInfo = SongInfo['PlaylistInfo']
                SongInfo = SongInfo['Tracks']
                Type = "Playlist"

            #**------------INPUT: ALBUM---------------**#

            elif "album" in Query:

                #** Get Album Info From Spotify Web API **
                SongInfo = SongData.GetAlbumInfo(SpotifyID)
                if SongInfo == "PlaylistNotFound":
                    raise commands.UserInputError(message="Bad URL")

                print(SongInfo)
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

                #** Create Track Object **
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
                    print(Track)
                    print(Track.duration)
                
                #** If Track Duration = 30s, Inform It's Only A Preview **
                if Track.duration == 3000:
                    await ctx.send("We could only fetch a preview for the requested song!")

                #** Send Queued Embed **
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
                    await ctx.message.delete()

                #**-----------------PLAY / ADD TO QUEUE--------------**#

                #** Add Song To Queue & Play if Not Already Playing **
                Player.add(requester=ctx.author.id, track=Track)
                if not(Player.is_playing):
                    await Player.play()

                #**-----------------ADD TO CACHE----------------**#

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
                    Database.AddFullSongCache(ToCache)
            
        elif Query.startswith("https://soundcloud.com/") or not(Query.startswith("https://")):

             #**------------INPUT: TEXT, TRACK OR PLAYLIST---------------**#

            #** Get Track(s) From Lavalink Player **
            if not(Query.startswith("https://")):
                Results = await Player.node.get_tracks("scsearch:"+Query)
                Results['tracks'] = [Results['tracks'][0]]
            else:
                Results = await Player.node.get_tracks(Query)
            print(Results)

            #**---------------SEARCH CACHE------------**#

            #** Check If Results Found & Iterate Through Results **
            if len(Results['tracks']) > 0:
                for ResultTrack in Results['tracks']:
                    URI = ResultTrack['info']['identifier'].split("/")
                    ID  = URI[4].split(":")[2]
                    ArtistURI = "/".join(ResultTrack['info']['uri'].split("/")[:4])
                    Cached = False
                    print(ID)

                    #** Check If Song Is In Cache & Set Cache To True If Data Found **
                    Spotify = Database.SearchCache(ID)
                    if Spotify != None:
                        SpotifyID = list(Spotify.keys())[0]
                        Spotify = Spotify[SpotifyID]
                        if Spotify['PartialCache']:
                            print("PartialCache")
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
                    print(Track)
                    print(Track.duration)
                    print(Track.extra['artistURI'])

                    #** If Track Duration = 30s, Inform It's Only A Preview **
                    if Track.duration == 3000:
                        await ctx.send("We could only fetch a preview for the requested song!")

                    #** Send Queued Embed If First Track In List **
                    if Results['tracks'].index(ResultTrack) == 0:
                        if Results['playlistInfo'] == {}:
                            Queued = discord.Embed(
                                title = self.Emojis["Soundcloud"]+" Track Added To Queue!",
                                description = "["+ResultTrack['info']['title']+"]("+ResultTrack['info']['uri']+") \nBy: *"+ResultTrack['info']['author']+"*")
                        else:
                            Queued = discord.Embed(
                                title = self.Emojis["Soundcloud"]+" Playlist Added To Queue!",
                                description = "["+Results['playlistInfo']['name']+"]("+Query+") - "+str(len(Results['tracks']))+" Tracks")
                        Queued.set_footer(text="Requested By "+ctx.author.display_name+"#"+str(ctx.author.discriminator))
                        await ctx.send(embed=Queued)
                        await ctx.message.delete()

                    #**-----------------PLAY / ADD TO QUEUE--------------**#

                    #** Add Song To Queue & Play if Not Already Playing **
                    Player.add(requester=ctx.author.id, track=Track)
                    if not(Player.is_playing):
                        await Player.play()
                        
                    #**-----------------ADD TO CACHE----------------**#

                    if not(Cached):
                        if Spotify != None:
                            RGB = Utils.get_colour(Spotify['Art'])
                            ToCache = {'SpotifyID': SpotifyID, 'SoundcloudID': ID, 'SoundcloudURL': Track.uri, 'Colour': RGB}
                            ToCache.update(Spotify)
                            if ToCache['Explicit'] == 'N/A':
                                ToCache['Explicit'] = None
                            Database.AddFullSongCache(ToCache)
                        else:
                            ToCache = {'SoundcloudID': ID, 'SoundcloudURL': Track.uri, 'Name': Track.title, 'Artists': [Track.author]}
                            Database.AddPartialSongCache(ToCache)


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
            Queue = "__**NOW PLAYING:**__\n"
            for i in range(-1, len(Player.queue)):
                if i == -1:
                    if Player.current.extra['spotify'] != {}:
                        Spotify = Player.current.extra['spotify']
                        Artists = Utils.format_artists(Spotify['artists'], Spotify['artistID'])
                        Queue += self.Emojis['Spotify']+"["+Spotify['name']+"]("+Spotify['URI']+")\nBy: "+Artists+"\n"
                    else:
                        Queue += self.Emojis['Soundcloud']+" ["+Player.current['title']+"]("+Player.current['uri']+")\nBy: "+Player.current['author']+"\n"
                    Queue += "--------------------\n__**UP NEXT:**__\n"
                else:
                    if Player.queue[i].extra['spotify'] != {}:
                        Spotify = Player.queue[i].extra['spotify']
                        Artists = Utils.format_artists(Spotify['artists'], Spotify['artistID'])
                        Queue += self.Emojis['Spotify']+" **"+str(i+1)+": **["+Spotify['name']+"]("+Spotify['URI']+")\nBy: "+Artists+"\n"
                    else:
                        Queue += self.Emojis['Soundcloud']+" **"+str(i+1)+": **["+Player.queue[i]['title']+"]("+Player.queue[i]['uri']+")\nBy: ["+Player.queue[i]['author']+"]("+Player.queue[i].extra['artistURI']+")\n"

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
        NowPlaying.add_field(name="Position:", value = Utils.format_time(Player.position)+" / "+ Utils.format_time(Player.current.duration))
        if Player.queue == []:
            NowPlaying.set_footer(text="Up Next: Nothing")
        else:
            NowPlaying.set_footer(text="Up Next: "+Player.queue[0]["title"])
        
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
            NowPlaying.insert_field_at(0, name="By:", value="["+Player.current.author+"]("+Player.current.extra['artistURI']+")")
            
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


    @commands.command(aliases=['song', 'i', 'songinfo'], description="Displays both basic and more in-depth information about a specified song.")
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
        
            #** Output Song Not Found If SongData.GetSongDetails() Returns Song Not Found **
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