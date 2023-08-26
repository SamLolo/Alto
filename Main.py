
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import sys
import tomlkit
import logging
import discord
import asyncio
import logging.handlers
from zipfile import ZipFile
from discord.ext import commands


#!--------------------------------CUSTOM LOGGING FORMAT---------------------------------#


#** Create Custom Coloured Formatter **
class ColouredFormat(logging.Formatter):
    
    #** ANSI Escape Colours (https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit) + ANSI Reset String **
    colours = {'yellow': "\x1b[38;5;220m",
               'red': "\x1b[38;5;9m",
               'orange': "\x1b[38;5;202m",
               'blue': "\x1b[38;5;25m",
               'light_purple': "\x1b[38;5;63m",
               'green': "\x1b[38;5;2m",
               'light_green': "\x1b[38;5;76m",
               'light_blue': "\x1b[38;5;45m",
               'grey': "\x1b[38;5;240m",
               'light_orange': "\x1b[38;5;216m",
               "dark_red": "\x1b[38;5;124m"}
    reset = "\x1b[0m"

    #** Set Colours For Logging Levels **
    levelFormats = {logging.DEBUG:  colours['green'] + "[%(levelname)s]" + reset,
                    logging.INFO: colours['blue'] + "[%(levelname)s]" + reset,
                    logging.WARNING: colours['yellow'] + "[%(levelname)s]" + reset,
                    logging.ERROR: colours['orange'] + "[%(levelname)s]" + reset,
                    logging.CRITICAL: colours['red'] + "[%(levelname)s]" + reset}

    #** Create Format Based On Inputted Record **
    def format(self, record):
        logFormat = "%(asctime)s " + self.levelFormats.get(record.levelno)
        
        if record.name.startswith("discord") and not(record.name == "discord.errors"):
            logFormat += self.colours['light_purple'] + " %(name)s"
        elif record.name.startswith("spotify"):
            logFormat += self.colours['light_green'] + " %(name)s"
        elif record.name.startswith("lavalink"):
            logFormat += self.colours['light_blue'] + " %(name)s"
        elif record.name.startswith("database"):
            logFormat += self.colours['light_orange'] + " %(name)s"
        elif "error" in record.name:
            logFormat += self.colours['dark_red'] + " %(name)s"
        else:
            logFormat += self.colours['grey'] + " %(name)s"
            
        if record.levelno == logging.CRITICAL:
            logFormat += self.reset +": "+ self.colours['red'] +"%(message)s"+ self.reset
        else:
            logFormat += self.reset +": %(message)s"
        
        formatter = logging.Formatter(logFormat, datefmt="%d-%m-%Y %H:%M:%S")
        return formatter.format(record)


#!--------------------------------DISCORD CLIENT-----------------------------------# 


#** Creating Bot Client **
class MyClient(commands.Bot):
    def __init__(self, intents: discord.Intents, config: dict):
        
        #** Setup Client Logger & Config File **
        self.logger = logging.getLogger('discord')
        self.config = config

        #** Initialise Discord Client Class **
        super().__init__(intents=intents, 
                         command_prefix=config['prefix'],
                         case_insensitive = True,
                         help_command = None)


    #{ Setup Hook Called Before Bot Connects To Discord }
    async def setup_hook(self):
        #** Work Through List Of Active Cog Names In Config File, Loading Each One As You Go **
        for cog, enabled in self.config['extensions'].items():
            if enabled:
                await self.load_extension(f"Cogs.{cog.title()}")
                self.logger.info(f"Extension Loaded: {cog.title()}.py")
            
        #** Record Startup Time As Client Object **
        self.startup = discord.utils.utcnow()
        self.logger.info("Setup Complete!")


    #{ Event Called Upon Bot's Internal Cache Filled }
    async def on_ready(self):
        self.logger.info("Bot Is Now Ready!")
        

    #{ Event Called Upon Bot Connection To Discord Gateway }
    async def on_connect(self):
        self.logger.info("Connection established to Discord gateway!")
        

    #{ Event Called Upon Bot Disconnection From Discord Gateway }
    async def on_disconnect(self):
        self.logger.warning("Connection lost to Discord gateway!")


    #{ Event Called When Bot Joins New Guild/Server }
    async def on_guild_join(self, Guild):
        #** Loop Through Channels Until You Find The First Text Channel
        if self.config['welcome']['enabled']:
            for Channel in Guild.channels:
                if isinstance(Channel, discord.channel.TextChannel):
                    await Channel.send(self.config['welcome']['message'])
                    break


