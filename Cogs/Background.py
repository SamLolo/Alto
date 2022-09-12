
#!---------------------------IMPORT MODULES-----------------------#


import logging
import discord
from discord.ext import tasks, commands


#!--------------------------BACKGROUND CLASS------------------------#


class BackgroundTasks(commands.Cog):

    def __init__(self, client: discord.Client):

        #** Assign Class Objects **
        self.client = client
        
        #** Setup Logging **
        self.logger = logging.getLogger("discord.background")
        
    
    def cog_unload(self):
        
        #** Gently Shutdown All Current Background Tasks **
        self.StatusRotation.stop()
        self.logger.info("Status rotation stopped")
        
        
    @commands.Cog.listener()
    async def on_ready(self):
        
        #** When Bot Startup Is Complete, Start Status Rotation & Auth Checking Background Tasks **
        self.StatusRotation.change_interval(seconds = self.client.config['StatusTime'])
        self.currentStatus = 0
        self.StatusRotation.start()
        self.logger.info("Started status rotation at time interval "+ str(self.client.config['StatusTime']) +" seconds")


    @tasks.loop()
    async def StatusRotation(self):
        
        #** Setup Status List **
        statusList = self.client.config['Status']
        
        #** If Current Status Is Last In List, Loop Back To The Start, Otherwise Increment Count By 1 **
        if self.currentStatus >= len(statusList)-1:
            self.currentStatus = 0
        else:
            self.currentStatus += 1
        
        #** Set Activity Type Based Of Specified Activity Type In Config File **
        if statusList[self.currentStatus][0].lower() == "playing":
            activity = discord.ActivityType.playing
        elif statusList[self.currentStatus][0].lower() == "listening":
            activity = discord.ActivityType.listening
        else:
            activity = discord.ActivityType.watching
        
        #** Update Presence On Discord **
        await self.client.change_presence(activity=discord.Activity(type=activity, name=f' {str(statusList[self.currentStatus][1])}'))
        self.logger.debug(f'Status Changed To: "{statusList[self.currentStatus][0]} {statusList[self.currentStatus][1]}"')


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(BackgroundTasks(client))