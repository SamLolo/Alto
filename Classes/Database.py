
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import logging
import mysql.connector


#!--------------------------------DATABASE OPERATIONS-----------------------------------#


class UserData():
    
    def __init__(self):
        
        #** Get Connection Details **
        user = os.environ["DATABASE_USER"]
        password = os.environ["DATABASE_PASS"]
            
        #** Create Connection Pool For Database **
        self.pool = mysql.connector.pooling.MySQLConnectionPool(pool_name = "bot",
                                                                pool_size = 5,
                                                                host = "localhost",
                                                                database = "alto",
                                                                user = user,
                                                                password = password)

        #** Delete Connection Details **
        del user
        del password
        
        #** Get Logger For Database **
        self.logger = logging.getLogger("database")


    def ensure_connection(self):
        
        try:
            connection = self.pool.get_connection()
            self.logger.debug("New connection established!")
            cursor = connection.cursor(buffered=True)
            return (connection, cursor)
        
        except Exception as e:
            self.logger.error("Failed to get new connection from pool!")
            self.logger.exception(e)
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


    def RemoveData(self, discordID: int, tables: list):
        
        #** Ensure Database Connection
        connection, cursor = self.ensure_connection()

        #** Remove Row From Each Specified Table With Specified Discord ID **
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE DiscordID='{discordID}';")
            self.logger.debug(f"Table '{table}' deleted for user: {discordID}!")
        connection.commit()
        connection.close()


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

        # Prepare sql and values for inserting given information into database
        if info['source'] == "spotify":
            sql = "INSERT INTO cache (Source, ID, URL, Name, Artists, Track, ArtistID, Album, AlbumID, Art, Colour, Release, Popularity, Explicit, Preview) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
            values = (info['source'], info['id'], info['url'], info['name'], info['artist'], info['track'], info['artistID'], info['album'], info['albumID'], info['art'], info['colour'], info['release'], info['popularity'], info['explicit'], info['preview'])
        elif info['source'] == "soundcloud":
            sql = "INSERT INTO cache (Source, ID, URL, Name, Artists, Track) VALUES (%s, %s, %s, %s, %s, %s);"
            values = (info['source'], info['id'], info['url'], info['name'], info['author'], info['track'])
        else:
            self.logger.warning(f"Unknown source '{info['source']}' encountered whilst trying to cache song!")
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
            self.logger.warning("Failed to search cache due to missing database connection!")
            return None

        # Query cache table and return connection to available pool
        cursor.execute(f"SELECT * FROM cache WHERE (ID = '{query}') OR (URL = '{query}');")
        result = cursor.fetchone()
        connection.close()

        #** Close Connection Once Finished & Format Full Data Into A Dict To Return **
        if result is None:
            return None
            
        # Format base data (for all source types) into a dictionary 
        data = {"cacheID": int(result[0]),
                "source": result[1],
                "id": result[2],
                "url": result[3],
                "name": result[4],
                "artists": result[5].replace("'", "").split(", "),
                "track": result[6],
                "updated": result[16]}
        
        # If source is spotify, add aditional track metadata
        if data['source'] == "Spotify":
            additonal = {"artistID": result[7].replace("'", "").split(", "),
                         "album": result[8],
                         "albumID": result[9],
                         "art": result[10],
                         "colour": tuple(result[11]),
                         "release": result[12],
                         "popularity": result[13],
                         "explicit": result[14],
                         "preview": result[15]}
            data.update(additonal)
        return data
