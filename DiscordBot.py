
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import numpy
import scipy
import base64
import string
import random
import asyncio
import discord
import requests
import pandas as pd
import mysql.connector
from time import sleep
from sklearn import tree
from datetime import datetime
from discord.utils import get
from discord.ext import commands


#!--------------------------------DATABASE CONNECTION-----------------------------------# 

#** Startup Sequence **
print("-----------------------STARTING UP----------------------")
print("Startup Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))

#** Get Connection Details **
Host = os.environ["DATABASE_HOST"]
User = os.environ["DATABASE_USER"]
Password = os.environ["DATABASE_PASS"]

#** Connect To Database **
connection = mysql.connector.connect(host = Host,
                                     database = "Melody",
                                     user = User,
                                     password = Password)

#** Setup Cursor and Output Successful Connection **                  
if connection.is_connected():
    cursor = connection.cursor()
    cursor.execute("select database();")
    record = cursor.fetchone()
    print("Connected To Database: "+record[0].title()+"\n")

#** Delete Connection Details **
del Host
del User
del Password


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
                print("----------------------RATE LIMIT REACHED--------------------")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                Time = SongData.headers['Retry-After']
                sleep(Time)
                SongData = requests.get('https://api.spotify.com/v1/playlists/'+str(PlaylistID), headers = self.BotHead)
                
            #** Check If Playlist Not Found, and Return "PlaylistNotFound" **
            elif 404 == SongData.status_code:
                return "PlaylistNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("----------------------UNEXPECTED ERROR--------------------")
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
            return Songs
        
        #** Return "PlaylistNotFound" if Request Body Is Empty (Shouldn't Happen) **
        else:
            return "PlaylistNotFound"
        

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
                print("----------------------RATE LIMIT REACHED--------------------")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                Time = Song.headers['Retry-After']
                sleep(Time)
                Song = requests.get("https://api.spotify.com/v1/tracks/"+str(SongID), headers=self.BotHead)
                
            #** Check If Song Not Found, and Return "SongNotFound" **
            elif 404 == Song.status_code:
                return "SongNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("----------------------UNEXPECTED ERROR--------------------")
                print("Location: Spotify -> GetSongInfo")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                print("Error: Spotify Request Code "+str(Song.status_code))
                return "UnexpectedError"

        #** Check If Song Info Returned & Format Certain Values Before Adding To Dictionary **
        if Song != []:
            Song = Song.json()

            #** Get Formatted Song Data **
            Songs = self.FormatSongData(Song)
            
            #** Return Dictionary Of Song Information **
            return Songs
        
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
                print("----------------------RATE LIMIT REACHED--------------------")
                print("Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
                Time = Features.headers['Retry-After']
                sleep(Time)
                Features = requests.get("https://api.spotify.com/v1/audio-features?ids="+str(SongIDs), headers = self.BotHead)
                
            #** Check If Features Not Found, and Return "FeaturesNotFound" **
            elif 404 == Features.status_code:
                return "FeaturesNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("----------------------UNEXPECTED ERROR--------------------")
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
        SongData = {Song['id']: {'Name': Song['name'], 'Artists': Artists, 'ArtistID': ArtistID, 'Album': Song['album']['name'], 'AlbumID': Song['album']['id'], 'Art': Song['album']['images'][0]['url'], 'Release': Date, 'Popularity': Song['popularity'], 'Explicit': Song['explicit'], 'Preview': Song['preview_url']}}
        return SongData


    def Search(self, Name, Artist):
        
        Name = "%20".join(Name.split(" "))
        print(Name)
        Artist = "%20".join(Artist.split(" "))
        print(Artist)
        
        Data = {'type': 'track', 'limit': '1', 'include_external': 'audio'}
        Result = requests.get('https://api.spotify.com/v1/search?q="'+Name+'"%20artist:'+Artist, Data, headers = self.BotHead)

        print(Result.json())


#!-------------------------------YOUTUBE-------------------------------------#


class Youtube():
    def __init__(self):
        
        #** Create Class Objects For Requests **
        self.Key = 'AIzaSyCzNECwDbkWMNGyHC1fRF08vNldmI8_5iE'
        self.Header = {'Accept': 'application/json'}
        
    
    def Search(self, Query):
        
        Data = {'part': 'snippet', 'q': Query, 'key': self.Key}
        Results = requests.get('https://youtube.googleapis.com/youtube/v3/search', Data, headers = self.Header).json()

        SearchDict = {}
        for Result in Results['items']:
            if Result['id']['kind'] == 'youtube#video':
                
                SearchDict.update({Result['id']['videoId']: {'Tittle': Result['snippet']['title'],
                                                             'Description': Result['snippet']['description'],
                                                             'Channel': Result['snippet']['channelTitle'], 
                                                             'ChannelID': Result['snippet']['channelId'],
                                                             'Thumbnail': Result['snippet']['thumbnails']['default']['url'],
                                                             'PublishDate': Result['snippet']['publishedAt']}})
                    
        return SearchDict
    
    
    def GetVideoInfo(self, VideoID):
        
        Data = {'part': 'player,contentDetails,topicDetails', 'id': 'gvUuAQsDrU0', 'key': self.Key}
        Info = requests.get('https://youtube.googleapis.com/youtube/v3/videos', Data, headers = self.Header).json()
        
        print(Info)
            

#!--------------------------------HISTORY-----------------------------------#


class Music(Spotify):
    def __init__(self):

        #** Initialise Spotify Class **
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
            with open('TestData - Copy.json') as TestFile:
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
            Features = SongData.GetAudioFeatures(List)

            #** Sort Audio Features Into Groups Based On Feature **
            for Song in Features:
                for Key in Data.keys():
                    List = Data[Key]
                    List.append(Song[Key])
                    Data[Key] = List

                #** Get Genre For Songs and Add To Collective List **
            Genres = SongData.PredictGenre(Features)
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


#!--------------------------------SPOTIFY USER-----------------------------------#


class SpotifyUser():
    def __init__(self, DiscordID):

        #** Get Spotify Details **
        self.SpotifyID = os.environ["SPOTIFY_CLIENT"]
        self.Secret = os.environ["SPOTIFY_SECRET"]

        #** Setup Header For Authentication **
        ClientData = self.SpotifyID+":"+self.Secret
        AuthStr =  base64.urlsafe_b64encode(ClientData.encode()).decode()
        self.AuthHead = {"Content-Type": "application/x-www-form-urlencoded", 'Authorization': 'Basic {0}'.format(AuthStr)}

        #** Get Spotify Credentials From Database **
        cursor.execute("SELECT spotify FROM users WHERE discordID='"+str(DiscordID)+"';")
        ID = cursor.fetchone()
        if str(ID) != 'None':
            if str(ID[0]) != 'None':
                cursor.execute("SELECT * FROM spotify WHERE ID='"+str(ID[0])+"';")
                Data = cursor.fetchone()

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


#!--------------------------------DATABASE CONNECTIONS-----------------------------------#


class UserData():
    def __init__(self, cursor, connection):

        #** Assign Class Objects **
        self.cursor = cursor
        self.connection = connection

    def GetUser(self, discordID):

        #** Get Info About Discord User From Database **
        self.cursor.execute("SELECT * FROM users WHERE DiscordID = '"+str(discordID)+"';")
        UserData = self.cursor.fetchone()

        #** Return Returned Row **
        return UserData

    def GetStats(self, ID):

        #** Get Users Statistics From Database **
        self.cursor.excute("SELECT * FROM user_stats WHERE ID = '"+str(ID)+"';")
        Stats = self.cursor.fetchone()

        #** Return Returned Row **
        return Stats

    def GetHistory(self, ID):

        #** Get Users Listening History From Database **
        self.cursor.execute("SELECT * FROM history WHERE ID = '"+str(ID)+"';")
        History = self.cursor.fetchone()

        #** Return Returned Row **
        return History

    def AddUser(self, discordID):

        #** Add Blank Listening History Row **
        self.cursor.execute("INSERT INTO history (Song1) VALUES ('None');")
        self.connection.commit()

        #** Get ID of Listening History **
        self.cursor.execute("SELECT LAST_INSERT_ID();")
        HistoryID = self.cursor.fetchone()[0]

        #** Add Blank Statistics Row **
        self.cursor.execute("INSERT INTO user_stats (TopSong) VALUES ('None');")
        self.connection.commit()

        #** Get ID of User Statistics **
        self.cursor.execute("SELECT LAST_INSERT_ID();")
        StatsID = self.cursor.fetchone()[0]

        #** Write Data About User To Users Table **
        Data = (discordID, str(HistoryID), str(StatsID), "None", "None")
        self.cursor.execute("INSERT INTO users VALUES "+str(Data)+";")
        self.connection.commit()

        #** Return User Data Just Created **
        return Data
    
    def RemoveSpotify(self, DiscordID):
        User = self.GetUser(DiscordID)
        self.cursor.execute("DELETE FROM spotify WHERE ID='"+User[4]+"'")
        self.cursor.execute("UPDATE users SET Spotify = 'None' WHERE DiscordID = '"+str(DiscordID)+"';")
        self.connection.commit()


#!--------------------------------DISCORD BOT-----------------------------------# 


#** Creating Bot Client **
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix = "!", case_insensitive=True, intents=intents)

#** Assigning Global Variables **
SongData = Music()
Database = UserData(cursor, connection)
ActiveStates = {}

#** Setup Global Variables **
NextIcon = None
BackIcon = None
SpotifyIcon = None
AlbumIcon = None
PreviewIcon = None
Tick = None
Cross = None

#!--------------------------------DISCORD EVENTS-----------------------------------# 


@client.event
async def on_ready():
    print("Connection Established!")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=" Beta V1.03"))
    print("Preparing Internal Cache...")
    await client.wait_until_ready()
    print("Bot Is Now Online & Ready!\n")

    #** Import Global Variables **
    global NextIcon
    global BackIcon
    global SpotifyIcon
    global AlbumIcon
    global PreviewIcon
    global Tick
    global Cross

    #** Get Emojis **
    NextIcon = client.get_emoji(817548034732064799)
    BackIcon = client.get_emoji(817548165217386566)
    SpotifyIcon = client.get_emoji(738865749824897077)
    AlbumIcon = client.get_emoji(809904275739639849)
    PreviewIcon = client.get_emoji(810242525247045692)
    Tick = client.get_emoji(738865801964027904)
    Cross = client.get_emoji(738865828648189972)


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        Temp = await ctx.message.channel.send("**Command Not Found!**\nFor a full list of commands, run `!help`")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        Temp = await ctx.message.channel.send("**Missing Paramater!**\nFor a full list of commands & their parameters, run `!help`")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()
        return
    else:
        raise error


