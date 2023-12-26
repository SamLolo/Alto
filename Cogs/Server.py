
#!-------------------------IMPORT MODULES--------------------#


import discord
from discord.ext import commands
from discord import app_commands


#!-------------------DJ SETTINGS--------------------------#


class DjSettings(app_commands.Group, name="dj", description="Server settings for the DJ-only mode."):
        
    @app_commands.command(description="Enable/Disable DJ-only mode for this server.")
    @app_commands.choices(state=[app_commands.Choice(name="Enabled", value=1),
                                 app_commands.Choice(name="Disabled", value=0)])
    async def state(self, interaction: discord.Interaction, state: app_commands.Choice[int]):
        await interaction.response.send_message(f"Set DJ-only mode to {state.name.lower()} for {interaction.guild.name}!", ephemeral=True)


    @app_commands.command(description="Add a role/user as a DJ.")
    async def add(self, interaction: discord.Interaction, role: discord.Role = None, user: discord.Member = None):
        print(role, user)
        pass
    
    
    @app_commands.command(description="Remove a role/user as a DJ.")
    async def remove(self, interaction: discord.Interaction, role: discord.Role = None, user: discord.Member = None):
        print(role, user)
        pass
    
    
#!-------------------VOLUME SETTINGS--------------------------#


class VolumeSettings(app_commands.Group, name="volume", description="Server settings for the volume controls."):
        
    @app_commands.command(description="Enable/Disable volume controls for this server.")
    @app_commands.choices(state=[app_commands.Choice(name="Enabled", value=1),
                                 app_commands.Choice(name="Disabled", value=0)])
    async def state(self, interaction: discord.Interaction, state: app_commands.Choice[int]):
        await interaction.response.send_message(f"Set volume controls to {state.name.lower()} for {interaction.guild.name}!", ephemeral=True)


    @app_commands.command(description="Set maximum volume level. Defaults to 100.")
    async def set_max(self, interaction: discord.Interaction, max: int):
        pass
    
    
    @app_commands.command(description="Sets the default volume level for new listening sessions. Default 25.")
    async def default(self, interaction: discord.Interaction, default: int):
        pass
    

    @app_commands.command(description="Sets wether the last volume level should be remembered between listening sessions.")
    @app_commands.choices(state=[app_commands.Choice(name="True", value=1),
                                 app_commands.Choice(name="False", value=0)])
    async def keep_volume(self, interaction: discord.Interaction, state: app_commands.Choice[int]):
        await interaction.response.send_message(f"Set keep last volume level to {state.name.lower()} for {interaction.guild.name}!", ephemeral=True)


#!---------------------SERVER SETTINGS COG-----------------------#


class GuildSettings(commands.Cog, name="Server"):

    def __init__(self, client: discord.Client):

        #** Assign Discord Bot Client As Class Object **
        self.client = client
        
        #** Add command groups to tree so they can be used **
        client.tree.add_command(DjSettings())
        client.tree.add_command(VolumeSettings())
 

#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(GuildSettings(client))