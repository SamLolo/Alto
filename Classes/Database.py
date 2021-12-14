
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
connection = mysql.connector.connect(host = Host,
                                    database = "Melody",
                                    user = User,
                                    password = Password)

#** Setup Cursor and Output Successful Connection **                  
if connection.is_connected():
    cursor = connection.cursor(buffered=True)
    cursor.execute("SELECT database();")
    print("Database Connection Established: "+datetime.now().strftime("%H:%M")+"\n")

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
        self.cursor.execute("SELECT * FROM users WHERE DiscordID = '"+str(discordID)+"';")
        UserData = self.cursor.fetchone()

        #** Format UserData To Dictionary **
        Dict = {"discordID": UserData[0],
                "stats": UserData[1],
                "history": UserData[2],
                "settings": UserData[3],
                "spotify": UserData[4]}

        #** Return Returned Row **
        return Dict


    def GetStats(self, ID):

        #** Get Users Statistics From Database **
        self.cursor.excute("SELECT * FROM user_stats WHERE ID = '"+str(ID)+"';")
        Stats = self.cursor.fetchone()

        #** Return Returned Row **
        return Stats


    def GetHistory(self, ID):

        #** Get Users Listening History From Database **
        self.cursor.execute("SELECT * FROM history WHERE ID = '"+str(ID)+"';")
        History = self.cursor.fetchone()

        #** Format History Into Dictionary **
        Songs = []
        for i in range(len(History)-3):
            Songs.append(History[i+3])
        Dict = {"inPointer": int(History[1]),
                "outPointer": int(History[2]),
                "queue": Songs}

        #** Return Returned Row **
        return Dict


    def GetSpotify(self, ID):

        #** Get Spotify Credentials From Database **
        self.cursor.execute("SELECT * FROM spotify WHERE ID='"+str(ID[0])+"';")
        Data = self.cursor.fetchone()

        #** Return Data **
        return Data


    def AddUser(self, discordID):

        #** Add Blank Listening History Row **
        self.cursor.execute("INSERT INTO history () VALUES ();")
        self.connection.commit()

        #** Get ID of Listening History **
        self.cursor.execute("SELECT LAST_INSERT_ID();")
        HistoryID = self.cursor.fetchone()[0]

        #** Add Blank Statistics Row **
        self.cursor.execute("INSERT INTO user_stats () VALUES ();")
        self.connection.commit()

        #** Get ID of User Statistics **
        self.cursor.execute("SELECT LAST_INSERT_ID();")
        StatsID = self.cursor.fetchone()[0]

        #** Write Data About User To Users Table **
        Data = (discordID, str(StatsID), str(HistoryID), "None", "None")
        self.cursor.execute("INSERT INTO users VALUES "+str(Data)+";")
        self.connection.commit()

        #** Return User Data Just Created **
        return Data
    

    def RemoveSpotify(self, DiscordID):
        User = self.GetUser(DiscordID)
        self.cursor.execute("DELETE FROM spotify WHERE ID='"+User[4]+"'")
        self.cursor.execute("UPDATE users SET Spotify = 'None' WHERE DiscordID = '"+str(DiscordID)+"';")
        self.connection.commit()


    def AddSongHistory(self, ID, Song):

        #** Get Current History **
        History = list(self.GetHistory(ID))

        #** Add New Song To Stack **
        try:
            Index = History.index(None)
            History.pop(Index)
            History.insert(Index, Song)
        except:
            History.pop(0)
            History.append(Song)

        #** Format SQL Execute String **
        ToExecute = "UPDATE history SET ID = '"+str(History[0])+"'"
        for i in range(49):
            if History[i+1] != None:
                ToExecute += ", Song"+str(i+1)+" = '"+str(History[i+1])+"'"
        ToExecute += " WHERE ID = '"+str(History[0])+"'"

        #** Write Changes To Database **
        self.cursor.execute(ToExecute)
        self.connection.commit()


    def AddSongCache(self, SpotifyID, SoundcloudID, AudioData):

        #** Format Data to Be Added To Cache **
        Columns = ['SpotifyID', 'SoundcloudID', 'Name', 'Artists', 'ArtistID', 'Album', 'AlbumID', 'Art', 'colour', 'Release', 'Popularity', 'Explicit', 'Preview']
        Values = [SpotifyID, SoundcloudID]
        for column in Columns[2:]:
            if column in AudioData.keys():
                value = AudioData[column]
                if type(value) == list:
                    value = ", ".join(value)
                elif str(value) == "N/A":
                    value = None
                Values.append(value)
            else:
                Values.append(None)
        print(Values)

        #** Add Data To Database **
        ToExecute = "INSERT INTO cache (SpotifyID, SoundcloudID, Name, Artists, ArtistID, Album, AlbumID, Art, Colour, ReleaseDate, Popularity, Explicit, Preview) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        Values = tuple(Values)
        self.cursor.execute(ToExecute, Values)
        self.connection.commit()
        print("Added To Cache")


    def AddFullSongCache(self, Info):

        #** Create Tuple With Formatted Data Inside **
        Values = (int(Info['SoundcloudID']), Info['SoundcloudURL'], Info['SpotifyID'], Info['Name'], str(Info['Artists']).strip("[]"), str(Info['ArtistID']).strip("[]"), 
                  Info['Album'], Info['AlbumID'], Info['Art'], str(Info['Colour']), Info['Release'], Info['Popularity'], Info['Explicit'], Info['Preview'])
        
        #** Write Data To Database Cache Replacing Any Old Columns Of Data With Same Primary Key **
        ToExecute = "REPLACE INTO cache (SoundcloudID, SoundcloudURL, SpotifyID, Name, Artists, ArtistID, Album, AlbumID, Art, Colour, ReleaseDate, Popularity, Explicit, Preview) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        self.cursor.execute(ToExecute, Values)
        self.connection.commit()
        print("Added To Cache")


    def SearchCache(self, ID):

        if len(ID) == 22:
            #** Get Song From Database Cache Using Spotify ID **
            self.cursor.execute("SELECT * FROM cache WHERE SpotifyID = '"+str(ID)+"';")
            Song = self.cursor.fetchone()

        else:
            #** Get Song From Database Cache Using Soundcloud ID **
            self.cursor.execute("SELECT * FROM cache WHERE SoundcloudID = '"+str(ID)+"';")
            Song = self.cursor.fetchone()

        if Song != None:
            #** Format Returned Data Into A Dict To Return **
            Song = {Song[2]: {"SoundcloudID": Song[0],
                    "SoundcloudURL": Song[1],
                    "Name": Song[3],
                    "Artists": Song[4].replace("'", "").split(", "),
                    "ArtistID": Song[5].replace("'", "").split(", "),
                    "Album": Song[6],
                    "AlbumID": Song[7],
                    "Art": Song[8],
                    "Colour": tuple(Song[9]),
                    "Release": Song[10],
                    "Popularity": Song[11],
                    "Explicit": Song[12],
                    "Preview": Song[13],
                    "LastUpdated": Song[14]}}
        return Song