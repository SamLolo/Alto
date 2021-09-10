
#!-------------------------IMPORT MODULES-----------------------!#


import os
import json
import base64
import requests
from datetime import datetime
from Classes.Database import UserData


#!--------------------------------SPOTIFY USER-----------------------------------#


class SpotifyUser():
    
    def __init__(self, DiscordID):

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
        ID = self.Database.GetUser(DiscordID)[4]
        print(ID)
        if str(ID) != 'None':
            Data = self.Database.GetSpotify(ID)
            print(Data)
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



#!-------------------------UTILS------------------------!#


class Users(SpotifyUser):
    
    def __init__(self):
        
        #** Initialise SpotifyUser & Listening History Classes **
        super().__init__()
