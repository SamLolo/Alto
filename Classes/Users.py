
#!-------------------------IMPORT MODULES-----------------------!#


import os
import json
import base64
import random
import requests
from datetime import datetime


#!--------------------------IMPORT CLASSES-------------------------!#


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

            #** Check SpotifyID Is Actually Present (Account Isn't Half Linked)
            if Data['spotifyID'] != None:

                #** Assign Class Objects **
                self.SpotifyData = Data
                self.SpotifyConnected = True

                #** Get UserToken & User Header For New User **
                self.RefreshUserToken()

            #** Set SpotifyConnected To False If A Connection Couldn't Be Made **
            else:
                self.SpotifyConnected = False
        else:
            self.SpotifyConnected = False


    def RefreshUserToken(self):

        #** Request New User Token From Spotify **
        data = {'grant_type': "refresh_token", 'refresh_token': self.SpotifyData['refresh'], 'client_id': self.SpotifyID, 'client_secret': self.Secret}
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
                if Playlist['owner']['id'] == self.SpotifyData['spotifyID']:
                    Playlists[Playlist['id']] = Playlist['name']
        
        #** Return Filled Dict Of Playlists **
        return Playlists


#!------------------------SONG HISTORY QUEUE-----------------------!#


class SongHistory(object):
    
    def __init__(self, DiscordID):

        super(SongHistory, self).__init__()

        #** Fetch Last Queue Session From Database, Returns Dict Of SongIDs & Data **
        self.History = self.database.GetHistory(DiscordID)

        #** Setup Pointers & Array, Defining The MaxSize & Setting Full To False
        self.inpointer = 0
        self.outpointer = 0
        self.array = list(self.History.keys())
        print(self.array)
        self.maxsize = 49
        if len(self.array) == 50:
            self.full = True
        else:
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
        self.user = self.database.GetUser(DiscordID)
        if self.user == None:
            self.discordUser = self.client.get_user(DiscordID)
            self.user = {"data": {"discordID": int(self.discordUser.id),
                                  "name": self.discordUser.name,
                                  "discriminator": self.discordUser.discriminator,
                                  "avatar": self.discordUser.avatar_url},
                        "recommendations": {"Popularity": [0, 50, 100],
                                            "Acoustic": [0.0018, 0.223396, 0.8350],
                                            "Dance": [0.3080, 0.684500, 0.9560],
                                            "Energy": [0.2860, 0.644640, 0.8970],
                                            "Instrument": [0, 0.001568, 0.0542],
                                            "Live": [0.0264, 0.163196, 0.4610],
                                            "Loud": [-11.8810, -6.250840, -2.7240],
                                            "Speech": [0.0282, 0.106186, 0.4020],
                                            "Valance": [0.0386, 0.521244, 0.9420]}}
        
        #** Initialise SpotifyUser, Music & Listening History Classes **
        super(Users, self).__init__(DiscordID)
        self.SongData = Music()


    async def save(self):
        
        #** Send Data To Database To Be Saved **
        self.database.AddSongHistory(self.user['data']['discordID'], self.History, self.outpointer)
        
    
    async def incrementHistory(self, TrackData):
        
        #** If Queue Is Currently Full, Clear Oldest Song From Queue **
        if self.check_full():
            OldSong = self.clearSong()
        
        #Features = self.SongData.GetAudioFeatures()
         
        #** Add New Song To Queue **
        self.addSong(TrackData)

    
    def getRecommendations(self):

        #** Create Lists Of Listened To Spotify Track ID's And Artists From Listening History **
        TrackIDs = []
        for songID in self.array:
            if self.History[songID]['SpotifyID'] is not None:
                TrackIDs.append(self.History[songID]['SpotifyID'])

        #** Select 3 Track ID's and 2 Artist ID's At Random From The Two Lists **
        while len(TrackIDs) > 3:
            TrackIDs.pop(random.randint(0, len(TrackIDs)-1))

        #** Create Recommendations Data To Send Off To Spotify Web API **
        Figures = self.user['recommendations']
        data = {'limit': 50, 'seed_tracks': ",".join(TrackIDs),
                'min_acousticness': Figures['Acoustic'][0], 'target_acousticness': Figures['Acoustic'][1], 'max_acousticness': Figures['Acoustic'][2], 
                'min_danceability': Figures['Dance'][1], 'target_danceability': Figures['Dance'][1], 'max_danceability': Figures['Dance'][2], 
                'min_energy': Figures['Energy'][0], 'target_energy': Figures['Energy'][1], 'max_energy': Figures['Energy'][2], 
                'min_instrumentalness': Figures['Instrument'][0], 'target_instrumentalness': Figures['Instrument'][1], 'max_instrumentalness': Figures['Instrument'][2], 
                'min_liveness': Figures['Live'][0], 'target_liveness': Figures['Live'][1], 'max_liveness': Figures['Live'][2], 
                'min_loudness': Figures['Loud'][0], 'target_loudness': Figures['Loud'][1], 'max_loudness': Figures['Loud'][2],
                'min_speechiness': Figures['Speech'][0], 'target_speechiness': Figures['Speech'][1], 'max_speechiness': Figures['Speech'][2], 
                'min_valence': Figures['Valance'][0], 'target_valence': Figures['Valance'][1], 'max_valence': Figures['Valance'][2],
                'min_popularity': Figures['Popularity'][0], 'target_popularity': Figures['Popularity'][1], 'max_popularity': Figures['Popularity'][2]}
        
        #** Get Set Of Track Recommendations From Spotify Web API & Return Tracks **
        Tracks = self.SongData.GetRecommendations(data)
        return Tracks