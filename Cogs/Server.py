
#!-------------------------IMPORT MODULES--------------------#


import discord
from discord.ext import commands
from discord import app_commands


#!-------------------DJ SETTINGS--------------------------#


class DjSettings(app_commands.Group, name="dj", description="Server settings for the DJ-only mode."):
        
    @app_commands.command(description="Enable/Disable DJ-only mode for this server.")
    @app_commands.choices(state=[app_commands.Choice(name="enabled", value=1),
                                    app_commands.Choice(name="disabled", value=0)])
    async def status(self, interaction: discord.Interaction, state: app_commands.Choice[int]):
        await interaction.response.send_message(f"Set DJ-only mode to {state.name} for {interaction.guild.name}!", ephemeral=True)


    @app_commands.command(description="Add a role/user as a DJ.")
    async def add(self, interaction: discord.Interaction, role: discord.Role = None, user: discord.Member = None):
        print(role, user)
        pass
    
    
    @app_commands.command(description="Remove a role/user as a DJ.")
    async def remove(self, interaction: discord.Interaction, role: discord.Role = None, user: discord.Member = None):
        print(role, user)
        pass


#!---------------------SERVER SETTINGS COG-----------------------#


class GuildSettings(commands.Cog, name="Server"):

    def __init__(self, client: discord.Client):

        #** Assign Discord Bot Client As Class Object **
        self.client = client
        
        #** Add command groups to tree so they can be used **
        client.tree.add_command(DjSettings())

  
#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(GuildSettings(client))