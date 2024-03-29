
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import logging
from mysql.connector import pooling, errors


#!--------------------------------DATABASE OPERATIONS-----------------------------------#


class Database():
    
    def __init__(self, pool: str = "main", size: int = 5):
        
        # Setup database logger
        self.logger = logging.getLogger("database")
            
        # Create connection pool for database
        user = os.environ["DATABASE_USER"]
        password = os.environ["DATABASE_PASS"]
        try:
            self.logger.info(f"Attempting to create new database pool '{pool}' of size {size}")
            self.pool = pooling.MySQLConnectionPool(pool_name = pool,
                                                                    pool_size = size,
                                                                    host = "localhost",
                                                                    database = "alto",
                                                                    user = user,
                                                                    password = password)
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
        del password
        self.failures = 0
        self.max_attempts = 3
        

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
        cursor.execute(f"SELECT * FROM users INNER JOIN recommendations WHERE users.DiscordID = '{id}';")
        result = cursor.fetchone()
        connection.close()
        self.logger.debug("Connection returned to pool!")

        # Format user data if row was found
        if result is not None:
            data = {"songs": result[1],
                    "history": result[3],
                    "public": result[4],
                    "created": result[2],
                    "recommendations": {"songcount": result[6],
                                        "popularity": [result[7], result[8], result[9]],
                                        "acousticness": [result[10], result[11], result[12]],
                                        "danceability": [result[13], result[14], result[15]],
                                        "energy": [result[16], result[17], result[18]],
                                        "instrumentalness": [result[19], result[20], result[21]],
                                        "liveness": [result[22], result[23], result[24]],
                                        "loudness": [result[25], result[26], result[27]],
                                        "speechiness": [result[28], result[29], result[30]],
                                        "valence": [result[31], result[32], result[33]]}}
            return data
        else:
            return None
        
    
    def saveUser(self, id: int, user: dict):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to save user data for '{id}' due to missing database connection!")
            raise ConnectionError(f"Failed to save user data for '{id}' due to missing database connection!")

        # Write new data into users table, updating the row if it already exists
        data = (id, user['songs'], user['created'], user['history'], user['public'])
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
        data = (id, recommendations['songcount'], 
                recommendations['popularity'][0], recommendations['popularity'][1], recommendations['popularity'][2],
                recommendations['acousticness'][0], recommendations['acousticness'][1], recommendations['acousticness'][2],
                recommendations['danceability'][0], recommendations['danceability'][1], recommendations['danceability'][2],
                recommendations['energy'][0], recommendations['energy'][1], recommendations['energy'][2],
                recommendations['instrumentalness'][0], recommendations['instrumentalness'][1], recommendations['instrumentalness'][2],
                recommendations['liveness'][0], recommendations['liveness'][1], recommendations['liveness'][2],
                recommendations['loudness'][0], recommendations['loudness'][1], recommendations['loudness'][2],
                recommendations['speechiness'][0], recommendations['speechiness'][1], recommendations['speechiness'][2],
                recommendations['valence'][0], recommendations['valence'][1], recommendations['valence'][2])
        cursor.execute("REPLACE INTO recommendations VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", data)
        
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
               "ORDER BY ListenedAt ASC;")
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
        print("Saving history!")
        
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
        print(deletedRows)
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
