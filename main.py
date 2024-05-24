
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import tomlkit
import logging
import discord
import asyncio
import logging.handlers
from common.logs import LoggingController
from clients.discord import CustomClient


#!-----------------------------SETUP FUNCTIONS-----------------------------!#
                    

def check_config(config: dict, logger: logging.Logger):
    
    # Check enviroment variables have values, and warn accordingly if not
    for variable, key in config['environment'].items():
        value = os.getenv(key, default=None)
        if value is None:
            if variable in ['spotify_secret', 'database_password', 'lavalink_password'] or (variable == 'bot_token' and config['development_mode'] is False):
                logger.critical(f'"{key}" is missing from environment variables! Please set this variable before continuing!')
                exit()
            elif variable == 'bot_token' and config['development_mode'] is True:
                logger.warning(f'"{key}" is missing from environment variables! The bot will not work outside of development mode. You can safely ignore this if you intend to use the bot for development only!')
            elif variable == 'dev_token' and config['development_mode'] is True:
                logger.critical(f"{key} is missing from environment variables! Please set this variable, or disable development mode before continuing!")
                exit()
            else:
                logger.warning(f'"{key}" is missing from environment variables! Some functionality may not work as a result.')


#!------------------------------MAIN FUNCTION------------------------------!#

  
async def main():
    
    # Load config.toml file
    try:
        with open("config.toml", "rb")  as configFile:
            config = tomlkit.load(configFile)
    except Exception as e:
        print(f"Failed to load config file! Error: {e}\nExiting...")
        exit()
        
    # Call helper class to configure logging setup for project
    try:
        controller = LoggingController()
        logger = controller.logger
    except:
        exit()
        
    # Check through config to see if anything is wrong before loading bot
    check_config(config, logger)
    
    # Get required intents for bot to function (must be enabled in Discord developer portal first)
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    
    # Instanciate MyClient class with requested intents and loaded config & establish bot connection to Discord
    async with CustomClient(intents=intents, config=config) as client:
        if not(config['development_mode']):
            await client.start(os.environ[config['environment']['bot_token']])
        else:
            await client.start(os.environ[config['environment']['dev_token']])
        
        
#!-----------------------------START ASYNCIO EVENT LOOP---------------------------!#

if __name__ == '__main__':
    asyncio.run(main())