#!--------------------------------DISCORD COMMANDS-----------------------------------# 


@client.command(aliases=['song', 'i', 'songinfo'])
async def info(ctx, SpotifyID):

    #** Format Input Data and Check To Make Sure It's A Valid ID **
    print(ctx.author.name)
    print(SpotifyID)
    Error = False
    if SpotifyID.startswith("https://open.spotify.com/track/"):
        SpotifyID = (SpotifyID.split("/"))[4].split("?")[0]
    if len(SpotifyID) == 22:

        #** Get Song Details And Check If Song Is Found **
        SongInfo = SongData.GetSongDetails(SpotifyID)
        if SongInfo != "SongNotFound":

            #** Format Returned Data Ready To Be Put Into The Embeds **
            SongInfo = SongInfo[SpotifyID]
            Description = "**By: **"
            for i in range(len(SongInfo['Artists'])):
                if i == 0:
                    Description += "["+SongInfo['Artists'][i]+"](https://open.spotify.com/artist/"+SongInfo['ArtistID'][i]+")"
                elif i != len(SongInfo['Artists'])-1:
                    Description += ", ["+SongInfo['Artists'][i]+"](https://open.spotify.com/artist/"+SongInfo['ArtistID'][i]+")"
                else:
                    Description += " & ["+SongInfo['Artists'][i]+"](https://open.spotify.com/artist/"+SongInfo['ArtistID'][i]+")"
            Links = str(SpotifyIcon)+" Song: [Spotify](https://open.spotify.com/track/"+SpotifyID+")\n"
            if SongInfo['Preview'] != None:
                Links += str(PreviewIcon)+" Song: [Preview]("+SongInfo['Preview']+")\n"
            if SongInfo['AlbumID'] != None:
                Links += str(AlbumIcon)+" Album: ["+SongInfo['Album']+"](https://open.spotify.com/album/"+SongInfo['AlbumID']+")"
            else:
                Links += str(AlbumIcon)+" Album: "+SongInfo['Album']
            
            #** Setup Embed With Basic Song Information **
            Basic = discord.Embed(
                title=SongInfo['Name'], 
                description=Description)
            if SongInfo['Art'] != None:
                Basic.set_thumbnail(url=SongInfo['Art'])
            Basic.set_footer(text="(1/2) React To See Advanced Song Information!")
            Basic.add_field(name="Length:", value=SongInfo['Duration'], inline=False)
            Basic.add_field(name="Released:", value=SongInfo['Release'], inline=True)
            Basic.add_field(name="Genre:", value=SongInfo['Genre'].title(), inline=True)
            Basic.add_field(name="Links:", value=Links, inline=False)
            
            #** Setup Embed With Advanced Song Information **
            Advanced = discord.Embed(
                title=SongInfo['Name'], 
                description=Description)
            if SongInfo['Art'] != None:
                Advanced.set_thumbnail(url=SongInfo['Art'])
            Advanced.set_footer(text="(2/2) React To See Basic Song Information!")
            Advanced.add_field(name="Popularity:", value=SongInfo['Popularity'], inline=True)
            Advanced.add_field(name="Explicit:", value=SongInfo['Explicit'], inline=True)
            Advanced.add_field(name="Tempo:", value=SongInfo['Tempo'], inline=True)
            Advanced.add_field(name="Key:", value=SongInfo['Key'], inline=True)
            Advanced.add_field(name="Beats Per Bar:", value=SongInfo['BeatsPerBar'], inline=True)
            Advanced.add_field(name="Mode:", value=SongInfo['Mode'], inline=True)

            #** Send First Embed To Discord And Add Reactions **
            Page = await ctx.send(embed=Basic)
            await Page.add_reaction(BackIcon)
            await Page.add_reaction(NextIcon)
            CurrentPage = 1

            #** Check Function To Be Called When Checking If Correct Reaction Has Taken Place **
            def ReactionAdd(Reaction):
                return (Reaction.message_id == Page.id) and (Reaction.user_id != 803939964092940308)

            #** Watches For Reactions, Checks Them And Then Acts Accordingly **
            while True:
                Reaction = await client.wait_for("raw_reaction_add", check=ReactionAdd)
                if Reaction.event_type == 'REACTION_ADD':
                    if Reaction.emoji == NextIcon or Reaction.emoji == BackIcon:
                        await Page.remove_reaction(Reaction.emoji, Reaction.member)
                        if CurrentPage == 1:
                            await Page.edit(embed=Advanced)
                            CurrentPage = 2
                        else:
                            await Page.edit(embed=Basic)
                            CurrentPage = 1
                    else:
                        await Page.remove_reaction(Reaction.emoji, Reaction.member)
    
        #** Output Song Not Found If Music.GetSongDetails() Returns Song Not Found **
        else:
            Error = True
    else:
        Error = True

    #** Output Error To User **
    if Error == True:
        Temp = await ctx.send("**Invalid SongID!**\nFor help with this command, run `!help info`")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()


