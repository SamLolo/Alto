
#!---------------------------IMPORT MODULES-----------------------#


import json
import discord
import asyncio
from discord.ext import commands
from discord.utils import get


#!--------------------------PAGINATION CLASS------------------------#


class EmbedPaginator(commands.Cog):

    def __init__(self, client):

        #** Assign Class Objects **
        self.client = client
        self.OpenPages = {}

        #** Load Config File **
        with open('Config.json') as ConfigFile:
            Config = json.load(ConfigFile)
            ConfigFile.close()
            
        #** Setup Emojis **
        self.Emojis = Config['Variables']['Emojis']

    
    async def add_page(self, MessageID, Data):

        #** Add Page To Open Pages **
        self.OpenPages[MessageID] = {'Current': 0, 'Embeds': Data}


    async def format_embed(self, MessageID, NewIndex):

        #** Get Embed Data **
        Data = self.OpenPages[MessageID]['Embeds']
        EmbedData = Data[str(NewIndex)]
        
        #** Construct Embed From JSON Data **
        NewEmbed = discord.Embed.from_dict(EmbedData)
        
        #** Return Embed Object **
        return NewEmbed


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, Reaction):
        
        #** Check Reaction Isn't Self-Reaction **
        if Reaction.user_id != 803939964092940308:

            #** Check If Reaction Added **
            if Reaction.event_type == 'REACTION_ADD':

                #** Get Channel & Page To Remove Reaction Just Added **
                Channel = get(self.client.get_all_channels(), guild__id=Reaction.guild_id, id=Reaction.channel_id)
                Page = await Channel.fetch_message(Reaction.message_id)
                await Page.remove_reaction(Reaction.emoji, Reaction.member)

                #** Check If Reaction Is One Of The Arrows **
                if str(Reaction.emoji) == self.Emojis['Next'] or str(Reaction.emoji) == self.Emojis['Back']:
                    
                    #** Get Current Index **
                    CurrentIndex = self.OpenPages[Reaction.message_id]['Current']
                    
                    #** Adjust Current Page Based On Reaction **
                    if CurrentIndex == len(self.OpenPages[Reaction.message_id]['Embeds'])-1 and str(Reaction.emoji) == self.Emojis['Next']:
                        CurrentIndex = 0
                    elif CurrentIndex == 0 and str(Reaction.emoji) == self.Emojis['Back']:
                        CurrentIndex = len(self.OpenPages[Reaction.message_id]['Embeds'])-1
                    else:
                        if str(Reaction.emoji) == self.Emojis['Next']:
                            CurrentIndex += 1
                        else:
                            CurrentIndex -= 1

                    #** Get New Embed **
                    NewPage = await self.format_embed(Reaction.message_id, CurrentIndex)
                    
                    #** Edit Current Page **
                    await Page.edit(embed=NewPage)

                    #** Save New Current Index **
                    self.OpenPages[Reaction.message_id]['Current'] = CurrentIndex


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(EmbedPaginator(client))