
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import mysql.connector
from datetime import datetime
from cryptography.fernet import Fernet


#!--------------------------------DATABASE CONNECTION---------------------------------#


#** Get Connection Details **
Host = os.environ["DATABASE_HOST"]
User = os.environ["DATABASE_USER"]
Password = os.environ["DATABASE_PASS"]

#** Connect To Database **
print("--------------------CONNECTING TO DATABASE--------------------")
connection = mysql.connector.connect(host = Host,
                                    database = "discordmusic",
                                    user = User,
                                    password = Password)

#** Setup Cursor and Output Successful Connection **                  
if connection.is_connected():
    cursor = connection.cursor(buffered=True)
    cursor.execute("SELECT database();")
    print("Database Connection Established: "+datetime.now().strftime("%H:%M")+"\n")
else:
    print("Database Connection Failed: "+datetime.now().strftime("%H:%M")+"\n")

#** Delete Connection Details **
del Host
del User
del Password


#!--------------------------------DATABASE OPERATIONS-----------------------------------#


class UserData():
    
    def __init__(self):

        #** Setup Objects **
        self.cursor = cursor
        self.connection = connection


    def return_connection(self):

        #** Return Database Connection & Cursor **
        return self.connection, self.cursor


    def GetUser(self, discordID):

        #** Get Info About Discord User From Database **
        self.cursor.execute("SELECT * FROM users INNER JOIN recommendations WHERE users.DiscordID = '"+str(discordID)+"';")
        Data = self.cursor.fetchone()
        self.connection.commit()

        #** Format UserData To Dictionary & Return Values **
        if Data != None:
            Dict = {"data": {"discordID": int(Data[0]),
                             "name": Data[1],
                             "discriminator": Data[2],
                             "avatar": Data[3],
                             "joined": Data[5],
                             "songs": Data[4]},
                    "recommendations": {"songcount": Data[7],
                                        "Popularity": [Data[8], Data[9], Data[10]],
                                        "Acoustic": [Data[11], Data[12], Data[13]],
                                        "Dance": [Data[14], Data[15], Data[16]],
                                        "Energy": [Data[17], Data[18], Data[19]],
                                        "Instrument": [Data[20], Data[21], Data[22]],
                                        "Live": [Data[23], Data[24], Data[25]],
                                        "Loud": [Data[26], Data[27], Data[28]],
                                        "Speech": [Data[29], Data[30], Data[31]],
                                        "Valance": [Data[32], Data[33], Data[34]]}}
            return Dict
        else:
            return None


    def GetHistory(self, discordID):

        #** Get Users Listening History From Database, Ordered By Most Recent First **
        Sql = ("SELECT history.SongID, history.ListenedAt, cache.SoundcloudURL, cache.SpotifyID, cache.Name, "
               "cache.Artists, cache.ArtistID, cache.Popularity "
               "FROM history "
               "INNER JOIN cache ON history.SongID = cache.SoundcloudID "
               "WHERE DiscordID = '"+str(discordID)+"' "
               "ORDER BY ListenedAt ASC;")
        self.cursor.execute(Sql)
        History = self.cursor.fetchall()
        self.connection.commit()

        #** Create Empty List & Iterate Through Returned Rows **
        List = []
        for Tuple in History:
            
            #** Create Dictionary Of Song Data From Returned Tuple **
            ID = int(Tuple[0])
            Dict = {"ID": ID,
                    "ListenedAt": Tuple[1],
                    "SpotifyID": Tuple[3],
                    "Name": Tuple[4],
                    "Artists": Tuple[5].replace("'", "").split(", "),
                    "URI": Tuple[2]}
            
            #** If Song Has Spotify ID, Add Spotify Data As Well **
            if Tuple[3] != None:
                Dict['ArtistIDs'] = Tuple[6].replace("'", "").split(", ")
                Dict['Popularity'] = Tuple[7]
                
            #** Add Dictionary To List **
            List.append(Dict)

        #** Return List Of Ordered Song Dictionaries **
        return List


    def GetSpotify(self, discordID):

        #** Get Spotify Data From Database & Return It **
        self.cursor.execute("SELECT * FROM spotify WHERE DiscordID='"+str(discordID)+"';")
        Data = self.cursor.fetchone()
        self.connection.commit()
        
        #** Check If Data Is Found & If Data Has Spotify ID**
        if Data != None:
            if Data[0] != None:

                #** Setup Symmetric Encryption Module **
                Key = os.environ['ENCRYPTION_KEY']
                Key = bytes(Key, 'utf-8')
                fernet = Fernet(Key)

                #** Decrypt Sensitive Information **
                Refresh = fernet.decrypt(bytes(Data[6], 'utf-8')).decode()
                Name = fernet.decrypt(bytes(Data[2], 'utf-8')).decode()
                Avatar = fernet.decrypt(bytes(Data[3], 'utf-8')).decode()
                SpotifyID = fernet.decrypt(bytes(Data[0], 'utf-8')).decode()

                #** Delete Variables To Keep Key Safe **
                del Key
                del fernet

                #** Format Data Into Dictionary & Return Dictionary**
                Dict = {"discordID": int(Data[1]),
                        "spotifyID": SpotifyID,
                        "name": Name,
                        "avatar": Avatar,
                        "followers": Data[4],
                        "subscription": Data[5],
                        "refresh": Refresh,
                        "linked": Data[7]}
                return Dict

        #** Return None If No Spotify Data Found **
            else:
                return None
        else:
            return None


    def SaveUserDetails(self, User):

        #** Write Data About User To Users Table / Update Row If Already Exists **
        Data = (str(User['data']['discordID']), User['data']['name'], User['data']['discriminator'], User['data']['avatar'], User['data']['songs'], User['data']['joined'])
        self.cursor.execute("REPLACE INTO users VALUES (%s, %s, %s, %s, %s, %s);", Data)
        self.connection.commit()

        #** Write Data About User Recommendation Data To Recommendations Table / Update If Already Exists **
        Data = (User['data']['discordID'], User['recommendations']['songcount'], 
                User['recommendations']['Popularity'][0], User['recommendations']['Popularity'][1], User['recommendations']['Popularity'][2],
                User['recommendations']['Acoustic'][0], User['recommendations']['Acoustic'][1], User['recommendations']['Acoustic'][2],
                User['recommendations']['Dance'][0], User['recommendations']['Dance'][1], User['recommendations']['Dance'][2],
                User['recommendations']['Energy'][0], User['recommendations']['Energy'][1], User['recommendations']['Energy'][2],
                User['recommendations']['Instrument'][0], User['recommendations']['Instrument'][1], User['recommendations']['Instrument'][2],
                User['recommendations']['Live'][0], User['recommendations']['Live'][1], User['recommendations']['Live'][2],
                User['recommendations']['Loud'][0], User['recommendations']['Loud'][1], User['recommendations']['Loud'][2],
                User['recommendations']['Speech'][0], User['recommendations']['Speech'][1], User['recommendations']['Speech'][2],
                User['recommendations']['Valance'][0], User['recommendations']['Valance'][1], User['recommendations']['Valance'][2])
        self.cursor.execute("REPLACE INTO recommendations VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", Data)
        self.connection.commit()

    
    def PrepareLink(self, discordID):

        #** Write Empty Row With DiscordID Into Spotify Table **
        self.cursor.execute("REPLACE INTO spotify (DiscordID) VALUES ("+str(discordID)+");")
        self.connection.commit()
    

    def RemoveData(self, discordID, Tables):
        
        #** Remove Row From Each Specified Table With Specified Discord ID **
        for Table in Tables:
            self.cursor.execute("DELETE FROM "+Table+" WHERE DiscordID='"+str(discordID)+"';")
            print("Table '"+Table+"' deleted for user: "+str(discordID)+"!")
        self.connection.commit()


    def AddSongHistory(self, discordID, History, OutPointer):

        #** Delete All Rows Older Than Oldest Song In Song History & Get Amount Deleted**
        Oldest = History[OutPointer]["ListenedAt"]
        self.cursor.execute("DELETE FROM history WHERE ListenedAt < '"+str(Oldest)+"';")
        DeletedRows = self.cursor.execute("SELECT ROW_COUNT();")

        #** If No Rows Deleted, Set Deleted Rows To Length Of List So All Songs Are Added. Using REPLACE INTO Avoids Errors For Duplicates, **
        #** As Columns With The Same Primary Key Are Just OverWritten **
        if DeletedRows == None:
            DeletedRows = len(History)
            
        #** Format SQL Execute String **
        for i in range(DeletedRows):
            Data = (str(discordID), History[i]['ID'], History[i]["ListenedAt"])
            self.cursor.execute("REPLACE INTO history (DiscordID, SongID, ListenedAt) VALUES (%s, %s, %s);", Data)
            
        #** Write Changes To Database **
        self.connection.commit()


    def AddPartialSongCache(self, Info):

        #** Create Tuple With Formatted Data Inside **
        Values = (str(Info['SoundcloudID']), Info['SoundcloudURL'], Info['Name'], str(Info['Artists']).strip("[]"))
        
        #** Insert New Row Into Database. Only Called When New Row Is Needed **
        ToExecute = "INSERT INTO cache (SoundcloudID, SoundcloudURL, Name, Artists) VALUES (%s, %s, %s, %s);"
        self.cursor.execute(ToExecute, Values)
        self.connection.commit()
        print("Partial Data Added To Cache")


    def AddFullSongCache(self, Info):

        #** Create Tuple With Formatted Data Inside **
        Values = (str(Info['SoundcloudID']), Info['SoundcloudURL'], Info['SpotifyID'], Info['Name'], str(Info['Artists']).strip("[]"), str(Info['ArtistID']).strip("[]"), 
                  Info['Album'], Info['AlbumID'], Info['Art'], str(Info['Colour']), Info['Release'], Info['Popularity'], Info['Explicit'], Info['Preview'])
        
        #** Write Data To Database Cache Replacing Any Old Columns Of Data With Same Primary Key **
        ToExecute = "REPLACE INTO cache (SoundcloudID, SoundcloudURL, SpotifyID, Name, Artists, ArtistID, Album, AlbumID, Art, Colour, ReleaseDate, Popularity, Explicit, Preview) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        self.cursor.execute(ToExecute, Values)
        self.connection.commit()
        print("Full Data Added To Cache")


    def SearchCache(self, ID):

        if len(ID) == 22:
            #** Get Song From Database Cache Using Spotify ID **
            self.cursor.execute("SELECT * FROM cache WHERE SpotifyID = '"+str(ID)+"';")
            Song = self.cursor.fetchone()

        else:
            #** Get Song From Database Cache Using Soundcloud ID **
            self.cursor.execute("SELECT * FROM cache WHERE SoundcloudID = '"+str(ID)+"';")
            Song = self.cursor.fetchone()

        #** Commit To Refresh Connection & Format Full Data Into A Dict To Return **
        self.connection.commit()
        if Song != None:
            if Song[2] != None:
                RGBList = Song[9].strip("()").split(", ")
                Song = {Song[2]: {"SoundcloudID": int(Song[0]),
                        "SoundcloudURL": Song[1],
                        "Name": Song[3],
                        "Artists": Song[4].replace("'", "").split(", "),
                        "ArtistID": Song[5].replace("'", "").split(", "),
                        "Album": Song[6],
                        "AlbumID": Song[7],
                        "Art": Song[8],
                        "Colour": (int(RGBList[0]), int(RGBList[1]), int(RGBList[2])),
                        "Release": Song[10],
                        "Popularity": Song[11],
                        "Explicit": Song[12],
                        "Preview": Song[13],
                        "LastUpdated": Song[14],
                        "PartialCache": False}}
            
            #** If Data Doesn't Have Spotify ID, Format Partial Data Into Dict To Return **
            else:
                Song = {Song[0]: {"SoundcloudURL": Song[1],
                                "Name": Song[3],
                                "Artists": Song[4].replace("'", "").split(", "),
                                "PartialCache": True}}
        return Song