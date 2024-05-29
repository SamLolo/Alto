
#!-------------------------IMPORT MODULES--------------------#


# External packages
import math
import copy
import logging
import discord
import lavalink
from discord import app_commands
from discord.ext import commands
from lavalink.events import TrackEndEvent, TrackExceptionEvent

# Internal classes/functions
from clients.voice import LavalinkVoiceClient
from clients.lavalink import CustomLavalinkClient
from common.utils import format_artists, format_time


#!------------------------MUSIC COG-----------------------#


class MusicCog(commands.Cog, name="Music"):

    def __init__(self, client: discord.Client):

        #** Assign Discord Bot Client As Class Object & Setup Logging **
        self.client = client 
        self.pagination = self.client.get_cog("EmbedPaginator")
        self.logger = logging.getLogger('extensions.music')

        #** If missing Lavalink client, create new lavalink client
        if not hasattr(client, 'lavalink'):
            self.logger.info("No previous Lavalink client found. Creating new instance...")
            self.client.lavalink = CustomLavalinkClient(client.user.id, self.client)
            self.client.add_listener(client.lavalink.voice_update_handler, 'on_socket_response')
            self.logger.debug("Lavalink listener added")
            self.logger.info("New client registered")
        else:
            self.logger.info("Found previous Lavalink client")

        #** Add Event Hooks **
        self.client.lavalink.add_event_hooks(self)
        self.logger.debug("Event hooks added")


    def cog_unload(self):
        
        #** Clear Event Hooks When Cog Unloaded **
        self.client.lavalink._event_hooks.clear()
        self.logger.debug("Cleared event hooks")
        
        #** Clear custom sources
        self.client.lavalink.sources.clear()
        self.logger.debug("Cleared custom sources")


    async def _disconnect(self, player: lavalink.DefaultPlayer, guild: discord.Guild = None):

        #** If Player Connected, Get Guild Object & Disconnect From VC **
        if player.is_connected:
            if guild is None:
                guild = self.client.get_guild(int(player.guild_id))
            await guild.voice_client.disconnect()

            #** Remove Old Now Playing Message & Delete Stored Value **
            await player.nowPlaying.delete()
            player.nowPlaying = None

            #** Save All Current Users Stored In Player To Database **
            for user in player.users:
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

                #** Store channel used for nowPlaying & voice channel player is in
                Player.channel = interaction.channel
                Player.voice = interaction.user.voice.channel
                
            #** If bot doesn't need to connect and isn't already connected, raise error
            elif interaction.command.name in ['pause', 'skip', 'queue', 'seek', 'nowplaying', 'loop']:
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
        await event.player.channel.send(f"**An error occured whilst trying to play {event.track.title} by {event.track.author}!**\nThe track has been skipped.")
        print(event.exception)
        print(event.severity)


    @app_commands.guild_only()
    @app_commands.command()
    async def play(self, interaction: discord.Interaction, input: str):
        """Allows you to play music through a Discord Voice Channel from a variety of sources.

        Args:
            interaction (discord.Interaction): The discord interaction object that triggered the command.
            input (str): The requested song to play.
        """
        
        # Ensure Voice To Make Sure Client Is Good To Run & Get Player In Process
        player = await self.ensure_voice(interaction)
        query = input.strip('<>')
        await interaction.response.defer()
        
        # If query is plain text, search spotify, otherwise get track(s) from lavalink
        if not(query.startswith("https://") or query.startswith("http://") or query.startswith("scsearch:") or query.startswith("spsearch:") or query.startswith("ytsearch:")):
            result = await self.client.lavalink.get_tracks(f"spsearch:{query}", check_local=True)
        else:
            result = await self.client.lavalink.get_tracks(query, check_local=True)

        # Check if track(s) loaded, and queue up (each) track
        if result.load_type in [lavalink.LoadType.TRACK, lavalink.LoadType.SEARCH]:
            track = result['tracks'][0]
            player.add(requester=interaction.user.id, track=track)
            if not(player.is_playing):
                await player.play()
            
            # Create queued embed for single track
            emoji = self.client.get_emoji(track.source_name.title())
            queued = discord.Embed(title = f"{str(emoji)+' ' if emoji is not None else ''}Track Added To Queue!",
                                   description = f"[{track.title}]({track.uri})")
            if track.source_name == "spotify":
                queued.description += f"\nBy: {format_artists(track.extra['metadata']['artists'])}"
            else:
                queued.description += f"\nBy: {track.author}"
        
        elif result.load_type == lavalink.LoadType.PLAYLIST:
            for i, track in enumerate(result['tracks']):
                player.add(requester=interaction.user.id, track=track)
                if i == 0 and not(player.is_playing):
                    await player.play()
            
            # Format queued embed for playlists
            emoji = self.client.get_emoji(result['tracks'][0]['source_name'].title())
            queued = discord.Embed(title = f"{str(emoji)+' ' if emoji is not None else ''}Playlist Added To Queue!",
                                   description = f"{result['playlist_info']['name']} - {len(result['tracks'])} Tracks")
        
        # If LoadType is empty or an error, return error message to user
        else:
            raise app_commands.CheckFailure("SongNotFound")
        
        # Output requester name & tag in footer
        queued.set_footer(text=f"Requested By {interaction.user.display_name}")
        await interaction.followup.send(embed=queued)
        

    @app_commands.guild_only()
    @app_commands.command()
    async def disconnect(self, interaction: discord.Interaction):
        """Stops music, clears queue and disconnects the bot!

        Args:
            interaction (discord.Interaction): The discord interaction object that triggered the command.
        """

        # Get player & check command is good to be run!
        player = await self.ensure_voice(interaction)
        if not(player.is_connected):
            raise app_commands.CheckFailure("BotVoice")

        # Clear queue and stop playback. Player will disconnect automatically
        player.queue.clear()
        if player.is_playing:
            await player.stop()
        else:
            await self._disconnect(player, guild=interaction.guild)
        await interaction.response.send_message("Disconnected!")


    @app_commands.guild_only()
    @app_commands.command()
    async def volume(self, interaction: discord.Interaction, percentage: app_commands.Range[int, 0, 100] = None):
        """Adjusts the volume of the audio player between 0% and 100%.

        Args:
            interaction (discord.Interaction): The discord interaction object that triggered the command.
            percentage (app_commands.Range[int, 0, 100], optional): The new percentage to set the volume level to. Defaults to None, 
                                                                    in which case the current volume level is displayed.
        """

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

    
    @app_commands.guild_only()
    @app_commands.command()
    async def pause(self, interaction: discord.Interaction):
        """Pauses or unpauses the audio player.

        Args:
            interaction (discord.Interaction): The discord interaction object that triggered the command.
        """
        
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
                    await Player.set_volume(Player.last_volume)
                await interaction.response.send_message("Player Unpaused!")

    
    @app_commands.guild_only()
    @app_commands.command()
    async def skip(self, interaction: discord.Interaction):
        """Skips the currently playing song and plays the next song in the queue.

        Args:
            interaction (discord.Interaction): The discord interaction object that triggered the command.
        """

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
    @app_commands.command()
    async def queue(self, interaction: discord.Interaction):
        """Displays the server's current queue of songs.
        
        Args:
            interaction (discord.Interaction): The discord interaction object that triggered the command.
        """
                
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
            footer = f"Shuffle: {self.client.get_emoji(player.shuffle)}   Loop: {self.client.get_emoji(True if player.loop in [1,2] else False)}"
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
                    emoji = self.client.get_emoji(player.current.source_name.title())
                    if player.current.source_name == "spotify":
                        artists = format_artists(player.current.extra['metadata']['artists'])
                        body += f"{emoji} [{player.current.title}]({player.current.uri})\nBy: {artists}\n"
                    else:
                        body += f"{str(emoji)+' ' if emoji is not None else ''}[{player.current.title}]({player.current.uri})\nBy: {player.current.author}\n"
                    body += "--------------------\n__**UP NEXT:**__\n"
                
                #** Add information about next 10 songs in queue that haven't already been displayed **
                if player.queue != []:
                    for j in range(i*10, (i+1)*10 if len(player.queue) >= (i+1)*10 else len(player.queue)):
                        emoji = self.client.get_emoji(player.queue[j]['source_name'].title())
                        if player.queue[j].source_name == "spotify":
                            artists = format_artists(player.queue[j].extra['metadata']['artists'])
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
    @app_commands.command()
    async def shuffle(self, interaction: discord.Interaction):
        """Shuffles & un-shuffles the playback of songs in the queue.

        Args:
            interaction (discord.Interaction): The discord interaction object that triggered the command.
        """
        
        #** Ensure Voice Before Allowing Command To Run & Get Guild Player **
        Player = await self.ensure_voice(interaction)

        #** Enable / Disable Shuffle Mode **
        Player.shuffle = not(Player.shuffle)
        if Player.shuffle:
            await interaction.response.send_message("Player Shuffled!")
        else:
            await interaction.response.send_message("Player No Longer Shuffled!")


    @app_commands.guild_only()
    @app_commands.command()
    @app_commands.choices(state=[app_commands.Choice(name="Off", value=0),
                                 app_commands.Choice(name="Current Track", value=1),
                                 app_commands.Choice(name="Current Queue", value=2)])
    async def loop(self, interaction: discord.Interaction, state: app_commands.Choice[int]):
        """Loops the current song or queue until the command is ran again.

        Args:
            interaction (discord.Interaction): The discord interaction object that triggered the command.
            state (app_commands.Choice[int]): The new choice for how the player should loop.
        """
        
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
    @app_commands.command()
    async def seek(self, interaction: discord.Interaction, forward: int = None, backward: int = None):
        """Skips seconds forward or backwards in time in the currently playing song.

        Args:
            interaction (discord.Interaction): The discord interaction object that triggered the command.
            forward (int, optional): The number of seconds to skip forwards through the current song. Defaults to None.
            backward (int, optional): The number of seconds to skip backwards through the current song. Defaults to None.
        """
        
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
    @app_commands.command()
    async def nowplaying(self, interaction: discord.Interaction):
        """Displays information about the currently playing song.

        Args:
            interaction (discord.Interaction): The discord interaction object that triggered the command.
        """
        
        #** Ensure Cmd Is Good To Run & Get Player **
        Player = await self.ensure_voice(interaction)
        
        #** Create Now Playing Embed **
        NowPlaying = self.client.lavalink.format_nowplaying(Player)
        if not(Player.current.stream):
            NowPlaying.set_field_at(1, name="Position:", value = f"{format_time(Player.position)} / {format_time(Player.current.duration)}")

        #** Add Requester To Embed & Send Embed To User **
        await interaction.response.send_message(embed=NowPlaying)


    @app_commands.command()
    async def info(self, interaction: discord.Interaction, song: str = ""):
        """Displays both basic and more in-depth information about a specified song.

        Args:
            interaction (discord.Interaction): The discord interaction object that triggered the command.
            song (str, optional): The track query to fetch information for. Defaults to "".
        """
        
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
                    description = "**By: **" + format_artists(songInfo['artists'], songInfo['artistID'])
                    links = f"{self.client.get_emoji('Spotify')} Song: [Spotify]({track.url})\n"
                    if songInfo['preview'] != None:
                        links += f"{self.client.get_emoji('Preview')} Song: [Preview]({songInfo['preview']})\n"
                    if songInfo['albumID'] != None and songInfo['album'] != None:
                        links += f"{self.client.get_emoji('Album')} Album: [{songInfo['album']}](https://open.spotify.com/album/{songInfo['albumID']})"
                    
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
                await interaction.response.send_message("Sorry, song info is currently only available for Spotify tracks!", ephemeral=True)
        else:
            await interaction.response.send_message("Your input must be a Spotify track URL or plain text search!", ephemeral=True)


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    """
    Adds the Music extension to the clients list of cogs.
    
    Parameters:
    client (discord.Client): The discord client that has loaded the extension.
    
    Returns:
    None
    """
    await client.add_cog(MusicCog(client))