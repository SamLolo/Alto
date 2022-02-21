
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import math
import json
import base64
import random
import requests
import pandas as pd
from time import sleep
from sklearn import tree
from datetime import datetime


#!--------------------------------SPOTIFY-----------------------------------#


class Spotify(object):
    
    def __init__(self):

        #** Get Spotify Tokens From Environment Variables **
        self.ID = os.environ["SPOTIFY_CLIENT"]
        self.Secret = os.environ["SPOTIFY_SECRET"]

        #** Setup Header For Authentication **
        ClientData = self.ID+":"+self.Secret
        AuthStr =  base64.urlsafe_b64encode(ClientData.encode()).decode()
        self.AuthHead = {"Content-Type": "application/x-www-form-urlencoded", 'Authorization': 'Basic {0}'.format(AuthStr)}

        #** Get An Initial Bot Token For API Calls **
        self.RefreshBotToken()


    def RefreshBotToken(self):

        #** Request a Token From Spotify Using Client Credentials **
        data = {'grant_type': 'client_credentials', 'redirect_uri': 'http://82.22.157.214:5000/', 'client_id': self.ID, 'client_secret': self.Secret}
        AuthData = requests.post("https://accounts.spotify.com/api/token", data, headers = {'Content-Type': 'application/x-www-form-urlencoded'}).json()
        self.BotToken = AuthData['access_token']

        #** Setup Header For Requests Using Client Credentials  **
        self.BotHead = {'Accept': "application/json", 'Content-Type': "application/json", 'Authorization': "Bearer "+self.BotToken}


    def GetPlaylistSongs(self, PlaylistID):

        #** Get A Playlists Songs **
        SongData = requests.get('https://api.spotify.com/v1/playlists/'+str(PlaylistID), headers = self.BotHead)

        #** Check If Request Was A Success **
        while SongData.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == SongData.status_code:
                self.RefreshBotToken()
                SongData = requests.get('https://api.spotify.com/v1/playlists/'+str(PlaylistID), headers = self.BotHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == SongData.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Location: Spotify -> GetPlaylistSongs")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                Time = SongData.headers['Retry-After']
                sleep(Time)
                SongData = requests.get('https://api.spotify.com/v1/playlists/'+str(PlaylistID), headers = self.BotHead)
                
            #** Check If Playlist Not Found, and Return "PlaylistNotFound" **
            elif 404 == SongData.status_code:
                return "PlaylistNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Location: Spotify -> GetPlaylistSongs")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Spotify Request Code "+str(SongData.status_code))
                return "UnexpectedError"
        
        #** Itterate Through Each Song And Check Ignore If Empty **
        if SongData != []:
            SongData = SongData.json()
            Songs = {}
            for Song in SongData['tracks']['items']:
                
                #** Get Formatted Data For Each Song **
                Songs.update(self.FormatSongData(Song['track']))
            
            #** Return Filled Dictionary Of Songs **
            Songs = {'PlaylistInfo': {'Name': SongData['name'], 'Length': SongData['tracks']['total']}, 'Tracks': Songs}
            return Songs
        
        #** Return "PlaylistNotFound" if Request Body Is Empty (Shouldn't Happen) **
        else:
            return "PlaylistNotFound"


    def GetAlbumInfo(self, AlbumID):

        #** Get An Albums Songs **
        AlbumData = requests.get('https://api.spotify.com/v1/albums/'+str(AlbumID), headers = self.BotHead)

        #** Check If Request Was A Success **
        while AlbumData.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == AlbumData.status_code:
                self.RefreshBotToken()
                AlbumData = requests.get('https://api.spotify.com/v1/albums/'+str(AlbumID), headers = self.BotHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == AlbumData.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Location: Spotify -> GetAlbumInfo")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                Time = AlbumData.headers['Retry-After']
                sleep(Time)
                AlbumData = requests.get('https://api.spotify.com/v1/albums/'+str(AlbumID), headers = self.BotHead)
                
            #** Check If Album Not Found, and Return "AlbumNotFound" **
            elif 404 == AlbumData.status_code:
                return "PlaylistNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Location: Spotify -> GetPlaylistSongs")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Spotify Request Code "+str(AlbumData.status_code))
                return "UnexpectedError"
        
        #** Iterate Through Each Song And Check Ignore If Empty **
        if AlbumData != []:
            AlbumData = AlbumData.json()
            Songs = {}
            for Song in AlbumData['tracks']['items']:
                
                #** Get Formatted Data For Each Song **
                Song['album'] = {'name': AlbumData['name'], 'id': AlbumData['id'], 'images': [{'url': AlbumData['images'][0]['url']}], 'album_type': AlbumData['album_type'], 'release_date': AlbumData['release_date']}
                Song['popularity'] = AlbumData['popularity']
                Songs.update(self.FormatSongData(Song))
            
            #** Return Filled Dictionary Of Songs **
            Songs = {'PlaylistInfo': {'Name': AlbumData['name'], 'Length': AlbumData['tracks']['total']}, 'Tracks': Songs}
            return Songs
        
        #** Return "AlbumNotFound" if Request Body Is Empty (Shouldn't Happen) **
        else:
            return "AlbumNotFound"
        

    def GetSongInfo(self, SongID):

        #** Get Information About A Song **
        Song = requests.get("https://api.spotify.com/v1/tracks/"+str(SongID), headers=self.BotHead)

        #** Check If Request Was A Success **
        while Song.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == Song.status_code:
                self.RefreshBotToken()
                Song = requests.get("https://api.spotify.com/v1/tracks/"+str(SongID), headers=self.BotHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == Song.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Location: Spotify -> GetSongInfo")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                Time = Song.headers['Retry-After']
                sleep(Time)
                Song = requests.get("https://api.spotify.com/v1/tracks/"+str(SongID), headers=self.BotHead)
                
            #** Check If Song Not Found, and Return "SongNotFound" **
            elif 404 == Song.status_code:
                return "SongNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Location: Spotify -> GetSongInfo")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Spotify Request Code "+str(Song.status_code))
                return "UnexpectedError"

        #** Check If Song Info Returned & Format Certain Values Before Adding To Dictionary **
        if Song != []:
            Song = Song.json()

            #** Get Formatted Song Data **
            SongInfo = self.FormatSongData(Song)
            
            #** Return Dictionary Of Song Information **
            return SongInfo
        
        #** Return "SongNotFound" if Request Body Is Empty (Shouldn't Happen) **
        else:
            return "SongNotFound"


    def GetAudioFeatures(self, SongIDs):

        #** Request Audio Features For a List of Spotify IDs **
        SongIDs = ",".join(SongIDs)
        Features = requests.get("https://api.spotify.com/v1/audio-features?ids="+str(SongIDs), headers = self.BotHead)

        #** Check If Request Was A Success **
        while Features.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == Features.status_code:
                self.RefreshBotToken()
                Features = requests.get("https://api.spotify.com/v1/audio-features?ids="+str(SongIDs), headers = self.BotHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == Features.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Location: Spotify -> GetAudioFeatures")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                Time = Features.headers['Retry-After']
                sleep(Time)
                Features = requests.get("https://api.spotify.com/v1/audio-features?ids="+str(SongIDs), headers = self.BotHead)
                
            #** Check If Features Not Found, and Return "FeaturesNotFound" **
            elif 404 == Features.status_code:
                return "FeaturesNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Location: Spotify -> GetAudioFeatures")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Spotify Request Code "+str(Features.status_code))
                return "UnexpectedError"
        
        #** Return Audio Features **
        Features = Features.json()
        return Features['audio_features']


    def FormatSongData(self, Song):
        
        #** Add All Artists To A List **
        Artists = []
        ArtistID = []
        for Artist in Song['artists']:
            if Artist['name'] != None:
                Artists.append(Artist['name'])
                ArtistID.append(Artist['id'])

        #** Format Album Name **
        if Song['album']['album_type'] == "single":
            if "feat" in Song['name']:
                Song['album']['name'] = str(Song['name'].split("(feat.")[0])+"- Single"
            else:
                Song['album']['name'] = str(Song['name'])+" - Single"

        #** Format Album Release Date **
        Months = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'}
        if Song['album'] != {}:
            if Song['album']['release_date'] != None:
                if "-" in Song['album']['release_date']:
                    if len(Song['album']['release_date']) > 7:
                        if Song['album']['release_date'][0] == 0:
                            Song['album']['release_date'] = Song['album']['release_date'][8].replace("0", "")
                        Date = Song['album']['release_date'].split("-")
                        Date = Date[2]+"th "+Months[Date[1]]+" "+Date[0]
                    else:
                        Date = Song['album']['release_date'].split("-")
                        Date = Months[Date[1]]+" "+Date[0]
                else:
                    Date = Song['album']['release_date']
            else:
                Date = "N/A"

        #** Fill in Empty Values if Album Information Missing **
        else:
            Song['album']['name'] = "N/A"
            Song['album']['id'] = None
            Song['album']['images'][0]['url'] = None
            Date = "N/A"
            
        #** Make Sure No Empty Values Are Left **
        for key in ['popularity', 'explicit']:
            if Song[key] == None or Song[key] == 0:
                Song[key] = "N/A"

        #** Return Dictionary (Songs) With Key: <SongID> and Value: <dict containing song infomation> **
        SongData = {Song['id']: {'Name': Song['name'], 
                                 'Artists': Artists, 
                                 'ArtistID': ArtistID, 
                                 'Album': Song['album']['name'], 
                                 'AlbumID': Song['album']['id'], 
                                 'Art': Song['album']['images'][0]['url'], 
                                 'Release': Date, 
                                 'Popularity': Song['popularity'], 
                                 'Explicit': Song['explicit'], 
                                 'Preview': Song['preview_url']}}
        return SongData


    def SearchSpotify(self, Name, Artist):
        
        #** Format Name & Artist To Fill Spaces With %20 **
        Name = "%20".join(Name.split(" "))
        Artist = "%20".join(Artist.split(" "))
        
        #** Fetch Top Search Result From Spotify **
        Data = {'type': 'track', 'limit': '1', 'include_external': 'audio'}
        Result = requests.get('https://api.spotify.com/v1/search?q="'+Name+'"%20artist:'+Artist, Data, headers = self.BotHead)

        #** Check If Request Was A Success **
        while Result.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == Result.status_code:
                self.RefreshBotToken()
                Result = requests.get('https://api.spotify.com/v1/search?q="'+Name+'"%20artist:'+Artist, Data, headers = self.BotHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == Result.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Location: Spotify -> SearchSpotify")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                Time = Result.headers['Retry-After']
                sleep(Time)
                Result = requests.get('https://api.spotify.com/v1/search?q="'+Name+'"%20artist:'+Artist, Data, headers = self.BotHead)
                
            #** Check If Song Not Found, and Return "SongNotFound" **
            elif 404 == Result.status_code:
                return "SongNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Location: Spotify -> SearchSpotify")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Spotify Request Code "+str(Result.status_code))
                return "UnexpectedError"

        #** Check if Request Body Empty (Shouldn't Happen) & Convert to Json **
        if Result != []:
            Result = Result.json()
            
            #** Check If Any Results Returned **
            if Result['tracks']['items'] != []:

                #** Get Formatted Song Data Of Top Result **
                SongInfo = self.FormatSongData(Result['tracks']['items'][0])
                
                #** Return Dictionary Of Song Information **
                return SongInfo
            
            #** Return Song Not Found If No Songs Returned **
            else:
                return "SongNotFound"
        
        #** Return "SongNotFound" If Request Body Is Empty (Shouldn't Happen) **
        else:
            return "SongNotFound"


    def GetRecommendations(self, data):
        
        #** Requests Recommendations From Spotify With The Data Provided **
        Recommendations = requests.get("https://api.spotify.com/v1/recommendations", data, headers = self.BotHead)

        #** Check If Request Was A Success **
        while Recommendations.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == Recommendations.status_code:
                self.RefreshBotToken()
                Recommendations = requests.get("https://api.spotify.com/v1/recommendations", data, headers = self.BotHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == Recommendations.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Location: Spotify -> GetRecommendations")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                Time = Recommendations.headers['Retry-After']
                sleep(Time)
                Recommendations = requests.get("https://api.spotify.com/v1/recommendations", data, headers = self.BotHead)
                
            #** Check If Recommendations Not Found, and Return "RecommendationsNotFound" **
            elif 404 == Recommendations.status_code:
                return "RecommendationsNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Location: Spotify -> GetRecommendations")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Spotify Request Code "+str(Recommendations.status_code))
                return "UnexpectedError"
        
        #** Iterate Through Each Song And Check Ignore If Empty **
        if Recommendations != []:
            Recommendations = Recommendations.json()

            #** Check Spotify Actually Returned Tracks In Request **
            if Recommendations['tracks'] != []:

                #** Return List Of Recommended Songs **
                Songs = {}
                for Song in Recommendations['tracks']:
                    Songs.update(self.FormatSongData(Song))
                return Songs

            #** "Return RecommendationsNotFound" If No Songs Returned **
            else:
                return "RecommendationsNotFound"

        #** Return "RecommendationsNotFound" If Request Body Is Empty (Shouldn't Happen) **
        else:
            return "RecommendationsNotFound"


