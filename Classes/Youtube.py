
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import requests
from datetime import datetime


#!---------------------------------YOUTUBE---------------------------------------#


class YoutubeAPI():
    
    def __init__(self):

        #** Create Class Objects For Requests **
        self.Key = os.environ["GOOGLE_KEY"]
        self.Header = {'Accept': 'application/json'}
        
    
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
                SearchDict.update({Result['id']['videoId']: {'Tittle': Result['snippet']['title'],
                                                             'Description': Result['snippet']['description'],
                                                             'Channel': Result['snippet']['channelTitle'], 
                                                             'ChannelID': Result['snippet']['channelId'],
                                                             'Thumbnail': Result['snippet']['thumbnails']['default']['url'],
                                                             'PublishDate': Result['snippet']['publishedAt']}})

        #** Returned Filled Dictionary With Search Results **      
        return SearchDict
    
    
    def GetVideoInfo(self, VideoID):
        
        #** Request Info About Video ID From Youtube API **
        Data = {'part': 'player,contentDetails,topicDetails,statistics', 'id': VideoID, 'key': self.Key}
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

        #** Fill Necessary Data Into A Dictionary Ready To Be Returned **
        SongData = {Info['id']: {'Duration': {'Hours': Hours, 'Minutes': Minutes, 'Seconds': Seconds},
                                            'Player': PlayerURL,
                                            'Music': Topic,
                                            'Views': Info['statistics']['viewCount'],
                                            'Likes': Info['statistics']['likeCount'],
                                            'Dislikes': Info['statistics']['dislikeCount']}}
        
        #** Return Filled SongData Dictionary **
        return SongData
