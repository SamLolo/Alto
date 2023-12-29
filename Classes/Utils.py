
#!-------------------------IMPORT MODULES-----------------------!#


import discord
import skimage
import lavalink
import numpy as np


#!-------------------------UTILS------------------------!#


class Utility():

    def __init__(self, client: discord.client = None):
        self.client = client

        
    def get_colour(self, url: str = None):
        
        # Return none if no url passed in
        if url is None:
            return None
        
        # Get most dominant colour in image
        img = skimage.io.imread(url)        
        colour = np.mean(img, axis=(0, 1), dtype=np.int32)
        
        # Return RGB colour tuple
        return tuple(colour)
    
    
    def format_nowplaying(self, player: lavalink.DefaultPlayer, track: lavalink.AudioTrack):
        
        # Create new embed
        nowPlaying = discord.Embed(title = "Now Playing:",
                                   description = f"[{track['title']}]({track['uri']})")
        
        # Set footer to be next song in queue
        if player.queue == []:
            nowPlaying.set_footer(text="Up Next: Nothing")
        else:
            nowPlaying.set_footer(text=f"Up Next: {player.queue[0]['title']}")
        
        # Set source of audio, with emoji if available
        emoji = self.get_emoji(track.source_name.title())  
        if emoji is not None:
            nowPlaying.set_author(name=f"Playing From {track.source_name.title()}", icon_url=emoji.url)
            
        #  If track has is from Spotify, format list of artists & add thumbnail
        if track.title != track.author:
            if track.source_name == "spotify":
                nowPlaying.set_thumbnail(url=track.artwork_url)
                nowPlaying.add_field(name="By:", value=self.format_artists(track.extra['metadata']['artists']))
            else:
                nowPlaying.add_field(name="By:", value=track.author)
            
        # If not a http stream, add duration field
        if not(track.stream):
            nowPlaying.add_field(name="Duration:", value = self.format_time(track.duration))
        
        # Add requester to embed
        user = self.client.get_user(track.requester)
        if user is not None:
            nowPlaying.add_field(name="Requested By: ", value=user.mention, inline=False)
        return nowPlaying


    def format_artists(self, artists: list):

        # Add comma up until 2nd to last artist in list, using & between the last 2 artists
        formatted = ""
        for index, artist in enumerate(artists):
            if index > 0 and index < len(artists)-1:
                formatted += ", "
            elif index == len(artists)-1 and index != 0:
                formatted += " & "
            
            # Format string based on whether links are available
            if 'id' in artist.keys() and artist['id'] is not None:
                formatted += f"[{artist['name']}](https://open.spotify.com/artist/{artist['id']})"
            else:
                formatted += artist['name']
        return formatted


    def format_time(self, time: int):
        
        # Parse time into datetime object, then create strings in 24hr clock format
        time = lavalink.parse_time(time)
        if time[1] == 0.0:
            return f'{int(time[2])}:{str(int(time[3])).zfill(2)}'
        else:
            return f'{int(time[1])}:{str(int(time[2])).zfill(2)}:{str(int(time[3])).zfill(2)}'
    
    
    def get_emoji(self, name: str):
        
        # Return unicode tick/cross if name is boolean value
        if name == True:
            return "✅"
        elif name == False:
            return "❌"
        
        # Search through sequence of client emojis and return found emoji object
        for emoji in self.client.emojis:
            if emoji.name == name:
                return emoji