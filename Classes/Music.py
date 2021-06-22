
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import requests
import pandas as pd
from time import sleep
from sklearn import tree
from datetime import datetime
from Classes.Spotify import Spotify


#!--------------------------------HISTORY-----------------------------------#


class Music(Spotify):
    
    def __init__(self):

        #** Initialise Youtube & Spotify Classes **
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


    def Recommend(self, Songs):

        #** Assign Variables **
        Data = {'duration_ms': [], 'key': [], 'mode': [], 'time_signature': [], 'acousticness': [], 'danceability': [], 'energy': [], 'instrumentalness': [], 'liveness': [], 'loudness': [], 'speechiness': [], 'valence': [], 'tempo': []}
        UserGenres = {'dance': 0, 'pop': 0, 'house': 0, 'alternative': 0, 'country': 0, 'classical': 0, 'electronic': 0, 'folk': 0, 'hip-hop': 0, 'rock': 0, 'heavy-metal': 0, 'indie': 0, 'jazz': 0, 'reggae': 0, 'rnb': 0}
        
        #** Sort All Song ID's Into Groups Of 100 and Get Audio Features For Each Group Of Song IDs **
        SongIDs = []
        for ID in Songs.keys():
            SongIDs.append(ID)
        SongIDs = [SongIDs[x:x+100] for x in range(0, len(SongIDs), 100)]
        for List in SongIDs:
            Features = self.GetAudioFeatures(List)

            #** Sort Audio Features Into Groups Based On Feature **
            for Song in Features:
                for Key in Data.keys():
                    List = Data[Key]
                    List.append(Song[Key])
                    Data[Key] = List

                #** Get Genre For Songs and Add To Collective List **
            Genres = self.PredictGenre(Features)
            print(len(Genres))
            for Genre in Genres:
                UserGenres[Genre] += 1
        UserGenres = {key:value for key, value in sorted(UserGenres.items(), key=lambda item: item[1], reverse=True)}

        #**Construct Pandas Dataframe and Get Averages and Max / Min of Data **
        Dataframe = pd.DataFrame(Data, columns = ['duration_ms', 'key', 'mode', 'time_signature', 'acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness', 'valence', 'tempo'])
        Max = Dataframe.max()
        Min = Dataframe.min()
        Avg = Dataframe.mean()

        #** Assign Data and Request to Spotify for 50 Recomendations **
        data = {'limit': 50, 'seed_genres': ",".join(list(UserGenres.keys())[:2]),
                'min_acousticness': Min[4], 'target_acousticness': Avg[4], 'max_acousticness': Max[4], 
                'min_danceability': Min[5], 'target_danceability': Avg[5], 'max_danceability': Max[5], 
                'min_energy': Min[6], 'target_energy': Avg[6], 'max_energy': Max[6], 
                'min_instrumentalness': Min[7], 'target_instrumentalness': Avg[7], 'max_instrumentalness': Max[7], 
                'min_liveness': Min[8], 'target_liveness': Avg[8], 'max_liveness': Max[8], 
                'min_loudness': Min[9], 'target_loudness': Avg[9], 'max_loudness': Max[9],
                'min_speechiness': Min[10], 'target_speechiness': Avg[10], 'max_speechiness': Max[10], 
                'min_valence': Min[11], 'target_valence': Avg[11], 'max_valence': Max[11],
                'min_tempo': Min[12], 'target_tempo': Avg[12], 'max_tempo': Max[12]}
        Recommendations = requests.get("https://api.spotify.com/v1/recommendations", data, headers = self.BotHead).json()

        #** If Error, Refresh Token and Try Again **
        if 'error' in Recommendations.keys():
            self.RefreshUserToken()
            Recommendations = requests.get("https://api.spotify.com/v1/recommendations", data, headers = self.BotHead).json()

        #** Return List Of Recommended Songs **
        return Recommendations['tracks']
