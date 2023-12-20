
#!-------------------------IMPORT MODULES-----------------------!#


import lavalink
import numpy as np
import skimage


#!-------------------------UTILS------------------------!#


class Utility():

    def __init__(self, client = None):

        #** Load Config File **
        self.client = client

        
    def get_colour(self, URL):
        
        #** Return None if Null passed in **
        if URL is None:
            return None
        
        #** Get Most Dominant Colour In Image **
        img = skimage.io.imread(URL)        
        colour = np.mean(img, axis=(0, 1), dtype=np.int32)
        
        #** Return RGB Colour Tuple **
        return tuple(colour)


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


    def format_time(self, time):
        
        #** Parse Time Into Days, Hours, Minutes & Seconds **
        Time = lavalink.parse_time(time)
        
        #** Create Strings Of Time In 24 Hour Clock **
        if Time[1] == 0.0:
            return f'{int(Time[2])}:{str(int(Time[3])).zfill(2)}'
        else:
            return f'{int(Time[1])}:{str(int(Time[2])).zfill(2)}:{str(int(Time[3])).zfill(2)}'
    
    
    def get_emoji(self, name):
        #** Return Unicode tick/cross if name is boolean value
        if name == True:
            return "✅"
        elif name == False:
            return "❌"
        
        #** Search through sequence of client emojis and return found emoji object **
        for emoji in self.client.emojis:
            if emoji.name == name:
                return emoji