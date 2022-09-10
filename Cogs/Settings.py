
#!-------------------------IMPORT MODULES--------------------#


import discord
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from dateutil.relativedelta import relativedelta


#!------------------------SETTINGS COG-----------------------#


class SettingsCog(commands.Cog, name="Settings"):

    def __init__(self, client: discord.Client):

        #** Assign Discord Bot Client As Class Object **
        self.client = client 
        
    @app_commands.guild_only()
    @app_commands.command(description="adjusts your default settings")
    @app_commands.describe(history="change if your listening history is recorded")
    async def usersettings(self, interaction: discord.Interaction, history: str = None):
        hist_value = "On"
        #** jiostrth **
        if history == "On":
            await interaction.response.send_message(f"History = {hist_value}", ephemeral=True)
        if history == "Off":
            hist_value = "Off"
            await interaction.response.send_message(f"History = {hist_value}", ephemeral=True)
        if history == "Me":
            hist_value = "Me"
            await interaction.response.send_message(f"History = {hist_value}", ephemeral=True)



#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(SettingsCog(client))