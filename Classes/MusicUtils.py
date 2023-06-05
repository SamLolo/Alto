
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import math
import json
import base64
import random
import logging
import asyncio
import requests
import pandas as pd
from sklearn import tree
from datetime import datetime


#!--------------------------------SPOTIFY-----------------------------------#


class Spotify(object):
    
    def __init__(self):

        #** Setup Logger **
        self.logger = logging.getLogger("spotify")

        #** Get Spotify Tokens From Environment Variables **
        self.CLIENT = "6d32b18995b542c59183be193900f1d5"
        self.SECRET = os.environ["DEV_SPOTIFY_SECRET"]

        #** Setup Header For Authentication **
        clientStr = self.CLIENT+":"+self.SECRET
        authStr =  base64.urlsafe_b64encode(clientStr.encode()).decode()
        self.authHead = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': 'Basic {0}'.format(authStr)}

        #** Get An Initial Bot Token For API Calls **
        self.RefreshBotToken()


    def RefreshBotToken(self):

        #** Request a Token From Spotify Using Client Credentials **
        self.logger.info("Refreshing Bot Token")
        data = {'grant_type': 'client_credentials', 'redirect_uri': 'http://82.22.157.214:5000/', 'client_id': self.CLIENT, 'client_secret': self.SECRET}
   
        self.logger.debug("New Request: https://accounts.spotify.com/api/token")
        response = requests.post("https://accounts.spotify.com/api/token", data, headers=self.authHead)

        #** Check If Request Was A Success **
        while response.status_code != 200:

            #** Check If Rate Limit Has Been Applied **
            if 429 == response.status_code:
                time = response.headers['Retry-After']
                self.logger.warning(f"Rate limited reached! Retrying in {time} seconds.")

                #** Retry Request **
                asyncio.sleep(time)
                self.logger.debug("New Request: https://accounts.spotify.com/api/token")
                response = requests.post("https://accounts.spotify.com/api/token", data, headers=self.authHead)
                
            #** If Other Error Occurs, Raise Error **
            else:
                self.logger.error(f"[RefreshBotToken] Unexpected Error Code '{response.status_code}'")
                self.logger.critical("Spotify Web API Connection Lost!")
                return "UnexpectedError"
        
        authData = response.json()
        token = authData['access_token']

        #** Setup Header For Requests Using Client Credentials  **
        self.botHead = {'Accept': "application/json", 'Content-Type': "application/json", 'Authorization': f"Bearer {token}"}
        self.logger.info("New bot token active!")


    def GetPlaylistSongs(self, PlaylistID: str):

        #** Get A Playlists Songs **
        self.logger.debug("New Request: https://api.spotify.com/v1/playlists/"+str(PlaylistID))
        SongData = requests.get('https://api.spotify.com/v1/playlists/'+str(PlaylistID), headers = self.botHead)

        #** Check If Request Was A Success **
        while SongData.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == SongData.status_code:
                self.logger.info("Bot Token Has Expired")
                self.RefreshBotToken()
                
                #** Retry Request **
                self.logger.debug("New Request: https://api.spotify.com/v1/playlists/"+str(PlaylistID))
                SongData = requests.get('https://api.spotify.com/v1/playlists/'+str(PlaylistID), headers = self.botHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == SongData.status_code:
                time = SongData.headers['Retry-After']
                self.logger.warning("Rate limited reached. Retrying in "+str(time)+" seconds.")
                
                #** Retry Request **
                asyncio.sleep(time)
                self.logger.debug("New Request: https://api.spotify.com/v1/playlists/"+str(PlaylistID))
                SongData = requests.get('https://api.spotify.com/v1/playlists/'+str(PlaylistID), headers = self.botHead)
                
            #** Check If Playlist Not Found, and Return "PlaylistNotFound" **
            elif 404 == SongData.status_code:
                self.logger.debug("[GetPlaylistSongs] Error Code '404' For ID '"+str(PlaylistID)+"'")
                raise Exception("PlaylistNotFound")
            
            #** If Other Error Occurs, Raise Error **
            else:
                self.logger.error("[GetPlaylistSongs] Unexpected Error Code '"+str(SongData.status_code)+"' For PlaylistID '"+str(PlaylistID)+"'")
                raise Exception("UnexpectedError")
        
        #** Iterate Through Each Song And Check Ignore If Empty **
        if SongData != []:
            SongData = SongData.json()
            Songs = []
            for Song in SongData['tracks']['items']:
                
                #** Get Formatted Data For Each Song **
                Songs.append(self.FormatSongData(Song['track']))
            
            #** Return Filled Dictionary Of Songs **
            Songs = {'playlistInfo': {'name': SongData['name'], 'length': SongData['tracks']['total']}, 'tracks': Songs}
            return Songs
        
        #** Return "PlaylistNotFound" if Request Body Is Empty (Shouldn't Happen) **
        else:
            self.logger.error("[GetPlaylistSongs] Empty Request Body For ID '"+str(PlaylistID)+"'")
            raise Exception("PlaylistNotFound")


    def GetAlbumInfo(self, AlbumID: str):

        #** Get An Albums Songs **
        self.logger.debug('New Request: https://api.spotify.com/v1/albums/'+str(AlbumID))
        AlbumData = requests.get('https://api.spotify.com/v1/albums/'+str(AlbumID), headers = self.botHead)

        #** Check If Request Was A Success **
        while AlbumData.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == AlbumData.status_code:
                self.logger.info("Bot Token Has Expired")
                self.RefreshBotToken()
                
                #** Retry Request **
                self.logger.debug('New Request: https://api.spotify.com/v1/albums/'+str(AlbumID))
                AlbumData = requests.get('https://api.spotify.com/v1/albums/'+str(AlbumID), headers = self.botHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == AlbumData.status_code:
                time = AlbumData.headers['Retry-After']
                self.logger.warning("Rate limited reached. Retrying in "+str(time)+" seconds.")
                
                #** Retry Request **
                asyncio.sleep(time)
                self.logger.debug('New Request: https://api.spotify.com/v1/albums/'+str(AlbumID))
                AlbumData = requests.get('https://api.spotify.com/v1/albums/'+str(AlbumID), headers = self.botHead)
                
            #** Check If Album Not Found, and Return "AlbumNotFound" **
            elif 404 == AlbumData.status_code:
                self.logger.debug("[GetAlbumInfo] Error Code '404' For ID '"+str(AlbumID)+"'")
                raise Exception("AlbumNotFound")
            
            #** If Other Error Occurs, Raise Error **
            else:
                self.logger.error("[GetAlbumInfo] Unexpected Error Code '"+str(AlbumData.status_code)+"' For ID '"+str(AlbumID)+"'")
                raise Exception("UnexpectedError")
        
        #** Iterate Through Each Song And Check Ignore If Empty **
        if AlbumData != []:
            AlbumData = AlbumData.json()
            Songs = []
            for Song in AlbumData['tracks']['items']:
                
                #** Get Formatted Data For Each Song **
                Song['album'] = {'name': AlbumData['name'], 'id': AlbumData['id'], 'images': [{'url': AlbumData['images'][0]['url']}], 'album_type': AlbumData['album_type'], 'release_date': AlbumData['release_date']}
                Song['popularity'] = AlbumData['popularity']
                Songs.append(self.FormatSongData(Song))
            
            #** Return Filled Dictionary Of Songs **
            Songs = {'playlistInfo': {'name': AlbumData['name'], 'length': AlbumData['tracks']['total']}, 'tracks': Songs}
            return Songs
        
        #** Return "AlbumNotFound" if Request Body Is Empty (Shouldn't Happen) **
        else:
            self.logger.error("[GetAlbumInfo] Empty Request Body For ID '"+str(AlbumID)+"'")
            raise Exception("AlbumNotFound")
        

    def GetSongInfo(self, SongID: str):

        #** Get Information About A Song **
        self.logger.debug("New Request: https://api.spotify.com/v1/tracks/"+str(SongID))
        Song = requests.get("https://api.spotify.com/v1/tracks/"+str(SongID), headers=self.botHead)

        #** Check If Request Was A Success **
        while Song.status_code != 200:
            
            #** Check if Bot Credentials Have Expired & If So Refresh Token **
            if 401 == Song.status_code:
                self.logger.info("Bot Token Has Expired")
                self.RefreshBotToken()
                
                #** Retry Request **
                self.logger.debug("New Request: https://api.spotify.com/v1/tracks/"+str(SongID))
                Song = requests.get("https://api.spotify.com/v1/tracks/"+str(SongID), headers=self.botHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == Song.status_code:
                time = Song.headers['Retry-After']
                self.logger.warning("Rate limited reached. Retrying in "+str(time)+" seconds.")
                
                #** Retry Request **
                asyncio.sleep(time)
                self.logger.debug("New Request: https://api.spotify.com/v1/tracks/"+str(SongID))
                Song = requests.get("https://api.spotify.com/v1/tracks/"+str(SongID), headers=self.botHead)
                
            #** Check If Song Not Found, and Return "SongNotFound" **
            elif 404 == Song.status_code:
                self.logger.debug("[GetSongInfo] Error Code '404' For ID '"+str(SongID)+"'")
                raise Exception("SongNotFound")
            
            #** If Other Error Occurs, Raise Error **
            else:
                self.logger.error("[GetSongInfo] Unexpected Error Code '"+str(Song.status_code)+"' For ID '"+str(SongID)+"'")
                raise Exception("UnexpectedError")

        #** Check If Song Info Returned & Format Certain Values Before Adding To Dictionary **
        if Song != []:
            Song = Song.json()

            #** Get Formatted Song Data **
            SongInfo = self.FormatSongData(Song)
            
            #** Return Dictionary Of Song Information **
            return {"tracks": [SongInfo]}
        
        #** Return "SongNotFound" if Request Body Is Empty (Shouldn't Happen) **
        else:
            self.logger.error("[GetSongInfo] Empty Request Body For ID '"+str(SongID)+"'")
            raise Exception("SongNotFound")


    def GetAudioFeatures(self, SongIDs: list):

        #** Request Audio Features For a List of Spotify IDs **
        SongIDs = ",".join(SongIDs)
        self.logger.debug("New Request: https://api.spotify.com/v1/audio-features?ids="+str(SongIDs))
        Features = requests.get("https://api.spotify.com/v1/audio-features?ids="+str(SongIDs), headers = self.botHead)

        #** Check If Request Was A Success **
        while Features.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == Features.status_code:
                self.logger.info("Bot Token Has Expired")
                self.RefreshBotToken()
                
                #** Retry Request **
                self.logger.debug("New Request: https://api.spotify.com/v1/audio-features?ids="+str(SongIDs))
                Features = requests.get("https://api.spotify.com/v1/audio-features?ids="+str(SongIDs), headers = self.botHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == Features.status_code:
                time = Features.headers['Retry-After']
                self.logger.warning("Rate limited reached. Retrying in "+str(time)+" seconds.")
                
                #** Retry Request **
                asyncio.sleep(time)
                self.logger.debug("New Request: https://api.spotify.com/v1/audio-features?ids="+str(SongIDs))
                Features = requests.get("https://api.spotify.com/v1/audio-features?ids="+str(SongIDs), headers = self.botHead)
                
            #** Check If Features Not Found, and Return "FeaturesNotFound" **
            elif 404 == Features.status_code:
                self.logger.debug("[GetAudioFeatures] Error Code '404' For ID's '"+str(SongIDs)+"'")
                raise Exception("FeaturesNotFound")
            
            #** If Other Error Occurs, Raise Error **
            else:
                self.logger.error("[GetAudioFeatures] Unexpected Error Code '"+str(Features.status_code)+"' For ID's '"+str(SongIDs)+"'")
                raise Exception("UnexpectedError")
        
        #** Return Audio Features **
        Features = Features.json()
        if Features != None or Features['audio_features'] != None:
            return Features['audio_features']
        else:
            raise Exception("FeaturesNotFound")


    def FormatSongData(self, Song: dict):
        
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
        SongData = {'id': Song['id'],
                    'name': Song['name'],
                    'artists': Artists, 
                    'artistID': ArtistID, 
                    'album': Song['album']['name'], 
                    'albumID': Song['album']['id'], 
                    'art': Song['album']['images'][0]['url'], 
                    'release': Date, 
                    'duration': Song['duration_ms'],
                    'popularity': Song['popularity'], 
                    'explicit': Song['explicit'], 
                    'preview': Song['preview_url'],
                    'updated': datetime.now()}
        return SongData


    def SearchSpotify(self, Name: str, Artist: str = ""):
        
        #** Format Name & Artist To Fill Spaces With %20 **
        Name = "%20".join(str(Name).split(" "))
        Artist = "%20".join(str(Artist).split(" "))
        
        #** Fetch Top Search Result From Spotify **
        Data = {'type': 'track', 'limit': '1', 'include_external': 'audio'}
        self.logger.debug('New Request: https://api.spotify.com/v1/search?q="'+Name+'"%20artist:'+Artist)
        Result = requests.get('https://api.spotify.com/v1/search?q="'+Name+'"%20artist:'+Artist, Data, headers = self.botHead)

        #** Check If Request Was A Success **
        while Result.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == Result.status_code:
                self.logger.info("Bot Token Has Expired")
                self.RefreshBotToken()
                
                #** Retry Request **
                self.logger.debug('New Request: https://api.spotify.com/v1/search?q="'+Name+'"%20artist:'+Artist)
                Result = requests.get('https://api.spotify.com/v1/search?q="'+Name+'"%20artist:'+Artist, Data, headers = self.botHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == Result.status_code:
                time = Result.headers['Retry-After']
                self.logger.warning("Rate limited reached. Retrying in "+str(time)+" seconds.")
                
                #** Retry Request **
                asyncio.sleep(time)
                self.logger.debug('New Request: https://api.spotify.com/v1/search?q="'+Name+'"%20artist:'+Artist)
                Result = requests.get('https://api.spotify.com/v1/search?q="'+Name+'"%20artist:'+Artist, Data, headers = self.botHead)
                
            #** Check If Song Not Found, and Return "SongNotFound" **
            elif 404 == Result.status_code:
                self.logger.debug("[SearchSpotify] Error Code '404' For Input: '"+Name+"' by '"+Artist+"'")
                raise Exception("SongNotFound")
            
            #** If Other Error Occurs, Raise Error **
            else:
                self.logger.error("[SearchSpotify] Unexpected Error Code '"+str(Result.status_code)+"' For Input: '"+Name+"' by '"+Artist+"'")
                raise Exception("UnexpectedError")

        #** Check if Request Body Empty (Shouldn't Happen) & Convert to Json **
        if Result != []:
            Result = Result.json()
            
            #** Check If Any Results Returned **
            if Result['tracks']['items'] != []:

                #** Get Formatted Song Data Of Top Result **
                SongInfo = self.FormatSongData(Result['tracks']['items'][0])
                
                #** Return Dictionary Of Song Information **
                return {"tracks": [SongInfo]}
            
            #** Return Song Not Found If No Songs Returned **
            else:
                self.logger.debug("[SearchSpotify] No Songs Returned For Input: '"+Name+"' by '"+Artist+"'")
                raise Exception("SongNotFound")
        
        #** Return "SongNotFound" If Request Body Is Empty (Shouldn't Happen) **
        else:
            self.logger.error("[SearchSpotify] Empty Request Body For Input: '"+Name+"' by '"+Artist+"'")
            raise Exception("SongNotFound")


    def GetRecommendations(self, data: dict):
        
        #** Requests Recommendations From Spotify With The Data Provided **
        self.logger.debug('New Request: https://api.spotify.com/v1/recommendations')
        Recommendations = requests.get("https://api.spotify.com/v1/recommendations", data, headers = self.botHead)

        #** Check If Request Was A Success **
        while Recommendations.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == Recommendations.status_code:
                self.logger.info("Bot Token Has Expired")
                self.RefreshBotToken()
                
                #** Retry Request **
                self.logger.debug('New Request: https://api.spotify.com/v1/recommendations')
                Recommendations = requests.get("https://api.spotify.com/v1/recommendations", data, headers = self.botHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == Recommendations.status_code:
                time = Recommendations.headers['Retry-After']
                self.logger.warning("Rate limited reached. Retrying in "+str(time)+" seconds.")
                
                #** Retry Request **
                asyncio.sleep(time)
                self.logger.debug('New Request: https://api.spotify.com/v1/recommendations')
                Recommendations = requests.get("https://api.spotify.com/v1/recommendations", data, headers = self.botHead)
                
            #** Check If Recommendations Not Found, and Return "RecommendationsNotFound" **
            elif 404 == Recommendations.status_code:
                self.logger.debug("[GetRecommendations] Error Code '404' For Input: '"+data+"'")
                raise Exception("RecommendationsNotFound")
            
            #** If Other Error Occurs, Raise Error **
            else:
                self.logger.error("[GetRecommendations] Unexpected Error Code '"+str(Recommendations.status_code)+"' For Input: '"+data+"'")
                raise Exception("UnexpectedError")
        
        #** Iterate Through Each Song And Check Ignore If Empty **
        if Recommendations != []:
            Recommendations = Recommendations.json()

            #** Check Spotify Actually Returned Tracks In Request **
            if Recommendations['tracks'] != []:

                #** Return List Of Recommended Songs **
                Songs = []
                for Song in Recommendations['tracks']:
                    Songs.append(self.FormatSongData(Song))
                return Songs

            #** "Return RecommendationsNotFound" If No Songs Returned **
            else:
                self.logger.debug("[GetRecommendations] No Songs Returned For Input: '"+data+"'")
                raise Exception("RecommendationsNotFound")

        #** Return "RecommendationsNotFound" If Request Body Is Empty (Shouldn't Happen) **
        else:
            self.logger.error("[GetRecommendations] Empty Request Body For Input: '"+data+"'")
            raise Exception("RecommendationsNotFound")


#!--------------------------------SONG DATA-----------------------------------#


class SongData(Spotify):
    
    def __init__(self):

        #** Initialise Spotify API Class **
        super().__init__()

        #** Assign Class Objects **
        self.Genres = ['dance', 'pop', 'house', 'alternative', 'country', 'classical', 'electronic', 'folk', 'hip-hop', 'rock', 'heavy-metal', 'indie', 'jazz', 'reggae', 'rnb']
        self.SongFeatures = ['acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'valence']
        self.Keys = {'0': 'C', '1': 'C# / D♭', '2': 'D', '3': 'D♯ / E♭', '4': 'E', '5': 'F', '6': 'F# / G♭', '7': 'G', '8': 'G# / A♭', '9': 'A', '10': 'A# / B♭', '11': 'B'}
        self.Volumes = {'Very Quiet': [-100, -55], 'Quite Quiet': [-55, -45], 'Quiet': [-45, -35], 'Normal': [-35, -25], 'Loud': [-25, -15], 'Quite Loud': [-15, -5], 'Very Loud': [-5, 100]}

        #** Load Test Data **
        with open('SongData.json') as TestFile:
            TestData = json.load(TestFile)
            TestFile.close()
        
        #** Split Test Data Into Prediction & Genre Data **
        PredictionData = []
        GenreData = []
        for Genre in self.Genres:
            for Data in TestData[Genre]:
                PredictionData.append(Data)
                GenreData.append(Genre)
                
        #** Fit Data Lists To Create Prediction Decision Tree **
        Tree = tree.DecisionTreeClassifier()
        self.GenrePredictor = Tree.fit(PredictionData, GenreData)


    def GetSongDetails(self, SongID: str):

        #** Get Song Information and Song Features **
        try:
            SongData = self.GetSongInfo(SongID)
            Features = self.GetAudioFeatures([SongID])[0]
            SongData = SongData['tracks'][0]
        except Exception as e:
            raise e

        #** Add Advanced Information Using Audio Features to Returned Song Info Dict **
        SongData["duration"] = f"{int(Features['duration_ms'] // 60000)} Mins {int((Features['duration_ms'] / 1000) - ((Features['duration_ms'] // 60000) * 60))} Seconds"
        SongData["key"] = self.Keys[str(Features['key'])]
        SongData["beats"] = Features['time_signature']
        SongData["tempo"] = int(Features['tempo'])
        if Features['mode'] <= 0.5:
            SongData["mode"] = "Minor"
        else:
            SongData["mode"] = "Major"
        for Volume, Range in self.Volumes.items():
            if int(Features['loudness']) > Range[0] and int(Features['loudness']) <= Range[1]:
                SongData["volume"] = Volume
                break
        
        #** Predict Genre Of The Song and Add it to The Song Info Dict **
        SongData['genre'] = self.PredictGenre([Features])[0]

        #** Returned Nicely Filled Song Info Dict **
        return SongData
    

    def PredictGenre(self, Features: list):

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


    def RecommendFromTracks(self, Tracks: dict):

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
            try:
                Features = self.GetAudioFeatures(TrackSet)
            except Exception as e:
                raise e

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

                    #** Sort To Sort List First **
                    Array = ToSort.pop(i)
                    ToSort.insert(i, Array[(len(Array) // 2):])
                    ToSort.insert(i, Array[:(len(Array) // 2)])

                    #** Sort Genres Identical To To Sort List **
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
        try:
            Tracks = self.GetRecommendations(data)
        except Exception as e:
            raise e
        
        #** Return Track List **
        return Tracks
    