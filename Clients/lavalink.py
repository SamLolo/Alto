
#!--------------------------------IMPORT MODULES-----------------------------------# 


import discord
import logging
import lavalink
from Players.custom import CustomPlayer


#!--------------------------------LAVALINK CLIENT-----------------------------------# 


class CustomLavalinkClient(lavalink.Client):
    
    def __init__(self, user_id: int|str, discord: discord.Client, player: lavalink.player.DefaultPlayer = CustomPlayer, **kwargs):
        CustomPlayer.set_client(discord)
        super().__init__(user_id, player, **kwargs)
        
        self.discord = discord
        self.logger = logging.getLogger("lavalink.client")