#!-----------------------------SETUP FUNCTIONS-----------------------------!#


def backup_logs(dir: str, backups: int):
    #** Get Log Directory From Config File & Create New Folder If Missing **
    if not(dir in os.listdir("./")):
        os.mkdir(dir)
        
    #** Create Backups Folder In Log Directory If Missing **
    if not("Backups" in os.listdir(f"{dir}/")):
        os.mkdir(f"{dir}/Backups")

    #** Loop Through Backups Folder In Reversed Order, incrementing each session record **
    if "master.log" in os.listdir(f"{dir}/"):
        sortedFiles = sorted(os.listdir(f"{dir}/Backups"), key = lambda x: int(x.split(".")[1]) if x.split(".")[1].isdecimal() else 0, reverse=True)
        for file in sortedFiles:
            if file != "Session.zip":
                count = int(file.split(".")[1])
                if count >= backups:
                    os.remove(f"{dir}/Backups/{file}")
                else:
                    os.rename(f"{dir}/Backups/{file}", f"{dir}/Backups/Session.{count+1}.zip")
        os.rename(f"{dir}/Backups/Session.zip", f"{dir}/Backups/Session.1.zip")
        
        #** Zip Log Files & Move Zip File Into Backups Folder & Delete Previous Log Files **
        with ZipFile(f"{dir}/Backups/Session.zip", 'w') as zip:
            for file in os.listdir(f"{dir}/"):
                if file.endswith(".log"):
                    zip.write(f"{dir}/{file}")
                    os.remove(f"{dir}/{file}")
                    

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
            elif variable == 'dev_token' and config['development_mode'] is False:
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
        
    # Call helper function to backup last session's logs
    logDir = config['logging']['directory']
    backups = config['logging']['backups']
    backup_logs(logDir, backups)

    # Get root logger & set default level from config
    logger = logging.getLogger()
    logger.setLevel(config['logging']['minimum_level'])

    # Setup master handler
    masterHandle = logging.handlers.RotatingFileHandler(
        filename=f'{logDir}/master.log',
        encoding='utf-8',
        maxBytes=8 * 1024 * 1024,
        backupCount=10)
    masterHandle.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%d-%m-%Y %H:%M:%S"))
    masterHandle.setLevel(config['logging']['levels']['master'])
    logger.addHandler(masterHandle)
    
    # Setup debug handler if enabled in config
    if config['logging']['handlers']['debug']:
        debugHandle = logging.handlers.RotatingFileHandler(
            filename=f'{logDir}/debug.log',
            encoding='utf-8',
            maxBytes=8 * 1024 * 1024,
            backupCount=10)
        debugHandle.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%d-%m-%Y %H:%M:%S"))
        debugHandle.setLevel(config['logging']['levels']['debug'])
        logger.addHandler(debugHandle)
        
    # Setup console output if enabled in config
    if config['logging']['handlers']['console']:
        consoleHandle = logging.StreamHandler(sys.stdout)
        consoleHandle.setFormatter(ColouredFormat())
        consoleHandle.setLevel(config['logging']['levels']['console'])
        logger.addHandler(consoleHandle)
        
    # Check through config to see if anything is wrong before loading bot
    logger.info("Loaded config.toml file")
    logger.info("Created master logging handler")
    for handler, enabled in config['logging']['handlers'].items():
        if enabled:
            logger.info(f"Added {handler} handler")
    check_config(config, logger)
    
    # Get required intents for bot to function (must be enabled in Discord developer portal first)
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    
    # Instanciate MyClient class with requested intents and loaded config & establish bot connection to Discord
    async with MyClient(intents=intents, config=config) as client:
        if not(config['development_mode']):
            await client.start(os.environ[config['environment']['bot_token']])
        else:
            await client.start(os.environ[config['environment']['dev_token']])
        
        
#!-----------------------------START ASYNCIO EVENT LOOP---------------------------!#

asyncio.run(main())
