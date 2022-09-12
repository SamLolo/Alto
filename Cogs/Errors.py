
#!---------------------------IMPORT MODULES-----------------------#


import discord
import logging
import traceback
from discord.ext import commands
from discord import app_commands


#!--------------------------BACKGROUND CLASS------------------------#


class ErrorHandler(commands.Cog):

    def __init__(self, client: discord.Client):

        #** Assign Class Objects **
        self.client = client
        self.logger = logging.getLogger("discord.errors")
        
        #** Set The Error Handler **
        client.tree.on_error = self.on_app_command_error
        
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        
        print(error)
        print(type(error))
        print(error.__dict__)
        
        #{ General Uncaught Error During Command Execution }#
        if isinstance(error, (app_commands.CommandInvokeError, app_commands.TranslationError)):
            self.logger.error(f'Unexpected Error "{error.original}" During Command "{error.command.name}"')
            traceback.print_exception(error.original)
            await interaction.response.send_message("An unexpected error occured whilst processing your request!", ephemeral=True)
        
        #{ Check Failure Error Raised By Check Or Manually By Code }#
        elif isinstance(error, app_commands.CheckFailure):
            
            #** If Error Message Is "UserVoice", Let User Know They Need To Join A VC **
            if str(error) == "UserVoice":
                await interaction.response.send_message("To use this command, please join a Voice Channel!", ephemeral=True)
                
            #** If Error Message Is "BotVoice", Let User Know The Bot Isn't In A VC **
            elif str(error) == "BotVoice":
                await interaction.response.send_message("I'm Not Currently Connected!")
                
            #** If Error Message Is "SameVoice", Let User Know They Need To Join A VC With The Bot **
            elif str(error) == "SameVoice":
                await interaction.response.send_message("You must be in my Voice Channel to use this!", ephemeral=True)
                
            #** If Error Message Is "NotPlaying", Let User Know Bot Isn't Currently Playing **
            elif str(error) == "NotPlaying":
                await interaction.response.send_message("I'm Not Currently Playing Anything!")
                
            #** If Error Message Is "History", Let User Know They Need To Get Some Listening History Before Running The Command **
            elif str(error) == "History":
                await interaction.response.send_message("**You must have listened to some songs before you can run this command!**\nJoin a Voice Channel and type `/play` to get listening.", ephemeral=True)

            #** If Error Message Is "SongNotFound", Let User Know They Need To Double Check Their Input **
            elif str(error) == "SongNotFound":
                await interaction.response.send_message("**We couldn't find any tracks for the provided input!**\nPlease check your input and try again.", ephemeral=True)
            
            #** If Error Message Is "DM", Let User Know They Need To Join A VC **
            elif str(error) == "DM":
                await interaction.response.send_message("**DM Failed!**\nPlease turn on `Allow Server Direct Messages` in Discord settings!", ephemeral=True)
                
            #** If Error Message Is "BadArgument", Direct User To Help Command For That Command **
            elif str(error) == "BadArgument":
                await interaction.response.send_message(f"**Oops, it seems the argument you gave was invalid!**\nFor a full list of valid arguments, type `/help {error}`", ephemeral=True)

            #** Called When An Unexpected Error Occurs, Shouldn't Happen Very Often **
            elif str(error) == "UnexpectedError":
                await interaction.response.send_message("**An Unexpected Error Occurred!**If this error persists, open a ticket in our Discord server:* `/discord`.", ephemeral=True)
            
            #** If Error Message Is Not Above, Let User Know They Can't Run The Command & Try Retry **
            else:
                self.logger.warning(f"Unknown Check Failure: {error}")
                await interaction.response.send_message("You are not able to run this command!\n*If you believe this is an error, open a ticket in our Discord server:* `/discord`.", ephemeral=True)
            
        #{ Error When User Tries To Run Command That Doesn't Exist }
        elif isinstance(error, app_commands.CommandNotFound):
            await interaction.response.send_message("**Command Not Found!**\nFor a full list of commands, type `/help`", ephemeral=True)
            
        #{ Errror When Bot Tries To Perform Action But Is Missing Permissions }
        elif isinstance(error, app_commands.BotMissingPermissions):
            await interaction.response.send_message(f"**To use this command, please ask a server own to give me the following permissions:**\n`{', '.join(error.missing_permissions)}`", ephemeral=True)
        


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(ErrorHandler(client))