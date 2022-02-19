
#!---------------------------IMPORT MODULES-----------------------#


import json
import discord
from discord.ext import tasks, commands


#!------------------------------IMPORT CLASSES----------------------------------#


from Classes.Database import UserData


#!--------------------------------STARTUP-----------------------------------# 


#** Startup Sequence **
print("-----------------------LOADING EXTENTION----------------------")
print("Name: Cogs.Background")
print("Modules Imported: ✓\n")


#!------------------------INITIALISE CLASSES-------------------#


Database = UserData()


#!--------------------------BACKGROUND CLASS------------------------#


class BackgroundTasks(commands.Cog):

    def __init__(self, client):

        #** Assign Class Objects **
        self.client = client

        #** Load Config File **
        with open('Config.json') as ConfigFile:
            Config = json.load(ConfigFile)
            ConfigFile.close()
            
        #** Setup Emojis **
        self.Emojis = Config['Variables']['Emojis']
        
        #** Start Status Rotation **
        self.CurrentStatus = 0
        self.Status = list(Config['Status'].items())
        self.StatusTime = Config['StatusTime']

        #** Setup Database Details **
        self.connection, self.cursor = Database.return_connection()
        
    
    def cog_unload(self):
        
        #** Gently Shutdown All Current Background Tasks **
        self.StatusRotation.stop()
        self.AuthCheck.stop()
        print("Background Cog Unloaded!")
        
        
    @commands.Cog.listener()
    async def on_ready(self):
        
        #** When Bot Startup Is Complete, Start Status Rotation & Auth Checking Background Tasks **
        self.StatusRotation.change_interval(seconds = self.StatusTime)
        self.StatusRotation.start()
        self.AuthCheck.start()


    @tasks.loop()
    async def StatusRotation(self):
        
        #** If Current Status Is Last In List, Loop Back To The Start, Otherwise Increment Count By 1 **
        if self.CurrentStatus == len(self.Status)-1:
            self.CurrentStatus = 0
        else:
            self.CurrentStatus += 1
        
        #** Set Activity Type Based Of Specified Activity Type In Config File **
        if self.Status[self.CurrentStatus][0] == "Playing":
            Activity = discord.ActivityType.playing
        elif self.Status[self.CurrentStatus][0] == "Listening":
            Activity = discord.ActivityType.listening
        else:
            Activity = discord.ActivityType.watching
        
        #** Update Presence On Discord **
        await self.client.change_presence(activity=discord.Activity(type=Activity, name=" "+str(self.Status[self.CurrentStatus][1])))


    @tasks.loop(seconds=120)
    async def AuthCheck(self):

        #** Get All Rows Updated In The Last Five Mins From Spotify Table **
        self.cursor.execute("SELECT * FROM spotify WHERE Linked BETWEEN DATE_SUB(NOW(), INTERVAL 2 MINUTE) AND NOW()")
        Recent = self.cursor.fetchall()
        self.connection.commit()

        #** For Row In Returned Row, Check If Spotify ID Present, ie, Change Has Been Made **
        for Update in Recent:
            if Update[0] != None:

                #** Get User And If One Found **
                User = self.client.get_user(int(Update[1]))
                if User != None:

                    #** Create DM Channel If One Doesn't Exist **
                    if User.dm_channel == None:
                        await User.create_dm()

                    #** Format Successful Link Embed & Try To Send To User **
                    try:
                        SuccessEmbed = discord.Embed(title = "Spotify Account Connected!",
                                colour = discord.Colour.blue())
                        SuccessEmbed.set_thumbnail(url="https://i.imgur.com/mUNosuh.png")
                        SuccessEmbed.set_thumbnail(url=Update[3])
                        SuccessEmbed.add_field(name="Username", value="["+Update[2]+"](https://open.spotify.com/user/"+Update[0]+")")
                        SuccessEmbed.add_field(name="What To Do Next?", value="- Start playing some of your private playlists through the bot using `!play`\n"
                                                                    +"- Get song recommendations using your Spotify playlists using `!recommendations spotify`\n"
                                                                    +"- Run `!profile` and check out your updated user profile", inline=False)
                        await User.dm_channel.send(embed=SuccessEmbed)

                    #** Print Error If Sending Embed Fails **
                    except:
                        print("User Had DMs Off Whilst Trying To Send Successful Auth Embed!")



#!-------------------SETUP FUNCTION-------------------#


def setup(client):
    client.add_cog(BackgroundTasks(client))