
#!---------------------------IMPORT MODULES-----------------------#


import json
import discord
import asyncio
from discord.ext import commands
from discord.utils import get


#!--------------------------------STARTUP-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Pagination\n")


#!-------------------------EMBED CLASS-----------------------!#


class EmbedQueue():
    
    def __init__(self, size):
        
        self.pages = []
        self.inPointer = 0
        self.outPointer = 0
        self.maxSize = size
        self.full = False
        
    def check_empty(self):
        
        #** Check Queue Isn't Full & Pointers Aren't The Same **
        return (not(self.full) and self.outPointer == self.inPointer)
        
    def check_full(self):
        
        #** Check If Queue Is Full & Pointers Are The Same **
        return (self.full and self.inPointer == self.outPointer)
        
    def enqueue(self, page):
        
        #** Check Queue Isn't Full & Add Page **
        if not(self.check_full()):
            try:
                self.pages[self.inPointer] = page
            except:
                self.pages.append(page)

            #** Adjust InPointer Forward 1 and Set Full To True If Same As OutPointer **
            if self.inPointer == (self.maxSize - 1):
                self.inPointer = 0
            else:
                self.inPointer += 1

            if self.inPointer == self.outPointer and len(self.pages) == self.maxSize:
                self.full = True
        
        #** Print Full If Queue Is Full **
        else:
            print("Queue is full!")
            
        
    def dequeue(self):
        
        #** Check If Queue Is Empty & Get Page Where OutPointer Currently Is ** 
        if not(self.check_empty()):
            Page = self.pages[self.outPointer]
            
            #** Adjust OutPointer Forward By 1 **
            if self.outPointer == (self.maxSize - 1):
                self.outPointer = 0
            else:
                self.outPointer += 1
            
            #** Set Full To False If Currently True & Return Page**
            if self.full:
                self.full = False
            return Page

        #** Print If Queue Is Empty & Return None Value **
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
        EmbedObj = EmbedQueue(len(Pages))
        
        #** Add Pages To Queue **
        for Page in Pages[1:]:
            EmbedObj.enqueue(Page)
        EmbedObj.enqueue(Pages[0])

        #** Add Page To Open Pages **
        self.OpenPages[MessageID] = EmbedObj


    async def format_embed(self, Embed):
        
        #** Construct Embed From JSON Data **
        NewEmbed = discord.Embed.from_dict(Embed)
        
        #** Return Embed Object **
        return NewEmbed
    
    
    async def get_next(self, MessageID):
        
        #** Get Embed Object **
        try:
            Embed = self.OpenPages[MessageID]
        except:
            return None
        
        #** Move Page To Back Of Queue **
        Page = Embed.dequeue()
        Embed.enqueue(Page)
        
        #** Return Embed Dictionary **
        return Page
    
    
    async def get_last(self, MessageID):
        
        #** Get Embed Object **
        try:
            Embed = self.OpenPages[MessageID]
        except:
            print("Pages not found!")
            return None
        
        #** Work Through Page Queue To Find Last Page **
        for i in range(Embed.maxSize - 1):
            Page = Embed.dequeue()
            Embed.enqueue(Page)
        
        #** Return Embed Dictionary **
        return Page
        

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

                #** Check If Reaction Is Next & Get New Embed **
                if str(Reaction.emoji) == self.Emojis['Next']:
                    NewEmbed = await self.get_next(Reaction.message_id)
                
                #** Check If Reaction Is Back & Get New Embed **
                elif str(Reaction.emoji) == self.Emojis['Back']:
                    NewEmbed = await self.get_last(Reaction.message_id)
                
                #** If Reaction Isn't Next Or Back, Don't Get New Embed **
                else:
                    NewEmbed = None

                #** Format New Embed & Edit Current Page **
                if NewEmbed != None:
                    NewPage = await self.format_embed(NewEmbed)
                    await Page.edit(embed=NewPage)


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(EmbedPaginator(client))