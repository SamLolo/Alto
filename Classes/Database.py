
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

        #** Return Returned Row **
        return UserData


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

        #** Return Returned Row **
        return History


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
        #self.cursor.execute(ToExecute, Values)
        #self.connection.commit()


    def SearchCache(self, Platform, ID):

        if Platform == "Spotify":
            #** Get Song From Database Cache Using Spotify ID **
            self.cursor.excute("SELECT * FROM cache WHERE SpotifyID = '"+str(ID)+"';")
            Song = self.cursor.fetchone()

        else:
            #** Get Song From Database Cache Using Soundcloud ID **
            self.cursor.excute("SELECT * FROM cache WHERE SoundcloudID = '"+str(ID)+"';")
            Song = self.cursor.fetchone()

        print(Song)
        return Song