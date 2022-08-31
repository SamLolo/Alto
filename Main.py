
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import sys
import json
import shutil
import asyncio
import logging
import discord
import logging.handlers
from datetime import datetime
from discord.ext import commands


#!--------------------------------SETUP LOGGING---------------------------------#

#** Save Previous Session Logs To Zip **
with open("Logs/master.log", 'r') as File:
    timestamp  = File.readline().replace(":", ".").split(" ")
os.mkdir("Logs/Session ("+" ".join(timestamp[0:2])+")")
files = os.listdir("Logs/")
print(files)
for name in files[2]:
    if name.endswith(".log"):
        print(name)
        shutil.move("Logs/"+name, "Logs/Session ("+" ".join(timestamp[0:2])+")/"+name)

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


#!--------------------------------DISCORD BOT-----------------------------------# 


#** Load Config File **
with open('Config.json') as ConfigFile:
    Config = json.load(ConfigFile)
    ConfigFile.close()

#** Creating Bot Client **
class MyClient(commands.Bot):
    
    def __init__(self, *args, intents: discord.Intents, **kwargs):
        #** Initialise Discord Client Class **
        super().__init__(*args, intents=intents, **kwargs)

    async def setup_hook(self):
        #** Work Through List Of Active Cog Names In Config File, Loading Each One As You Go **
        for Cog in Config['Active_Extensions']:
            await self.load_extension(Cog)

#** Instanciate Bot Client Class **
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
client = MyClient(command_prefix = Config['Prefix'], 
                  case_insensitive=True, 
                  intents=intents,
                  help_command=None)
client.logger = logging.getLogger('discord')

#** Setup Emojis **
Emojis = Config['Variables']['Emojis']
Emojis["True"] = "✅"
Emojis["False"] = "❌"


#!--------------------------------DISCORD EVENTS-----------------------------------# 


#{ Event Called Upon Bot Startup }
@client.event
async def on_ready():

    #** Make Sure Client Waits Until Fully Connected **
    client.logger.info("Waiting until ready...")
    await client.wait_until_ready()
    
    #** Record Startup Time As Client Object & Print Bot Is Ready **
    client.startup = datetime.now()
    client.logger.info("Bot Is Now Online & Ready!")


#{ Event Called When Bot Joins New Guild/Server }
@client.event
async def on_guild_join(Guild):
    for Channel in Guild.channels:
        if isinstance(Channel, discord.channel.TextChannel):
            await Channel.send(Config['Welcome_Message'])
            break


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
        if ctx.author.id in [315237737538125836]:
            return True
        return False
    return commands.check(predicate)


#!--------------------------------DISCORD COMMANDS-----------------------------------# 


@client.command(hidden=True)
@is_admin()
async def reload(ctx, CogName):
    
    #** Dictionary Describing What Needs To Be Reloaded For Each Class **
    Classes = {'musicutils': ['users', 'Cogs.Account', 'Cogs.Music'], 
               'database': ['users', 'Cogs.Account', 'Cogs.Background', 'Cogs.Music'],
               'users': ['Cogs.Account', 'Cogs.Music'],
               'utils': ['Cogs.Account', 'Cogs.Music']}
    
    #** If Passed Name Is A Class, Get Requirements From Dictionary **
    if CogName.lower() in Classes.keys():
        ToReload = Classes[CogName.lower()]
        
        #** Check If Any Requirements Are Other Classes, And Those Extra Requirements **
        for cog in ToReload:
            if not(cog.startswith('Cogs.')):
                Extra = Classes[cog]
                ToReload.remove(cog)
                
                #** For Each Extra Requirement, If Not Already Being Reloaded Add To List **
                for extracog in Extra:
                    if not(extracog in ToReload):
                        ToReload.append(extracog)
        
        #** Create Initial Class Reloading Message & Send To User **
        Message = "**Reloading Class: "+CogName.title()+"**\n-------------------------\n"
        Temp = await ctx.send(Message)
        
    #** If Just One Cog, Create Single Cog List & Let User One Just One Cog Is being Reloaded **
    else:
        ToReload = ["Cogs."+CogName.title()]
        Message = "**Reloading Cog: "+CogName.title()+"**\n-------------------------\n"
        Temp = await ctx.send(Message)
        
    #** Loop Through Each Cog In Reload List, Waiting 1 Second Each Time & Keeping Track Of Errors **
    Error = False
    for cog in ToReload:
        await asyncio.sleep(1)
        
        #** Attempt To Reload Cog & Edit Message To User If Successful **
        try:
            client.reload_extension(cog)
            Message += "*"+cog+" Successfully Reloaded*\n"
            await Temp.edit(content=Message)
            
        #** If Reload Fails, Set Error To True & Break For Loop, Letting User Know Which Cog Failed To Load **
        except:
            Message += "*"+cog+" Failed To Load*\n"
            await Temp.edit(content=Message)
            Error = True
            break
        
    #** If Error, Let User Know Else Add Reload Complete To Message **
    if Error:
        Message += "**Reload Failed Due To An Error Occuring During The Reloading Process!**"
    else:
        Message += "**Reload Completed!**"
    
    #** Edit Message To New Completed Message, & Delete Both Messages After 10 Second Wait **
    await Temp.edit(content=Message)
    await asyncio.sleep(10)
    await ctx.message.delete()
    await Temp.delete()


#!--------------------------------DISCORD LOOP-----------------------------------# 

#** Connecting To Discord **    
client.run(os.environ["DEV_TOKEN"], log_handler=None)