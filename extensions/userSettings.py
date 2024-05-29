
#!-------------------------IMPORT MODULES--------------------#


# External packages
import discord
from discord.ext import commands
from discord import app_commands


#!------------------------SETTINGS COG-----------------------#


class UserSettings(commands.Cog, name="Settings"):

    def __init__(self, client: discord.Client):
        self.client = client 


    @app_commands.command(description="Configure/Disable Listening History")
    @app_commands.describe(history="Ajust how listening history is recorded")
    @app_commands.choices(history=[app_commands.Choice(name="All Songs", value=2),
                                   app_commands.Choice(name="Only Songs Queued By Me", value=1),
                                   app_commands.Choice(name="Disabled", value=0)])
    async def history(self, interaction: discord.Interaction, mode: app_commands.Choice[int]):
        pass


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(UserSettings(client))