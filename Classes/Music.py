
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import base64
import requests
import pandas as pd
from time import sleep
from sklearn import tree
from datetime import datetime
from Classes.Database import UserData


#!--------------------------------SPOTIFY-----------------------------------#


class Spotify():
    
    def __init__(self):

        #** Get Spotify Details **
        self.ID = os.environ["SPOTIFY_CLIENT"]
        self.Secret = os.environ["SPOTIFY_SECRET"]

        #** Setup Header For Authentication **
        ClientData = self.ID+":"+self.Secret
        AuthStr =  base64.urlsafe_b64encode(ClientData.encode()).decode()
        self.AuthHead = {"Content-Type": "application/x-www-form-urlencoded", 'Authorization': 'Basic {0}'.format(AuthStr)}

        #** Get A Bot Token For API Calls **
        self.RefreshBotToken()

        #** Setup Database **
        self.Database = UserData()


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
                if Songs != []:
                
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
        
        #** Itterate Through Each Song And Check Ignore If Empty **
        if AlbumData != []:
            AlbumData = AlbumData.json()
            Songs = {}
            for Song in AlbumData['tracks']['items']:
                if Songs != []:
                
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


#!---------------------------------YOUTUBE---------------------------------------#


class YoutubeAPI():
    
    def __init__(self):

        #** Create Class Objects For Requests **
        self.Key = os.environ["GOOGLE_KEY"]
        self.Header = {'Accept': 'application/json'}

        #** Setup Database Connection **
        self.Database = UserData()
        
    
    def Search(self, Query):
        
        #** Search Youtube API For Specified Query **
        Data = {'part': 'snippet', 'q': Query, 'key': self.Key}
        Results = requests.get('https://youtube.googleapis.com/youtube/v3/search', Data, headers = self.Header)

        #** Check If Request Was A Success **
        while Results.status_code != 200:
                
            #** Check If Quota Limit Has Been Applied **
            if 403 == Results.status_code:
                print("----------------------QUOTA LIMIT REACHED--------------------")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                return "UnexpectedError"
                
            #** Check If Playlist Not Found, and Return "ContentNotFound" **
            elif 404 == Results.status_code:
                return "ContentNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("----------------------UNEXPECTED ERROR--------------------")
                print("Location: Youtube -> Search")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Youtube Request Code "+str(Results.status_code))
                return "UnexpectedError"

        #** For Each Returned Video, Check if Valid Video and Add Data To Dictionary **
        Results = Results.json()
        SearchDict = {}
        for Result in Results['items']:
            if Result['id']['kind'] == 'youtube#video':    
                SearchDict.update({Result['id']['videoId']: {'Title': Result['snippet']['title'],
                                                             'Description': Result['snippet']['description'],
                                                             'Channel': Result['snippet']['channelTitle'], 
                                                             'ChannelID': Result['snippet']['channelId'],
                                                             'Thumbnail': Result['snippet']['thumbnails']['default']['url'],
                                                             'PublishDate': Result['snippet']['publishedAt']}})

        #** Returned Filled Dictionary With Search Results **      
        return SearchDict
    
    
    def GetVideoInfo(self, Track):
        
        #** Get Video ID **
        print(Track)
        VideoID = Track.uri.split("=")[1]
    
        #** Check If Song Title Is A Music Video
        if ("Official Video" in Track.title or 'Official Music Video' in Track.title or 'Official Lyric Video' in Track.title or (Track.author+" - ").lower() in Track.title.lower()) and Track.duration <= 600000:
            Title = (Track.title.lower()).replace('official video', '').replace('official music video', '').replace('official lyric video', '').replace('[]', '').replace('()', '')
            
            #** Get Title & Artist Of Song **
            if " - " in Title:
                Title = Title.split(" - ")
                Artist = Title[0]
                Title = Title[1]
            else:
                Artist = Track.author
            
            #** Set Music To True & Add New Title **
            SongData = {VideoID: {'Music': True,
                                  'Title': Title.title(), 
                                  'Artist': Artist.title()}}
            
            #** Return Data **
            return SongData
        
        #** Request Info About Video ID From Youtube API **
        Data = {'part': 'snippet,player,contentDetails,topicDetails,statistics', 'id': VideoID, 'key': self.Key}
        Info = requests.get('https://youtube.googleapis.com/youtube/v3/videos', Data, headers = self.Header)

        #** Check If Request Was A Success **
        while Info.status_code != 200:
                
            #** Check If Quota Limit Has Been Applied **
            if 403 == Info.status_code:
                print("----------------------QUOTA LIMIT REACHED--------------------")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                return "UnexpectedError"
                
            #** Check If Playlist Not Found, and Return "ContentNotFound" **
            elif 404 == Info.status_code:
                return "ContentNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("----------------------UNEXPECTED ERROR--------------------")
                print("Location: Youtube -> Search")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Youtube Request Code "+str(Info.status_code))
                return "UnexpectedError"
        
        #** Read Request Json and Prepare For Formatting **
        Info = Info.json()
        Info = Info['items'][0]

        #** Format Player Embed URL **
        Embed = Info['player']['embedHtml']
        Embed = Embed.split(" ")[3]
        PlayerURL = Embed.replace('src="//', '').replace('"', '')

        #** Check If Topic Is Music **
        Topic = False
        Topics = Info['topicDetails']['topicCategories']
        for URL in Topics:
            if 'music' in URL.lower():
                Topic = True

        #** Format Duration Into Hours, Minutes, and Seconds **
        Duration = Info['contentDetails']['duration'].replace('PT', '')
        if 'H' in Duration:
            Duration = Duration.split('H')
            Hours = int(Duration[0])
            Minutes = int(Duration[1].split('M')[0])
            Seconds = int(Duration[1].split('M')[1].replace('S', ''))
        elif 'M' in Duration:
            Duration = Duration.split('M')
            Hours = None
            Minutes = int(Duration[0])
            Seconds = int(Duration[1].replace('S', ''))
        else:
            Hours = None
            Minutes = None
            Seconds = int(Duration.replace('S', ''))
        
        #** Get Artist / Author Of Video **
        if " - " in Track.title:
            Artist = Track.title.split(" - ")[0]
        else:
            Artist = Track.author

        #** Fill Necessary Data Into A Dictionary Ready To Be Returned **
        SongData = {Info['id']: {'Duration': {'Hours': Hours, 'Minutes': Minutes, 'Seconds': Seconds},
                                 'Player': PlayerURL,
                                 'Music': Topic,
                                 'Artist': Artist,
                                 'Views': Info['statistics']['viewCount'],
                                 'Likes': Info['statistics']['likeCount'],
                                 'Dislikes': Info['statistics']['dislikeCount'],
                                 'Title': Info['snippet']['title'],
                                 'Description': Info['snippet']['description'],
                                 'Channel': Info['snippet']['channelTitle'], 
                                 'ChannelID': Info['snippet']['channelId'],
                                 'Thumbnail': Info['snippet']['thumbnails']['default']['url'],
                                 'PublishDate': Info['snippet']['publishedAt']}}
        
        #** Return Filled SongData Dictionary **
        return SongData


