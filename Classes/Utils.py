
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


    def format_artists(self, Artists, IDs):

        #** Prepare Empty String & Start Loop Through Artists **
        Formatted = ""
        for i in range(len(Artists)):

            #** If First Index, Add Artist & Link **
            if i == 0:
                Formatted += f"[{Artists[i]}](https://open.spotify.com/artist/{IDs[i]})"

            #** If Not Last Index, Add Comma Before Artist **
            elif i != len(Artists)-1:
                Formatted += f", [{Artists[i]}](https://open.spotify.com/artist/{IDs[i]})"

            #** If Last Index, add & Before Artist **
            else:
                Formatted += f" & [{Artists[i]}](https://open.spotify.com/artist/{IDs[i]})"

        #** Returned Formatted String **
        return Formatted


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