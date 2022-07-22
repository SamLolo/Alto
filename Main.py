
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import json
import asyncio
import discord
from datetime import datetime
from discord.ext import commands


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


#{ Event Called Upon Bot Startup }
@client.event
async def on_ready():

    #** Make Sure Client Waits Until Fully Connected **
    print("Connection Established!")
    print("Preparing Internal Cache...")
    await client.wait_until_ready()
    
    #** Record Startup Time As Client Object & Print Bot Is Ready **
    client.startup = datetime.now()
    print("Bot Is Now Online & Ready!\n")


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
        Temp = await ctx.message.channel.send("**Command Not Found!**\nFor a full list of commands, run `!help`")
        await asyncio.sleep(10)
        await ctx.message.delete()
        await Temp.delete()
        return
    
    #** If Raised Error Is Missing Required Parameter: **
    elif isinstance(error, commands.MissingRequiredArgument):
        
        #** Send Error Message With Missing Parameter & Delete Input & Error Message After 10 Seconds **
        Temp = await ctx.message.channel.send("**Missing Parameter `"+str(error.param)+"`!**\nFor a full list of commands & their parameters, run `!help`")
        await asyncio.sleep(10)
        await ctx.message.delete()
        await Temp.delete()
        return
    
    #** If Raised Error Is Missing Required Parameter: **
    elif isinstance(error, commands.BadArgument):
        
        #** Send Error Message & Delete Input & Error Message After 10 Seconds **
        Temp = await ctx.message.channel.send("**Oops, it seems the argument you gave was invalid!**\nFor a full list of valid arguments, run `!help "+str(error)+"`")
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
            
        #** If Error Message Is "Spotify", Let User Know They Need To Connect Their Spotify**
        elif str(error) == "Spotify":
            Temp = await ctx.message.channel.send("**Spotify Not Connected!**\nTo run this command, first run `!link`.")
            
        #** If Error Message Is "History", Let User Know They Need To Get Some Listening History Before Running The Command **
        elif str(error) == "History":
            Temp = await ctx.message.channel.send("**You must have listened to some songs before you can run this command!**\nJoin a Voice Channel and run `!play <song>` to get listening.")

        #** If Error Message Is "SongNotFound", Let User Know They Need To Double Check Their Input **
        elif str(error) == "SongNotFound":
            Temp = await ctx.message.channel.send("**We couldn't find any tracks for the provided input!**\nPlease check your input and try again.")
        
        #** If Error Message Is "DM", Let User Know They Need To Join A VC **
        elif str(error) == "DM":
            Temp = await ctx.message.channel.send("**DM Failed!**\nPlease turn on `Allow Server Direct Messages` in Discord settings in order to link your account")

        #** Called When An Unexpected Error Occurs, Shouldn't Happen Very Often **
        elif str(error) == "UnexpectedError":
            Temp = await ctx.message.channel.send("**An Unexpected Error Occurred!**If this error persists, contact Lolo#6699.")
        
        #** If Error Message Is Not Above, Let User Know They Can't Run The Command & Try Retry **
        else:
            Temp = await ctx.message.channel.send("You are not able to run this command!\n*If you believe this is an error, contact Lolo#6699.*")
        
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


#!-------------------------------LOAD COGS-------------------------------#


#** Work Through List Of Active Cog Names In Config File, Loading Each One As You Go **
for Cog in Config['Active_Extensions']:
    client.load_extension(Cog)


#!--------------------------------DISCORD LOOP-----------------------------------# 

#** Connecting To Discord **    
print("---------------------CONNECTING TO DISCORD--------------------")
client.run(os.environ["ALTO_TOKEN"])