#!---------------------------------SOUNDCLOUD---------------------------------------#


class SoundcloudAPI():
    
    def __init__(self):

        #** Create Class Objects For Requests **
        self.ClientID = os.environ["SOUNDCLOUD_ID"]

        #** Setup Database Connection **
        self.Database = UserData()
        
    
    def GetSoundcloudTrack(self, ID):
        
        #** Get Info From Soundcloud API **
        Result = requests.get("https://api-v2.soundcloud.com/tracks?ids=%s&client_id=%s", data=[ID, self.ClientID])

        print(Result)


#!--------------------------------HISTORY-----------------------------------#


class Music(Spotify, YoutubeAPI, SoundcloudAPI):
    
    def __init__(self):

        #** Initialise Youtube, Soundcloud & Spotify API Classes **
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
                
        UserGenres = {key:value for key, value in sorted(UserGenres.items(), key=lambda item: item[1], reverse=True)} #! Replace with
                                                                                                                      #! Sorting Algorithm

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


    def GetLyrics(self, Query):
        
        #** Request Lyrics From API **
        Lyrics = requests.get("https://lyrics-api.powercord.dev/lyrics?", params={"input": Query.replace(" ", "%20")})
        
        #** Check If Request Was A Success **
        while Lyrics.status_code != 200:
                
            #** Check If Lyrics Not Found, and Return "LyricsNotFound" **
            if 404 == Lyrics.status_code:
                return "LyricsNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Location: Music -> GetLyrics")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Request Status Code "+str(Lyrics.status_code))
                return "UnexpectedError"
        
        #** Get Lyrics Json **
        Lyrics = Lyrics.json()['data'][0]
        
        LyricData = {"Lyrics": Lyrics['lyrics'],
                     "Meta": {
                         "Title": Lyrics['name'],
                         "Artist": Lyrics['artist'],
                         "Art": Lyrics['album_art'],
                         "URL": Lyrics['url']},
                     "Spotify": {
                         "TrackID": Lyrics['meta']['spotify']['track'],
                         "ArtistID": Lyrics['meta']['spotify']['artists']}}
        
        #** Return Formatted Data **
        return LyricData
    