
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
                songCount = self.recommendations['songcount']
                
                # Create average using new track data with previous average
                for key, value in self.recommendations.items():
                    if key == "songcount":
                        pass
                    elif songCount == 0:
                        newValue = features[key]
                    else:
                        newValue = ((value * songCount) + features[key]) / (songCount + 1)
                    
                    # Save new values & increment songCount for recommendations only
                    self.recommendations[key] = newValue
                self.recommendations['songcount'] += 1
                self.cached['recommendations'] = False
            
        # Add new song data to history array
        self.history.insert(0, data)
        self.logger.debug(f"Song added to history for user '{self.user.id}'!")
        self.songs += 1
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
            data = self.client.database.getUser(id)
        except ConnectionError as e:
            self.logger.info(f"Can't load user data for '{self.user.id}' due to connection error!")
            raise RuntimeError(e.message)
        except Exception as e:
            self.logger.exception(e)
            self.logger.error(f"Unknown exception encountered while loading user data for '{self.user.id}")
            raise RuntimeError(e.message)
        else:
            
            # Add cached data as class attributes or fill in default data if new account
            if data is None:
                self.songs = 0
                self.history_mode = 2
                self.public = True
                self.created = datetime.now()
            else:
                self.songs = data['songs']
                self.history_mode = data['history']
                self.public = data['public']
                self.created = data['created']
                
                # Add recommendations data if present, else create default dictionary ready for use
                if data['recommendations'] is not None:
                    self.recommendations = data['recommendations']
                else:
                    self.recommendations = {"songcount": 0,
                                            "acousticness": 0,
                                            "danceability": 0,
                                            "duration_ms": 0,
                                            "energy": 0,
                                            "instrumentalness": 0,
                                            "key": 0,
                                            "mode": 0,
                                            "popularity": 0,
                                            "liveness": 0,
                                            "loudness": 0,
                                            "speechiness": 0,
                                            "tempo": 0,
                                            "time_signature": 0,
                                            "valence": 0}
            
            # Load song history for user
            super(User, self).__init__(self.user.id)
                
            # Set flags to check if user data has been changed since initialization
            self.cached = {"user": True if data is not None else False,
                           "recommendations": True,
                           "history": True}


    def save(self): 
        # Update database tables if data has been changed when using user object
        try:
            if len(self.history) > 0 and not(self.cached['history']):
                self.client.database.saveHistory(self.user.id, self.history)
            
            if not(self.cached['user']):
                self.client.database.saveUser(self.user.id, self.songs, self.history_mode, self.public, self.created)

            if self.recommendations['songcount'] > 0 and not(self.cached['recommendations']):
                self.client.database.saveRecommendations(self.user.id, self.recommendations)
        except:
            self.logger.warning(f"User data not saved for id: {self.user.id}!")

    
    def getRecommendations(self):

        # Create a dictionary recording how often each track and artist appears
        tracks = {}
        artists = {}
        for track in self.history:
            if track['source'] == "spotify":
                tracks[track['id']] += 1
                for artist in track['artistID']:
                    artists[artist] += 1
                    
        # Sort top tracks and select 3 most listened to (randomly choicing if multiple tracks have the same listening count)
        top_tracks = []
        temp = []
        last_count = 999999999999999999999999999
        for id, count in sorted(tracks.items(), key=lambda item: item[1]):
            if count > last_count and temp != []:
                if len(temp) + len(top_tracks) == 3:
                    top_tracks += temp
                    break
                elif len(temp) + len(top_tracks) < 3:
                    top_tracks += temp
                else:
                    top_tracks += random.choices(temp, k = 3-len(top_tracks))
                    break
            last_count = count
            temp.append(id)
        
        # Repeat above to get top 2 artists
        top_artists = []
        temp = []
        last_count = 999999999999999999999999999
        for id, count in sorted(artists.items(), key=lambda item: item[1]):
            if count > last_count and temp != []:
                if len(temp) + len(top_artists) == 2:
                    top_artists += temp
                    break
                elif len(temp) + len(top_artists) < 2:
                    top_artists += temp
                else:
                    top_artists += random.choices(temp, k = 2-len(top_artists))
                    break
            last_count = count
            temp.append(id)

        # Create json to send to Spotify API recommendations endpoint
        data = {'limit': 100, 'seed_tracks': ",".join(top_tracks), 'seed_artists': ",".join(top_artists),
                'target_acousticness': self.recommendations['acousticness'], 
                'target_danceability': self.recommendations['danceability'],
                'target_duration_ms': int(self.recommendations['duration_ms']),
                'target_energy': self.recommendations['energy'],
                'target_instrumentalness': self.recommendations['instrumentalness'],
                'target_key': int(self.recommendations['key']) + (0 if self.recommendations['key'] % 1 < 0.5 else 1),
                'target_liveness': self.recommendations['liveness'],
                'target_loudness': self.recommendations['loudness'],
                'target_mode': 0 if self.recommendations['key'] < 0.5 else 1,
                'target_popularity': int(self.recommendations['popularity']) + (0 if self.recommendations['popularity'] % 1 < 0.5 else 1),
                'target_speechiness': self.recommendations['speechiness'],
                'target_tempo': self.recommendations['tempo'],
                'target_time_signature': int(self.recommendations['time_signature']) + (0 if self.recommendations['time_signature'] % 1 < 0.5 else 1),
                'target_valence': self.recommendations['valence']}
        
        # Return none if no tracks available else return list of tracks
        try:
            tracks = self.client.music.GetRecommendations(data)
        except Exception as e:
            self.logger.warning(f"Unexpected error getting recommendations for user: {self.user.id}!")
            self.logger.exception(e)
            raise RuntimeError(e.message)
        else:
            return tracks