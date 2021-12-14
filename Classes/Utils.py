
#!-------------------------IMPORT MODULES-----------------------!#


import os
import json
import requests
import lavalink
from datetime import datetime
from colorthief import ColorThief


#!-------------------------UTILS------------------------!#


class Utility():
    
    def __init__(self):
        
        print()
        
    
    def get_colour(self, URL):
        
        #** Get Contents Of Image URL **
        Image = requests.get(URL)

        #** Write Image To Temp PNG File **
        File = open("temp.png", "wb")
        File.write(Image.content)
        File.close()
        
        #** Get Most Dominant Colour In Image **
        Colour = ColorThief('temp.png').get_color(quality=1)
        
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
