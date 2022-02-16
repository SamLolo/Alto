
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import asyncio
import discord
from datetime import datetime
from discord.utils import get
from discord.ext import commands
from Classes.Users import Users


#!--------------------------------STARTUP-----------------------------------# 


#** Startup Sequence **
print("--------------------------STARTING UP-------------------------")
print("Startup Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y")+"\n")


#!--------------------------------DISCORD BOT-----------------------------------# 


#** Load Config File **
with open('Config.json') as ConfigFile:
    Config = json.load(ConfigFile)
    ConfigFile.close()

#** Creating Bot Client **
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix = Config['Prefix'], 
                      case_insensitive=True, 
                      intents=intents,
                      help_command=None)

#** Setup Emojis **
Emojis = Config['Variables']['Emojis']
Emojis["True"] = "✅"
Emojis["False"] = "❌"


#!--------------------------------DISCORD EVENTS-----------------------------------# 


@client.event
async def on_ready():

    #** Make Sure Client Waits Until Fully Connected & Record Startup Time **
    print("Connection Established!")
    print("Preparing Internal Cache...")
    await client.wait_until_ready()
    client.startup = datetime.now()
    print("Bot Is Now Online & Ready!\n")


@client.event
async def on_guild_join(Guild):
    for Channel in Guild.channels:
        if isinstance(Channel, discord.channel.TextChannel):
            await Channel.send(Config['Welcome_Message'])
            break


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound) or ctx.command.qualified_name in ['reload']:
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
    elif isinstance(error, commands.BadArgument):
        Temp = await ctx.message.channel.send("**Oops, it seems that paramater is incorrect!**\nFor a full list of valid parameters, run `!help "+str(error)+"`")
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
        elif str(error) == "Spotify":
            Temp = await ctx.send("**Spotify Not Connected!**\nTo run this command, first run `!link`.")
        elif str(error) == "History":
            Temp = await ctx.send("**You must have listened to some songs before you can run this command!**\nJoin a Voice Channel and run `!play <song>` to get listening.")
        elif str(error) == "DM":
            Temp = await ctx.message.channel.send("**DM Failed!**\nPlease turn on `Allow Server Direct Messages` in Discord settings in order to link your account")
        else:
            Temp = await ctx.message.channel.send("You are not able to run this command!\n*If you believe this is an error, contact Lolo#6699.*")
        await asyncio.sleep(5)
        await ctx.message.delete()
        await Temp.delete()
        return
    else:
        raise error
    

#!--------------------------------COMMAND CHECKS-----------------------------------#


def is_admin():
    async def predicate(ctx):
        print("checking...")
        print(ctx.author.id)
        if ctx.author.id in [315237737538125836]:
            return True
        return False
    return commands.check(predicate)


#!--------------------------------DISCORD COMMANDS-----------------------------------# 


@client.command()
@is_admin()
async def reload(ctx, CogName):
    try:
        client.reload_extension("Cogs."+CogName.title())
        Temp = await ctx.send(CogName.title()+" Successfully Reloaded!")
    except:
        Temp = await ctx.send(CogName.title()+" Not Found!")
    await asyncio.sleep(5)
    await ctx.message.delete()
    await Temp.delete()


#!-------------------------------LOAD COGS-------------------------------#


#** Work Through List Of Active Cog Names In Config File, Loading Each One As You Go **
for Cog in Config['Active_Extensions']:
    client.load_extension(Cog)


#!--------------------------------DISCORD LOOP-----------------------------------# 

#** Connecting To Discord **    
print("---------------------CONNECTING TO DISCORD--------------------")
client.run(os.environ["MUSICA_TOKEN"])