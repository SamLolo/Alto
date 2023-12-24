
#!--------------------IMPORT MODULES-----------------------#


import lavalink
from datetime import datetime
from Classes.Users import User


#!-------------------AUTOMATIC PLAYER---------------------#


class CustomPlayer(lavalink.DefaultPlayer):
    
    def __init__(self, guildID: int, node: lavalink.Node):
        super().__init__(guildID, node)
        self.history = []
        self.MAX_HISTORY = 20
        self.recommendations = []
        self.auto = False
        
        # Set default volume based on the server


    def generate_recommendations(self):
        pass
    
    
    def load_next(self):
        pass
    
    
    def start(self, user: User):
        self.auto = True
        pass
    
    
    async def play(self, track: lavalink.AudioTrack = None, start_time: int = 0, pause: bool = False, **kwargs):
        #if len(self.history) == self.MAX_HISTORY:
        #    self.history.pop(-1)
        #self.history.insert(0, {"track": track, "listenedAt": datetime.now()})
        await super().play(track, start_time, pause=pause, **kwargs)
        
    
    async def stop(self):
        if self.auto:
            self.auto = False
            self.recommendations.clear()
        await super().stop()