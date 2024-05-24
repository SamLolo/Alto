
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import sys
import tomlkit
import logging
import logging.handlers
from copy import deepcopy
from zipfile import ZipFile


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
        elif record.name.startswith("mysql"):
            logFormat += self.colours['blue'] + " %(name)s"
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
    
    
#!--------------------LOGGING SETUP CLASS----------------------------#


class LoggingController():
    
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        
        # Load config file
        with open("config.toml", "rb")  as configFile:
            self.config = tomlkit.load(configFile)['logging']
        
        # Setup console handler so initial setup can be logged
        consoleHandle = logging.StreamHandler(sys.stdout)
        consoleHandle.setFormatter(ColouredFormat())
        consoleHandle.setLevel(logging.INFO)
        self.logger.addHandler(consoleHandle)
        self.logger.info("Code execution started!")
        self.logger.info("Loaded config file!")
        self.logger.info("Setting up logging...")
        
        # Set console logging level
        try:
            consoleHandle.setLevel(self.config['handlers']['console']['level'])
            self.logger.info(f"Console handler's level set to {self.config['handlers']['console']['level']} from config.")
        except KeyError:
            self.logger.warning("Console handler level config missing! Defaulting to 'logging.INFO'.")
        except:
            self.logging.error("Failed to set console handler level! Defaulting to 'logging.INFO'.")
              
        # Get logging directory and create if missing
        try:
            self.dir = self.config['directory']
        except KeyError:
            self.logger.warning("Log directory missing from config! Defaulting to './Logs'.")
            self.dir = "Logs"
            
        # Create log directory and backup folder if it's missing
        if not(self.dir in os.listdir("./")):
            os.mkdir(self.dir)
            self.logger.info(f"Creating new logging directory '{self.dir}'.")
        if not("Backups" in os.listdir(f"{self.dir}/")):
            os.mkdir(f"{self.dir}/Backups")
            
        # Backup previous log files
        try:
            self.backup_logs()
            self.logger.info("Successfully backed up previous session logs!")
        except Exception as ex:
            self.logger.critical("An error occured whilst backing up logs. Exiting to save data loss...")
            raise ex
        
        # Set minimum logging level to be used by all logging levels, adjusted in config
        try:
            self.logger.setLevel(self.config['minimum_level'])
            self.logger.info(f"Minimum logging level set to {self.config['minimum_level']}.")
        except:
            self.logger.error("Minimum logging level couldn't be set. Check it's been configured properly! Defaulting to 'logging.DEBUG'.")
            
        # Load additonal handlers
        for name, data in self.config['handlers'].items():
            enabled = data.pop('enabled', True)
            if enabled:
                if name != "console":
                    if 'type' in data.keys():
                        if "File" in data['type'] and not("filename" in data.keys()):
                            data['filename'] = name+".log"
                        args = deepcopy(data)
                        args.pop('type')
                        if 'level' in args.keys():
                            level = args.pop('level')
                        else:
                            level = logging.NOTSET
                            self.logger.warning(f"Level not specified in config for additional handler 'logging.handlers.{name}'.")
                        self.logger.info(f"Creating additonal logging handler: handlers.{name}")
                        self.createHandler(data['type'], 
                                           level,
                                           **args)
                        self.logger.info(f"Successfully created handler!")
                    else:
                        self.logger.error(f"Failed to create additonal handler 'logging.handlers.{name}' as type config is missing.")
            
        
    def backup_logs(self):
        # Get backup count from config
        try:
            backups = self.config['backups']
            if type(backups) is not int and backups < 0:
                raise TypeError
        except KeyError as ex:
            self.logger.critical("Failed to backup previous log files due to missing backup count.")
            raise ex
        except TypeError as ex:
            self.logger.critical(f"Failed to backup log files as the given backups count '{backups}' is invalid!")
            raise ex

        # Loop through backups folder in reverse order, incrementing each session record
        if "master.log" in os.listdir(f"{self.dir}/"):
            sortedFiles = sorted(os.listdir(f"{self.dir}/Backups"), key = lambda x: int(x.split(".")[1]) if x.split(".")[1].isdecimal() else 0, reverse=True)
            for file in sortedFiles:
                if file != "Session.zip":
                    count = int(file.split(".")[1])
                    if count >= backups:
                        os.remove(f"{self.dir}/Backups/{file}")
                    else:
                        os.rename(f"{self.dir}/Backups/{file}", f"{self.dir}/Backups/Session.{count+1}.zip")
            if "Session.zip" in f"{self.dir}/Backups/":
                os.rename(f"{self.dir}/Backups/Session.zip", f"{self.dir}/Backups/Session.1.zip")
            
            # Zip log files & move zip file into backups folder & delete previous log files
            with ZipFile(f"{self.dir}/Backups/Session.zip", 'w') as zip:
                for file in os.listdir(f"{self.dir}/"):
                    if file.endswith(".log"):
                        zip.write(f"{self.dir}/{file}")
                        os.remove(f"{self.dir}/{file}")
                        
                        
    def createHandler(self, type: str, level: str = logging.NOTSET, **kwargs):
        # Check specified handler class exists, else log error
        handlerClass = getattr(logging.handlers, type)
        if handlerClass is None:
            handlerClass = getattr(logging, type)
        if handlerClass is not None:
            
            # Load handler class with any key-word arguments passed into function, and set format and level.
            if "filename" in kwargs.keys():
                kwargs["filename"] = self.dir+"/"+kwargs["filename"]
            handler = handlerClass(**kwargs)
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%d-%m-%Y %H:%M:%S"))
            handler.setLevel(level)
            self.logger.addHandler(handler)
        else:
            self.logger.error(f"Failed to create new handler as type '{type}' isn't a valid logging.handlers class.")