@client.command()
async def user(ctx, discordID):
    User = Database.GetUser(discordID)
    if User == None:
        User = Database.AddUser(discordID)
    await ctx.send(User)


@client.command(aliases=['l', 'connect'])
async def link(ctx):
    
    Error = False
    Spotify = SpotifyUser(ctx.author.id)
    if Spotify.Connected == False:

        #** Add User To Database **
        User = Database.GetUser(ctx.author.id)
        if User == None:
            User = Database.AddUser()

        #** Generate Random State and Make Sure It Isn't Active **
        while True:
            State = []
            for i in range(10):
                State.append(random.choice(string.ascii_letters))
            State = "".join(State)
            if not(State in ActiveStates.keys()):
                ActiveStates[State] = ctx.author.id
                break

        #** Send Embed With Auth URL Into User's DMs And Notify User **
        AuthURL = "https://accounts.spotify.com/authorize?client_id=710b5d6211ee479bb370e289ed1cda3d&response_type=code&redirect_uri=http%3A%2F%2F82.22.157.214:5000%2F&scope=playlist-read-private%20playlist-read-collaborative&state="+State
        Embed = discord.Embed(
            title = "Link Your Spotify Account!",
            description = "To link your spotify account, [Click Here]("+AuthURL+")!\nOnce authorised, you'll receive a confirmation underneath!",
            colour = discord.Colour.dark_green())
        Embed.set_footer(text="Authentication Will Time Out After 10 Minutes")
        DMChannel = await ctx.message.author.create_dm()
        try:
            AuthEmbed = await DMChannel.send(embed=Embed)
            await ctx.send("I've sent you a DM!")
        except :
            Error = True

        #** Check For User Details In Database Every 5 Seconds For 10 Mins **
        if not(Error):
            print(State)
            await asyncio.sleep(10)
            cursor.execute("SELECT * FROM spotify WHERE State = '"+str(State)+"';")
            Spotify = cursor.fetchone()
            connection.commit()
            print(Spotify)
            for Count in range(118):
                if Spotify != None:
                    break
                await asyncio.sleep(5)
                cursor.execute("SELECT * FROM spotify WHERE State = '"+str(State)+"';")
                Spotify = cursor.fetchone()
                connection.commit()
                print(Spotify)
            ActiveStates.pop(State)

            #** Update Users To Include Spotify Table ID **
            if Spotify != None:
                cursor.execute("UPDATE users SET Spotify = '"+str(Spotify[0])+"' WHERE DiscordID = '"+str(ctx.author.id)+"';")
                connection.commit()
            
                #** Let User Know They're Connected **
                Embed = discord.Embed(
                    title = "Account Connected!",
                    colour = discord.Colour.dark_green())
                Embed.set_thumbnail(url=Spotify[5])
                Embed.add_field(name="Username", value="["+Spotify[3]+"](https://open.spotify.com/user/"+Spotify[4]+")")
                await AuthEmbed.edit(embed=Embed)

            #** Let User Know If Authentication Times Out **
            else:
                await AuthEmbed.edit(content="Authentication Timed Out!\nTo restart the linking process, re-run `!link`!")
            
    else:
        #** Send Embed Asking User If They'd Like To Unlink Into DMs **
        UnlinkEmbed = discord.Embed(
            title = "Your Spotify Is Already Linked!",
            description = "**Account:**\n["+Spotify.Name+"](https://open.spotify.com/user/"+Spotify.ID+")\n\nIf You'd Like To Unlink Your Account, Please:\n`React To The Tick Below`",
            colour = discord.Colour.dark_green())
        DMChannel = await ctx.message.author.create_dm()
        try:
            Unlink = await DMChannel.send(embed=UnlinkEmbed)
            await ctx.send("I've sent you a DM!")
        except :
            Error = True
            
        if not(Error):
            await Unlink.add_reaction(Tick)
            
            #** Check Function To Be Called When Checking If Correct Reaction Has Taken Place **
            def ReactionAdd(Reaction):
                return (Reaction.message_id == Unlink.id) and (Reaction.user_id != 803939964092940308)

            #** Watches For Reactions, Checks Them And Then Acts Accordingly **
            while True:
                Reaction = await client.wait_for("raw_reaction_add", check=ReactionAdd)
                if Reaction.event_type == 'REACTION_ADD':
                    print(Reaction.emoji)
                    if Reaction.emoji == Tick:
                        Database.RemoveSpotify(ctx.author.id)
                        await DMChannel.send("**Spotify Account Unlinked!**\nIf you need to relink at any time, simply run `!link`.")
                          
    #** If Error, Tell User To Open Their DMs With The Bot **
    if Error == True:
        Temp = await ctx.message.channel.send("**DM Failed!**\nPlease turn on `Allow Server Direct Messages` in Discord settings in order to link your account")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()


