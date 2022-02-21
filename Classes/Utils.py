
#!-------------------------IMPORT MODULES-----------------------!#


import json
import requests
import lavalink
from colorthief import ColorThief


#!-------------------------UTILS------------------------!#


class Utility():

    def __init__(self):

        #** Load Config File **
        with open('Config.json') as ConfigFile:
            Config = json.load(ConfigFile)
            ConfigFile.close()
            
        #** Setup Emojis **
        self.Emojis = Config['Variables']['Emojis']

        
    def get_colour(self, URL):
        
        #** Get Contents Of Image URL **
        Image = requests.get(URL)

        #** Write Image To Temp PNG File **
        File = open("ColourCheck.png", "wb")
        File.write(Image.content)
        File.close()
        
        #** Get Most Dominant Colour In Image **
        Colour = ColorThief('ColourCheck.png').get_color(quality=1)
        
        #** Return RGB Colour Tuple **
        return Colour
    
    
    def format_artists(self, Artists, IDs):
        
        #** Prepare Empty String & Start Loop Through Artists **
        Formatted = ""
        for i in range(len(Artists)):
            
            #** If First Index, Add Artist & Link **
            if i == 0:
                Formatted += "["+Artists[i]+"](https://open.spotify.com/artist/"+IDs[i]+")"
                
            #** If Not Last Index, Add Comma Before Artist **
            elif i != len(Artists)-1:
                Formatted += ", ["+Artists[i]+"](https://open.spotify.com/artist/"+IDs[i]+")"
                
            #** If Last Index, add & Before Artist **
            else:
                Formatted += " & ["+Artists[i]+"](https://open.spotify.com/artist/"+IDs[i]+")"

        #** Returned Formatted String **
        return Formatted

    
    def format_time(self, time):
        
        #** Parse Time Into Days, Hours, Minutes & Seconds **
        Time = lavalink.parse_time(time)
        
        #** Create Strings Of Time In 24 Hour Clock **
        if Time[1] == 0.0:
            return str(int(Time[2]))+":"+str(int(Time[3])).zfill(2)
        else:
            return str(int(Time[1]))+":"+str(int(Time[2])).zfill(2)+":"+str(int(Time[3])).zfill(2)

        
    def format_song(self, SongData):

        #** If Spotify Song, Format Artists & Create Create String With Spotify Emoji **
        if SongData['SpotifyID'] is not None:
            FormattedArtists = self.format_artists(SongData['Artists'], SongData['ArtistIDs'])
            FormattedSong = self.Emojis['Spotify']+" ["+SongData['Name']+"](https://open.spotify.com/track/"+SongData['SpotifyID']+")\nBy: "+FormattedArtists+""
        
        #** If Soundcloud, Format Song Title & Add Single Artist With Link From Song Data **
        else:
            FormattedSong = self.Emojis['Soundcloud']+" ["+SongData['Name']+"]("+SongData['URI']+")\n"
            FormattedSong += "By: ["+SongData['Artists'][0]+"]("+("/".join(SongData['URI'].split("/")[:4]))+")"

        #** Return Formatted String **
        return FormattedSong
