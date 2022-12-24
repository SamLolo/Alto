
#!---------------------------IMPORT MODULES-----------------------#


import discord
import logging
from discord.utils import get
from discord.ext import commands


#!-------------------------PAGED EMBED CLASS-----------------------!#


class PagedEmbed():
    
    def __init__(self, pages: list, currentPage: int = 0):
        """
        Create new pagedEmbed object to keep track of an embed with multiple pages
        
        Parameters:
        pages (list): array of dictionaries representing the embeds
        currentPage (int): the index of the page currently being displayed   [Default: 0]
        
        Returns:
        None
        """
        self.pages = pages
        self.current = currentPage
        
    
    def next(self):
        """
        Gets the next embed dictionary in the pages array
        
        Parameters:
        None
        
        Returns:
        (dict): discord embed object representing the embed page requested
        """
        #** Adjust current pointer & return associated embed obj
        self.current += 1
        if self.current == len(self.pages):
            self.current = 0

        page = discord.Embed.from_dict(self.pages[self.current])
        return page


    def previous(self):
        """
        Gets the previous embed dictionary in the pages array
        
        Parameters:
        None
        
        Returns:
        (discord.Embed): discord embed object representing the embed page requested
        """
        #** Adjust current pointer & return associated embed obj
        self.current -= 1
        if self.current == -1:
            self.current = len(self.pages) - 1
            
        page = discord.Embed.from_dict(self.pages[self.current])
        return page


#!--------------------------PAGINATION EXTENSION------------------------#


class EmbedPaginator(commands.Cog):

    def __init__(self, client: discord.Client):
        """
        Instanciates the EmbedPaginator extension, creating required attributes for functions within the class
        
        Parameters:
        client (discord.Client): the discord client the extension has been loaded with
        
        Returns:
        None
        """
        self.client = client
        self.openPages = {}
        self.logger = logging.getLogger("discord.pagination")

    
    async def add_embed(self, messageID: int/str, pages: list, currentPage: int = 0):
        """
        Create new pagedEmbed object to keep track of an embed with multiple pages
        
        Parameters:
        messageID (int/str): the message ID to create a paged embed obj for
        pages (list): array of dictionaries representing the embeds
        currentPage (int): the index of the page currently being displayed   [Default: 0]
        
        Returns:
        None
        """
        #** Add paged embed obj to open pages dictionary
        self.openPages[str(messageID)] = PagedEmbed(pages, currentPage)
        
    
    async def get_embed(self, messageID: str/int):
        """
        Fetches the paged embed object associated with the passed-in message ID
        
        Parameters:
        messageID (str/int): the message ID to get the paged embed obj for
        
        Returns:
        (PagedEmbed): paged embed object for the requested message ID
        (None): paged embed object not found for message ID
        """
        #** Get paged embed obj for messageID
        if messageID in self.openPages.keys():
            embedQueue = self.openPages[str(messageID)]
            return embedQueue
        else:
            self.logger.warning(f"Pages not found for messageID: {messageID}")
            return None


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction: discord.Reaction):
        """
        Listens for reactions to paged embeds and adjusts the embed accoridngly
        
        Parameters:
        reaction (discord.Reaction): the reaction object recieved from the discord event
        
        Returns:
        None
        """
        #** Check rection is an add, not carried out by the user
        if reaction.user_id != self.client.user.id:
            if reaction.event_type == 'REACTION_ADD':
                
                #** Chek if paged embed object exists for reactions message ID
                pagedEmbed = self.get_embed(reaction.message_id)
                if pagedEmbed is not None:

                    #** Check if reaction is back or next emojis, and if so, get channel
                    nextEmoji = self.client.utils.get_emoji('Next')
                    backEmoji = self.client.utils.get_emoji('Back')
                    if (reaction.emoji.id == nextEmoji.id) or (reaction.emoji.id == backEmoji.id):
                        channel = get(self.client.get_all_channels(), guild__id=reaction.guild_id, id=reaction.channel_id)
                        if channel != None:

                            #** Get message and remove reaction just added
                            try:
                                message = await channel.fetch_message(reaction.message_id)
                                await message.remove_reaction(reaction.emoji, reaction.member)

                                #** Get new embed based on reaction emoji
                                if reaction.emoji.id == nextEmoji.id:
                                    newEmbed = pagedEmbed.next()
                                elif reaction.emoji.id == backEmoji.id:
                                    newEmbed = pagedEmbed.previous()
                                else:
                                    newEmbed = None

                                #** Edit message to show requested page
                                if newEmbed != None:
                                    await message.edit(embed=newEmbed)
                            except:
                                self.logger.debug(f"Message not found whilst getting new page: {reaction.message_id}")


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    """
    Adds the Embed Pagination extension to the clients list of cogs
    
    Parameters:
    client (discord.Client): the discord client to use
    
    Returns:
    None
    """
    await client.add_cog(EmbedPaginator(client))