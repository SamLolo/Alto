
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
            
            #** Format string based on whether links are available
            formatted = ""
            for i in range(len(artists)):
                if IDs is not None:
                    formatted += f", [{artists[i]}](https://open.spotify.com/artist/{IDs[i]})"
                else:
                    formatted += artists[i]
                
                #** Add comma up until 2nd to last artist in list, using & between the last 2 artists
                if i <= len(artists)-3:
                    formatted += ", "
                elif i == len(artists)-2:
                    formatted += " & "

        #** Returned Formatted Strings
            return formatted.strip(", ")
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

        
    def format_song(self, SongData):

        #** If Spotify Song, Format Artists & Create Create String With Spotify Emoji **
        if SongData['SpotifyID'] is not None:
            FormattedArtists = self.format_artists(SongData['Artists'], SongData['ArtistIDs'])
            FormattedSong = f"{self.get_emoji('Spotify')} [{SongData['Name']}](https://open.spotify.com/track/{SongData['SpotifyID']})\nBy: {FormattedArtists}"
        
        #** If Soundcloud, Format Song Title & Add Single Artist With Link From Song Data **
        else:
            FormattedSong = f"{self.get_emoji('Soundcloud')} [{SongData['Name']}]({SongData['URI']})\n"
            FormattedSong += f"By: [{SongData['Artists'][0]}]({('/'.join(SongData['URI'].split('/')[:4]))})"

        #** Return Formatted String **
        return FormattedSong
    
    
    def get_emoji(self, name):
        
        #** Search through sequence of client emojis and return found emoji object **
        for emoji in self.client.emojis:
            if emoji.name == name:
                return emoji