
#!-------------------------IMPORT MODULES-----------------------!#


import random
import discord
import logging
from datetime import datetime
from discord.ext import commands


#!------------------------SONG HISTORY QUEUE-----------------------!#


class SongHistory(object):
    
    def __init__(self, discordID: int):
        super(SongHistory, self).__init__()

        # Fetch current song history from database
        try:
            self.history = self.client.database.getHistory(discordID)
        except ConnectionError as e:
            self.logger.info(f"Can't load song history for '{discordID}' due to connection error!")
            raise RuntimeError(e.message)
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(f"Unknown exception encountered while loading song history for '{discordID}")
            raise RuntimeError(e.message)
        else:
            self.maxsize = 20
        

    def addSongHistory(self, data: dict):
        
        # If queue is full, clear song from history first
        if len(self.history) == self.maxsize:
            self.clearSong()
        
        # If spotify track, average new song data into users recommendations figures
        if data['source'] == "spotify":
            try:
                features = self.client.music.GetAudioFeatures([data['id']])
            except Exception as e:
                self.logger.warning("Unexpected error getting audio features whilst adding song history!")
                self.logger.exception(e)
            else:
                features = features[0]
                songCount = self.metadata['recommendations']['songcount']
                
                # Create average using new track data with previous average (popularity must remain an integer)
                for key, values in self.metadata['recommendations'].items():
                    if key == "songcount":
                        pass
                    elif key == "popularity" and data['popularity'] is not None:
                        values[1] = int(((values[1] * songCount) + data['popularity']) / (songCount + 1))
                        if values[1] >= 5:
                            values[0] = values[1] - 5
                        else:
                            values[0] = 0
                        if values[1] <= 95:
                            values[2] = values[1] + 5
                        else:
                            values[2] = 100
                    else:
                        newValue = ((values[1] * songCount) + features[key]) / (songCount + 1)
                    
                        # Add 1/10th of difference to get min/max values either side of average
                        delta = values[1] - newValue
                        
                        if values[0] + (delta / 10) >= 0 and values[0] + (delta / 10) <= values[1]:
                            values[0] = values[0] + (delta / 10)
                        elif values[0] + (delta / 10) > values[1]:
                            values[0] = values[1]
                        else:
                            values[0] = 0
                        
                        if values[2] + (delta / 10) <= 1 and values[2] + (delta / 10) >= values[1]:
                            values[2] = values[2] + (delta / 10)
                        elif values[2] + (delta / 10) < values[1]:
                            values[2] = values[1]
                        else:
                            values[2] = 1
                            
                        if newValue > values[2]:
                            values[1] = values[2]
                        elif newValue < values[0]:
                            values[1] = values[0]
                        else:
                            values[1] = newValue
                    
                    # Save new values & increment songCount for recommendations only
                    self.metadata['recommendations'][key] = values
                self.metadata['recommendations']['songcount'] += 1
                self.cached['recommendations'] = False
            
        # Add new song data to history array
        self.history.insert(0, data)
        self.logger.debug(f"Song added to history for user '{self.user.id}'!")
        self.metadata['songs'] += 1
        self.cached['user'] = False
        self.cached['history'] = False
        

    def clearSong(self):
        
        # Check if queue is empty and return none if true
        if not(len(self.history) == 0):
            
            # Remove oldest song in queue and return data of song just removed
            data = self.history.pop(-1)
            self.logger.debug(f"Song removed from history for user '{self.user.id}'!")
            return data
        else:
            self.logger.warning(f"Attempted to remove history from empty queue! (User: {self.user.id})")
            return None
        

#!-------------------------USER OBJECT------------------------!#


