
#!-------------------------IMPORT MODULES-----------------------!#


import random
from datetime import datetime
from discord.ext import commands


#!------------------------SONG HISTORY QUEUE-----------------------!#


class SongHistory(object):
    
    def __init__(self, discordID: int):
        super(SongHistory, self).__init__()

        # Fetch current song history from database
        self.history = self.client.database.getHistory(discordID)
        self.maxsize = 20
        

    def addSongHistory(self, data: dict):
        
        # If queue is full, clear song from history first
        if len(self.history) < self.maxsize:
            self.clearSong()
            
        # Add new song data to history array
        self.history.insert(0, data)
        self.client.logger.debug(f"Song added to history for user '{self.discord}'!")
        

    def clearSong(self):
        
        # Check if queue is empty and return none if true
        if not(len(self.history) == 0):
            
            # Remove oldest song in queue and return data of song just removed
            data = self.history.pop(-1)
            self.client.logger.debug(f"Song removed from history for user '{self.discord}'!")
            return data
        else:
            self.client.logger.warning(f"Attempted to remove history from empty queue! (User: {self.discord})")
            return None
        

#!-------------------------USER OBJECT------------------------!#


class User(SongHistory):
    
    def __init__(self, client: commands.Bot, discordID: int):
        
        #** Setup Discord Client object & Instantiate Music & Database Modules **
        self.client = client
        self.discord = discordID

        #** Initialise Listening History Classe **
        super(User, self).__init__(discordID)
        
        #** Get User Dictionary **
        self.user = self.client.database.GetUser(discordID)
        if self.user == None:
            discordUser = self.client.get_user(discordID)
            self.user = {"data": {"discordID": int(discordUser.id),
                                  "name": discordUser.name,
                                  "discriminator": discordUser.discriminator,
                                  "avatar": str(discordUser.default_avatar.url),
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
        self.client.database.saveHistory(self.user['data']['discordID'], self.History, self.outpointer)
        #self.client.database.SaveUserDetails(self.user)
        
    
    async def incrementHistory(self, TrackData):
        
        #** If Queue Is Currently Full, Clear Oldest Song From Queue **
        if len(self.history) < self.maxsize:
            OldSong = self.clearSong()
            
            #** Check If OldSong Has A Spotify ID & Get Audio Features **
            if OldSong['spotifyID'] != None:
                try:
                    Features = self.client.music.GetAudioFeatures(OldSong['spotifyID'])
                except:
                    pass
                else:
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
        self.addSongHistory(TrackData)

    
    def getRecommendations(self):

        #** Create Lists Of Listened To Spotify Track ID's And Artists From Listening History **
        TrackIDs = []
        for i in range(len(self.array)):
            if self.history[i]['SpotifyID'] is not None:
                TrackIDs.append(self.history[i]['SpotifyID'])

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
        try:
            Tracks = self.client.music.GetRecommendations(data)
        except:
            return None
        return Tracks