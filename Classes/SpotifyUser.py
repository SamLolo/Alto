
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import base64
import requests
import mysql.connector
from time import sleep
from datetime import datetime


#!--------------------------------SPOTIFY USER-----------------------------------#


class SpotifyUser():
    def __init__(self, DiscordID, Cursor, Connection):

        #** Set Database Connection Details **
        self.cursor = Cursor
        self.connection = Connection

        #** Get Spotify Details **
        self.SpotifyID = os.environ["SPOTIFY_CLIENT"]
        self.Secret = os.environ["SPOTIFY_SECRET"]

        #** Setup Header For Authentication **
        ClientData = self.SpotifyID+":"+self.Secret
        AuthStr =  base64.urlsafe_b64encode(ClientData.encode()).decode()
        self.AuthHead = {"Content-Type": "application/x-www-form-urlencoded", 'Authorization': 'Basic {0}'.format(AuthStr)}

        #** Get Spotify Credentials From Database **
        self.cursor.execute("SELECT spotify FROM users WHERE discordID='"+str(DiscordID)+"';")
        ID = self.cursor.fetchone()
        if str(ID) != 'None':
            if str(ID[0]) != 'None':
                self.cursor.execute("SELECT * FROM spotify WHERE ID='"+str(ID[0])+"';")
                Data = self.cursor.fetchone()

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
