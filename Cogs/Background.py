
#!---------------------------IMPORT MODULES-----------------------#


import logging
import discord
from itertools import cycle
from discord.ext import tasks, commands


#!--------------------------BACKGROUND CLASS------------------------#


class BackgroundTasks(commands.Cog):

    def __init__(self, client: discord.Client):

        #** Assign Class Objects **
        self.client = client
        
        #** Setup Logging **
        self.logger = logging.getLogger("discord.background")
        
    
    def convert_activity(self, activity):
        
        #** Convert activity str into Discord Enum (defaults to 'playing' if unknown) **
        if activity.lower() == "watching":
            return discord.ActivityType.watching
        elif activity.lower() == "listening":
            return discord.ActivityType.listening
        elif activity.lower() == "streaming":
            return discord.ActivityType.streaming
        else:
            return discord.ActivityType.playing
        
    
    async def cog_load(self):
        
        #** Setup & Start Status Rotation if enabled **
        if self.client.config['status']['enabled']:
            self.statusMessages = cycle(self.client.config['status']['messages'])
            self.statusRotation.change_interval(seconds = self.client.config['status']['interval'])
            self.statusRotation.start()
        
        #** If disabled, set default status message **  
        else:
            if self.client.is_ready():
                await self.client.change_presence(activity=discord.Activity(type=self.convert_activity(self.config["status"]["default"][0]), 
                                                                            name=self.config["status"]["default"][1]))
                self.logger.debug(f'Status Set To: "{self.config["status"]["default"][0]} {self.config["status"]["default"][1]}"')
    
    
    def cog_unload(self):
        
        #** Gently Shutdown All Current Background Tasks **
        if self.statusRotation.is_running():
            self.statusRotation.stop()
            self.logger.info("Status rotation stopped")
            
    
    @commands.Cog.listener()
    async def on_ready(self):
        
        #** Set default status on startup if status rotation is disabled **
        if not(self.client.config['status']['enabled']):
            await self.client.change_presence(activity=discord.Activity(type=self.convert_activity(self.config["status"]["default"][0]), 
                                                                            name=self.config["status"]["default"][1]))
            self.logger.debug(f'Status Set To: "{self.config["status"]["default"][0]} {self.config["status"]["default"][1]}"')


    @tasks.loop()
    async def statusRotation(self):
        
        #** Update Presence On Discord **
        newActivity = next(self.statusMessages)
        await self.client.change_presence(activity=discord.Activity(type=self.convert_activity(newActivity[0]), 
                                                                    name=newActivity[1]))
        self.logger.debug(f'Status Updated To: "{newActivity[0]} {newActivity[1]}"')


    @statusRotation.before_loop
    async def statusReady(self):
        #** Wait until bot is ready before starting status loop **
        await self.client.wait_until_ready()
        self.logger.info(f"Started status rotation at time interval: {self.client.config['status']['interval']} seconds")


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(BackgroundTasks(client))