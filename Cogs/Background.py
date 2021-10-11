
#!---------------------------IMPORT MODULES-----------------------#


import json
import discord
import asyncio
from discord.ext import commands
from discord.utils import get


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


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(BackgroundTasks(client))