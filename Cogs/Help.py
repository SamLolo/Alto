
#!-------------------------IMPORT MODULES--------------------#


import math
import copy
import discord
from discord.ext import commands
from discord import app_commands


#!-------------------------HELP COG-----------------------------#


class HelpCog(commands.Cog):

    def __init__(self, client: discord.Client):
        
        #** Assign Class Objects **
        self.client = client
        self.Pagination = self.client.get_cog("EmbedPaginator")
        self.cogDescriptions = {'Music': 'All music-related commands, including controlling the audio player and finding out information about songs.', 
                                'Account': 'Commands involving your Alto account, such as getting information about your account, and managing spotify connections.', 
                                'Utility': 'Miscellaneous and utility commands, such as information about the bot and it\'s operation.'}
                
    
    @app_commands.command()
    @app_commands.describe(category="A catergory of commands, shown by running /help",
                           command="A command to get information about.")
    @app_commands.choices(category=[app_commands.Choice(name="Music", value=1),
                                     app_commands.Choice(name="Account", value=2),
                                     app_commands.Choice(name="Utility", value=3)])
    async def help(self, interaction: discord.Interaction, category: app_commands.Choice[int] = None, command: str = None):
            
        #**--------------COMMAND CATERGORY---------------**#
        
        if category is not None:
            
            #** Get Cog Object **
            Cog = self.client.get_cog(category.name)
            
            #** Create Basic Embed **
            CategoryEmbed = discord.Embed(title = "Catergory: "+category.name,
                                colour=discord.Colour.blue())
            CategoryEmbed.set_thumbnail(url="https://i.imgur.com/mUNosuh.png")
            
            #** Iterate Through Commands In Cog **
            PageData = []
            for CommandNo, command in enumerate(Cog.walk_commands()):
                
                #** If 10 Commands Reached, Add To Embed Page Number & Create Pagination Object. **
                if (CommandNo % 6) == 0 and CommandNo != 0:
                    CategoryEmbed.set_footer(text="Page "+str(CommandNo // 6))
                    PageDict = copy.deepcopy(CategoryEmbed.to_dict())
                    PageData.append(PageDict)
                    
                    #** If First Page, Send Embed & Add Reactions **#
                    if (CommandNo / 6) == 1:
                        Page = await interaction.channel.send(embed=CategoryEmbed)
                        await Page.add_reaction(self.Emojis['Back'])
                        await Page.add_reaction(self.Emojis['Next'])
                    
                    #** Clear Embed Fields **
                    CategoryEmbed.clear_fields()
                
                #** Create Field Description With Command Description & Wether It's Guild Only **
                if command.dm_permission:
                    Value = "`Sever-Only: No`"
                else:
                    Value = "`Sever-Only: Yes`"
                Value += f"\n*{command.description}*\n ---------------------------"

                #** Add Field About Command To Embed **
                CategoryEmbed.add_field(name="**__"+command.name.title()+"__**", value=Value, inline=False)
            
            if len(list(Cog.walk_commands())) > 6 and (CommandNo % 6) != 0:
                CategoryEmbed.set_footer(text="Page "+str(int(math.ceil(CommandNo / 6))))
                PageData.append(CategoryEmbed.to_dict())
                
            #** Send Embed if less than 6 commands otherwise Create Pagination For Embed **
            if PageData == []:
                await interaction.channel.send(embed=CategoryEmbed)
            else:
                await self.Pagination.add_pages(Page.id, PageData)
                
        #**------------------SINGLE COMMAND------------------**#
                
        elif input.lower() in self.activeCommands:
            
            #** Get Command Object **
            Command = self.client.get_command(input.lower())
            
            #** Create Embed Description
            Description = "\n*"+Command.description+"*"
            if Command.aliases != []:
                Description = "`Aliases: !"+(", /".join(Command.aliases))+"`"+Description
            else:
                Description = "`Aliases: None`"+Description
                
            #** Create Embed About Command **
            CommandEmbed = discord.Embed(title = "Command: "+input.title(),
                                description = Description,
                                colour = discord.Colour.blue())
            CommandEmbed.set_thumbnail(url="https://i.imgur.com/mUNosuh.png")
            
            #** Add Usage Field **
            if Command.usage != None:
                Usage = "`"+Command.usage+"`"
            else:
                Usage = "`!"+input.lower()+"`"
            if Command.brief != None:
                Usage += "\n*"+Command.brief+"*"
            CommandEmbed.add_field(name="Usage:", value=Usage, inline=False)

            #** Add Paramaters Field **
            if Command.help != None:
                CommandEmbed.add_field(name="Paramters:", value=Command.help, inline=False)
            
            #** Send Embed To Discord **
            await interaction.response.send(embed=CommandEmbed)

        #**------------------UNKNOWN INPUT------------------**#

        else:
            #** Let User Know Input Is Invalid **
            Temp = await interaction.channel.send("`/"+input.title()+"` **is not a valid command or catergory!**\nPlease, check your input and try again.")

        

#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(HelpCog(client))