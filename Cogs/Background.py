
#!---------------------------IMPORT MODULES-----------------------#


import json
import discord
from discord.ext import tasks, commands


#!------------------------------IMPORT CLASSES----------------------------------#


from Classes.Database import UserData


#!--------------------------------STARTUP-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Background")
print("Modules Imported: ✓\n")


#!------------------------INITIALISE CLASSES-------------------#


Database = UserData()


#!--------------------------BACKGROUND CLASS------------------------#


class BackgroundTasks(commands.Cog):

    def __init__(self, client):

        #** Assign Class Objects **
        self.client = client

        #** Load Config File **
        with open('Config.json') as ConfigFile:
            Config = json.load(ConfigFile)
            ConfigFile.close()
            
        #** Setup Emojis **
        self.Emojis = Config['Variables']['Emojis']
        
        #** Start Status Rotation **
        self.CurrentStatus = 0
        self.Status = list(Config['Status'].items())
        self.StatusTime = Config['StatusTime']

        #** Setup Database Details **
        self.connection, self.cursor = Database.return_connection()
        
    
    def cog_unload(self):
        
        #** Gently Shutdown All Current Background Tasks **
        self.StatusRotation.stop()
        print("Background Cog Unloaded!")
        
        
    @commands.Cog.listener()
    async def on_ready(self):
        
        #** When Bot Startup Is Complete, Start Status Rotation & Auth Checking Background Tasks **
        self.StatusRotation.change_interval(seconds = self.StatusTime)
        self.StatusRotation.start()


    @tasks.loop()
    async def StatusRotation(self):
        
        #** If Current Status Is Last In List, Loop Back To The Start, Otherwise Increment Count By 1 **
        if self.CurrentStatus == len(self.Status)-1:
            self.CurrentStatus = 0
        else:
            self.CurrentStatus += 1
        
        #** Set Activity Type Based Of Specified Activity Type In Config File **
        if self.Status[self.CurrentStatus][0] == "Playing":
            Activity = discord.ActivityType.playing
        elif self.Status[self.CurrentStatus][0] == "Listening":
            Activity = discord.ActivityType.listening
        else:
            Activity = discord.ActivityType.watching
        
        #** Update Presence On Discord **
        await self.client.change_presence(activity=discord.Activity(type=Activity, name=" "+str(self.Status[self.CurrentStatus][1])))


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(BackgroundTasks(client))