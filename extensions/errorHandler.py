
#!---------------------------IMPORT MODULES-----------------------#


import json
import discord
import logging
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
        
        #** Load Error Messages **
        with open('data/errors.json') as errorFile:
            self.errors = json.load(errorFile)
        errorFile.close()
        self.logger.info("Loaded error messages from server!")
        
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        
        #{ Check Failure Error Raised By Check Or Manually By Code }#
        if isinstance(error, app_commands.CheckFailure):
            
            #** Get response based on type of check failure raised **
            try:
                response = self.errors['CheckFailure'][str(error)]
            
            #** If Error Message doesn't exist for given check failure, raise general error **
            except KeyError:
                self.logger.error(f"Unknown Check Failure: {error}")
                response = self.errors['Unknown']
            
        #{ Error When User Tries To Run Command That Doesn't Exist }
        elif isinstance(error, app_commands.CommandNotFound):
            response = self.errors['CommandNotFound']
            
        #{ Errror When Bot Tries To Perform Action But Is Missing Permissions }
        elif isinstance(error, app_commands.BotMissingPermissions):
            response = self.errors['BotMissingPermissions']
            response['message'] = response['message'].format(', '.join(error.missing_permissions))
            
        #{ Unexpected Error }
        else:
            self.logger.error(f'Unexpected Error "{type(error)}" During Command "{error.command.name}"')
            self.logger.exception(error)
            response = self.errors['Unknown']
            
        #** Respond to original interaction with error message **
        if interaction.response.type is None:
            try:
                await interaction.response.send_message(response['message'], ephemeral=response['ephemeral'])
            except discord.InteractionResponded:
                self.logger.warning(f'Interaction already responded to for command {error.command.name} with error {type(error)}')
            except Exception as e:
                self.logger.error(f"Unexpected error {type(e)} raised whilst trying to send error message {type(error)}")
        
        #** If Interaction has already been deferred, use followup webhook instead **
        elif interaction.response.type == discord.InteractionResponseType.deferred_message_update or interaction.response.type == discord.InteractionResponseType.deferred_channel_message:
            try:
                await interaction.followup.send(response['message'], ephemeral=response['ephemeral'])
            except Exception as e:
                self.logger.error(f"Unexpected error {type(e)} raised whilst trying to send error message {type(error)} to deferred interaction!")
        
        
     

#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(ErrorHandler(client))