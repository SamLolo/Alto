
#!--------------------IMPORT MODULES-----------------------#


import discord
import lavalink
from datetime import datetime
from Classes.Users import User
from Classes.Server import Server
from lavalink.events import TrackStartEvent, TrackEndEvent


#!-------------------AUTOMATIC PLAYER---------------------#


class CustomPlayer(lavalink.DefaultPlayer):
    discordClient = None
    
    @classmethod
    def set_client(cls, client: discord.client):
        cls.discordClient = client


    def __init__(self, guildID: int, node: lavalink.Node):
        super().__init__(guildID, node)
        self.history = []
        self.MAX_HISTORY = 20
        self.auto = False
        self.users = []
        
        # Set blank attributes to be used once the player has been initialised
        self.channel = None
        self.voice = None
        self.nowPlaying = None
        
        # Set default volume based on the server
        self.server = Server(self.discordClient, guildID, self)
        if self.server.volume["previous"] is not None:
            self.volume = self.server.volume["previous"]
        else:
            self.volume = self.server.volume["default"]
        self.last_volume = self.volume
        
    
    async def _handle_event(self, event: lavalink.Event):
        if isinstance(event, TrackStartEvent):
            await self.onTrackStart(event)
        elif isinstance(event, TrackEndEvent):
            await self.onTrackEnd(event)
        await super()._handle_event(event)
        
        
    async def onTrackStart(self, event: lavalink.Event):
        if len(self.history) == self.MAX_HISTORY:
            self.history.pop(-1)
        self.history.insert(0, {"track": event.track, "listenedAt": datetime.now()})
    
    
    async def onTrackEnd(self, event: lavalink.Event):
        pass


    def generate_recommendations(self):
        pass
    
    
    def load_next(self):
        pass
    
    
    async def start(self, user: User):
        self.auto = True
        pass
    
    
    async def set_volume(self, vol: int):
        self.last_volume = self.volume
        self.volume = vol
        await self.node.update_player(self._internal_id, volume=vol)
    
    
    async def play(self, track: lavalink.AudioTrack = None, start_time: int = 0, pause: bool = False, **kwargs):
        await super().play(track, start_time, pause=pause, **kwargs)
        
    
    async def stop(self):
        if self.auto:
            self.auto = False
            self.recommendations.clear()
        await super().stop()