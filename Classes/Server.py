
#!-------------------------IMPORT MODULES-----------------------!#


import discord


#!-------------------------SERVER OBJECT------------------------!#


class Server():
    
    def __init__(self, client: discord.Client, guild: discord.Guild):
        
        #** Setup server with default settings **
        self.dj = {"enabled": False,
                   "roles": [],
                   "users": []}
        self.volume = {"enabled": True,
                       "default": 25}
        self.allowed_voice = []
        self.allowed_channels = []
        self.save_queue = False
        self.vote_skip = False
        
        #** Get previously saved settings from database **
        self.client = client
        self.server = guild
        self.load()
    
    
    def load(self):
        
        # Get results from database
        data = self.client.database.loadServer(self.server.id)
        if data is not None:
            
            # Save data as class attributes for easy access
            self.dj = data['dj']
            self.dj['roles'] = [self.server.get_role(id) for id in data['dj']['roles']]
            self.dj['users'] = [self.server.get_member(id) for id in data['dj']['users']]
            
            self.volume = data['volume']
            self.allowed_voice = [self.server.get_channel(id) for id in data['voice']]
            self.allowed_channels = [self.server.get_channel(id) for id in data['channels']]
            self.save_queue = data['queue']
            self.vote_skip = data['skip']
    
    
    def save(self):
    
        # Format data ready to be saved
        self.dj['roles'] = [role.id for role in self.dj['roles']]
        self.dj['users'] = [user.id for user in self.dj['users']]
        self.allowed_voice = [channel.id for channel in self.allowed_voice]
        self.allowed_channels = [channel.id for channel in self.allowed_channels]
        
        # Write data to database
        self.client.database.saveServer(id = self.server.id,
                                        dj = self.dj,
                                        volume = self.volume,
                                        voice = self.allowed_voice,
                                        channels = self.allowed_channels,
                                        queue = self.save_queue,
                                        skip = self.vote_skip)