
#!---------------------------IMPORT MODULES-----------------------#


import json
import discord
import asyncio
from discord.ext import commands
from discord.utils import get


#!-------------------------EMBED CLASS-----------------------!#


class Embed():
    
    def __init__(self):
        
        self.pages = []
        self.inPointer = 0
        self.outPointer = 0
        self.maxSize = 10
        self.full = False
        
    def check_empty(self):
            
        return not(self.full)
        
    def check_full(self):
        
        if self.inPointer == self.outPointer and len(self.pages) == self.maxSize:
            self.full = True
            return True
        
        return False
        
    def enqueue(self, page):
        
        if not(self.check_full()):
            
            self.pages[self.inPointer] = page
            if self.inPointer == self.maxSize:
                self.inPointer = 0
            else:
                self.inPointer += 1
                
            print(self.pages)
            
        else:
            print("Queue is full!")
            
        
    def dequeue(self):
        
        if not(self.check_empty()):
            
            Page = self.pages[self.outPointer]
            if self.outPointer == self.maxSize:
                self.outPointer = 0
            else:
                self.outPointer += 1
            
            if self.full:
                self.full = False
                
            return Page
                
        else:
            print("Nothing To Dequeue!")
            return None


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

    
    async def add_pages(self, MessageID, Pages):
        
        #** Setup New Embed **
        Embed = Embed()
        
        #** Add Pages To Queue **
        for Page in Pages[1:]:
            Embed.enqueue(Page)
        Embed.enqueue(Pages[0])

        #** Add Page To Open Pages **
        self.OpenPages[MessageID] = Embed


    async def format_embed(self, Embed):
        
        #** Construct Embed From JSON Data **
        NewEmbed = discord.Embed.from_dict(Embed)
        
        #** Return Embed Object **
        return NewEmbed
    
    
    async def get_next(self, MessageID):
        
        #** Get Embed Object **
        Embed = self.OpenPages[MessageID]
        
        #** Move Page To Back Of Queue **
        Page = Embed.dequeue()
        Embed.enqueue(Page)
        
        #** Format Embed & Return Embed Object **
        NewEmbed = self.format_embed(Page)
        return NewEmbed
    
    
    async def get_last(self, MessageID):
        
        #** Get Embed Object **
        Embed = self.OpenPages[MessageID]
        
        #** Move Page To Back Of Queue **
        Embed.outPointer = Embed.maxSize
        Temp = Embed.dequeue()
        Page = Embed.dequeue()
        Embed.enqueue(Page)
        Embed.enqueue(Temp)
        
        #** Format Embed & Return Embed Object **
        NewEmbed = self.format_embed(Page)
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