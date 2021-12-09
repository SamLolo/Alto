
#!-------------------------IMPORT MODULES--------------------#


import discord
import asyncio
from datetime import datetime
from discord.ext import commands


#!--------------------------------STARTUP-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Help")


#!------------------------HELP COMMAND CLASS-----------------------#


class HelpCommand(object):
    
    def __init__(self):
        
        #** Assign Class Objects **
        self.activeCogs = {'Music': 'All music-related commands, including playing music.', 'Account': '', 'Utility': ''}         
        print("Custom Help Command Initiated!\n")
        
    
    def MainMenu(self):
        
        #** Create Help Embed Showing Command Catergories & Basic Info **
        Embed = discord.Embed(title = "Using The Bot",
                              description = "",
                              colour=discord.Colour.orange())
        
        #** Return Embed Object **
        return Embed
    

    def Extension(self, CogName):
        
        #** Get Cog Object **
        Cog = self.client.get_cog(CogName)
        
        #** Create Basic Embed **
        Embed = discord.Embed(title = "Catergory: "+CogName,
                              colour=discord.Colour.orange())
        
        #** Itterate Through Commands In Cog **
        for command in Cog.walk_commands():
            
            #** Create Field Description With Command Aliases And Command Description **
            Value = "*"+command.description+"*\n ---------------------------"
            if command.aliases != []:
                Value = "`Aliases: !"+(", !".join(command.aliases))+"`\n"+Value
            else:
                Value = "`Aliases: None`"+Value
                
            #** Add Field About Command To Embed **
            Embed.add_field(name="**__"+command.name.title()+"__**", value=Value, inline=False)
        
        #** Return Embed Object **
        return Embed
    
    
    def Command(self, CommandName):
        
        #** Get Command Object **
        Command = self.client.get_command(CommandName)
        
        #** Create Embed Description
        Description = "\n*"+Command.description+"*"
        if Command.aliases != []:
            Description = "`Aliases: !"+(", !".join(Command.aliases))+"`\n"+Description
        else:
            Description = "`Aliases: None`"+Description
            
        #** Create Embed About Command **
        Embed = discord.Embed(title = "Command: "+CommandName,
                              description = Description,
                              colour = discord.Colour.orange())
        
        #** Return Embed Object **
        return Embed


#!-------------------------HELP COG-----------------------------#


class HelpCog(commands.Cog, HelpCommand):

    def __init__(self, client):

        #** Initialise Custom HelpCommand Class **
        super(HelpCog, self).__init__()
        
        #** Assign Class Objects **
        self.client = client
        
        #** Get List Of Active Commands **
        self.activeCommands = []
        for Command in self.client.walk_commands():
            if not(Command.hidden):
                self.activeCommands.append(Command.name)

    
    @commands.command()
    async def help(self, ctx, *args):
        
        input = " ".join(args)
        print("'"+input+"'")
        if input == "":
            Embed = self.MainMenu()
        elif input.title() in list(self.activeCogs.keys()):
            Embed = self.Extension(input.title())
        elif input.lower() in self.activeCommands:
            Embed = self.Command(input.lower())
            
        await ctx.send(embed=Embed)
        

#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(HelpCog(client))