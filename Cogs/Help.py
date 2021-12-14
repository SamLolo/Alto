
#!-------------------------IMPORT MODULES--------------------#


import math
import json
import copy
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
        self.Pagination = self.client.get_cog("EmbedPaginator")
        self.activeCogs = {'Music': 'All music-related commands, including playing music.', 'Account': '', 'Utility': ''}
        
        #** Load Config File **
        with open('Config.json') as ConfigFile:
            Config = json.load(ConfigFile)
            ConfigFile.close()
            
        #** Setup Emojis **
        self.Emojis = Config['Variables']['Emojis']
        
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
            
        #**--------------COMMAND CATERGORY---------------**#
        
        elif input.title() in list(self.activeCogs.keys()):
            
            #** Get Cog Object **
            Cog = self.client.get_cog(input.title())
            
            #** Create Basic Embed **
            CategoryEmbed = discord.Embed(title = "Catergory: "+input.title(),
                                colour=discord.Colour.orange())
            
            #** Iterate Through Commands In Cog **
            PageData = []
            for CommandNo, command in enumerate(Cog.walk_commands()):
                
                #** If 10 Commands Reached, Add To Embed Page Number & Create Pagination Object. **
                if (CommandNo % 10) == 0 and CommandNo != 0:
                    CategoryEmbed.set_footer(text="Page "+str(CommandNo // 10))
                    PageDict = copy.deepcopy(CategoryEmbed.to_dict())
                    PageData.append(PageDict)
                    print("[PAGE]\n")
                    print(PageData)
                    print()
                    
                    #** If First Page, Send Embed & Add Reactions **#
                    if (CommandNo / 10) == 1:
                        Page = await ctx.send(embed=CategoryEmbed)
                        await Page.add_reaction(self.Emojis['Back'])
                        await Page.add_reaction(self.Emojis['Next'])
                    
                    #** Clear Embed Fields **
                    CategoryEmbed.clear_fields()
                    print(PageDict)
                
                #** Create Field Description With Command Aliases And Command Description **
                Value = "*"+command.description+"*\n ---------------------------"
                if command.aliases != []:
                    Value = "`Aliases: !"+(", !".join(command.aliases))+"`\n"+Value
                else:
                    Value = "`Aliases: None`"+Value
                    
                #** Add Field About Command To Embed **
                CategoryEmbed.add_field(name="**__"+command.name.title()+"__**", value=Value, inline=False)
            
            if len(list(Cog.walk_commands())) > 10 and (CommandNo % 10) != 0:
                CategoryEmbed.set_footer(text="Page "+str(int(math.ceil(CommandNo / 10))))
                PageData.append(CategoryEmbed.to_dict())
                print("[PAGE]\n")
                print(PageData)
                print()
                
            #** Send Embed if less than 10 commands otherwise Create Pagination For Embed **
            if PageData == []:
                await ctx.send(embed=CategoryEmbed)
            else:
                await self.Pagination.add_pages(Page.id, PageData)
                print("Pagination Sent!")
                
        #**------------------SINGLE COMMAND------------------**#
                
        elif input.lower() in self.activeCommands:
            Embed = self.Command(input.lower())
        

#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(HelpCog(client))