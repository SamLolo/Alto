
#!-------------------------IMPORT MODULES--------------------#


import discord
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from dateutil.relativedelta import relativedelta


#!-------------------------------IMPORT CLASSES--------------------------------#


import Classes.Database


#!------------------------SETTINGS COG-----------------------#


class SettingsCog(commands.Cog, name="Settings"):

    def __init__(self, client: discord.Client):

        #** Assign Discord Bot Client As Class Object **
        self.client = client 
        
    @app_commands.guild_only()
    @app_commands.command(description="adjusts your default settings")
    @app_commands.describe(history="change if your listening history is recorded")
    @app_commands.choices(history=[app_commands.Choice(name="On", value="On"),
                                 app_commands.Choice(name="On, personal", value="On, personal"),
                                 app_commands.Choice(name="Off", value="Off")])

    async def usersettings(self, interaction: discord.Interaction, history: app_commands.Choice[str]):

        #** jiostrth **
        if history.name == "On":
            hist_value = "On"
            await interaction.response.send_message(f"History = {hist_value}", ephemeral=True)
        if history.name == "Off":
            hist_value = "Off"
            await interaction.response.send_message(f"History = {hist_value}", ephemeral=True)
        if history.name == "On, personal":
            hist_value = "On, personal"
            await interaction.response.send_message(f"History = {hist_value}", ephemeral=True)


class GuildSettingsCog(commands.Cog, name="GuildSettings"):

    def __init__(self, client: discord.Client):

        #** Assign Discord Bot Client As Class Object **
        self.client = client 


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(SettingsCog(client))
    await client.add_cog(GuildSettingsCog(client))