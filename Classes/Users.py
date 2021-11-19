
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
    
    def __init__(self):

        super(SpotifyUser, self).__init__()

        #** Set Database Class **
        self.Database = UserData()

        DiscordID = self.userData['discordID']

        #** Get Spotify Details **
        self.SpotifyID = os.environ["SPOTIFY_CLIENT"]
        self.Secret = os.environ["SPOTIFY_SECRET"]

        #** Setup Header For Authentication **
        ClientData = self.SpotifyID+":"+self.Secret
        AuthStr =  base64.urlsafe_b64encode(ClientData.encode()).decode()
        self.AuthHead = {"Content-Type": "application/x-www-form-urlencoded", 'Authorization': 'Basic {0}'.format(AuthStr)}

        #** Get Spotify Credentials From Database **
        ID = self.userData['spotify']
        if str(ID) != 'None':
            Data = self.Database.GetSpotify(ID)
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


#!------------------------SONG HISTORY QUEUE-----------------------!#


class SongHistory(object):
    
    def __init__(self):

        super(SongHistory, self).__init__()

        #** Fetch Last Queue Session From Database **
        History = self.database.GetHistory(self.userData["history"])

        self.inpointer = History['inPointer']
        self.outpointer = History['outPointer']
        self.array = History['queue']
        self.maxsize = 49

        
    def check_empty(self):
        
        #** Check If First Value Is None, and If True Return True **
        if self.array[self.outpointer] == None:     
            return True

        #** If Not Return False **
        return False
        
        
    def check_full(self):
        
        #** Check If Pointers Match & Queue Has Values Inside. If True Return True **
        if self.inpointer == self.outpointer and self.array[self.maxsize] != None:
            return True

        #** If False Return False **
        return False
        

    def addSong(self, data):
        
        #** Check If Queue Is Full **
        if not(self.check_full()):
            
            #** Add Value To Array & Increment In-Pointer **
            self.array[self.inpointer] = data
            if self.inpointer == self.maxsize:
                self.inpointer = 0
            else:
                self.inpointer += 1

            print("\nIN")
            print(self.array)
            print(self.inpointer)
        
    def clearSong(self):
        
        #** Check If Queue Is Empty **
        if not(self.check_empty()):
            
            #** Pop Data Point From Array & Increment Out Pointer **
            Data = self.array[self.outpointer]
            if self.outpointer == self.maxsize:
                self.outpointer = 0
            else:
                self.outpointer += 1

            print("\nOUT")
            print(self.array)
            print(self.outpointer)

            #** Return Removed Data Point ** 
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
        self.userData = self.database.GetUser(DiscordID)
        
        #** Initialise SpotifyUser, Music & Listening History Classes **
        super(Users, self).__init__()
        self.SongData = Music()

    
    async def save(self):
        
        #** Format Queue Into MySQL Update String **
        ToExecute = "UPDATE history SET ID = '"+str(self.userData["history"])+"'"
        if self.inpointer != '0':
            ToExecute += ", Pointer1 = '"+str(self.inpointer)+"'"
        if self.outpointer != '0':
            ToExecute += ", Pointer2 = '"+str(self.outpointer)+"'"
        for i in range(50):
            if self.array[i] != None:
                ToExecute += ", Song"+str(i+1)+" = '"+str(self.array[i])+"'"
        ToExecute += " WHERE ID = '"+str(self.userData["history"])+"'"

        #** Write Song History Queue To MySQL Database **
        self.database.cursor.execute(ToExecute)
        self.database.connection.commit()
        
    
    async def incrementHistory(self, Song):
        
        #** If Queue Is Currently Full, Clear Oldest Song From Queue **
        if self.check_full():
            OldSong = self.clearSong()
        
        #Features = self.SongData.GetAudioFeatures()
         
        #** Add New Song To Queue **
        self.addSong(Song)
        
        