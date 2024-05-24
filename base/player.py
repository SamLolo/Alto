
#!--------------------IMPORT MODULES-----------------------#


import logging
import discord
import lavalink
from datetime import datetime
from common.user import User
from common.server import Server
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
        self.users = {}
        self.logger = logging.getLogger("lavalink.player")
        
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
        # Add history entry upon start of track to internal player history array
        if len(self.history) == self.MAX_HISTORY:
            self.history.pop(-1)
        self.history.insert(0, {"track": event.track, "listenedAt": datetime.now()})
        
        # Send Now Playing Embed To Channel Where First Play Cmd Was Ran
        nowPlaying = self.client.format_nowplaying(self)
        message = await self.channel.send(embed=nowPlaying)

        # Clear previous now playing embed
        if self.nowPlaying is not None:
            await self.nowPlaying.delete()
        self.nowPlaying = message
    
    
    async def onTrackEnd(self, event: lavalink.Event):
        # Disable listening history system when database is unavailable as user's can't be loaded
        if self.client.database.connected:

            # Check current users are still listening, if not, save any changes to the database
            current = [member.id for member in self.voice.members if not(member.bot)]
            for discordID, user in self.users.items():
                if not(int(discordID) in current):
                    user.save()
                    self.users.pop(discordID)
                else:
                    current.remove(int(discordID))
            
            # Add any new users to the internal storage, creating new user class instance for that id
            for discordID in current:
                try:
                    self.users[str(discordID)] = self.client.userClass.User(self.client, id=discordID)
                except:
                    self.logger.debug("Exception whilst loading new user!")

            # If track has been cached, add it to the user's history if they're not deafened
            if event.track.extra['metadata']['cacheID'] is not None:
                for id, user in self.users:
                    if user.history_mode == 2 or (user.history_mode == 1 and event.track.requester == user.user.id):
                        member = self.server.guild.get_member(id)
                        if user.deafened and user.deafened == member.voice.deaf:
                            continue
                        elif user.deafened != member.voice.deaf:
                            user.deafened = member.voice.deaf
                        
                        # Get matching entry from players internal song history and add to user's history
                        for entry in self.history:
                            if (entry["track"].identifier == event.track.identifier) and (datetime.now() - entry['listenedAt']).total_seconds() >= 5:
                                user.addSongHistory(entry)
                                break


    def generate_recommendations(self):
        pass
    
    
    def load_next(self):
        pass
    
    
    async def start(self, user: User):
        self.auto = True
        pass
    
    
    async def set_volume(self, vol: int):
        # Set last volume level to be current volume level the overwrite it
        self.last_volume = self.volume
        self.volume = vol
        await self.node.update_player(self._internal_id, volume=vol)
        
    
    async def stop(self):
        if self.auto:
            self.auto = False
            self.recommendations.clear()
        await super().stop()