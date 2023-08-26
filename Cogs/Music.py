
#!-------------------------IMPORT MODULES--------------------#


import os
import math
import copy
import logging
import discord
import asyncio
import lavalink
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from lavalink.events import TrackEndEvent, TrackStartEvent, TrackExceptionEvent
from Classes.Database import Database


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
        self.pagination = self.client.get_cog("EmbedPaginator")
        self.logger = logging.getLogger('lavalink')

        #** Create Client If One Doesn't Already Exist **
        if not hasattr(client, 'lavalink'):
            self.logger.info("No Previous Lavalink Client Found. Creating New Connection...")
            client.lavalink = lavalink.Client(client.user.id)
            client.lavalink.logger = self.logger
            client.add_listener(client.lavalink.voice_update_handler, 'on_socket_response')
            self.logger.debug("Lavalink listener added")
            self.logger.info("New Client Registered")
            
            #** Add Datbase Connection for Lavalink
            client.lavalink.database = Database(client.config, pool=client.config['database']['lavalink']['poolname'], size=client.config['database']['lavalink']['size'])
        else:
            self.logger.info("Found Previous Lavalink Connection")
            
        #** Connect To Lavalink If Not Already Connected **
        if len(client.lavalink.node_manager.available_nodes) == 0:
            host = client.config['lavalink']['host']
            if host == "":
                host = os.getenv(client.config['environment']['lavalink_host'], default=None)
                if host is None:
                    self.logger.error('"lavalink.host" is not set in config or environment variables!')
            port = client.config['lavalink']['port']
            if port == "":
                port = os.getenv(client.config['environment']['lavalink_port'], default=None)
                if port is None:
                    self.logger.error('"lavalink.port" is not set in config or environment variables!')

            client.lavalink.add_node(host = host, 
                                     port = port, 
                                     password = os.environ[client.config['environment']['lavalink_password']], 
                                     region = client.config['lavalink']['region'], 
                                     name = client.config['lavalink']['name'],
                                     reconnect_attempts = client.config['lavalink']['reconnect_attempts'])
            self.logger.debug(f"Connecting to {client.config['lavalink']['name']}@{host}:{port}...")
            del host
            del port

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
            
        #** If Track Has Spotify Info, Format List of Artists & Add Thumbnail
        if track.title != track.author:
            if track.source_name == "spotify":
                nowPlaying.set_thumbnail(url=track.extra['metadata']['art'])
                nowPlaying.add_field(name="By:", value=self.client.utils.format_artists(track.extra['metadata']['artists'], track.extra['metadata']['artistID']))
            else:
                nowPlaying.add_field(name="By:", value=track['author'])
            
        #** If Not A Stream, Add Duration Field
        if not(track.stream):
            nowPlaying.add_field(name="Duration:", value = self.client.utils.format_time(track.duration))
        
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
                user.save()
        
        #** Raise error to user if bot isn't already in vc
        else:
            raise app_commands.CheckFailure("BotVoice")


    async def ensure_voice(self, interaction: discord.Interaction):
        
        #** Check if there are any availbale nodes **
        if len(self.client.lavalink.node_manager.available_nodes) == 0:
            raise app_commands.CheckFailure("Lavalink")

        #** If Command Needs User To Be In VC, Check if Author is in Voice Channel
        if not(interaction.command.name in ['play', 'queue', 'nowplaying']):
            if not(interaction.user.voice) or not(interaction.user.voice.channel):
                raise app_commands.CheckFailure("UserVoice")
        
        #** Returns a Player If One Exists, Otherwise Creates One
        Player = self.client.lavalink.player_manager.create(interaction.guild_id)

        #** Join vc if not already connected & required by command
        if not(Player.is_connected):
            if interaction.command.name in ['play']:
                
                #** Check bot has permission to join and that channel has space for the bot **
                permissions = interaction.user.voice.channel.permissions_for(interaction.guild.me)
                if not(permissions.view_channel and permissions.connect and permissions.speak):
                    raise app_commands.CheckFailure("PlayPermissions")
                elif len(interaction.user.voice.channel.voice_states) >= interaction.user.voice.channel.user_limit and interaction.user.voice.channel.user_limit != 0:
                    raise app_commands.CheckFailure("ChannelFull")
                else:
                    await interaction.user.voice.channel.connect(cls=LavalinkVoiceClient)

                #** Store Key, Value Pairs In Player & Set Default Volume To 25%
                Player.store('Channel', interaction.channel_id)
                Player.store('Voice', interaction.user.voice.channel)
                Player.store('Users', {})
                Player.store('Last_Volume', 25)
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
    
    
    @lavalink.listener(TrackExceptionEvent)
    async def on_track_error(self, event: TrackExceptionEvent):
        
        #** Let user know that error has occured and which song isn't being played anymore **
        channel = self.client.get_channel(int(event.player.fetch("Channel")))
        await channel.send(f"**An error occured whilst trying to play {event.track.title} by {event.track.author}!**\nThe track has been skipped.")
        print(event.exception)
        print(event.severity)
    

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
        
        #** Disable listening history system when database is unavailable as songs won't be cached **
        if self.client.database.connected:

            #** Check If Track Should Be Added To History & Fetch Voice Channel**
            await asyncio.sleep(10)
            voice = event.player.fetch("Voice")

            #** Get List Of Members In Voice Channel **
            users = []
            for member in voice.members:
                if not(member.id in [803939964092940308, 1008107176168013835]):
                    users.append(member.id)

            #** Check Old Users Stored In Players Are Still Listening, If Not Teardown User Object **
            userDict = event.player.fetch('Users')
            for discordID, user in userDict.items():
                if not(int(discordID) in users):
                    user.save()
                    userDict.pop(discordID)
                else:
                    users.remove(int(discordID))
            
            #** Add New User Objects For Newly Joined Listeners & Store New User Dict Back In Player **
            for discordID in users:
                try:
                    userDict[str(discordID)] = self.client.userClass.User(self.client, id=discordID)
                except:
                    self.logger.debug("Exception whilst loading new user!")
            event.player.store('Users', userDict)

            #** Format Current Track Data Into Dict To Be Added To History **
            if event.track.source_name in ["spotify"] and event.track.extra['metadata']['cacheID'] is not None:
                data = {"cacheID": event.track.extra['metadata']['cacheID'],
                        "source": event.track.source_name,
                        "id": event.track.identifier,
                        "url": event.track.uri,
                        "name": event.track.title,
                        "artists": event.track.extra['metadata']['artists'],
                        "artistID": event.track.extra['metadata']['artistID'],
                        "popularity": event.track.extra['metadata']['popularity'],
                        "listenedAt": timestamp}
                
                #** For All Current Listeners, Add New Song To Their Song History **
                for user in userDict.values():
                    if user.metadata['history'] == 2 or (user.metadata['history'] == 1 and event.track.requester == user.user.id):
                        user.addSongHistory(data)


    @app_commands.guild_only()
    @app_commands.command(description="Allows you to play music through a Discord Voice Channel from a variety of sources.")
    async def play(self, interaction: discord.Interaction, input: str):
        
        #** Ensure Voice To Make Sure Client Is Good To Run & Get Player In Process **
        Player = await self.ensure_voice(interaction)
        query = input.strip('<>')
        await interaction.response.defer()
        
        #** If query is plain text, search spotify**
        if not(query.startswith("https://") or query.startswith("http://") or query.startswith("scsearch:") or query.startswith("spsearch:") or query.startswith("ytsearch:")):
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
            emoji = self.client.utils.get_emoji(Results['tracks'][0]['source_name'].title())
            Queued = discord.Embed(title = f"{str(emoji)+' ' if emoji is not None else ''}Track Added To Queue!",
                                   description = f"[{Results['tracks'][0]['title']}]({Results['tracks'][0]['uri']})")
            
            #** Format artists based on information avaiable
            if Results['tracks'][0]['title'] != Results['tracks'][0]['author']:
                if Results['tracks'][0]['source_name'] == "spotify":
                    Queued.description += f"\nBy: {self.client.utils.format_artists(Results['tracks'][0]['extra']['metadata']['artists'], Results['tracks'][0]['extra']['metadata']['artistID'])}"
                else:
                    Queued.description += f"\nBy: {Results['tracks'][0]['author']}"
        
        elif Results["loadType"] == 'PLAYLIST_LOADED':
            for i, track in enumerate(Results['tracks']):
                Player.add(requester=interaction.user.id, track=track)
                if i == 0 and not(Player.is_playing):
                    await Player.play()
            
            #** Format queued embed for playlists
            emoji = self.client.utils.get_emoji(Results['tracks'][0]['source_name'].title())
            Queued = discord.Embed(title = f"{str(emoji)+' ' if emoji is not None else ''}Playlist Added To Queue!",
                                   description = f"{Results['playlist_info']['name']} - {len(Results['tracks'])} Tracks")
        
        #** If URL Can't Be Loaded, Raise Error
        else:
            raise app_commands.CheckFailure("SongNotFound")
        
        #** Output requester name & tag in footer
        Queued.set_footer(text=f"Requested By {interaction.user.display_name}")
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
            current = Player.volume
            await Player.set_volume(percentage)
            message = f"Volume Set To {percentage}%"
            
            #** Unpause if volume increased from 0, or pause if volume set to 0
            if current == 0 and percentage > 0:
                await Player.set_pause(False)
                message += "\n*Player has been unpaused!*"
            elif current > 0 and percentage == 0:
                await Player.set_pause(True)
                message += "\n*Player has been paused!\nTo continue listening, set the volume level >0 or use the* `/pause` *command!*"
            await interaction.response.send_message(message)
                
            #** Update previously stored Last_Volume if volume has changed
            if current != percentage:
                Player.store('Last_Volume', current)

    
    @app_commands.guild_only()
    @app_commands.command(description="Pauses or unpauses the audio player.")
    async def pause(self, interaction: discord.Interaction):
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(interaction)
        
        #** Check If Player Is Actually Playing A Song **
        if not(Player.is_playing):
            raise app_commands.CheckFailure("NotPlaying")

        #** If connected, flip current pause status
        else:
            await Player.set_pause(not(Player.paused))
            if Player.paused:
                await interaction.response.send_message("Player Paused!")
            else:
                #** If volume is 0 whilst paused, restore volume to previous level before unpausing
                if Player.volume == 0:
                    volume = Player.fetch("Last_Volume")
                    await Player.set_volume(volume)
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
        player = await self.ensure_voice(interaction)
        
        #** Format Basic Queue Embed Which Follows Same Structure For All Pages **
        if player.is_playing:
            queueEmbed = discord.Embed(
                title = f"Queue For {interaction.user.voice.channel.name}:",
                colour = discord.Colour.blue())
            if interaction.guild.icon is not None:
                queueEmbed.set_thumbnail(url=interaction.guild.icon.url)
            
            #** Format Footer Based On Whether Shuffle & Repeat Are Active **
            footer = f"Shuffle: {self.client.utils.get_emoji(player.shuffle)}   Loop: {self.client.utils.get_emoji(True if player.loop in [1,2] else False)}"
            if player.loop == 2:
                footer += " (Current Queue)"
            elif player.loop == 1:
                footer += " (Current Track)"
            queueEmbed.set_footer(text=footer)
            
            #** Copy queueEmbed object for number of pages needed to be displayed! **
            pages = [copy.deepcopy(queueEmbed.to_dict()) for x in range(math.ceil((len(player.queue)+1)/10))]
            for i, page in enumerate(pages):
                
                #** Add information about currently playing song to first page! **
                body = ""
                if i == 0:
                    body = "__**NOW PLAYING:**__\n"
                    emoji = self.client.utils.get_emoji(player.current.source_name.title())
                    if player.current.source_name == "spotify":
                        artists = self.client.utils.format_artists(player.current.extra['metadata']['artists'], player.current.extra['metadata']['artistID'])
                        body += f"{emoji} [{player.current.title}]({player.current.uri})\nBy: {artists}\n"
                    else:
                        body += f"{str(emoji)+' ' if emoji is not None else ''}[{player.current.title}]({player.current.uri})\nBy: {player.current.author}\n"
                    body += "--------------------\n__**UP NEXT:**__\n"
                
                #** Add information about next 10 songs in queue that haven't already been displayed **
                if player.queue != []:
                    for j in range(i*10, (i+1)*10 if len(player.queue) >= (i+1)*10 else len(player.queue)):
                        emoji = self.client.utils.get_emoji(player.queue[j]['source_name'].title())
                        if player.queue[j].source_name == "spotify":
                            artists = self.client.utils.format_artists(player.queue[j].extra['metadata']['artists'], player.queue[j].extra['metadata']['artistID'])
                            body += f"{emoji} **{j+1}: **[{player.queue[j]['title']}]({player.queue[j]['uri']})\nBy: {artists}\n"
                        else:
                            body += f"{str(emoji)+' ' if emoji is not None else ''}**{j+1}: **[{player.queue[j]['title']}]({player.queue[j]['uri']})\nBy: {player.queue[j]['author']}\n"
                else:
                    body += "*Queue is currently empty!*"
                
                #** Add description to page & send page to discord if first page **    
                page['description'] = body
                if i == 0:
                    pageEmbed = discord.Embed.from_dict(page)
                    await interaction.response.send_message(embed=pageEmbed)
        
            #** Create Pagination For Message If Needed **
            if len(pages) > 1:
                message = await interaction.original_response()
                await self.pagination.setup(message, pages)
        
        #** If Queue Empty, Just Send Plain Text **
        else:
            await interaction.response.send_message("Queue Is Currently Empty!", ephemeral=True)


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

                #** Check If Seek Time Is Within Current Track & Seek Forward Specified Time in ms **
                if (forward * 1000) < (Player.current.duration - Player.position):
                    await Player.seek(Player.position + (forward * 1000))
                    await interaction.response.send_message(f"Skipped Forwards {forward * 1000} Seconds!")

                #** Otherwise Skip Track**
                else:
                    await Player.skip()
                    await interaction.response.send_message("Current Track Skipped!")
            
            elif backward is not None:
                #** If Time Is Less Than Start, Seek Backwards Specified Time in ms **
                if (backward * 1000) < Player.position:
                    await Player.seek(Player.position - (backward * 1000))
                    await interaction.response.send_message(f"Skipped Backwards {backward * 1000} Seconds!")
                
                #** Seek back to start if greater than current position **
                else:
                    await Player.seek(0)
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

        #** Add Requester To Embed & Send Embed To User **
        await interaction.response.send_message(embed=NowPlaying)


    @app_commands.command(description="Displays both basic and more in-depth information about a specified song.")
    async def info(self, interaction: discord.Interaction, song: str = ""):
        
        #** Get player & ensure command is ok to be run
        player = await self.ensure_voice(interaction)
        query = song.strip('<>')
        
        #** If query is plain text, search spotify
        if not(query.startswith("https://") or query.startswith("http://") or query.startswith("scsearch:") or query.startswith("spsearch:") or query.startswith("ytsearch:")):
            if not(query.lower() in ["", "nowplaying"]):
                results = await player.node.get_tracks(f"spsearch:{query}", check_local=True)
            else:
                if player.is_playing:
                    results = [player.current]
                else:
                    await interaction.response.send_message("There isn't a song currently playing. Please specifiy a track instead!", ephemeral=True)
    
        #** If query is a URL, get track(s) from lavalink
        else:
            results = await player.node.get_tracks(query, check_local=True)

        #** Check if track loaded, and queue up each track
        if results["loadType"] in ['TRACK_LOADED', 'SEARCH_RESULT']:
            track = results[0]
            if track.source_name == "spotify":
                try:
                    songInfo = self.client.music.GetSongDetails(track.identifier)
                except Exception as e:
                    raise app_commands.CheckFailure(e.message)
                else:
                    #** Format Returned Data Ready To Be Put Into The Embeds **
                    description = "**By: **" + self.client.utils.format_artists(songInfo['artists'], songInfo['artistID'])
                    links = f"{self.client.utils.get_emoji('Spotify')} Song: [Spotify]({track.url})\n"
                    if songInfo['preview'] != None:
                        links += f"{self.client.utils.get_emoji('Preview')} Song: [Preview]({songInfo['preview']})\n"
                    if songInfo['albumID'] != None and songInfo['album'] != None:
                        links += f"{self.client.utils.get_emoji('Album')} Album: [{songInfo['album']}](https://open.spotify.com/album/{songInfo['albumID']})"
                    
                    #** Setup Embed With Advanced Song Information **
                    baseEmbed = discord.Embed(title=songInfo['name'], 
                                            description=description)
                    if songInfo['art'] != None:
                        baseEmbed.set_thumbnail(url=songInfo['art'])
                    baseEmbed.set_footer(text="(2/2) React To See Basic Song Information!")
                    baseEmbed.add_field(name="Popularity:", value=songInfo['popularity'], inline=True)
                    baseEmbed.add_field(name="Explicit:", value=songInfo['explicit'], inline=True)
                    baseEmbed.add_field(name="Tempo:", value=songInfo['tempo'], inline=True)
                    baseEmbed.add_field(name="Key:", value=songInfo['key'], inline=True)
                    baseEmbed.add_field(name="Beats Per Bar:", value=songInfo['beats'], inline=True)
                    baseEmbed.add_field(name="Mode:", value=songInfo['mode'], inline=True)
                    advanced = copy.deepcopy(baseEmbed.to_dict())

                    #** Setup Embed With Basic Song Information **
                    baseEmbed.clear_fields()
                    baseEmbed.set_footer(text="(1/2) React To See Advanced Song Information!")
                    baseEmbed.add_field(name="Length:", value=songInfo['duration'], inline=False)
                    baseEmbed.add_field(name="Released:", value=songInfo['release'], inline=True)
                    baseEmbed.add_field(name="Genre:", value=songInfo['genre'].title(), inline=True)
                    baseEmbed.add_field(name="Links:", value=links, inline=False)
                    basic = baseEmbed.to_dict()

                    #** Send First Page & Setup Pagination Object **
                    await interaction.response.send_message(embed=baseEmbed)
                    message = await interaction.original_response()
                    await self.pagination.setup(message, [basic, advanced])
            else:
                await interaction.response.send_message("Info is currently only available for Spotify tracks!", ephemeral=True)
        else:
            await interaction.response.send_message("Input must be a Spotify track URL or plain text search!", ephemeral=True)


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(MusicCog(client))