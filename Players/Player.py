
#!--------------------IMPORT MODULES-----------------------#


import lavalink
from Classes.Users import User


#!-------------------AUTOMATIC PLAYER---------------------#


class CustomPlayer(lavalink.DefaultPlayer):
    
    def __init__(self, guildID: int, node: lavalink.Node):
        super().__init__(guildID, node)
        self.history = []
        self.MAX_HISTORY = 20
        self.recommendations = []
        self.auto = False


    def generate_recommendations(self):
        pass
    
    
    def load_next(self):
        pass
    
    
    def start(self, user: User):
        self.auto = True
        pass
    
    
    async def play(self, track: lavalink.AudioTrack, start_time: int = None, end_time: int = None, no_replace: bool = None, volume: int = None, pause: bool = None):
        if len(self.history) < self.MAX_HISTORY:
            self.history.insert(0, track)
        else:
            self.history.pop(-1)
            self.history.insert(0, track)
        await super().play(track, start_time, end_time, no_replace, volume, pause)
        
    
    async def stop(self):
        if self.auto:
            self.auto = False
            self.recommendations.clear()
        await super().stop()