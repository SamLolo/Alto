
#!-------------------------IMPORT MODULES-----------------------!#


import random
import discord
import logging
from datetime import datetime
from discord.ext import commands
        

#!-------------------------USER OBJECT------------------------!#


class User():
    
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
            data = self.client.database.getUser(self.user.id)
        except Exception as e:
            if type(e) != ConnectionError:
                self.logger.exception(e)
                self.logger.error(f"Unknown exception encountered while loading user data for '{self.user.id}")
            raise RuntimeError(e.message)
            
        # Add cached data as class attributes or fill in default data if new account
        self.deafened = None
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
            
        # Load song history for user
        try:
            self.history = self.client.database.getHistory(self.user.id)
        except Exception as e:
            if type(e) != ConnectionError:
                self.logger.exception(e)
                self.logger.error(f"Unknown exception encountered while loading song history for '{self.user.id}")
            raise RuntimeError(e.message)
        self.MAX_HISTORY = 20
            
        # Set flags to check if user data has been changed since initialization
        self.cached = {"user": True if data is not None else False,
                       "history": True}


    def save(self): 
        # Update database tables if data has been changed when using user object
        try:
            if len(self.history) > 0 and not(self.cached['history']):
                self.client.database.saveHistory(self.user.id, self.history)
            if not(self.cached['user']):
                self.client.database.saveUser(self.user.id, self.songs, self.history_mode, self.public, self.created)
        except:
            self.logger.warning(f"User data not saved for id: {self.user.id}!")
            
    
    def addSongHistory(self, entry: dict):
        # If queue is full, clear song from history first
        if len(self.history) == self.MAX_HISTORY:
            self.history.pop(-1)
        
        # Add track to history with current timestamp as time-listened
        self.history.insert(0, entry)
        self.logger.debug(f"Song added to history for user '{self.user.id}'!")
            
        # Update flags so data is cached upon next save
        self.songs += 1
        self.cached['user'] = False
        self.cached['history'] = False

    
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