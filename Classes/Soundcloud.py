

#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import requests
from datetime import datetime
from Classes.Database import UserData


#!---------------------------------SOUNDCLOUD---------------------------------------#


class SoundcloudAPI():
    
    def __init__(self):

        #** Create Class Objects For Requests **
        self.ClientID = os.environ["SOUNDCLOUD_ID"]

        #** Setup Database Connection **
        self.Database = UserData()
        
    
    def get_track(self, ID):
        
        #** Get Info From Soundcloud API **
        Result = requests.get("https://api-v2.soundcloud.com/tracks?ids=%s&client_id=%s", data=[ID, self.ClientID])

        print(Result)