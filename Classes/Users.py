
#!-------------------------IMPORT MODULES-----------------------!#


import os
import json
import base64
import random
import requests
from datetime import datetime


#!--------------------------IMPORT CLASSES-------------------------!#


from Classes.Database import UserData
from Classes.MusicUtils import Music


#!--------------------------------SPOTIFY USER-----------------------------------#


class SpotifyUser(object):
    
    def __init__(self, DiscordID):

        super(SpotifyUser, self).__init__(DiscordID)

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

        #** Fetch Last Queue Session From Database, Returns List Of Dictionaries **
        self.History = self.Database.GetHistory(DiscordID)
        
        #** Create Array Of SongIDs **
        self.array = []
        for dict in self.History:
            self.array.append(dict['ID'])

        #** Setup Pointers, Defining The MaxSize & Setting Full To False
        self.inpointer = 0
        self.outpointer = 0
        self.maxsize = 19
        if len(self.array) == 20:
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
            
            #** Add Value To Array & Data To History & Increment In-Pointer **
            ID = list(data.values())[0]
            if len(self.array) == self.maxsize:
                self.array[self.inpointer] = ID
                self.History[self.inpointer] = data
            else:
                self.array.append(ID)
                self.History.append(data)
            if self.inpointer == self.maxsize:
                self.inpointer = 0
            else:
                self.inpointer += 1

            print("Song History Added To Queue!")

            #** Set Full To True If Same As OutPointer **
            if self.inpointer == self.outpointer and len(self.array) == self.maxsize:
                self.full = True
        

    def clearSong(self):
        
        #** Check If Queue Is Empty **
        if not(self.check_empty()):
            
            #** Pop Data Point From History Array & Increment Out Pointer **
            data = self.History.pop(self.outpointer)
            if self.outpointer == self.maxsize:
                self.outpointer = 0
            else:
                self.outpointer += 1

            print("Song History Removed From Queue!")

            #** Set Full To False If Currently True & Return Removed Data Point **
            if self.full:
                self.full = False
            return data
            
        #** Return None If No Value Removed **    
        else:
            return None
        

#!-------------------------USER OBJECT------------------------!#


class Users(SpotifyUser, SongHistory):
    
    def __init__(self, client, DiscordID):
        
        #** Setup Discord Client object & Instantiate Music & Database Modules **
        self.client = client
        self.SongData = Music()
        self.Database = UserData()

        #** Initialise SpotifyUser, & Listening History Classes **
        super(Users, self).__init__(DiscordID)
        
        #** Get User Dictionary **
        self.user = self.Database.GetUser(DiscordID)
        if self.user == None:
            discordUser = self.client.get_user(DiscordID)
            self.user = {"data": {"discordID": int(discordUser.id),
                                  "name": discordUser.name,
                                  "discriminator": discordUser.discriminator,
                                  "avatar": str(discordUser.avatar_url),
                                  "joined": datetime.now(),
                                  "songs": 0},
                        "recommendations": {"songcount": 0,
                                            "Popularity": [0, 50, 100],
                                            "Acoustic": [0.0, 0.223396, 1.0],
                                            "Dance": [0.0, 0.684500, 1.0],
                                            "Energy": [0.0, 0.644640, 1.0],
                                            "Instrument": [0, 0.001568, 1.0],
                                            "Live": [0.0, 0.163196, 1.0],
                                            "Loud": [-15.0, -6.250840, 0.0],
                                            "Speech": [0.0, 0.106186, 1.0],
                                            "Valance": [0.0, 0.521244, 1.0]}}


    async def save(self):
        
        #** Send Data To Database To Be Saved **
        self.Database.AddSongHistory(self.user['data']['discordID'], self.History, self.outpointer)
        self.Database.SaveUserDetails(self.user)
        
    
    async def incrementHistory(self, TrackData):
        
        #** If Queue Is Currently Full, Clear Oldest Song From Queue **
        if self.check_full():
            OldSong = self.clearSong()
            
            #** Check If OldSong Has A Spotify ID & Get Audio Features **
            if OldSong['spotifyID'] != None:
                Features = self.SongData.GetAudioFeatures(OldSong['spotifyID'])
                
                #** Create Conversions Dict Between Recommendations Data & Feature Keys From Request **
                Conversions = {'Acoustic':'acousticness', 
                               'Dance': 'danceability',
                               'Energy': 'energy',
                               'Instrument': 'instrumentalness',
                               'Live': 'liveness',
                               'Loud': 'loudness',
                               'Speech': 'speechiness',
                               'Valance': 'valence'}
                
                #** Get Song Count For Recommendations **
                SongCount = self.user['recommendations']['songcount']
                
                #** Create New Value By Adding New Value To Total & Dividing By New Song Count **
                for key, values in self.user['recommendations']:
                    if key == "Popularity":
                        if OldSong['Popularity'] != None:
                            NewValue = int(((values[1] * SongCount) + OldSong['Popularity']) / (SongCount + 1))
                        else:
                            NewValue = int(((values[1] * SongCount) + 50) / (SongCount + 1))
                    else:
                        NewValue = int(((values[1] * SongCount) + Features[Conversions[key]]) / (SongCount + 1))
                    
                    #** Get Difference Between Old Average & New Average **
                    Difference = values[1] - NewValue
                    
                    #** Add 1/10th Of Difference To Min & Max Values Either Side Of Average **
                    values[0] = values[0] + (Difference / 10)
                    values[1] = NewValue
                    values[2] = values[2] + (Difference / 10)
                    
                    #** Add 1 To Song Count For Recommendations & Add New Values For Each Key **
                    self.user['recommendations']['songcount'] += 1
                    self.user['recommendations'][key] = values

            #** Add Song To Overall Song Count Regardless **
            self.user['data']['songs'] += 1

        #** Add New Song To Queue **
        self.addSong(TrackData)

    
    def getRecommendations(self):

        #** Create Lists Of Listened To Spotify Track ID's And Artists From Listening History **
        TrackIDs = []
        for i in range(len(self.array)):
            if self.History[i]['SpotifyID'] is not None:
                TrackIDs.append(self.History[i]['SpotifyID'])

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