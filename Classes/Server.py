
#!-------------------------IMPORT MODULES-----------------------!#


import discord
from enum import Enum


#!------------------------PERMISSIONS ENUMS---------------------!#


class UserPermissions(Enum):
    PLAY = 1
    VOLUME = 2
    SKIP = 3
    EDIT_QUEUE = 4
    SEEK = 5


#!-------------------------SERVER OBJECT------------------------!#


class Server():
    
    def __init__(self, client: discord.Client, guild: discord.Guild):
        
        #** Setup server with default settings **
        self.volume = {"default": 25,
                       "previous": 25}
        self.allowed_voice = []
        self.allowed_channels = []
        self.save_queue = False
        self.permissions = {"default": [UserPermissions.PLAY, UserPermissions.VOLUME, UserPermissions.SKIP, UserPermissions.EDIT_QUEUE, UserPermissions.SEEK],
                            "users": {},
                            "roles": {}}
        
        #** Get previously saved settings from database **
        self.client = client
        self.server = guild
        self.load()
    
    
    def load(self):
        
        # Get results from database
        data = self.client.database.loadServer(self.server.id)
        if data is not None:
            
            # Save data as class attributes for easy access
            self.volume = data['volume']
            self.allowed_voice = [self.server.get_channel(id) for id in data['voice']]
            self.allowed_channels = [self.server.get_channel(id) for id in data['channels']]
            self.save_queue = data['queue']
            self.permissions = data['permissions']
    
    
    def save(self):
        
        # Write data to database
        self.client.database.saveServer(id = self.server.id,
                                        volume = self.volume,
                                        voice = [channel.id for channel in self.allowed_voice],
                                        channels = [channel.id for channel in self.allowed_channels],
                                        queue = self.save_queue,
                                        permissions = self.permissions)