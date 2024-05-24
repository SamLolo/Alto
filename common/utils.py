
#!-------------------------IMPORT MODULES-----------------------!#


import skimage
import lavalink
import numpy as np


#!-------------------------UTILITY FUNCTIONS------------------------!#

        
def get_colour(url: str = None):
    
    # Return none if no url passed in
    if url is None:
        return None
    
    # Get most dominant colour in image
    img = skimage.io.imread(url)        
    colour = np.mean(img, axis=(0, 1), dtype=np.int32)
    
    # Return RGB colour tuple
    return tuple(colour)


def format_artists(artists: list):

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


def format_time(time: int):
    
    # Parse time into datetime object, then create strings in 24hr clock format
    time = lavalink.parse_time(time)
    if time[1] == 0.0:
        return f'{int(time[2])}:{str(int(time[3])).zfill(2)}'
    else:
        return f'{int(time[1])}:{str(int(time[2])).zfill(2)}:{str(int(time[3])).zfill(2)}'