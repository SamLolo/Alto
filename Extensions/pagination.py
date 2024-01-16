
#!---------------------------IMPORT MODULES-----------------------#


import discord
import logging
from discord.ext import commands


#!-------------------------PAGED EMBED CLASS-----------------------!#


class PagedEmbed():
    
    def __init__(self, pages: list, currentPage: int = 0):
        """
        Instanciates the pagedEmbed class, creating required attributes for functions within the class
        
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

    
    async def setup(self, message: discord.Message, pages: list, currentPage: int = 0):
        """
        Create new pagedEmbed object to keep track of an embed with multiple pages
        
        Parameters:
        message (discord.Message): the message to create a paged embed obj for
        pages (list): array of dictionaries representing the embeds
        currentPage (int): the index of the page currently being displayed   [Default: 0]
        
        Returns:
        None
        """
        #** Add Reactions And Created PagedEmbed For Message
        await message.add_reaction(self.client.utils.get_emoji('Back'))
        await message.add_reaction(self.client.utils.get_emoji('Next'))
        self.openPages[str(message.id)] = PagedEmbed(pages, currentPage)
        
    
    def get_embed(self, messageID: int):
        """
        Fetches the paged embed object associated with the passed-in message ID
        
        Parameters:
        messageID (str/int): the message ID to get the paged embed obj for
        
        Returns:
        (PagedEmbed): paged embed object for the requested message ID
        (None): paged embed object not found for message ID
        """
        #** Get paged embed obj for messageID
        if str(messageID) in self.openPages.keys():
            embedQueue = self.openPages[str(messageID)]
            return embedQueue
        else:
            self.logger.warning(f"Pages not found for messageID: {messageID}")
            return None


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        """
        Listens for reactions to paged embeds and adjusts the embed accoridngly
        
        Parameters:
        reaction (discord.RawReactionActionEvent): the reaction object recieved from the discord event
        
        Returns:
        None
        """
        #** Check rection is an add, not carried out by the user
        if reaction.user_id != self.client.user.id:
            
            #** Get channel and message if they exist & remove reaction if message belongs to bot
            channel = self.client.get_channel(reaction.channel_id)
            if channel != None:
                message = await channel.fetch_message(reaction.message_id)
                if message != None and message.author.id == self.client.user.id:
                    await message.remove_reaction(reaction.emoji, reaction.member)
                
                    #** Chek if paged embed object exists for reactions message ID
                    pagedEmbed = self.get_embed(reaction.message_id)
                    if pagedEmbed is not None:

                        #** Get new embed based on reaction emoji
                        nextEmoji = self.client.utils.get_emoji('Next')
                        backEmoji = self.client.utils.get_emoji('Back')
                        if reaction.emoji.id == nextEmoji.id:
                            newEmbed = pagedEmbed.next()
                        elif reaction.emoji.id == backEmoji.id:
                            newEmbed = pagedEmbed.previous()
                        else:
                            newEmbed = None

                        #** Edit message to show requested page
                        if newEmbed != None:
                            await message.edit(embed=newEmbed)
                
                #** Log deleted message and remove pages from active pagination list
                elif message == None:
                    self.logger.debug(f"Message not found whilst getting new page: {reaction.message_id}")
                    try:
                        self.openPages.pop(str(reaction.message_id))
                        self.logger.debug(f"Removed message with id '{reaction.message_id}' from active pagination list!")
                    except:
                        pass


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