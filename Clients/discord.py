
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import logging
import discord
from discord.ext import commands


#!--------------------------------DISCORD CLIENT-----------------------------------# 


class CustomClient(commands.Bot):
    
    def __init__(self, intents: discord.Intents, config: dict):
        self.logger = logging.getLogger('discord.client')
        self.config = config

        # Instanciate Discord bot client
        super().__init__(intents=intents, 
                         command_prefix=config['prefix'],
                         case_insensitive = True,
                         help_command = None)


    async def setup_hook(self):
        # Load each extension listed in the config file if set to enabled!
        for name, enabled in self.config['extensions'].items():
            if not(f"{name}.py" in os.listdir("./Extensions")):
                self.logger.error(f"Couldn't load extension '{name}' as it doesn't exist in the Extensions directory!")
            elif enabled:
                await self.load_extension(f"Extensions.{name}")
                self.logger.info(f"Loading extension: {name}.py")
            elif not enabled and name in ['errorHandler', 'pagination']:
                self.logger.warning(f"Extension '{name}' is set to disabled in config.toml! This is likely to cause unexpected behaviour!")
            
        # Record startup time as client attrribute
        self.startup = discord.utils.utcnow()
        self.logger.info("Setup Complete!")


    async def on_ready(self):
        self.logger.info("Bot Is Now Ready!")
        

    async def on_connect(self):
        self.logger.info("Connection established to Discord gateway!")
        

    async def on_disconnect(self):
        self.logger.warning("Connection lost to Discord gateway!")


    async def on_guild_join(self, guild: discord.Guild):
        # Send welcome message from config to first text channel in new server if enabled
        if self.config['welcome']['enabled']:
            for Channel in guild.channels:
                if isinstance(Channel, discord.channel.TextChannel):
                    await Channel.send(self.config['welcome']['message'])
                    break
                
    
    def get_emoji(self, name: str):
        # Return unicode tick/cross if name is boolean value
        if name == True:
            return "✅"
        elif name == False:
            return "❌"
        
        # Search through sequence of client emojis and return found emoji object
        for emoji in self.client.emojis:
            if emoji.name == name:
                return emoji