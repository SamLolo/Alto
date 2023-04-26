
#!-------------------------IMPORT MODULES--------------------#


import math
import copy
import logging
import discord
import asyncio
import lavalink
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from lavalink.events import TrackEndEvent, TrackStartEvent


#!------------------------IMPORT CUSTOM SOURCES-----------------#


from Sources.Spotify import SpotifySource


#!--------------------CUSTOM VOICE PROTOCOL------------------#


class LavalinkVoiceClient(discord.VoiceClient):

    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        
        #** Setup Class Attributes **
        self.client = client
        self.channel = channel
        self.lavalink = self.client.lavalink


    async def on_voice_server_update(self, data):

        #** Transform Server Data & Hand It Down To Lavalink Voice Update Handler **
        lavalink_data = {'t': 'VOICE_SERVER_UPDATE',
                         'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)
        
    
    async def on_voice_state_update(self, data):
        
        #** Transform Voice State Data & Hand It Down To Lavalink Voice Update Handler **
        lavalink_data = {'t': 'VOICE_STATE_UPDATE',
                         'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)


    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False):
        
        #** Change Voice State To Channel Passed Into Voice Protocol**
        await self.channel.guild.change_voice_state(channel=self.channel)
        

    async def disconnect(self, *, force: bool = False):

        #** Get Player & Change Voice Channel To None **
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=None)
        
        #** Cleanup VoiceState & Player Attributes **
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
            self.logger.info("No Previous Lavalink Client Found. Creating New Connection...")
            client.lavalink = lavalink.Client(client.user.id)
            client.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'eu', name='default-node')
            client.add_listener(client.lavalink.voice_update_handler, 'on_socket_response')
            client.logger.debug("Lavalink listener added")
            self.logger.info("New Client Registered")
        else:
            self.logger.info("Found Previous Lavalink Connection")

        #** Add Event Hook **
        self.client.lavalink.add_event_hooks(self)
        self.logger.debug("Event hooks added")
        
        #** Register Custom Sources
        self.client.lavalink.register_source(SpotifySource(client))
        self.logger.debug("Registered custom sources")


    def cog_unload(self):
        
        #** Clear Event Hooks When Cog Unloaded **
        self.client.lavalink._event_hooks.clear()
        self.logger.debug("Cleared event hooks")
        
        #** Clear custom sources
        self.client.lavalink.sources.clear()
        self.logger.debug("Cleared custom sources")


    def _format_nowplaying(self, player: lavalink.DefaultPlayer, track: lavalink.AudioTrack):
        
        #** Create Now Playing Embed
        nowPlaying = discord.Embed(title = "Now Playing:",
                                   description = f"[{track['title']}]({track['uri']})")
        
        #** Add Up Next To Footer Of Embed
        if player.queue == []:
            nowPlaying.set_footer(text="Up Next: Nothing")
        else:
            nowPlaying.set_footer(text=f"Up Next: {player.queue[0]['title']}")
        
        #** Set source of audio, with emoji if available
        emoji = self.client.utils.get_emoji(track.source_name.title())  
        if emoji is not None:
            nowPlaying.set_author(name=f"Playing From {track.source_name.title()}", icon_url=emoji.url)
        else:
            nowPlaying.set_author(name=f"Playing From {track.source_name.title()}")
            
        #** If Track Has Spotify Info, Format List of Artists & Add Thumbnail
        if "spotify" in track.extra.keys():
            nowPlaying.set_thumbnail(url=track.extra['spotify']['art'])
            nowPlaying.add_field(name="By:", value=self.client.utils.format_artists(track.extra['spotify']['artists'], track.extra['spotify']['artistID']))
        else:
            nowPlaying.add_field(name="By:", value=track['author'])
            
        #** If Not A Stream, Add Duration Field
        if not(track.stream):
            nowPlaying.add_field(name="Duration:", value = self.client.utils.format_time(track.duration))
        else:
            nowPlaying.add_field(name="Duration: ", value="N/A")
        
        #** Add requester to embed
        user = self.client.get_user(track.requester)
        if user is not None:
            nowPlaying.add_field(name="Requested By: ", value=user.mention, inline=False)
        return nowPlaying


    async def _disconnect(self, player: lavalink.DefaultPlayer, guild: discord.Guild = None):

        #** If Player Connected, Get Guild Object & Disconnect From VC **
        if player.is_connected:
            if guild is None:
                guild = self.client.get_guild(int(player.guild_id))
            await guild.voice_client.disconnect()

            #** Remove Old Now Playing Message & Delete Stored Value **
            oldMessage = player.fetch('NowPlaying')
            await oldMessage.delete()
            player.delete('NowPlaying')

            #** Save All Current Users Stored In Player To Database **
            userDict = player.fetch('Users')
            for user in userDict.values():
                await user.save()
        
        #** Raise error to user if bot isn't already in vc
        else:
            raise app_commands.CheckFailure("BotVoice")


    async def ensure_voice(self, interaction: discord.Interaction):

        #** If Command Needs User To Be In VC, Check if Author is in Voice Channel
        if not(interaction.command.name in ['queue', 'nowplaying']):
            if not(interaction.user.voice) or not(interaction.user.voice.channel):
                raise app_commands.CheckFailure("UserVoice")
        
        #** Returns a Player If One Exists, Otherwise Creates One
        Player = self.client.lavalink.player_manager.create(interaction.guild_id)

        #** Join vc if not already connected & required by command
        if not(Player.is_connected):
            if interaction.command.name in ['play']:
                await interaction.user.voice.channel.connect(cls=LavalinkVoiceClient)

                #** Store Key, Value Pairs In Player & Set Default Volume To 25%
                Player.store('Channel', interaction.channel_id)
                Player.store('Voice', interaction.user.voice.channel)
                Player.store('Users', {})
                await Player.set_volume(25)
                
            #** If bot doesn't need to connect and isn't already connected, raise error
            elif interaction.command.name in ['stop', 'pause', 'skip', 'queue', 'seek', 'nowplaying', 'loop']:
                raise app_commands.CheckFailure("BotVoice")
          
        #** Raise error is user in different vc to bot
        else:
            if int(Player.channel_id) != interaction.user.voice.channel.id:
                raise app_commands.CheckFailure("SameVoice")
            
        return Player


    @lavalink.listener(TrackEndEvent)
    async def on_track_end(self, event: TrackEndEvent):
            
        #** If Queue Empty, Save User Data & Disconnect From VC
        if event.player.queue == [] and event.player.is_connected:
            await self._disconnect(event.player)
            

    @lavalink.listener(TrackStartEvent)
    async def on_track_start(self, event: TrackStartEvent):
            
        #** Get Channel & Print Out Now Playing Information When New Track Starts
        timestamp = datetime.now()
        channel = self.client.get_channel(int(event.player.fetch("Channel")))
        
        #** Send Now Playing Embed To Channel Where First Play Cmd Was Ran
        nowPlaying = self._format_nowplaying(event.player, event.track)
        message = await channel.send(embed=nowPlaying)

        #** Clear previous now playing embed & output new one into previous channel
        old = event.player.fetch('NowPlaying')
        event.player.store('NowPlaying', message)
        await asyncio.sleep(0.5)
        if old != None:
            await old.delete()

        #**-------------Add Listening History-------------**#

        #** Check If Track Should Be Added To History & Fetch Voice Channel**
        await asyncio.sleep(5)
        voice = event.player.fetch("Voice")

        #** Get List Of Members In Voice Channel **
        users = []
        for member in voice.members:
            if member.id != 803939964092940308:
                users.append(member.id)

        #** Check Old Users Stored In Players Are Still Listening, If Not Teardown User Object **
        userDict = event.player.fetch('Users')
        for discordID, user in userDict.items():
            if not(int(discordID) in users):
                await user.save()
                userDict.pop(discordID)
            else:
                users.remove(int(discordID))
        
        #** Add New User Objects For Newly Joined Listeners & Store New User Dict Back In Player **
        for discordID in users:
            userDict[str(discordID)] = self.client.userClass.User(self.client, discordID)
        event.player.store('Users', userDict)

        #** Format Current Track Data Into Dict To Be Added To History **
        #uri = event.track['identifier'].split("/")
        #Id  = uri[4].split(":")[2]
        #trackData = {"ID": id,
        #             "ListenedAt": timestamp,
        #             "SpotifyID": None,
        #             "Name": event.track['title'],
        #             "Artists": [event.track['author']],
        #             "URI": event.track['uri']}
        #if 'spotify' in event.track.extra.keys():
        #    trackData['Artists'] = event.track.extra['spotify']['artists']
        #    trackData['ArtistIDs'] = event.track.extra['spotify']['artistID']
        #    trackData['Popularity'] = event.track.extra['spotify']['popularity']
        #
        #** For All Current Listeners, Add New Song To Their Song History **
        #for user in userDict.values():
        #    await user.incrementHistory(trackData)


    @app_commands.guild_only()
    @app_commands.command(description="Allows you to play music through a Discord Voice Channel from a variety of sources.")
    async def play(self, interaction: discord.Interaction, input: str):
        
        #** Ensure Voice To Make Sure Client Is Good To Run & Get Player In Process **
        Player = await self.ensure_voice(interaction)
        query = input.strip('<>')
        await interaction.response.defer()
        
        #** If query is plain text, search spotify**
        if not(query.startswith("https://") or query.startswith("http://") or query.startswith("scsearch:")):
            Results = await Player.node.get_tracks(f"spsearch:{query}", check_local=True)
    
        #** If query is a URL, Get track(s) from lavalink
        else:
            Results = await Player.node.get_tracks(query, check_local=True)

        #** Check if track loaded, and queue up each track
        if Results["loadType"] in ['TRACK_LOADED', 'SEARCH_RESULT']:
            Player.add(requester=interaction.user.id, track=Results['tracks'][0])
            if not(Player.is_playing):
                await Player.play()
            
            #** Create queued embed for single track
            Queued = discord.Embed(title = f"{self.client.utils.get_emoji(Results['tracks'][0]['source_name'].title())} Track Added To Queue!",
                                   description = f"[{Results['tracks'][0]['title']}]({Results['tracks'][0]['uri']})")
            
            #** Format artists based on information avaiable
            if "spotify" in Results['tracks'][0]['extra'].keys():
                Queued.description += f"\nBy: {self.client.utils.format_artists(Results['tracks'][0]['extra']['spotify']['artists'], Results['tracks'][0]['extra']['spotify']['artistID'])}"
            else:
                Queued.description += f"\nBy: {Results['tracks'][0]['author']}"
        
        elif Results["loadType"] == 'PLAYLIST_LOADED':
            for i, track in enumerate(Results['tracks']):
                Player.add(requester=interaction.user.id, track=track)
                if i == 0 and not(Player.is_playing):
                    await Player.play()
            
            #** Format queued embed for playlists
            Queued = discord.Embed(title = f"{self.client.utils.get_emoji(Results['tracks'][0]['source_name'].title())} Playlist Added To Queue!",
                                   description = f"{Results['playlist_info']['name']} - {len(Results['tracks'])} Tracks")
        
        #** If URL Can't Be Loaded, Raise Error
        else:
            raise app_commands.CheckFailure("SongNotFound")
        
        #** Output requester name & tag in footer
        Queued.set_footer(text=f"Requested By {interaction.user.display_name}#{interaction.user.discriminator}")
        await interaction.followup.send(embed=Queued)
        

    @app_commands.guild_only()
    @app_commands.command(description="Stops music, clears queue and disconnects the bot!")
    async def disconnect(self, interaction: discord.Interaction):

        #** Ensure Voice To Make Sure Client Is Good To Run & Get Guild Player**
        Player = await self.ensure_voice(interaction)

        #** Clear Queue & Stop Playing Music If Music Playing**
        if Player.is_playing:
            await Player.stop()
            Player.queue.clear()
        
        #** Disconnect From VC & Send Message Accordingly **
        await self._disconnect(Player, guild=interaction.guild)
        await interaction.response.send_message("Disconnected!")


    @app_commands.guild_only()
    @app_commands.command(description="Adjusts the volume of the audio player between 0% and 100%.")
    async def volume(self, interaction: discord.Interaction, percentage: app_commands.Range[int, 0, 100] = None):

        #** Ensure Voice To Make Sure Client Is Good To Run & Get Player
        Player = await self.ensure_voice(interaction)
        
        #** If No Volume Change, Return Current Volume
        if percentage is None:
            await interaction.response.send_message(f"**Current Volume:** {Player.volume}%")

        #** If Connected Set Volume & Confirm Volume Change
        else: 
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
        
        #** Format Queue Into Embed & Send Into Discord **
        if Player.queue != []:
            queueEmbed = discord.Embed(
                title = f"Queue For {interaction.user.voice.channel.name}:",
                colour = discord.Colour.blue())
            queueEmbed.set_thumbnail(url=interaction.guild.icon.url)
            
            #** Format Footer Based On Whether Shuffle & Repeat Are Active **
            if Player.shuffle:
                footer = "Shuffle: ✅  "
            else:
                footer = "Shuffle: ❌  "
            if Player.repeat:
                footer += "Loop: ✅"
            else:
                footer += "Loop: ❌"
            queueEmbed.set_footer(text=footer)
            
            pages = [copy.deepcopy(queueEmbed.to_dict()) for x in range(math.ceil(len(Player.queue)/10))]
            print(pages)
            print(Player.current)
            print(Player.queue)
            
            #** Format body of each page of 
            body = "__**NOW PLAYING:**__\n"
            
            #** If Not Stream, Check If Has Spotify Data **
            emoji = self.client.utils.get_emoji(Player.current.source_name.title())
            if "spotify" in Player.current.extra.keys():

                #** Format Data For Spotify Else Format And Add Data For SoundCloud Instead **
                Artists = self.client.utils.format_artists(Player.current.extra['spotify']['artists'], Player.current.extra['spotify']['artistID'])
                body += f"{self.client.utils.get_emoji('Spotify')} [{Player.current['title']}]({Player.current['uri']})\nBy: {Artists}\n"
            else:
                body += f"{self.client.utils.get_emoji('Soundcloud')} [{Player.current['title']}]({Player.current['uri']})\nBy: {Player.current['author']}\n"
            body += "--------------------\n__**UP NEXT:**__\n"

            #** Loop Through Queue **
            for i in range(-1, len(Player.queue)):

                #** -1 Indicates Currently Playing Song, Added First **
                if i == -1:

                    #** If Not Stream, Check If Has Spotify Data **
                    if not(Player.current.stream):
                        if "spotify" in Player.current.extra.keys():

                            #** Format Data For Spotify Else Format And Add Data For SoundCloud Instead **
                            Artists = self.client.utils.format_artists(Player.current.extra['spotify']['artists'], Player.current.extra['spotify']['artistID'])
                            body += f"{self.client.utils.get_emoji('Spotify')} [{Player.current['title']}]({Player.current['uri']})\nBy: {Artists}\n"
                        else:
                            body += f"{self.client.utils.get_emoji('Soundcloud')} [{Player.current['title']}]({Player.current['uri']})\nBy: {Player.current['author']}\n"
                    
                    #** If Stream, Format Data For Stream, And Add Up Next Seperator For Rest Of Queue **
                    else:
                        body += "["+Player.current['title']+"]("+Player.current['uri']+")\nBy: "+Player.current['author']+"\n"
                    body += "--------------------\n__**UP NEXT:**__\n"
                
                #** For i>=0, Work Though Index's In Queue **
                else:

                    #** If Track At Index Is Not Stream, Check If Song Has Spotify Data **
                    if not(Player.queue[i].stream):
                        if "spotify" in Player.queue[i].extra.keys():

                            #** Format Data For Spotify Else Format And Add Data For SoundCloud Instead **
                            Spotify = Player.queue[i].extra['spotify']
                            Artists = self.client.utils.format_artists(Spotify['artists'], Spotify['artistID'])
                            body += f"{self.client.utils.get_emoji('Spotify')} **{i+1}: **[{Player.current['title']}]({Player.current['uri']})\nBy: {Artists}\n"
                        else:
                            body += f"{self.client.utils.get_emoji('Soundcloud')} **{i+1}: **[{Player.queue[i]['title']}]({Player.queue[i]['uri']})\nBy: {Player.queue[i]['author']}\n"
                    
                    #** If Stream, Format Data For Stream & Add To String **
                    else:
                        body += f"**{i+1}: **[{Player.queue[i]['title']}]({Player.queue[i]['uri']})\nBy: {Player.queue[i]['author']}\n"

            queueEmbed.description = body
            await interaction.response.send_message(embed=queueEmbed)
        
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
        NowPlaying = self._format_nowplaying(Player, Player.current)
        if not(Player.current.stream):
            NowPlaying.set_field_at(1, name="Position:", value = f"{self.client.utils.format_time(Player.position)} / {self.client.utils.format_time(Player.current.duration)}")
        else:
            NowPlaying.set_field_at(1, name="Position:", value = "N/A")

        #** Add Requester To Embed & Send Embed To User **
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
            try:
                SongInfo = self.client.music.GetSongDetails(SpotifyID)
            except Exception as e:
                raise app_commands.CheckFailure(e.message)
            else:
                
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
                await self.Pagination.add_embed(Page.id, [Basic, Advanced])


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(MusicCog(client))