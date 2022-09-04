
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import sys
import json
import asyncio
import logging
import discord
import importlib
import logging.handlers
from zipfile import ZipFile
from datetime import datetime
from discord.ext import commands


#!-------------------------------IMPORT CLASSES--------------------------------#


import Classes.Users
import Classes.Utils
import Classes.Database
import Classes.Music


#!--------------------------------CUSTOM LOGGING FORMAT---------------------------------#


#** Create Custom Coloured Formatter hello sam
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
               'light_orange': "\x1b[38;5;216m"}
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
        
        if record.name.startswith("discord"):
            logFormat += self.colours['light_purple'] + " %(name)s"+ self.reset +": %(message)s"
        elif record.name.startswith("spotify"):
            logFormat += self.colours['light_green'] + " %(name)s"+ self.reset +": %(message)s"
        elif record.name.startswith("lavalink"):
            logFormat += self.colours['light_blue'] + " %(name)s"+ self.reset +": %(message)s"
        elif record.name.startswith("database"):
            logFormat += self.colours['light_orange'] + " %(name)s"+ self.reset +": %(message)s"
        else:
            logFormat += self.colours['grey'] + " %(name)s"+ self.reset +": %(message)s"
        
        formatter = logging.Formatter(logFormat, datefmt="%d-%m-%Y %H:%M:%S")
        return formatter.format(record)
    
    
#** Create Logs & Backup Folders Either Are Missing **
if not("Logs" in os.listdir("./")):
    os.mkdir("Logs")
if not("Backups" in os.listdir("Logs/")):
    os.mkdir("Logs/Backups")

#** Get Time Of Last Session Startup From Master File **
if "master.log" in os.listdir("Logs/"):
    with open("Logs/master.log", 'r') as File:
        timestamp  = File.readline().replace(":", ".").split(" ")
        
    #** Zip Log Files & Move Zip File Into Backups Folder **
    with ZipFile("Logs/Backups/Session ("+" ".join(timestamp[0:2])+").zip", 'w') as zipFile:
        for file in os.listdir("Logs/"):
            if file.endswith(".log"):
                zipFile.write("Logs/"+file)

