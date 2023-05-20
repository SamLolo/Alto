
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import logging
import mysql.connector


#!--------------------------------DATABASE OPERATIONS-----------------------------------#


class Database():
    
    def __init__(self, pool="main", size=5):
        
        # Setup database logger
        self.logger = logging.getLogger("database")
            
        # Create connection pool for database
        user = os.environ["DATABASE_USER"]
        password = os.environ["DATABASE_PASS"]
        try:
            self.logger.info(f"Attempting to create new database pool '{pool}' of size {size}")
            self.pool = mysql.connector.pooling.MySQLConnectionPool(pool_name = pool,
                                                                    pool_size = size,
                                                                    host = "localhost",
                                                                    database = "alto",
                                                                    user = user,
                                                                    password = password)
        except mysql.connector.errors.DatabaseError as failure:
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


    def GetUser(self, discordID: int):
        
        #** Ensure Database Connection
        connection, cursor = self.ensure_connection()

        #** Get Info About Discord User From Database **
        cursor.execute(f"SELECT * FROM users INNER JOIN recommendations WHERE users.DiscordID = '{discordID}';")
        result = cursor.fetchone()
        connection.close()

        #** Format Userdata To Dictionary & Return Values **
        if result != None:
            data = {"result": {"discordID": int(result[0]),
                               "name": result[1],
                               "discriminator": result[2],
                               "avatar": result[3],
                               "joined": result[5],
                               "songs": result[4]},
                    "recommendations": {"songcount": result[7],
                                        "Popularity": [result[8], result[9], result[10]],
                                        "Acoustic": [result[11], result[12], result[13]],
                                        "Dance": [result[14], result[15], result[16]],
                                        "Energy": [result[17], result[18], result[19]],
                                        "Instrument": [result[20], result[21], result[22]],
                                        "Live": [result[23], result[24], result[25]],
                                        "Loud": [result[26], result[27], result[28]],
                                        "Speech": [result[29], result[30], result[31]],
                                        "Valance": [result[32], result[33], result[34]]}}
            return data
        else:
            return None
            

    def GetHistory(self, discordID: int):
        
        #** Ensure Database Connection
        connection, cursor = self.ensure_connection()

        #** Get Users Listening History From Database, Ordered By Most Recent First **
        sql = ("SELECT history.SongID, history.ListenedAt, cache.SoundcloudURL, cache.SpotifyID, cache.Name, cache.Artists, cache.ArtistID, cache.Popularity "
               "FROM history "
               "INNER JOIN cache ON history.SongID = cache.SoundcloudID "
              f"WHERE DiscordID = '{discordID}' "
               "ORDER BY ListenedAt ASC;")
        cursor.execute(sql)
        result = cursor.fetchall()
        connection.close()

        #** Create Empty List & Iterate Through Returned Rows **
        history = []
        for row in result:

            #** Create Dictionary Of Song Data From Returned Tuple **
            data = {"ID": int(row[0]),
                    "ListenedAt": row[1],
                    "SpotifyID": row[3],
                    "Name": row[4],
                    "Artists": row[5].replace("'", "").split(", "),
                    "URI": row[2]}

            #** If Song Has Spotify ID, Add Spotify Data As Well **
            if row[3] != None:
                data['ArtistIDs'] = row[6].replace("'", "").split(", ")
                data['Popularity'] = row[7]
      
            #** Add Dictionary To List **
            history.append(data)

        #** Return List Of Ordered Song Dictionaries **
        return history


    def SaveUserDetails(self, user: dict):
        
        #** Ensure Database Connection
        connection, cursor = self.ensure_connection()

        #** Write Data About User To Users Table / Update Row If Already Exists **
        userdata = user['data']
        data = (str(userdata['discordID']), userdata['name'], userdata['discriminator'], userdata['avatar'], userdata['songs'], userdata['joined'])
        cursor.execute("REPLACE INTO users VALUES (%s, %s, %s, %s, %s, %s);", data)

        #** Write Data About User Recommendation Data To Recommendations Table / Update If Already Exists **
        recommendations = user['recommendations']
        data = (userdata['discordID'], recommendations['songcount'], 
                recommendations['Popularity'][0], recommendations['Popularity'][1], recommendations['Popularity'][2],
                recommendations['Acoustic'][0], recommendations['Acoustic'][1], recommendations['Acoustic'][2],
                recommendations['Dance'][0], recommendations['Dance'][1], recommendations['Dance'][2],
                recommendations['Energy'][0], recommendations['Energy'][1], recommendations['Energy'][2],
                recommendations['Instrument'][0], recommendations['Instrument'][1], recommendations['Instrument'][2],
                recommendations['Live'][0], recommendations['Live'][1], recommendations['Live'][2],
                recommendations['Loud'][0], recommendations['Loud'][1], recommendations['Loud'][2],
                recommendations['Speech'][0], recommendations['Speech'][1], recommendations['Speech'][2],
                recommendations['Valance'][0], recommendations['Valance'][1], recommendations['Valance'][2])
        cursor.execute("REPLACE INTO recommendations VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", data)
        connection.commit()
        connection.close()


    def removeData(self, discordID: int, tables: list):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to delete tables '{', '.join(tables)}' for discordID '{discordID}' due to missing database connection!")
            return None

        # Remove user entry from each table and return database connection to pool
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE DiscordID='{discordID}';")
            self.logger.debug(f"Table '{table}' deleted for user: {discordID}!")
        connection.commit()
        connection.close()
        self.logger.debug("Connection returned to pool!")
        

    def AddSongHistory(self, discordID: int, history: dict, outPointer: int):
        
        #** Ensure Database Connection
        connection, cursor = self.ensure_connection()

        #** Delete All Rows Older Than Oldest Song In Song History & Get Amount Deleted**
        oldest = history[outPointer]["ListenedAt"]
        cursor.execute(f"DELETE FROM history WHERE ListenedAt < '{oldest}';")
        deletedRows = cursor.execute("SELECT ROW_COUNT();")

        #** If No Rows Deleted, Set Deleted Rows To Length Of List So All Songs Are Added. Using REPLACE INTO Avoids Errors For Duplicates, **
        #** As Columns With The Same Primary Key Are Just OverWritten **
        if deletedRows is None:
            deletedRows = len(history)
    
        #** Format SQL Execute String **
        for i in range(deletedRows):
            data = (str(discordID), history[i]['ID'], history[i]["ListenedAt"])
            cursor.execute("REPLACE INTO history (DiscordID, SongID, ListenedAt) VALUES (%s, %s, %s);", data)

        #** Write Changes To Database **
        connection.commit()
        connection.close()


    def cacheSong(self, info: dict):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to cache song with {info['source']} ID '{info['id']}' due to missing database connection!")
            return None
        
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
        connection.close()
        self.logger.debug("Connection returned to pool!")


    def searchCache(self, query: str):
        
        # Get database connection from pool
        connection, cursor = self.ensure_connection()
        if connection is None:
            self.logger.warning(f"Failed to search cache with query '{query}' due to missing database connection!")
            return None

        # Query cache table and return connection to available pool
        cursor.execute(f"SELECT * FROM cache WHERE (ID = '{query}') OR (URL = '{query}');")
        result = cursor.fetchone()
        connection.close()

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
