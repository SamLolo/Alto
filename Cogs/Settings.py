
#!-------------------------IMPORT MODULES--------------------#


import discord
from discord.ext import commands
from discord import app_commands


#!------------------------SETTINGS COG-----------------------#


class Settings(commands.Cog):

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


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(Settings(client))