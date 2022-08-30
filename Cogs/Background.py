
#!---------------------------IMPORT MODULES-----------------------#


import json
import discord
from discord.ext import tasks, commands


#!------------------------------IMPORT CLASSES----------------------------------#


from Classes.Database import UserData


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
        
        #** Output Logging **
        client.logger.info("Extension Loaded: Cogs.Background")
        
    
    def cog_unload(self):
        
        #** Gently Shutdown All Current Background Tasks **
        self.StatusRotation.stop()
        self.client.logger.info("Status rotation stopped")
        self.client.logger.info("Extension Unloaded: Cogs.Background")
        
        
    @commands.Cog.listener()
    async def on_ready(self):
        
        #** When Bot Startup Is Complete, Start Status Rotation & Auth Checking Background Tasks **
        self.StatusRotation.change_interval(seconds = self.StatusTime)
        self.StatusRotation.start()
        self.client.logger.info("Started status rotation at time interval "+ str(self.StatusTime) +" seconds")


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


async def setup(client):
    await client.add_cog(BackgroundTasks(client))