
#!-------------------------IMPORT MODULES-----------------------!#


import os
import json
import base64
from discord.ext.commands.converter import IDConverter
import requests
from datetime import datetime
from Classes.Database import UserData
from Classes.Music import Music


#!--------------------------------SPOTIFY USER-----------------------------------#


class SpotifyUser(object):
    
    def __init__(self, DiscordID):

        super(SpotifyUser, self).__init__(DiscordID)

        #** Set Database Class **
        self.Database = UserData()

        #** Get Spotify Details **
        self.SpotifyID = os.environ["SPOTIFY_CLIENT"]
        self.Secret = os.environ["SPOTIFY_SECRET"]

        #** Setup Header For Authentication **
        ClientData = self.SpotifyID+":"+self.Secret
        AuthStr =  base64.urlsafe_b64encode(ClientData.encode()).decode()
        self.AuthHead = {"Content-Type": "application/x-www-form-urlencoded", 'Authorization': 'Basic {0}'.format(AuthStr)}

        #** Get Spotify Credentials From Database **
        Data = self.Database.GetSpotify(DiscordID)
        if Data != None:

            #** Assign Class Objects **
            self.Refresh = Data[2]
            self.Name = Data[3]
            self.ID = Data[4]
            self.Pic = Data[5]
            self.Connected = True

            #** Get UserToken & User Header For New User **
            self.RefreshUserToken()

        else:
            self.Connected = False


    def RefreshUserToken(self):

        #** Request New User Token From Spotify **
        data = {'grant_type': "refresh_token", 'refresh_token': self.Refresh, 'client_id': self.SpotifyID, 'client_secret': self.Secret}
        AuthData = requests.post("https://accounts.spotify.com/api/token", data, self.AuthHead).json()

        #** Update Token and User Header **
        self.Token = AuthData['access_token']
        self.UserHead = {'Accept': "application/json", 'Content-Type': "application/json", 'Authorization': "Bearer "+self.Token}


    def GetUserPlaylists(self):

        #** Iterate Through Requests For User Playlists (50 per Request) **
        Playlists = {}
        NextURL = "https://api.spotify.com/v1/me/playlists?limit=50"
        while str(NextURL) != "None":
            UserData = requests.get(str(NextURL), headers = self.UserHead).json()

            #** If Error, Refresh Token and Retry **
            if 'error' in UserData.keys():
                self.RefreshUserToken()
                UserData = requests.get(str(NextURL), headers = self.UserHead).json()

            #** Sort User Playlists into a dictionary **
            NextURL = UserData['next']
            for Playlist in UserData['items']:
                if Playlist['owner']['id'] == self.ID:
                    Playlists[Playlist['id']] = Playlist['name']
        
        #** Return Filled Dict Of Playlists **
        return Playlists


#!------------------------SONG HISTORY QUEUE-----------------------!#


class SongHistory(object):
    
    def __init__(self, DiscordID):

        super(SongHistory, self).__init__()

        #** Fetch Last Queue Session From Database **
        self.History = self.database.GetHistory(DiscordID)

        self.inpointer = 0
        self.outpointer = 0
        self.array = list(self.History.keys())
        self.maxsize = 49
        self.full = False

        
    def check_empty(self):
        
        #** Check Queue Isn't Full & Pointers Aren't The Same **
        return (not(self.full) and self.outpointer == self.inpointer)
        
        
    def check_full(self):
        
        #** Check If Queue Is Full & Pointers Are The Same **
        return (self.full and self.inpointer == self.outpointer)
        

    def addSong(self, data):
        
        #** Check If Queue Is Full **
        if not(self.check_full()):
            
            #** Add Value To Array & Increment In-Pointer **
            if len(self.array) == self.maxsize:
                self.array[self.inpointer] = list(data.keys())[0]
            else:
                self.array.append(list(data.keys())[0])
            self.History.update(data)
            if self.inpointer == self.maxsize:
                self.inpointer = 0
            else:
                self.inpointer += 1

            print("\nIN")
            print(self.array)
            print(self.inpointer)

            #** Set Full To True If Same As OutPointer **
            if self.inpointer == self.outpointer and len(self.array) == self.maxsize:
                self.full = True
        

    def clearSong(self):
        
        #** Check If Queue Is Empty **
        if not(self.check_empty()):
            
            #** Pop Data Point From Array & Increment Out Pointer **
            songID = self.array[self.outpointer]
            Data = self.History.pop(songID)
            if self.outpointer == self.maxsize:
                self.outpointer = 0
            else:
                self.outpointer += 1

            print("\nOUT")
            print(self.array)
            print(self.outpointer)

            #** Set Full To False If Currently True & Return Removed Data Point **
            if self.full:
                self.full = False
            return Data
            
        #** Return None If No Value Removed **    
        else:
            return None
        

#!-------------------------USER OBJECT------------------------!#


class Users(SpotifyUser, SongHistory):
    
    def __init__(self, client, DiscordID):
        
        #** Setup Discord Client object **
        self.client = client
        self.database = UserData()
        
        #** Get User Object **
        self.user = self.client.get_user(DiscordID)
        
        #** Initialise SpotifyUser, Music & Listening History Classes **
        super(Users, self).__init__(DiscordID)
        self.SongData = Music()

    
    async def save(self):
        
        #** Send Data To Database To Be Saved **
        self.database.AddSongHistory(self.user.id, self.History, self.outpointer)
        
    
    async def incrementHistory(self, TrackData):
        
        #** If Queue Is Currently Full, Clear Oldest Song From Queue **
        if self.check_full():
            OldSong = self.clearSong()
        
        #Features = self.SongData.GetAudioFeatures()
         
        #** Add New Song To Queue **
        self.addSong(TrackData)
        
        