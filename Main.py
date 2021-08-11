
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import string
import random
import asyncio
import discord
import mysql.connector
from datetime import datetime
from discord.utils import get
from discord.ext import commands


#!--------------------------------DATABASE CONNECTION-----------------------------------# 


#** Startup Sequence **
print("-----------------------STARTING UP----------------------")
print("Startup Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))

#** Get Connection Details **
Host = os.environ["DATABASE_HOST"]
User = os.environ["DATABASE_USER"]
Password = os.environ["DATABASE_PASS"]

#** Connect To Database **
connection = mysql.connector.connect(host = Host,
                                     database = "Melody",
                                     user = User,
                                     password = Password)

#** Setup Cursor and Output Successful Connection **                  
if connection.is_connected():
    cursor = connection.cursor()
    cursor.execute("SELECT database();")
    Record = cursor.fetchone()
    print("Connected To Database: "+Record[0].title()+"\n")

#** Delete Connection Details **
del Host
del User
del Password


#!-------------------------------FETCH CLASSES-----------------------------#


from Classes.Youtube import YoutubeAPI
from Classes.SpotifyUser import SpotifyUser
from Classes.Database import UserData
from Classes.Music import Music

Youtube = YoutubeAPI()
Database = UserData(cursor, connection)
SongData = Music()


#!--------------------------------DISCORD BOT-----------------------------------# 


#** Load Config File **
with open('Config.json') as ConfigFile:
    Config = json.load(ConfigFile)
    ConfigFile.close()

#** Creating Bot Client **
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix = Config['Prefix'], case_insensitive=True, intents=intents)


#!--------------------------------DISCORD EVENTS-----------------------------------# 


@client.event
async def on_ready():
    print("Connection Established!")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=" Beta V1.03"))
    print("Preparing Internal Cache...")
    await client.wait_until_ready()
    print("Bot Is Now Online & Ready!\n")

    #** Setup Emojis **
    self.Emojis = Config['Variables']['Emojis']
    self.Emojis["True"] = "✅"
    self.Emojis["False"] = "❌"


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        Temp = await ctx.message.channel.send("**Command Not Found!**\nFor a full list of commands, run `!help`")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        Temp = await ctx.message.channel.send("**Missing Paramater `"+str(error.param)+"`!**\nFor a full list of commands & their parameters, run `!help`")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()
        return
    elif isinstance(error, commands.CheckFailure):
        print(error)
        if str(error) == "UserVoice":
            Temp = await ctx.message.channel.send("To use this command, please join a Voice Channel!")
        elif str(error) == "BotVoice":
            Temp = await ctx.message.channel.send("I'm Not Currently Connected!")
        elif str(error) == "SameVoice":
            Temp = await ctx.message.channel.send("You must be in my Voice Channel to use this!")
        elif str(error) == "NotPlaying":
            Temp = await ctx.message.channel.send("I'm Not Currently Playing Anything!")
        else:
            raise error
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()
        return
    else:
        raise error


#!--------------------------------DISCORD COMMANDS-----------------------------------# 


@client.command()
async def reload(ctx, CogName):
    client.reload_extension("Cogs."+CogName)
    await ctx.message.delete()


#!-------------------------------LOAD COGS-------------------------------#


for Cog in Config['Active_Extensions']:
    client.load_extension(Cog)


#!--------------------------------DISCORD LOOP-----------------------------------# 

#** Connecting To Discord **    
print("--------------------CONNECTING TO DISCORD--------------------")
client.run(os.environ["MUSICA_TOKEN"])