class User(SongHistory):
    
    def __init__(self, client: commands.Bot, id: int = None, user: discord.User = None):
        
        # Setup user attributes and initialise user listening history
        self.client = client
        self.logger = logging.getLogger("discord.user")
        self.logger.debug(f"New user object created for ID: {id}")
        
        # Get Discord user object if one isn't passed through
        if user is None:
            self.user = self.client.get_user(id)
        else:
            self.user = user
        if self.user is None:
            raise RuntimeError(f"Couldn't find user with ID: {id}")
            
        # Check to see if user has stored information, otherwise create new profile
        try:
            self.metadata = self.client.database.getUser(id)
        except ConnectionError as e:
            self.logger.info(f"Can't load user data for '{self.user.id}' due to connection error!")
            raise RuntimeError(e.message)
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(f"Unknown exception encountered while loading user data for '{self.user.id}")
            raise RuntimeError(e.message)
        else:
            if self.metadata is None:
                self.metadata = {"songs": 0,
                                 "history": 2,
                                 "public": True,
                                 "created": datetime.now(),
                                 "recommendations": {"songcount": 0,
                                                     "popularity": [0, 50, 100],
                                                     "acousticness": [0.0, 0.223396, 1.0],
                                                     "danceability": [0.0, 0.684500, 1.0],
                                                     "energy": [0.0, 0.644640, 1.0],
                                                     "instrumentalness": [0, 0.001568, 1.0],
                                                     "liveness": [0.0, 0.163196, 1.0],
                                                     "loudness": [-15.0, -6.250840, 0.0],
                                                     "speechiness": [0.0, 0.106186, 1.0],
                                                     "valence": [0.0, 0.521244, 1.0]}}
            
            # Load song history for user
            super(User, self).__init__(self.user.id)
                
            # Set flags to check if user data has been changed since initialization
            self.cached = {"user": True,
                           "recommendations": True,
                           "history": True}


    def save(self): 
        # Update database tables if data has been changed when using user object
        try:
            if len(self.history) > 0 and not(self.cached['history']):
                self.client.database.saveHistory(self.user.id, self.history)
            
            if not(self.cached['user']):
                self.client.database.saveUser(self.user.id, self.metadata)

            if not(self.cached['recommendations']):
                self.client.database.saveRecommendations(self.user.id, self.metadata['recommendations'])
        except:
            self.logger.warning(f"User data not saved for id: {self.user.id}!")

    
    def getRecommendations(self):

        # Create array of all spotify track ids within listening history
        trackIDs = []
        for track in self.history:
            if track['source'] == "spotify":
                trackIDs.append(track['id'])

        # Select 3 random track IDs from array
        while len(trackIDs) > 3:
            trackIDs.pop(random.randint(0, len(trackIDs)-1))

        # Create json to send to Spotify API recommendations endpoint
        print(self.metadata)
        figures = self.metadata['recommendations']
        data = {'limit': 50, 'seed_tracks': ",".join(trackIDs),
                'min_acousticness': figures['acousticness'][0], 'target_acousticness': figures['acousticness'][1], 'max_acousticness': figures['acousticness'][2], 
                'min_danceability': figures['danceability'][0], 'target_danceability': figures['danceability'][1], 'max_danceability': figures['danceability'][2], 
                'min_energy': figures['energy'][0], 'target_energy': figures['energy'][1], 'max_energy': figures['energy'][2], 
                'min_instrumentalness': figures['instrumentalness'][0], 'target_instrumentalness': figures['instrumentalness'][1], 'max_instrumentalness': figures['instrumentalness'][2], 
                'min_liveness': figures['liveness'][0], 'target_liveness': figures['liveness'][1], 'max_liveness': figures['liveness'][2], 
                'min_loudness': figures['loudness'][0], 'target_loudness': figures['loudness'][1], 'max_loudness': figures['loudness'][2],
                'min_speechiness': figures['speechiness'][0], 'target_speechiness': figures['speechiness'][1], 'max_speechiness': figures['speechiness'][2], 
                'min_valence': figures['valence'][0], 'target_valence': figures['valence'][1], 'max_valence': figures['valence'][2],
                'min_popularity': figures['popularity'][0], 'target_popularity': figures['popularity'][1], 'max_popularity': figures['popularity'][2]}
        
        # Return none if no tracks available else return list of tracks
        try:
            tracks = self.client.music.GetRecommendations(data)
        except Exception as e:
            self.logger.warning(f"Unexpected error getting recommendations for user: {self.user.id}!")
            self.logger.exception(e)
            raise RuntimeError(e.message)
        else:
            return tracks