
#!-------------------------IMPORT MODULES--------------------#


import logging
import discord


#!--------------------CUSTOM VOICE PROTOCOL------------------#


class LavalinkVoiceClient(discord.VoiceClient):

    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        self.lavalink = client.lavalink
        self.logger = logging.getLogger("lavalink.voice")


    async def on_voice_server_update(self, data):
        
        #** Transform Server Data & Hand It Down To Lavalink Voice Update Handler **
        lavalink_data = {'t': 'VOICE_SERVER_UPDATE',
                         'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)
        
    
    async def on_voice_state_update(self, data):
        
        #** Transform Voice State Data & Hand It Down To Lavalink Voice Update Handler **
        lavalink_data = {'t': 'VOICE_STATE_UPDATE',
                         'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)


    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False):
        
        #** Change Voice State To Channel Passed Into Voice Protocol**
        self.logger.debug("Connected to voice channel '%s'", self.channel.id)
        await self.channel.guild.change_voice_state(channel=self.channel)
        

    async def disconnect(self, *, force: bool = False):

        #** Get Player & Change Voice Channel To None **
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        self.logger.debug("Disconnected from voice channel '%s'", self.channel.id)
        await self.channel.guild.change_voice_state(channel=None)
        
        #** Cleanup VoiceState & Player Attributes **
        player.channel_id = None
        self.cleanup()