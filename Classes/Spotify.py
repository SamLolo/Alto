
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import base64
import requests
from time import sleep
from datetime import datetime


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
        SongData = {Song['id']: {'Name': Song['name'], 'Artists': Artists, 'ArtistID': ArtistID, 'Album': Song['album']['name'], 'AlbumID': Song['album']['id'], 'Art': Song['album']['images'][0]['url'], 'Release': Date, 'Popularity': Song['popularity'], 'Explicit': Song['explicit'], 'Preview': Song['preview_url']}}
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

            #** Get Formatted Song Data **
            SongInfo = self.FormatSongData(Result['items'][0])
            
            #** Return Dictionary Of Song Information **
            return SongInfo
        
        #** Return "SongNotFound" if Request Body Is Empty (Shouldn't Happen) **
        else:
            return "SongNotFound"
        
