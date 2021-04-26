
#!-------------------------IMPORT MODULES--------------------#


import os
import discord
import random
import string
import asyncio
import mysql.connector
import lavalink
from datetime import datetime
from discord.ext import commands


#!------------------------------IMPORT CLASSES----------------------------------#


from Classes.SpotifyUser import SpotifyUser
from Classes.Database import UserData
from Classes.Music import Music
from Classes.Youtube import YoutubeAPI


#!--------------------------------DATABASE CONNECTION-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Music")
print("Startup Time: "+datetime.now().strftime("%H:%M - %d/%m/%Y"))
print("Modules Imported: ✓")

#** Get Connection Details **
Host = os.environ["DATABASE_HOST"]
User = os.environ["DATABASE_USER"]
Password = os.environ["DATABASE_PASS"]

#** Connect To Database **
connection = mysql.connector.connect(host = Host,
                                     database = "Melody",
                                     user = User,
                                     password = Password)

#** Setup Cursor and Output Successful Connection **                  
if connection.is_connected():
    cursor = connection.cursor()
    cursor.execute("SELECT database();")
    Record = cursor.fetchone()
    print("Database Connected: ✓")

#** Delete Connection Details **
del Host
del User
del Password


#!------------------------INITIALISE CLASSES-------------------#


Youtube = YoutubeAPI()
Database = UserData(cursor, connection)
SongData = Music()


#!------------------------MUSIC COG-----------------------#


class MusicCog(commands.Cog):

    def __init__(self, client):

        #** Assign Discord Bot Client As Class Object **
        self.client = client 

        if not hasattr(client, 'lavalink'):  # This ensures the client isn't overwritten during cog reloads.
            client.lavalink = lavalink.Client(client.user.id)
            client.lavalink.add_node('127.0.0.1', 2333, 'youshallnotpass', 'eu', 'default-node')  # Host, Port, Password, Region, Name
            client.add_listener(client.lavalink.voice_update_handler, 'on_socket_response')

        lavalink.add_event_hook(self.track_hook)
        print("Lavalink Started: ✓")

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        """ Command before-invoke handler. """
        guild_check = ctx.guild is not None
        #  This is essentially the same as `@commands.guild_only()`
        #  except it saves us repeating ourselves (and also a few lines).

        if guild_check:
            await self.ensure_voice(ctx)
            #  Ensure that the bot and command author share a mutual voicechannel.

        return guild_check


#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(MusicCog(client))