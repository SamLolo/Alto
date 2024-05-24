
#!--------------------------------IMPORT MODULES-----------------------------------# 


import discord
import logging
import lavalink
from players.custom import CustomPlayer
from common.utils import format_artists, format_time


#!--------------------------------LAVALINK CLIENT-----------------------------------# 


class CustomLavalinkClient(lavalink.Client):
    
    def __init__(self, user_id: int|str, discord: discord.Client, player: lavalink.player.DefaultPlayer = CustomPlayer, **kwargs):
        CustomPlayer.set_client(discord)
        super().__init__(user_id, player, **kwargs)
        
        self.discord = discord
        self.logger = logging.getLogger("lavalink.client")
        
    
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