#** Setup Logging **
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#** Setup Handlers **
masterHandle = logging.handlers.RotatingFileHandler(
    filename='Logs/master.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=10)
debugHandle = logging.handlers.RotatingFileHandler(
    filename='Logs/debug.log',
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=10)
consoleHandle = logging.StreamHandler(sys.stdout)
    
#** Set Formatters **
masterHandle.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%d-%m-%Y %H:%M:%S"))
debugHandle.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%d-%m-%Y %H:%M:%S"))
consoleHandle.setFormatter(ColouredFormat())

#** Add Handlers & Log Code Start **
debugHandle.setLevel(logging.DEBUG)
logger.addHandler(masterHandle)
logger.addHandler(consoleHandle)
logger.addHandler(debugHandle)
logger.info("Code Started!")


#!--------------------------------DISCORD CLIENT-----------------------------------# 


#** Creating Bot Client **
class MyClient(commands.Bot):
    
    def __init__(self, intents: discord.Intents):
        #** Setup Client Logger **
        self.logger = logging.getLogger('discord')
        
        #** Load Config File **
        with open('Config.json') as ConfigFile:
            self.config = json.load(ConfigFile)
            logger.info("Loaded Config File")
            ConfigFile.close()
        
        #** Initialise Discord Client Class **
        super().__init__(intents=intents, 
                         command_prefix=self.config['Prefix'],
                         case_insensitive = True,
                         help_command = None)


    #{ Setup Hook Called When Bot Before It Connects To Discord }
    async def setup_hook(self):
        #** Work Through List Of Active Cog Names In Config File, Loading Each One As You Go **
        for Cog in self.config['Active_Extensions']:
            await self.load_extension(Cog)
            self.logger.info(f"Extension Loaded: {Cog}")


    #{ Event Called Upon Bot Connection To Discord Gateway }
    async def on_ready(self):

        #** Make Sure Client Waits Until Fully Connected **
        self.logger.info("Waiting until ready...")
        await self.wait_until_ready()
        
        #** Record Startup Time As Client Object & Print Bot Is Ready **
        self.startup = datetime.now()
        self.logger.info("Bot Is Now Online & Ready!")

  
    #{ Event Called When Bot Joins New Guild/Server }
    async def on_guild_join(self, Guild):
        #** Loop Through Channels Until 
        for Channel in Guild.channels:
            if isinstance(Channel, discord.channel.TextChannel):
                await Channel.send(self.config['Welcome_Message'])
                break
            

#** Instanciate Bot Client Class **
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = MyClient(intents=intents)

#** Instanciate Classes **
client.database = Classes.Database.UserData()
client.music = Classes.Music.SongData()
client.utils = Classes.Utils.Utility(client)
client.userClass = Classes.Users


#!--------------------------------DISCORD EVENTS-----------------------------------# 


#{ Event Called When Discord Error Occurs During Code Execution }
@client.event
async def on_command_error(ctx, error):
    
    #** If Raised Error Is Command Not Found, Or Command Is Hidden Command: **
    if isinstance(error, commands.CommandNotFound) or ctx.command.qualified_name in ['reload']:
        
        #** Send Error Message, & Delete Input & Error Message After 10 Seconds **
        Temp = await ctx.message.channel.send("**Command Not Found!**\nFor a full list of commands, type `/help`")
        await asyncio.sleep(10)
        await ctx.message.delete()
        await Temp.delete()
        return
    
    #** If Raised Error Is Missing Required Parameter: **
    elif isinstance(error, commands.MissingRequiredArgument):
        
        #** Send Error Message With Missing Parameter & Delete Input & Error Message After 10 Seconds **
        Temp = await ctx.message.channel.send("**Missing Parameter `"+str(error.param)+"`!**\nFor a full list of commands & their parameters, type `/help`")
        await asyncio.sleep(10)
        await ctx.message.delete()
        await Temp.delete()
        return
    
    #** If Raised Error Is Missing Required Parameter: **
    elif isinstance(error, commands.BadArgument):
        
        #** Send Error Message & Delete Input & Error Message After 10 Seconds **
        Temp = await ctx.message.channel.send("**Oops, it seems the argument you gave was invalid!**\nFor a full list of valid arguments, type `/help "+str(error)+"`")
        await asyncio.sleep(10)
        await ctx.message.delete()
        await Temp.delete()
        return
    
    #** If Raised Error Is Check Failure: **
    elif isinstance(error, commands.CheckFailure):
        
        #** If Error Message Is "UserVoice", Let User Know They Need To Join A VC **
        if str(error) == "UserVoice":
            Temp = await ctx.message.channel.send("To use this command, please join a Voice Channel!")
            
        #** If Error Message Is "BotVoice", Let User Know The Bot Isn't In A VC **
        elif str(error) == "BotVoice":
            Temp = await ctx.message.channel.send("I'm Not Currently Connected!")
            
        #** If Error Message Is "SameVoice", Let User Know They Need To Join A VC With The Bot **
        elif str(error) == "SameVoice":
            Temp = await ctx.message.channel.send("You must be in my Voice Channel to use this!")
            
        #** If Error Message Is "NotPlaying", Let User Know Bot Isn't Currently Playing **
        elif str(error) == "NotPlaying":
            Temp = await ctx.message.channel.send("I'm Not Currently Playing Anything!")
            
        #** If Error Message Is "History", Let User Know They Need To Get Some Listening History Before Running The Command **
        elif str(error) == "History":
            Temp = await ctx.message.channel.send("**You must have listened to some songs before you can run this command!**\nJoin a Voice Channel and type `/play <song>` to get listening.")

        #** If Error Message Is "SongNotFound", Let User Know They Need To Double Check Their Input **
        elif str(error) == "SongNotFound":
            Temp = await ctx.message.channel.send("**We couldn't find any tracks for the provided input!**\nPlease check your input and try again.")
        
        #** If Error Message Is "DM", Let User Know They Need To Join A VC **
        elif str(error) == "DM":
            Temp = await ctx.message.channel.send("**DM Failed!**\nPlease turn on `Allow Server Direct Messages` in Discord settings!")

        #** Called When An Unexpected Error Occurs, Shouldn't Happen Very Often **
        elif str(error) == "UnexpectedError":
            Temp = await ctx.message.channel.send("**An Unexpected Error Occurred!**If this error persists, open a ticket in our Discord server:* `/discord`.")
        
        #** If Error Message Is Not Above, Let User Know They Can't Run The Command & Try Retry **
        else:
            Temp = await ctx.message.channel.send("You are not able to run this command!\n*If you believe this is an error, open a ticket in our Discord server:* `/discord`.")
        
        #** Delete Input & Error Message After 10 Seconds **
        await asyncio.sleep(10)
        await ctx.message.delete()
        await Temp.delete()
        return
    
    #** If Error Isn't Caught, Raise Error To Stop Code Execution **
    else:
        raise error
    

#!--------------------------------COMMAND CHECKS-----------------------------------#


#{ Check Function To See If User ID Is Bot Admin }
def is_admin():
    
    #** When Called, Check If User Id In List & If So Return True **
    async def predicate(ctx):
        if ctx.author.id in [315237737538125836, 233641884801695744]:
            return True
        return False
    return commands.check(predicate)


#!--------------------------------DISCORD COMMANDS-----------------------------------# 


@client.command(hidden=True)
@is_admin()
async def reload(ctx, input):
    
    #** If Passed Name Is A Class, Use Importlib To Reload File **
    if input.lower() in ['music', 'database', 'users', 'utils']:      
        try:   
            #** Re-add Attribute To Client Class **
            if input.lower() == "database":
                importlib.reload(Classes.Database)
                client.database = Classes.Database.UserData()
            elif input.lower() == "music":
                importlib.reload(Classes.Music)
                client.music = Classes.Music.SongData()
            elif input.lower() == "utils":
                importlib.reload(Classes.Utils)
                client.utils = Classes.Utils.Utility(client)
            else:
                importlib.reload(Classes.Users)
                client.userClass = Classes.Users

        except Exception as e:
            #** Return Error To User **
            await ctx.send(f"**An Error Occured Whilst Trying To Reload The {input.title()} Class!**\n```{e}```")
            return
    
    #** If Input Is 'Config', reload Config File **
    elif input.lower() == "config":  
        try:
            #** ReLoad Config File **
            with open('Config.json') as ConfigFile:
                client.config = json.load(ConfigFile)
                logger.info("Loaded Config File")
                ConfigFile.close()

        except Exception as e:
            #** Return Error To User **
            await ctx.send(f"**An Error Occured Whilst Trying To Reload The Config File!**\n```{e}```")
            return
        
    #** If Input Not Config Or Class, Try To Reload Cog Under Name **
    else:
        
        try:
            #** ReLoad Specified Cog **
            await client.reload_extension("Cogs."+input.title())

        except Exception as e:
            #** Return Error To User **
            await ctx.send(f"**An Error Occured Whilst Trying To Reload {input.title()} Cog!**\n```{e}```")
            return
        
    #** Send Confirmation Message **
    await ctx.send(f"**Sucessfully Reloaded:** `{input.title()}`!")
    

@client.command(hidden=True)
@is_admin()
async def sync(ctx, *args):
    
    #** If Input is Blank, Sync Application Commands To Current Guild **
    if not(args):
        args = ["Current Server"]
        client.tree.copy_global_to(guild=ctx.guild)
    
    #** If Input = Global, Send Warning Message **
    elif args[0].lower() == "global":
        warning = await ctx.send("**Warning! Syncing Globally Will Make The Changes Available To __All Servers__!**\n*Are You Sure You Want To Continue?*")
        
        #** Add Reactions **
        await warning.add_reaction(client.emojis["True"])
        await warning.add_reaction(client.emojis["False"])
        
        def ReactionAdd(Reaction):
            return (Reaction.message_id == warning.id) and (Reaction.user_id != client.user.id)

        #** Wait For User To React To Tick & Stop Function Execution When Reacting With No **
        while True:
            Reaction = await client.wait_for("raw_reaction_add", check=ReactionAdd)
            if Reaction.event_type == 'REACTION_ADD':
                if str(Reaction.emoji) == client.emojis['False']:
                    await warning.delete()
                    temp = await ctx.send("Cancelled Command Sync Operation!")
                    await asyncio.sleep(10)
                    await ctx.message.delete()
                    await temp.delete()
                    return
                elif str(Reaction.emoji) == client.emojis['True']:
                    await warning.delete()
                    break
    
    #** If Input is Integer, Check If Guild ID, & Sync To That Guild
    elif args[0].isdecimal():
        guild = client.get_guild(int(args[0]))
        if guild is None:
            raise commands.BadArgument()
        client.tree.copy_global_to(guild=guild)
    
    #** If Invalid Argument Supplied, Raise Error
    else:
        raise commands.BadArgument()
    
    #** Carry Out Sync **
    await client.tree.sync()
        
    #** Send Confirmation Message If Sucessfull **
    temp = await ctx.send(f"Sucessfully Synced Application Commands!\nScope: `{str(args[0])}`")


#!--------------------------------DISCORD LOOP-----------------------------------# 


#** Connecting To Discord **    
client.run(os.environ["DEV_TOKEN"], log_handler=None)