
#!-------------------------IMPORT MODULES-----------------------!#


import lavalink
import numpy as np
import skimage


#!-------------------------UTILS------------------------!#


class Utility():

    def __init__(self, client):

        #** Load Config File **
        self.client = client

        
    async def get_colour(self, URL):
        
        #** Get Most Dominant Colour In Image **
        img = skimage.io.imread(URL)        
        colour = np.mean(img, axis=(0, 1), dtype=np.int32)
        
        #** Return RGB Colour Tuple **
        return tuple(colour)


    def format_artists(self, artists, IDs = None):

        #** Return artist is not a list
        if type(artists) == list:
            formatted = ""
            for i in range(len(artists)):
                
                #** Add comma up until 2nd to last artist in list, using & between the last 2 artists
                if i > 0 and i < len(artists)-1:
                    formatted += ", "
                elif i == len(artists)-1 and i != 0:
                    formatted += " & "
                
                #** Format string based on whether links are available
                if IDs is not None:
                    formatted += f"[{artists[i]}](https://open.spotify.com/artist/{IDs[i]})"
                else:
                    formatted += artists[i]

        #** Returned Formatted Strings
            return formatted
        else:
            return artists


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