@client.command(aliases=['r', 'recommend', 'suggest', 'songideas'])
async def recommendations(ctx):

    #** Add User To Database **
    User = SpotifyUser(ctx.author.id)
    if User.Connected:
        print("User Found")
        
        #** Get User Playlists & Songs In Those Playlists **
        Playlists = User.GetUserPlaylists()
        print("Got Playlists")
        Songs = {}
        for PlaylistID in Playlists.keys():
            Songs.update(SongData.GetPlaylistSongs(PlaylistID))
        print("Got Songs")
        
        #** Get Recommendations From Returned Songs **
        NewSongs = SongData.Recommend(Songs)
        print("Got Recomendations")
        
        #** Randomly Choose 10 Songs From 50 Recomendations **
        Recommendations = {}
        Description = ""
        for i in range(10):
            Song = random.choice(NewSongs)
            while Song in Recommendations.values():
                Song = random.choice(NewSongs)
            Recommendations[i] = Song

        #** Prepare Data On Songs Ready To Be Displayed **
        Data = Recommendations[0]
        Song = Data['name']+"\nBy: "
        for i in range(len(Data['artists'])):
            if i == 0:
                Song += "["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
            elif i != len(Data['artists'])-1:
                Song += ", ["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
            else:
                Song += " & ["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
        Links = str(SpotifyIcon)+" Song: [Spotify]("+Data['external_urls']['spotify']+")\n"
        if Data['preview_url'] != None:
            Links += str(PreviewIcon)+" Song: [Preview]("+Data['preview_url']+")\n"
        Links += str(AlbumIcon)+" Album: ["+Data['album']['name']+"]("+Data['album']['external_urls']['spotify']+")"

        #** Setup Base Embed With Fields For First Song **
        BaseEmbed = discord.Embed(
            title = "Your Recommendations")
        BaseEmbed.set_thumbnail(url=Recommendations[0]['album']['images'][0]['url'])
        BaseEmbed.add_field(name="Song 1:", value=Song, inline=False)
        BaseEmbed.add_field(name="Links:", value=Links, inline=False)
        BaseEmbed.set_footer(text="(1/10) React To See More Recommendations!")

        #** Send First Embed To Discord And Add Reactions **
        Page = await ctx.send(embed=BaseEmbed)
        await Page.add_reaction(BackIcon)
        await Page.add_reaction(NextIcon)
        CurrentPage = 0
        print("Sent!")

        #** Check Function To Be Called When Checking If Correct Reaction Has Taken Place **
        def ReactionAdd(Reaction):
            return (Reaction.message_id == Page.id) and (Reaction.user_id != 803939964092940308)

        #** Watches For Reactions, Checks Them And Then Acts Accordingly **
        while True:
            Reaction = await client.wait_for("raw_reaction_add", check=ReactionAdd)
            if Reaction.event_type == 'REACTION_ADD':
                await Page.remove_reaction(Reaction.emoji, Reaction.member)
                if Reaction.emoji == NextIcon or Reaction.emoji == BackIcon:
                    
                    #** Adjust Current Page Based On Reaction **
                    if CurrentPage == 9 and Reaction.emoji == NextIcon:
                        CurrentPage = 0
                    elif CurrentPage == 0 and Reaction.emoji == BackIcon:
                        CurrentPage = 9
                    else:
                        if Reaction.emoji == NextIcon:
                            CurrentPage += 1
                        else:
                            CurrentPage -= 1
                            
                    #** Prepare New Data For Next Song **
                    Data = Recommendations[CurrentPage]
                    Song = Data['name']+"\nBy: "
                    for i in range(len(Data['artists'])):
                        if i == 0:
                            Song += "["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
                        elif i != len(Data['artists'])-1:
                            Song += ", ["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
                        else:
                            Song += " & ["+Data['artists'][i]['name']+"]("+Data['artists'][i]['external_urls']['spotify']+")"
                    Links = str(SpotifyIcon)+" Song: [Spotify]("+Data['external_urls']['spotify']+")\n"
                    if Data['preview_url'] != None:
                        Links += str(PreviewIcon)+" Song: [Preview]("+Data['preview_url']+")\n"
                    Links += str(AlbumIcon)+" Album: ["+Data['album']['name']+"]("+Data['album']['external_urls']['spotify']+")"
                    
                    #** Format New Embed And Sent It Into Discord **
                    BaseEmbed.set_thumbnail(url=Recommendations[CurrentPage]['album']['images'][0]['url'])
                    BaseEmbed.clear_fields()
                    BaseEmbed.add_field(name="Song "+str(CurrentPage+1)+":", value=Song, inline=False)
                    BaseEmbed.add_field(name="Links:", value=Links, inline=False)
                    BaseEmbed.set_footer(text="("+str(CurrentPage+1)+"/10) React To See More Recommendations!")
                    await Page.edit(embed=BaseEmbed)
                    
    #** Let User Know If They've Not Connected Their Spotify **
    else:
        Temp = await ctx.send("**Spotify Not Connected!**\nTo run this command, first run `!link`")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()


@client.command()
async def search(ctx, *args):
    
    Query = " ".join(args[:])
    Tube = Youtube()
    Results = Tube.Search(Query)
    
    
    Tube.GetVideoInfo(list(Results.keys())[0])

#!--------------------------------DISCORD LOOP-----------------------------------# 

#** Connecting To Discord **    
print("--------------------CONNECTING TO DISCORD--------------------")
client.run(os.environ["MUSICA_TOKEN"])