
#!---------------------------IMPORT MODULES-----------------------#


import discord
import asyncio
from discord.ext import commands
from discord.utils import get


#!--------------------------ADD PAGE FUNCTION-----------------------#


#** Setup Page Dictionary **
OpenPages = {}

async def add_page(self, Message, Data):

    #** Add Page To Open Pages **
    OpenPages[Message.id] = {'Current': 0, 'Embeds': Data}


#!--------------------------PAGINATION CLASS------------------------#


class EmbedPaginator(commands.Cog):

    def __init__(self, client):

        #** Assign Class Objects **
        self.client = client


    async def format_embed(self, MessageID, NewIndex):

        #** Get Embed Data **
        Data = OpenPages[MessageID]


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
                if Reaction.emoji == self.Emojis['Next'] or Reaction.emoji == self.Emojis['Back']:
                    
                    #** Get Current Index **
                    CurrentIndex = OpenPages[Reaction.message_id]['Current']
                    
                    #** Adjust Current Page Based On Reaction **
                    if CurrentIndex == len(OpenPages[Reaction.message_id]['Embeds'])-1 and Reaction.emoji == self.Emojis['Next']:
                        CurrentIndex = 0
                    elif CurrentIndex == 0 and Reaction.emoji == self.Emojis['Back']:
                        CurrentIndex = len(OpenPages[Reaction.message_id]['Embeds'])-1
                    else:
                        if Reaction.emoji == self.Emojis['Next']:
                            CurrentIndex += 1
                        else:
                            CurrentIndex -= 1



#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(EmbedPaginator(client))