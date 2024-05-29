
#!--------------------------------IMPORT MODULES-----------------------------------# 


# External packages
import os
import discord
import logging
import tomlkit
import lavalink

# Internal classes/functions
from common.players import CustomPlayer
from common.database import DatabasePool
from common.utils import format_artists, format_time
from sources.spotify import SpotifySource


#!--------------------------------LAVALINK CLIENT-----------------------------------# 


class CustomLavalinkClient(lavalink.Client):
    
    def __init__(self, user_id: int|str, discord: discord.Client, player: lavalink.player.DefaultPlayer = CustomPlayer, **kwargs):
        # Create reference to Discord Client
        self.discord = discord
        CustomPlayer.set_client(discord)
        
        # Initialise client & setup logging
        super().__init__(user_id, player, **kwargs)
        self.logger = logging.getLogger("lavalink.client")
        
        # Load config
        with open("config.toml", "rb")  as configFile:
            self.config = tomlkit.load(configFile)
        
        # Create database connection
        self.database = DatabasePool(name=self.config['database']['lavalink']['poolname'], size=self.config['database']['lavalink']['size'])
        
        # Connect to Lavalink if no previous connection has been established
        if len(self.node_manager.available_nodes) == 0:
            self.__connect()
        
        # Register Custom Sources
        super().register_source(SpotifySource(self))
        self.logger.debug("Registered custom sources")
        
    
    def __connect(self):
        host = self.config['lavalink']['host']
        if host == "":
            host = os.getenv(self.config['environment']['lavalink_host'], default=None)
            if host is None:
                self.logger.error('"lavalink.host" is not set in config or environment variables!')
        port = self.config['lavalink']['port']
        if port == "":
            port = os.getenv(self.config['environment']['lavalink_port'], default=None)
            if port is None:
                self.logger.error('"lavalink.port" is not set in config or environment variables!')

        self.client.lavalink.add_node(host = host, 
                                        port = port, 
                                        password = os.environ[self.config['environment']['lavalink_password']], 
                                        region = self.config['lavalink']['region'], 
                                        name = self.config['lavalink']['name'])
        self.logger.debug(f"Connecting to {self.config['lavalink']['name']}@{host}:{port}...")
        del host
        del port
        
    
    def format_nowplaying(self, player: lavalink.DefaultPlayer):
        
        # Create new embed
        track = player.current
        nowPlaying = discord.Embed(title = "Now Playing:",
                                   description = f"[{track['title']}]({track['uri']})")
        
        # Set footer to be next song in queue
        if player.queue == []:
            nowPlaying.set_footer(text="Up Next: Nothing")
        else:
            nowPlaying.set_footer(text=f"Up Next: {player.queue[0]['title']}")
        
        # Set source of audio, with emoji if available
        emoji = self.discord.get_emoji(track.source_name.title())  
        if emoji is not None:
            nowPlaying.set_author(name=f"Playing From {track.source_name.title()}", icon_url=emoji.url)
            
        #  If track has is from Spotify, format list of artists & add thumbnail
        if track.title != track.author:
            if track.source_name == "spotify":
                nowPlaying.set_thumbnail(url=track.artwork_url)
                nowPlaying.add_field(name="By:", value=format_artists(track.extra['metadata']['artists']))
            else:
                nowPlaying.add_field(name="By:", value=track.author)
            
        # If not a http stream, add duration field
        if not(track.stream):
            nowPlaying.add_field(name="Duration:", value = format_time(track.duration))
        
        # Add requester to embed
        user = self.discord.get_user(track.requester)
        if user is not None:
            nowPlaying.add_field(name="Requested By: ", value=user.mention, inline=False)
        return nowPlaying