#!--------------------------------MUSIC-----------------------------------#


class Music(Spotify):
    
    def __init__(self):

        #** Initialise Spotify API Class **
        super().__init__()

        #** Assign Class Objects **
        self.Genres = ['dance', 'pop', 'house', 'alternative', 'country', 'classical', 'electronic', 'folk', 'hip-hop', 'rock', 'heavy-metal', 'indie', 'jazz', 'reggae', 'rnb']
        self.SongFeatures = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'valence']
        self.Keys = {'0': 'C', '1': 'C# / D♭', '2': 'D', '3': 'D♯ / E♭', '4': 'E', '5': 'F', '6': 'F# / G♭', '7': 'G', '8': 'G# / A♭', '9': 'A', '10': 'A# / B♭', '11': 'B'}
        self.Volumes = {'Very Quiet': [-100, -55], 'Quite Quiet': [-55, -45], 'Quiet': [-45, -35], 'Normal': [-35, -25], 'Loud': [-25, -15], 'Quite Loud': [-15, -5], 'Very Loud': [-5, 100]}

        #** Load Genre Data and Setup Genre Prediction Decision Tree **
        PredictionData = []
        GenreData = []
        for Genre in self.Genres:
            with open('SongData.json') as TestFile:
                TestData = json.load(TestFile)
                TestFile.close()
            for Data in TestData[Genre]:
                PredictionData.append(Data)
                GenreData.append(Genre)
        Tree = tree.DecisionTreeClassifier()
        self.GenrePredictor = Tree.fit(PredictionData, GenreData)


    def GetSongDetails(self, SongID):

        #** Get Song Information and Song Features **
        SongData = self.GetSongInfo(SongID)
        if SongData in ["SongNotFound", "UnexpectedError"]:
            return SongData
        Features = self.GetAudioFeatures([SongID])[0]

        #** Add Advanced Information Using Audio Features to Returned Song Info Dict **
        SongData[SongID]["Duration"] = str(int(Features['duration_ms'] // 60000))+" Mins "+str(int((Features['duration_ms'] / 1000) - ((Features['duration_ms'] // 60000) * 60)))+" Seconds"
        SongData[SongID]["Key"] = self.Keys[str(int(Features['key']))]
        SongData[SongID]["BeatsPerBar"] = str(int(Features['time_signature']))
        SongData[SongID]["Tempo"] = str(int(Features['tempo']))
        if Features['mode'] <= 0.5:
            SongData[SongID]["Mode"] = "Minor"
        else:
            SongData[SongID]["Mode"] = "Major"
        for Volume, Range in self.Volumes.items():
            if int(Features['loudness']) > Range[0] and int(Features['loudness']) <= Range[1]:
                SongData[SongID]["Volume"] = Volume
                break
        
        #** Predict Genre Of The Song and Add it to The Song Info Dict **
        SongData[SongID]['Genre'] = self.PredictGenre([Features])[0]

        #** Returned Nicely Filled Song Info Dict **
        return SongData
    

    def PredictGenre(self, Features):

        #** Predict Genre From List Of Features **
        Combined = []
        for Song in Features:
            Values = []
            for Feature in self.SongFeatures:
                Values.append(Song[Feature])
            Combined.append(Values)
        Prediction = self.GenrePredictor.predict(Combined)

        #** Return Predicted Genre **
        return Prediction


    def RecommendFromTracks(self, Tracks):

        #** Create Dictionaries Used To Sort Data **
        Data = {'duration_ms': [], 'key': [], 'mode': [], 'time_signature': [], 'acousticness': [], 'danceability': [], 'energy': [], 'instrumentalness': [], 'liveness': [], 'loudness': [], 'speechiness': [], 'valence': [], 'tempo': [], 'popularity': []}
        UserGenres = {'dance': 0, 'pop': 0, 'house': 0, 'alternative': 0, 'country': 0, 'classical': 0, 'electronic': 0, 'folk': 0, 'hip-hop': 0, 'rock': 0, 'heavy-metal': 0, 'indie': 0, 'jazz': 0, 'reggae': 0, 'rnb': 0}
        
        #** Form 2 Lists Of SongIDs and ArtistIDs & Add Popularity Of Songs To Data Dict **
        SongIDs = []
        ArtistIDs = []
        for ID, Info in Tracks.items():
            SongIDs.append(ID)
            if Info['Popularity'] != 'N/A':
                Data['popularity'].append(Info['Popularity'])
            else:
                Data['popularity'].append(None)
            for Artist in Info['ArtistID']:
                ArtistIDs.append(Artist)

        #** Split SongIDs List Up Into Lists Of Max 100 Length **
        SplitSongs = []
        if len(SongIDs) > 100:
            while SongIDs != []:
                TempList = []
                for i in range(100):
                    if SongIDs != []:
                        TempList.append(SongIDs[0])
                        SongIDs.pop(0)
                    else:
                        break
                SplitSongs.append(TempList)
        else:
            SplitSongs = SongIDs
            SongIDs = []

        #** Get Audio Features For Each List Of Songs **
        for TrackSet in SplitSongs:
            Features = self.GetAudioFeatures(TrackSet)

            #** Sort Audio Features Into Data Dict Based On Key Ignoring Popularity **
            for Song in Features:
                for Key in Data.keys():
                    if Key != "popularity":
                        Data[Key].append(Song[Key])

            #** Predict Genre For All 100 Songs Using List Of Song Features Returned Above and Add To UserGenres Dict **
            Genres = self.PredictGenre(Features)
            for Genre in Genres:
                UserGenres[Genre] += 1
        
        #** Setup Lists Of Values To Sort & Their Keys and Get Length Of Data To Sort **
        ToSort = [list(UserGenres.values())]
        Genres = [list(UserGenres.keys())]
        ArrayNum = len(ToSort[0])
            
        #** Split To Sort Into Individual Subsets **
        while len(ToSort) < ArrayNum:
            for i in range(len(ToSort)):
                if len(ToSort[i]) > 1:

                    #** Sort To Sort **
                    Array = ToSort.pop(i)
                    ToSort.insert(i, Array[(len(Array) // 2):])
                    ToSort.insert(i, Array[:(len(Array) // 2)])

                    #** Sort Genres **
                    Array = Genres.pop(i)
                    Genres.insert(i, Array[(len(Array) // 2):])
                    Genres.insert(i, Array[:(len(Array) // 2)])

        #** While To Sort Isn't One Complete List Again **
        while len(ToSort) > 1:

            #** Loop Through Rounded-Up Half Of The Length Of To Sort, ie Two Subsets At A Time **
            for i in range(math.ceil(len(ToSort) / 2)):
                
                #** Check Second Subset Isn't Outside Range Of List **
                if i+1 < len(ToSort):

                    #** For Value In Second Subset, Compare Against Each Value In The First Subset From Left To Right **
                    for k in range(len(ToSort[i+1])):
                        for j in range(len(ToSort[i])):

                            #** If Value Smaller Than Value In Subset, Insert Value From Second Subset Before Value In First Subset **
                            if ToSort[i][j] < ToSort[i+1][k]:
                                ToSort[i].insert(j, ToSort[i+1][k])
                                Genres[i].insert(j, Genres[i+1][k])
                                break

                        #** If Bigger Than All Values In Subset, Append To End Of First Subset **
                        if not(ToSort[i+1][k] in ToSort[i]):
                            ToSort[i].append(ToSort[i+1][k])
                            Genres[i].append(Genres[i+1][k])
                    
                    #** Remove Second Subset From To Sort List **
                    ToSort.pop(i+1)
                    Genres.pop(i+1)
        
        #** Set Ordered Genres Lists For Use When Generating Recommendations **
        OrderedGenres = Genres[0]

        #** Construct Pandas Dataframe With Data and Get Averages and Max / Min of Data **
        Dataframe = pd.DataFrame(Data, columns = ['duration_ms', 'key', 'mode', 'time_signature', 'acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'valence', 'tempo', 'popularity'])
        Max = Dataframe.max()
        Min = Dataframe.min()
        Avg = Dataframe.mean()

        #** Recreate List Of SongIDs To Pick From **
        for List in SplitSongs:
            SongIDs.extend(List)

        #** Select 2 Random Tracks & Artists As Seeds **
        Seeds = {"tracks": [], "artists": []}
        for Type, ChoiceList in Seeds.items():
            while len(ChoiceList) < 2:
                Choice = random.choice(SongIDs)
                if not(Choice in ChoiceList):
                    ChoiceList.append(Choice)
                Seeds[Type] = ChoiceList

        #** Assign Data and Call GetRecommendations Method With Data Dict **
        data = {'limit': 50, 'seed_genres': str(OrderedGenres[0]), 
                'seed_tracks': ",".join(Seeds['tracks']), 'seed_artists': ",".join(Seeds['artists']),
                'min_acousticness': Min[4], 'target_acousticness': Avg[4], 'max_acousticness': Max[4], 
                'min_danceability': Min[5], 'target_danceability': Avg[5], 'max_danceability': Max[5], 
                'min_energy': Min[6], 'target_energy': Avg[6], 'max_energy': Max[6], 
                'min_instrumentalness': Min[7], 'target_instrumentalness': Avg[7], 'max_instrumentalness': Max[7], 
                'min_liveness': Min[8], 'target_liveness': Avg[8], 'max_liveness': Max[8], 
                'min_loudness': Min[9], 'target_loudness': Avg[9], 'max_loudness': Max[9],
                'min_speechiness': Min[10], 'target_speechiness': Avg[10], 'max_speechiness': Max[10], 
                'min_valence': Min[11], 'target_valence': Avg[11], 'max_valence': Max[11],
                'min_tempo': Min[12], 'target_tempo': Avg[12], 'max_tempo': Max[12],
                'min_popularity': int(Min[13]), 'target_popularity': int(Avg[13]), 'max_popularity': int(Max[13])}
        Tracks = self.GetRecommendations(data)
        
        #** Return Track List **
        return Tracks
    