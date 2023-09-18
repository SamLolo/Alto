
#!-------------------------IMPORT MODULES--------------------#


import os
import tomlkit
import discord
import logging
import asyncio
import importlib
from discord.ext import commands


#!-------------------------------IMPORT CLASSES--------------------------------#


import Classes.Users
import Classes.Utils
import Classes.MusicUtils
import Classes.Database


#!------------------------ADMIN COG-----------------------#


class AdminCog(commands.Cog, name="Admin"):

    def __init__(self, client: discord.Client):

        #** Assign Discord Bot Client As Class Object **
        self.client = client
        self.logger = logging.getLogger("discord.admin")
        
        #** Instanciate Classes If One Or More Attributes Missing **
        if not hasattr(client, 'database'):
            client.database = Classes.Database.Database(client.config, pool=client.config['database']['main']['poolname'], size=client.config['database']['main']['size'])
        if not hasattr(client, 'music'): 
            client.music = Classes.MusicUtils.SongData()
        if not hasattr(client, 'utils'):
            client.utils = Classes.Utils.Utility(client)
        if not hasattr(client, 'userClass'):
            client.userClass = Classes.Users
            
    
    async def cog_load(self):
        
        #** Get application team from Discord **
        application = await self.client.application_info()
        self.admins = []
        for member in application.team.members:
            self.admins.append(member.id)


    def is_admin():
    
        #** When Called, Check If User Id In List & If So Return True **
        async def predicate(ctx):
            if ctx.author.id in ctx.cog.admins:
                return True
            return False
        return commands.check(predicate)
    
    
    @commands.command(hidden=True)
    @is_admin()
    async def reload(self, ctx, input):
        
        #** If Passed Name Is A Class, Use Importlib To Reload File **
        if input.lower() in ['musicutils', 'database', 'users', 'utils']:      
            try:   
                #** Re-add Attribute To Client Class **
                if input.lower() == "database":
                    importlib.reload(Classes.Database)
                    self.client.database = Classes.Database.Database(self.client.config, pool=self.client.config['database']['main']['poolname'], size=self.client.config['database']['main']['size'])
                elif input.lower() == "music":
                    importlib.reload(Classes.MusicUtils)
                    self.client.music = Classes.MusicUtils.SongData()
                elif input.lower() == "utils":
                    importlib.reload(Classes.Utils)
                    self.client.utils = Classes.Utils.Utility(self.client)
                else:
                    importlib.reload(Classes.Users)
                    self.client.userClass = Classes.Users

            #** Log error & inform user **
            except Exception as e:
                self.logger.warning(f"An error occured when reloading class: {input.title()}!")
                self.logger.exception(e)
                await ctx.send(f"**An Error Occured Whilst Trying To Reload The {input.title()} Class!**\n```{e}```")
                return
        
        #** If Input Is 'Config', reload Config File **
        elif input.lower() == "config":  
            try:
                with open("config.toml", "rb")  as configFile:
                    self.client.config = tomlkit.load(configFile)

            #** Log error & inform user **
            except Exception as e:
                self.logger.warning("An error occured when reloading config file!")
                self.logger.exception(e)
                await ctx.send(f"**An Error Occured Whilst Trying To Reload The Config File!**\n```{e}```")
                return
            
        #** If Input Not Config Or Class, Try To Reload Cog Under Name **
        else:
            try:
                #** ReLoad Specified Cog **
                await self.client.reload_extension("Cogs."+input.title())
                self.client.logger.info(f"Extension Loaded: Cogs.{input.title()}")

            #** Log error & inform user **
            except Exception as e:
                self.logger.warning(f"An error occured when reloading cog: {input.title()}!")
                self.logger.exception(e)
                await ctx.send(f"**An Error Occured Whilst Trying To Reload {input.title()} Cog!**\n```{e}```")
                return
            
        #** Send Confirmation Message **
        self.logger.debug(f"Sucessfully reloaded {input.title()}!")
        await ctx.send(f"**Sucessfully Reloaded:** `{input.title()}`!")
    

    @commands.command(hidden=True)
    @is_admin()
    async def sync(self, ctx, *args):
        
        #** If Input is Blank, Sync Application Commands To Current Guild **
        if not(args):
            args = ["Current Server"]
            self.client.tree.copy_global_to(guild=ctx.guild)
        
        #** If Input = Global, Send Warning Message **
        elif args[0].lower() == "global":
            warning = await ctx.send("**Warning! Syncing Globally Will Make The Changes Available To __All Servers__!**\n*Are You Sure You Want To Continue?*")
            
            #** Add Reactions **
            await warning.add_reaction("✅")
            await warning.add_reaction("❌")
            
            def ReactionAdd(Reaction):
                return (Reaction.message_id == warning.id) and (Reaction.user_id != self.client.user.id)

            #** Wait For User To React To Tick & Stop Function Execution When Reacting With No **
            while True:
                Reaction = await self.client.wait_for("raw_reaction_add", check=ReactionAdd)
                if str(Reaction.emoji) == "❌":
                    await warning.delete()
                    temp = await ctx.send("Cancelled Command Sync Operation!")
                    await asyncio.sleep(10)
                    await ctx.message.delete()
                    await temp.delete()
                    return
                elif str(Reaction.emoji) == "✅":
                    await warning.delete()
                    break
        
        #** If Input is Integer, Check If Guild ID, & Sync To That Guild
        elif args[0].isdecimal():
            guild = self.client.get_guild(int(args[0]))
            if guild is None:
                raise commands.BadArgument()
            self.client.tree.copy_global_to(guild=guild)
        
        #** If Invalid Argument Supplied, Raise Error
        else:
            raise commands.BadArgument()
        
        #** Carry Out Sync **
        await self.client.tree.sync()
            
        #** Send Confirmation Message If Sucessfull **
        self.client.logger.info(f"Synced Application Commands. Scope: '{args[0]}'")
        temp = await ctx.send(f"Sucessfully Synced Application Commands!\nScope: `{args[0]}`")
        
        
    @commands.command(hidden=True)
    @is_admin()
    async def debug(self, ctx, option):
        
        #** Format Original Embed **
        embed = discord.Embed(title=f"Debug Information For `{option.title()}`",
                              colour=discord.Colour.blue())
        
        #** If Option Is 'Lavalink', Format Embed Description With Current Lavalink Node Info **
        if option.lower() == "lavalink":
            if hasattr(self.client, 'lavalink'):
                
                #** Start Description Embed & Locate Default Node From Lavalink Node Manager **
                description = f"Available Nodes: `{len(self.client.lavalink.node_manager.available_nodes)}`\n\n**Stats For Default-Node:**\n"
                for node in self.client.lavalink.node_manager.nodes:
                    if node.name == "default-node":
                        
                        #** Check If Node Is Available Or Not & Add Stats To Description Before Breaking For Loop **
                        if node.available:
                            if not(node.stats.is_fake):
                                description += f"```Total Players: {node.stats.players}\nActive Players: {node.stats.playing_players}```"
                                embed.add_field(name="CPU Usage:", value=f"{round(node.stats.lavalink_load * 100, 2)}%")
                                embed.add_field(name="Memory Usage:", value=f"{round(node.stats.memory_used / 1000000000, 2)}GB")
                                embed.add_field(name="Allocated Memory:", value=f"{round(node.stats.memory_allocated / 1000000000, 2)}GB")
                                embed.add_field(name="Uptime:", value=self.client.utils.format_time(node.stats.uptime))
                                embed.add_field(name="Missing Frames:", value=f"{node.stats.frames_deficit * -1}")
                                embed.add_field(name="Lavalink Penalty:", value=f"{round(node.stats.penalty.total, 2)}")
                            else:
                                description += "*Stats are not yet available for this node!*"
                        
                        #** Format Description With Node Offline & Break For Loop
                        else:
                            description += "*Node Unavailable!*"
                            break
                
                #** Set Embed Description To Formatted Embed **
                embed.description = description
            else:
                embed.description = "Lavalink Not Connected!"
            
        #** If Option Is 'Database', Format Embed Description With Database Connection Info **
        elif option.lower() == "database":
            pass
            
        #** Send Embed To Discord **
        await ctx.send(embed=embed)
        self.logger.debug(f"Debug info requested for '{option.title()}' by user: {ctx.author.id}")
        
    
    @commands.command(hidden=True)
    @is_admin()
    async def logs(self, ctx):
        
        # Create List Of Discord File Objects For All Current Log Files In Directory 
        logDir = self.client.config['logging']['directory']
        download = []
        for file in os.listdir(f"{logDir}/"):
            if file.endswith(".log"):
                download.append(discord.File(open(f"{logDir}/{file}", "rb")))
        
        # Attach logs files to Discord Message 
        await ctx.send("Current session logs:", files=download)
        self.logger.info(f"Session logs downloaded by user: {ctx.author.id}")
        
    
    @commands.command(hidden=True)
    @is_admin()
    async def force_disconnect(self, ctx, server="current"):
        # Get guild object for requested server
        if server.lower() == "current":
            guild = ctx.guild
        else:
            guild = self.client.get_guild(int(server))
        
        # Handle standard disconnect procedure by force disconnecting the bot and saving user data
        if guild is not None:
            await guild.voice_client.disconnect()
            player = self.client.lavalink.player_manager.get(guild.id)
            
            # If player found, remove old nowPlaying message if one exists
            if player is not None:
                oldMessage = player.fetch('NowPlaying')
                if oldMessage is not None:
                    await oldMessage.delete()
                    player.delete('NowPlaying')

                # Save all user data within the player
                userDict = player.fetch('Users')
                for user in userDict.values():
                    user.save()
    

#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(AdminCog(client))