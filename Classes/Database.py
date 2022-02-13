
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import requests
from datetime import datetime
import mysql.connector


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
        print(Data)

        #** Format UserData To Dictionary & Return Values **
        if Data != None:
            Dict = {"data": {"discordID": int(Data[0]),
                             "name": Data[1],
                             "discriminator": Data[2],
                             "avatar": Data[3]},
                    "recommendations": {"Popularity": [Data[5], Data[6], Data[7]],
                                        "Acoustic": [Data[8], Data[9], Data[10]],
                                        "Dance": [Data[11], Data[12], Data[13]],
                                        "Energy": [Data[14], Data[15], Data[16]],
                                        "Instrument": [Data[17], Data[18], Data[19]],
                                        "Live": [Data[20], Data[21], Data[22]],
                                        "Loud": [Data[23], Data[24], Data[25]],
                                        "Speech": [Data[26], Data[27], Data[28]],
                                        "Valance": [Data[29], Data[30], Data[31]]}}
            return Dict
        else:
            return None


    def GetHistory(self, discordID):

        #** Get Users Listening History From Database **
        self.cursor.execute("SELECT history.SongID, history.ListenedAt, cache.SpotifyID, cache.Name, cache.Artists, cache.ArtistID, cache.Popularity FROM history INNER JOIN cache ON history.SongID = cache.SoundcloudID WHERE DiscordID = '"+str(discordID)+"' ORDER BY ListenedAt ASC;")
        History = self.cursor.fetchall()

        Dict = {}
        for Tuple in History:
            Dict[int(Tuple[0])] = {"ListenedAt": Tuple[1],
                                   "SpotifyID": Tuple[2],
                                   "Name": Tuple[3],
                                   "Artists": Tuple[4].replace("'", "").split(", "),
                                   "ArtistIDs": Tuple[5].replace("'", "").split(", "),
                                   "Popularity": Tuple[6]}

        #** Return List Of Ordered Song IDs **
        print(Dict)
        return Dict


    def GetSpotify(self, discordID):

        #** Get Spotify Data From Database & Return It **
        self.cursor.execute("SELECT * FROM spotify WHERE DiscordID='"+str(discordID)+"';")
        Data = self.cursor.fetchone()
        
        #** Format Spotify Data To Dictionary & Return Values **
        if Data != None:
            Dict = {"discordID": int(Data[1]),
                    "spotifyID": Data[0],
                    "name": Data[2],
                    "avatar": Data[3],
                    "followers": Data[4],
                    "subscription": Data[5],
                    "refresh": Data[6],
                    "linked": Data[7]}
            return Dict
        else:
            return None


    def AddUser(self, UserData, Recommendations):

        #** Write Data About User To Users Table **
        self.cursor.execute("INSERT INTO users VALUES "+str(UserData)+";")
        self.connection.commit()

        #** Write Data About User Recommendation Data To Recommendations Table **
        self.cursor.execute("INSERT INTO recommendations VALUES "+str(Recommendations)+";")
        self.connection.commit()
    

    def RemoveSpotify(self, discordID):
        
        #** Remove Row From Spotify With Specified Discord ID **
        self.cursor.execute("DELETE FROM spotify WHERE DiscordID='"+str(discordID)+"'")
        self.connection.commit()


    def AddSongHistory(self, discordID, SongDict, OutPointer):

        #** Separate SongDict Into 2 Lists **
        SongIDs = list(SongDict.keys())

        #** Delete All Rows Older Than Oldest Song In Song History & Get Amount Deleted**
        Oldest = list(SongDict.values())[OutPointer]["ListenedAt"]
        self.cursor.execute("DELETE FROM history WHERE ListenedAt < '"+str(Oldest)+"';")
        DeletedRows = self.cursor.execute("SELECT ROW_COUNT();")

        #** If No Rows Deleted, Set Deleted Rows To Length Of List So All Songs Are Added. Using REPLACE INTO Avoids Errors For Duplicates, **
        #** As Columns With The Same Primary Key Are Just OverWritten **
        if DeletedRows == None:
            DeletedRows = len(SongIDs)
            
        #** Format SQL Execute String **
        for i in range(DeletedRows):
            Data = (str(discordID), SongIDs[i], SongDict[SongIDs[i]]["ListenedAt"])
            print(Data)
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

        #** Format Full Data Into A Dict To Return **
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