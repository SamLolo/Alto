
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import logging
from lavalink import AudioTrack
from datetime import datetime
from lavalink.errors import LoadError
from mysql.connector import pooling, errors
from Classes.Server import UserPermissions
from Classes.Utils import Utility


#!--------------------------------DATABASE OPERATIONS-----------------------------------#


class Database():
    
    def __init__(self, config: dict, pool: str = "main", size: int = 5):
        
        # Setup database logger
        self.logger = logging.getLogger("database")
        self.utils = Utility()
            
        # Create connection pool for database
        host = config['database']['host']
        if host == "":
            host = os.getenv(config['environment']['database_host'], default=None)
            if host is None:
                self.logger.warning('"database.host" is not set in config or environment variables!')
        user = config['database']['username']
        if user == "":
            user = os.getenv(config['environment']['database_user'], default=None)
            if user is None:
                self.logger.warning('"database.user" is not set in config or environment variables!')
        try:
            self.logger.info(f"Attempting to create new database pool '{pool}' of size {size}")
            self.pool = pooling.MySQLConnectionPool(pool_name = pool,
                                                    pool_size = size,
                                                    host = host,
                                                    database = config['database']['schema'],
                                                    user = user,
                                                    password = os.environ[config['environment']['database_password']])
        except errors.DatabaseError as failure:
            self.logger.error(f"Database connection failed with error: {failure}")
            self.connected = False
            self.logger.critical("Database functionality unavailable!")
        except Exception as error:
            self.logger.exception(error)
            self.connected = False
            self.logger.critical("Database functionality unavailable!")
        else:
            self.connected = True
            self.logger.info("New database pool created!")
        
        # Use parameter to keep track of attempts to create new database connection from pool
        del user
        del host
        self.failures = 0
        self.max_attempts = config['database']['max_retries']
        

    def ensure_connection(self):
        
        # If pool exists, try to create a new database connection
        if self.connected:
            try:
                connection = self.pool.get_connection()
                self.logger.debug("New connection established!")
                cursor = connection.cursor(buffered=True)
                self.failures = 0
                return (connection, cursor)
            # If error occurs, record new failed attempt & take database offline if max attempts reached
            except Exception as e:
                self.logger.error("Failed to get new connection from pool!")
                self.logger.exception(e)
                if self.failures == self.max_attempts:
                    self.connected = False
                    self.logger.critical("Maximum connection attempts reached! Database functionality is now disabled!")
                self.failures += 1
                return (None, None)
        # If pool has failed, automatically return no connection
        else:
            return (None, None)


    def getUser(self, id: int):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to get user data for '{id}' due to missing database connection!")
            raise ConnectionError(f"Failed to get user data for '{id}' due to missing database connection!")

        # Fetch user data from database
        cursor.execute(f"SELECT * FROM users WHERE DiscordID = '{id}';")
        user = cursor.fetchone()
        connection.close()
        self.logger.debug("Connection returned to pool!")

        # Format user data if row was found
        if user is not None:
            data = {"songs": user[1],
                    "history": user[3],
                    "public": bool(user[4]),
                    "created": user[2]}
            return data
        else:
            return None  
        
    
    def saveUser(self, id: int, songs: int, history: int, public: bool, created: datetime):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to save user data for '{id}' due to missing database connection!")
            raise ConnectionError(f"Failed to save user data for '{id}' due to missing database connection!")

        # Write new data into users table, updating the row if it already exists
        data = (id, songs, created, history, public)
        cursor.execute("REPLACE INTO users VALUES (%s, %s, %s, %s, %s);", data)
        
        # Commit changes and return connection to pool
        connection.commit()
        connection.close()
        self.logger.debug(f"Saved user data for user '{id}'")
        self.logger.debug("Connection returned to pool!")
            

    def getHistory(self, discordID: int):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to get history for user '{discordID}' due to missing database connection!")
            raise ConnectionError(f"Failed to get history for user '{discordID}' due to missing database connection!")

        # Get listening history from database, ordered by most recent first
        sql = f"""SELECT SongID, ListenedAt
                  FROM history 
                  WHERE DiscordID = '{discordID}'
                  ORDER BY ListenedAt DESC;"""
        cursor.execute(sql)
        result = cursor.fetchall()

        # Create array of song objects with information just gained
        history = []
        for row in result:
            track = self.searchCache(int(row[0]))
            if track is not None:
                history.append({"track": track,
                                "listenedAt": row[1]})
            else:
                self.logger.error(f"Unknown cache ID '{int(row[0])}' found when loading history for discordID '{discordID}'")
                cursor.execute(f"DELETE FROM history WHERE SongID = '{row[0]}';")

        # Return connection to pool once all history has been loaded and verified
        self.logger.debug(f"Successfully fetched song history for user '{discordID}'!")
        connection.close()
        self.logger.debug("Connection returned to pool!")
        return history
    
    
    def saveHistory(self, discordID: int, history: dict):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to save history for user '{discordID}' due to missing database connection!")
            raise ConnectionError(f"Failed to save history for user '{discordID}' due to missing database connection!")

        # Delete all rows in history that are older than oldest song in history & get number of rows just deleted
        oldest = history[-1]["listenedAt"]
        cursor.execute(f"DELETE FROM history WHERE ListenedAt < '{oldest}';")
        cursor.execute("SELECT ROW_COUNT();")
        deletedRows = cursor.fetchone()
        if deletedRows is not None:
            deletedRows = deletedRows[0]
    
            # Add new songs in history to database, based on number deleted above
            if deletedRows > 0:
                for i in range(deletedRows):
                    data = (discordID, history[i]['track']['extra']['metadata']['cacheID'], history[i]["listenedAt"])
                    cursor.execute("REPLACE INTO history (DiscordID, SongID, ListenedAt) VALUES (%s, %s, %s);", data)
            
            # Add all songs if deletedRows is 0 incase user has no cached history 
            else:
                for entry in history:
                    data = (discordID, entry['track']['extra']['metadata']['cacheID'], entry["listenedAt"])
                    cursor.execute("REPLACE INTO history (DiscordID, SongID, ListenedAt) VALUES (%s, %s, %s);", data)
                
        # Commit changes and return connection
        connection.commit()
        connection.close()
        self.logger.debug(f"Saved history for user '{discordID}'!")
        self.logger.debug("Connection returned to pool!")


    def removeData(self, discordID: int, tables: list):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to delete tables '{', '.join(tables)}' for discordID '{discordID}' due to missing database connection!")
            raise ConnectionError(f"Failed to delete tables '{', '.join(tables)}' for discordID '{discordID}' due to missing database connection!")

        # Remove user entry from each table and return database connection to pool
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE DiscordID='{discordID}';")
            self.logger.debug(f"Table '{table}' deleted for user: {discordID}!")
        connection.commit()
        connection.close()
        self.logger.debug("Connection returned to pool!")


    def cacheSong(self, track: AudioTrack):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to cache song with {track.source_name} ID '{track.identifier}' due to missing database connection!")
            raise ConnectionError(f"Failed to cache song with {track.source_name} ID '{track.identifier}' due to missing database connection!")
        
        # Insert into cache table the main track info
        cache = "INSERT INTO cache (source, ID, url, name, author, duration, track, albumID, art, colour) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        cache_values = (track.source_name, track.identifier, track.uri, track.title, track.author, track.duration, track.track, track.extra['album']['id'] if 'album' in track.extra.keys() else None, track.artwork_url, ", ".join(track.extra['metadata']['colour']) if 'metadata' in track.extra.keys() else self.utils.get_colour(track.artwork_url))
        cursor.execute(cache, cache_values)
        
        # Insert artists if more than one available (author is cached in main table)
        if 'metadata' in track.extra.keys():
            for artist in track.extra['metadata']['artists']:
                cursor.execute("INSERT INTO artists (name, identifier, trackID) VALUES (%s, %s, %s);", (artist['name'], artist['id'], track.identifier))

        # Insert spotify information if it's available
        if track.source_name == "spotify":
            spotify = "INSERT INTO spotify (spotifyID, release, popularity, explicit, preview) VALUES (%s, %s, %s, %s, %s)"
            spotify_values = (track.identifier, track.extra['metadata']['release'], track.extra['metadata']['popularity'], track.extra['metadata']['explicit'], track.extra['metadata']['preview'])
            cursor.execute(spotify, spotify_values)
            
            features = "INSERT INTO features (spotifyID, acousticness, danceability, duration_ms, energy, instrumentalness, key, liveness, loudness, mode, speechiness, tempo, time_signature, valence) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            features_values = (track.identifier, track.extra['features']['acousticness'], track.extra['features']['danceability'], track.extra['features']['duration_ms'], track.extra['features']['energy'], track.extra['features']['instrumentalness'], track.extra['features']['key'], 
                               track.extra['features']['liveness'], track.extra['features']['loudness'], track.extra['features']['mode'], track.extra['features']['speechiness'], track.extra['features']['tempo'], track.extra['features']['time_signature'], track.extra['features']['valence'])
            cursor.execute(features, features_values)
            
            album = "INSERT INTO album (id, name, type, image, release, length) VALUES (%s, %s, %s, %s, %s, %s);"
            album_values = tuple(track.extra['album'].values())
            cursor.execute(album, album_values)
        
        # Get cache ID generated for information just inserted
        self.logger.debug(f"New insert into cache for {track.source_name} ID: {track.identifier}")
        connection.commit()
        cursor.execute("SELECT LAST_INSERT_ID()")
        uid = cursor.fetchone()[0]
        
        # Return connection to available pool
        connection.close()
        self.logger.debug("Connection returned to pool!")
        return uid


    def searchCache(self, query: str = None, uid: int = None):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to search cache with query '{query}' due to missing database connection!")
            raise ConnectionError(f"Failed to search cache with query '{query}' due to missing database connection!")

        # Format sql query in cache table for track metadata
        sql = f"""SELECT cache.*, spotify.release, spotify.popularity, spotify.explicit, spotify.preview, album.name, album.type, album.image, album.release, album.length
                  features.acousticness, features.danceability, features.duration_ms, features.energy, features.instrumentalness, features.key, features.liveness,
                  features.loudness, features.mode, features.speechiness, features.tempo, features.time_signature, features.valence
                  FROM cache
                  INNER JOIN spotify ON spotify.spotifyID = cache.ID
                  INNER JOIN album ON album.id = cache.albumID
                  INNER JOIN features ON features.spotifyID = cache.ID"""
        if query is not None:    
            sql += f"WHERE (cache.ID = '{query}') OR (cache.url = '{query}');"
        else:
            sql += f"WHERE cache.uid = '{uid}';"

        # Get results for database
        cursor.execute(sql)
        result = cursor.fetchone()
        if result is None or result == ():
            self.logger.warning(f"Failed to find results for query '{query}' or with cacheID '{uid}'!")
            return None
        
        # Get all artists features on track seperately
        cursor.execute(f"""SELECT *
                           FROM artists
                           WHERE trackID = {result[2]}""")
        artists = cursor.fetchall()
        
        # Return connection to available pool
        connection.close()
        self.logger.debug("Connection returned to pool!")
        
        # If track has spotify data, add appropiate metadata
        if result[1] == "spotify":
            track = AudioTrack({'track': result[7],
                                'identifier': result[2],  
                                'isSeekable': True,
                                'author': result[5],
                                'length': result[6],
                                'isStream': False,
                                'title': result[4],
                                'uri': result[3],
                                'artworkUrl': result[9],
                                'sourceName': 'spotify'},
                                requester = 0,
                                metadata={
                                    "cacheID": int(result[0]),
                                    "artists": [{"id": artist[2], "name": artist[1]} for artist in artists],
                                    "colour": tuple(result[10]) if result[10] is not None else None,
                                    "release": result[12],
                                    "popularity": result[13],
                                    "explcit": result[14],
                                    "preview": result[15]
                                },
                                features={
                                    "acoustiness": result[21],
                                    "danceabilty": result[22],
                                    "duration_ms": result[23],
                                    "energy": result[24],
                                    "instrumentalness": result[25],
                                    "key": result[26],
                                    "liveness": result[27],
                                    "loudness": result[28],
                                    "mode": result[29],
                                    "speechiness": result[30],
                                    "tempo": result[31],
                                    "time_signature": result[32],
                                    "valence": result[33]
                                },
                                album={
                                    "id": result[8],
                                    "name": result[16],
                                    "type": result[17],
                                    "art": result[18],
                                    "release": result[19],
                                    "length": result[20]
                                })
        
        # If cached track is any other type except spotify
        else:
            track = AudioTrack({'track': result[7],
                                'identifier': result[2],  
                                'isSeekable': True,
                                'author': result[5],
                                'length': result[6],
                                'isStream': False,
                                'title': result[4],
                                'uri': result[3],
                                'artworkUrl': result[9],
                                'sourceName': result[1]},
                                requester = 0,
                                metadata = {
                                    "cacheID": int(result[0]),
                                    "artists": [{"id": artist[2], "name": artist[1]} for artist in artists],
                                    "colour": tuple(result[10]) if result[10] is not None else None
                                })
            
        # Return resulting <AudioTrack> object
        return track
    
    
    def saveServer(self, id: int, volume: dict, voice: list, channels: list, queue: bool, permissions: dict):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to save server with id '{id}' due to missing database connection!")
            raise ConnectionError(f"Failed to save server with id '{id}' due to missing database connection!")
        
        # Replace current server settings in database
        sql = f"REPLACE INTO servers (id, Default Volume, Last Volume, Save Queue, Voice Channels, Text Channels, Play, Volume, Skip, Edit Queue, Seek) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        values = (id, volume['default'], volume['previous'], queue, voice, channels)
        for i in range(1, 6):
            if UserPermissions(i) in permissions['default']:
                values.append(True)
            else:
                values.append(False)
        cursor.execute(sql, values)
        self.logger.debug(f"Saved server settings for guild id '{id}'")
        
        # Save list of dj roles and users for server
        for user, perms in permissions['users'].items():
            sql = f"REPLACE INTO permissions (id, Type, Server, Play, Volume, Skip, Edit Queue, Seek) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
            values = (user, "user", id)
            if UserPermissions(i) in perms:
                values.append(True)
            else:
                values.append(False)
            cursor.execute(sql, values)
        for role, perms in permissions['roles'].items():
            sql = f"REPLACE INTO permissions (id, Type, Server, Play, Volume, Skip, Edit Queue, Seek) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
            values = (role, "role", id)
            if UserPermissions(i) in perms:
                values.append(True)
            else:
                values.append(False)
            cursor.execute(sql, values)
        self.logger.debug(f"Saved permissions for guild id '{id}'")
        
        # Commit changes and return connection to pool
        connection.commit()
        connection.close()
        self.logger.debug("Connection returned to pool!")
        
        
    def loadServer(self, id: int):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to get server settings for id '{id}' due to missing database connection!")
            raise ConnectionError(f"Failed to get server settings for id '{id}' due to missing database connection!")
        
        # Get settings for server table
        cursor.execute(f"SELECT * FROM servers WHERE id = '{id}';")
        result = cursor.fetchone()
        
        # Format result into dictionary if row found
        if result is not None:
            data = {"volume": {
                        "default": result[1],
                        "previous": result[2]
                    },
                    "voice": json.loads(result[4]),
                    "channels": json.loads(result[5]),
                    "queue": bool(result[3]),
                    "permissions": {
                        "default": [UserPermissions(x) for x, value in enumerate(result[6:], start=1) if value == 1],
                        "users": {},
                        "roles": {}
                    }}
        else:
            return None
        
        # Load DJ roles and users from dj table
        cursor.execute(f"SELECT * FROM permissions WHERE Server = '{id}';")
        results = cursor.fetchall()
        for result in results:
            if result[1] == "user":
                data['permissions']['users'][result[0]] = [UserPermissions(x) for x, value in enumerate(result[3:], start=1) if value == 1]
            elif result[1] == "role":
                data['permissions']['roles'][result[0]] = [UserPermissions(x) for x, value in enumerate(result[3:], start=1) if value == 1]
            else:
                self.logger.warning(f"Result found in table 'permissions' with unknown type '{result[1]}'!")
        
        # Return connection to available pool
        print(data)
        connection.close()
        self.logger.debug("Connection returned to pool!")
        return data