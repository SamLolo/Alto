
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import sys
import json
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
    def __init__(self, intents: discord.Intents, config):
        
        #** Setup Client Logger & Config File **
        self.logger = logging.getLogger('discord')
        self.config = config

        #** Initialise Discord Client Class **
        super().__init__(intents=intents, 
                         command_prefix=self.config['Prefix'],
                         case_insensitive = True,
                         help_command = None)


    #{ Setup Hook Called Before Bot Connects To Discord }
    async def setup_hook(self):
        #** Work Through List Of Active Cog Names In Config File, Loading Each One As You Go **
        for Cog in self.config['Active_Extensions']:
            await self.load_extension(Cog)
            self.logger.info(f"Extension Loaded: {Cog}")
            
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
        if self.config['Welcome']['enabled']:
            for Channel in Guild.channels:
                if isinstance(Channel, discord.channel.TextChannel):
                    await Channel.send(self.config['Welcome']['message'])
                    break
            

#! -------------------------------MAIN FUNCTION-------------------------------!#

  
async def main():
    
    #** Load Config File **
    with open('config.json') as ConfigFile:
        config = json.load(ConfigFile)
        ConfigFile.close()
    
    #** Get Log Directory From Config File & Create New Folder If Missing **
    logDir = config['logging']['directory']
    if not(logDir in os.listdir("./")):
        os.mkdir(logDir)
        
    #** Create Backups Folder In Log Directory If Missing **
    if not("Backups" in os.listdir(f"{logDir}/")):
        os.mkdir(f"{logDir}/Backups")

    #** Loop Through Backups Folder In Reversed Order **
    if "master.log" in os.listdir(f"{logDir}/"):
        sortedFiles = sorted(os.listdir(f"{logDir}/Backups"), key = lambda x: int(x.split(".")[1]) if x.split(".")[1].isdecimal() else 0, reverse=True)
        for file in sortedFiles:

            #** If File Has A Number In It, Split Name To Get Number ***
            if str(file) != "Session.zip":
                number = str(file).split(".")[1]
                
                #** If Number > OR = To Max Log Count, Delete File **
                if int(number) >= config['logging']['backups']:
                    os.remove(f"{logDir}/Backups/{file}")
                
                #** If Number Valid, Increase Number Of Log File **
                else:
                    os.rename(f"{logDir}/Backups/{file}", f"{logDir}/Backups/Session.{int(number)+1}.zip")
        os.rename(f"{logDir}/Backups/Session.zip", f"{logDir}/Backups/Session.1.zip")
        
        #** Zip Log Files & Move Zip File Into Backups Folder & Delete Previous Log Files **
        with ZipFile(f"{logDir}/Backups/Session.zip", 'w') as zipFile:
            for file in os.listdir(f"{logDir}/"):
                if file.endswith(".log"):
                    zipFile.write(f"{logDir}/"+file)
                    os.remove(f"{logDir}/"+file)

    #** Get Root Logger & Set Default Level From Config File **
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    #** Setup Handlers **
    masterHandle = logging.handlers.RotatingFileHandler(
        filename=f'{logDir}/master.log',
        encoding='utf-8',
        maxBytes=8 * 1024 * 1024,
        backupCount=10)
    debugHandle = logging.handlers.RotatingFileHandler(
        filename=f'{logDir}/debug.log',
        encoding='utf-8',
        maxBytes=8 * 1024 * 1024,
        backupCount=10)
    consoleHandle = logging.StreamHandler(sys.stdout)
        
    #** Set Formatters For Each Handler **
    masterHandle.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%d-%m-%Y %H:%M:%S"))
    debugHandle.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%d-%m-%Y %H:%M:%S"))
    consoleHandle.setFormatter(ColouredFormat())

    #** Set Level Of Handlers From Config File **
    masterHandle.setLevel(config['logging']['levels']['masterFile'])
    debugHandle.setLevel(config['logging']['levels']['debugFile'])
    consoleHandle.setLevel(config['logging']['levels']['console'])
    
    #** Add Handlers To Logger **
    logger.addHandler(masterHandle)
    logger.addHandler(debugHandle)
    logger.addHandler(consoleHandle)
    
    #** Log Code Start & Config File Load **
    logger.info("Code Started!")
    logger.info("Loaded Config File")
    
    #** Get Required Intents For Bot **
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    
    #** Instanciate My Client Class & Connect Bot To Discord **
    async with MyClient(intents=intents, config=config) as client: 
        await client.start(os.environ["ALTO_TOKEN"])
        
        
#!-----------------------------START ASYNCIO EVENT LOOP---------------------------!#

asyncio.run(main())
