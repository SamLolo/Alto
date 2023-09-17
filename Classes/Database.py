
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import logging
from datetime import datetime
from mysql.connector import pooling, errors
from Classes.Server import UserPermissions


#!--------------------------------DATABASE OPERATIONS-----------------------------------#


class Database():
    
    def __init__(self, config: dict, pool: str = "main", size: int = 5):
        
        # Setup database logger
        self.logger = logging.getLogger("database")
            
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
        cursor.execute(f"SELECT * FROM recommendations WHERE DiscordID = '{id}';")
        recommendations = cursor.fetchone()
        connection.close()
        self.logger.debug("Connection returned to pool!")

        # Format user data if row was found
        if user is not None:
            data = {"songs": user[1],
                    "history": user[3],
                    "public": bool(user[4]),
                    "created": user[2]}
        else:
            return None  
        
        # Add recommendations data if available and return found info
        if recommendations is not None:
            data["recommendations"] = {"songcount": recommendations[1],
                                       "acousticness": recommendations[2],
                                       "danceability": recommendations[3],
                                       "duration_ms": recommendations[4],
                                       "energy": recommendations[5],
                                       "instrumentalness": recommendations[6],
                                       "key": recommendations[7],
                                       "mode": recommendations[8],
                                       "popularity": recommendations[9],
                                       "liveness": recommendations[10],
                                       "loudness": recommendations[11],
                                       "speechiness": recommendations[12],
                                       "tempo": recommendations[13],
                                       "time_signature": recommendations[14],
                                       "valence": recommendations[15]}
        else:
            data['recommendations'] = None
        return data
        
    
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

    
    def saveRecommendations(self, id: int, recommendations: dict):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to save recommendations data for '{id}' due to missing database connection!")
            raise ConnectionError(f"Failed to save recommendations data for '{id}' due to missing database connection!")
    
        # write user recommendation data to recommendations table (update if already exists)
        data = (id, recommendations['songcount'], recommendations['acousticness'], recommendations['danceability'], recommendations['duration_ms'], recommendations['energy'], 
                recommendations['instrumentalness'], recommendations['key'], recommendations['mode'], recommendations['popularity'], recommendations['liveness'],
                recommendations['loudness'], recommendations['speechiness'], recommendations['tempo'], recommendations['time_signature'], recommendations['valence'])
        cursor.execute("REPLACE INTO recommendations VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", data)
        
        # Commit changes and return connection to pool
        connection.commit()
        connection.close()
        self.logger.debug(f"Saved recommendations data for user '{id}'!")
        self.logger.debug("Connection returned to pool!")
            

    def getHistory(self, discordID: int):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to get history for user '{discordID}' due to missing database connection!")
            raise ConnectionError(f"Failed to get history for user '{discordID}' due to missing database connection!")

        # Get listening history from database, ordered by most recent first
        sql = ("SELECT history.SongID, history.ListenedAt, cache.Source, cache.ID, cache.URL, cache.Name, cache.Artists, cache.ArtistID, cache.Popularity "
               "FROM history "
               "INNER JOIN cache ON history.SongID = cache.uid "
              f"WHERE DiscordID = '{discordID}' "
               "ORDER BY ListenedAt DESC;")
        cursor.execute(sql)
        result = cursor.fetchall()
        connection.close()
        self.logger.debug("Connection returned to pool!")

        # Create array of song objects with information just gained
        history = []
        for row in result:
            data = {"cacheID": int(row[0]),
                    "source": row[2],
                    "id": row[3],
                    "url": row[4],
                    "name": row[5],
                    "artists": row[6].replace("'", "").split(", "),
                    "listenedAt": row[1]}
            if data["source"] == "spotify":
                data['artistID'] = row[7].replace("'", "").split(", ")
                data['popularity'] = row[8]
            history.append(data)
        self.logger.debug(f"Successfully fetched song history for user '{discordID}'!")
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
                    data = (discordID, history[i]['cacheID'], history[i]["listenedAt"])
                    cursor.execute("REPLACE INTO history (DiscordID, SongID, ListenedAt) VALUES (%s, %s, %s);", data)
            
            # Add all songs if deletedRows is 0 incase user has no cached history 
            else:
                for track in history:
                    data = (discordID, track['cacheID'], track["listenedAt"])
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


    def cacheSong(self, info: dict):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to cache song with {info['source']} ID '{info['id']}' due to missing database connection!")
            raise ConnectionError(f"Failed to cache song with {info['source']} ID '{info['id']}' due to missing database connection!")
        
        # Reformat python lists into strings
        if type(info['artists']) is list:
            info['artists'] = ", ".join(info['artists'])
        if 'artistID' in info.keys():
            info['artistID'] = ", ".join(info['artistID'])
        if 'colour' in info.keys() and info['colour'] is not None:
            info['colour'] = ", ".join(info['colour'])
            
        # Replace N/A with None
        if 'explicit' in info.keys() and info['explicit'] == "N/A":
            info['explicit'] = None

        # Prepare sql and values for inserting given information into database
        if info['source'] == "spotify":
            sql = "INSERT INTO cache (Source, ID, URL, Name, Artists, Duration, Track, ArtistID, Album, AlbumID, Art, Colour, `Release`, Popularity, Explicit, Preview) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            values = (info['source'], info['id'], info['url'], info['name'], info['artists'], info['duration'], info['track'], info['artistID'], info['album'], info['albumID'], info['art'], info['colour'], info['release'], info['popularity'], info['explicit'], info['preview'])
        elif info['source'] == "soundcloud":
            sql = "INSERT INTO cache (Source, ID, URL, Name, Artists, Duration, Track) VALUES (%s, %s, %s, %s, %s, %s, %s);"
            values = (info['source'], info['id'], info['url'], info['name'], info['artists'], info['duration'], info['track'])
        else:
            self.logger.warning(f"Unknown source '{info['source']}' encountered whilst trying to cache song!")
            connection.close()
            self.logger.debug("Connection returned to pool!")
            return None   

        # Execute SQL query and return connection to available pool
        cursor.execute(sql, values)
        self.logger.debug(f"New insert into cache for {info['source']} ID: {info['id']}")
        connection.commit()
        
        # Get cache ID generated for information just inserted
        cursor.execute("SELECT LAST_INSERT_ID()")
        key = cursor.fetchone()[0]
        
        # Return connection to available pool
        connection.close()
        self.logger.debug("Connection returned to pool!")
        return key


    def searchCache(self, query: str):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to search cache with query '{query}' due to missing database connection!")
            raise ConnectionError(f"Failed to search cache with query '{query}' due to missing database connection!")

        # Query cache table and return connection to available pool
        cursor.execute(f"SELECT * FROM cache WHERE (ID = '{query}') OR (URL = '{query}');")
        result = cursor.fetchone()
        connection.close()
        self.logger.debug("Connection returned to pool!")

        # Check if any results were found
        if result is None:
            return None
            
        # Format base data (for all source types) into a dictionary 
        data = {"cacheID": int(result[0]),
                "source": result[1],
                "id": result[2],
                "url": result[3],
                "name": result[4],
                "artists": result[5].replace("'", "").split(", "),
                "duration": result[6],
                "track": result[7],
                "updated": result[17]}
        
        # If source is spotify, add aditional track metadata
        if data['source'] == "spotify":
            data.update({"artistID": result[8].replace("'", "").split(", "),
                         "album": result[9],
                         "albumID": result[10],
                         "art": result[11],
                         "release": result[13],
                         "popularity": result[14],
                         "explicit": result[15],
                         "preview": result[16]})
            if result[12] is not None:
                data["colour"] = tuple(result[12])
            else:
                data["colour"] = None
        return data
    
    
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