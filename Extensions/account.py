
#!-------------------------IMPORT MODULES--------------------#


import copy
import math
import random
import discord
from datetime import datetime
from discord.ext import commands
from discord import app_commands
from dateutil.relativedelta import relativedelta


#!------------------------UTILITY COG-----------------------#


class AccountCog(commands.Cog, name="Account"):

    def __init__(self, client: discord.Client):

        #** Assign Discord Bot Client As Class Object & Get Pagination Cog**
        self.client = client
        self.pagination = self.client.get_cog("EmbedPaginator")

 
    @app_commands.command(description="Displays information about your alto profile.")
    async def profile(self, interaction: discord.Interaction):
        
        #** Setup Base Profile Embed With Title & User's Colour **
        ProfileEmbed = discord.Embed(title=interaction.user.display_name+"'s Profile",
                                     colour=discord.Colour.blue())
        if interaction.user.avatar is not None:
            ProfileEmbed.set_thumbnail(url=interaction.user.avatar.url)

        #** Try Getting User Object From Player If User Is In VC **
        CurrentUser = None
        if (interaction.user.voice is not None) and (interaction.user.voice.channel is not None):
            Player = self.client.lavalink.player_manager.get(interaction.user.voice.channel.guild.id)
            if Player is not None:
                UserDict = Player.fetch('Users')
                if str(interaction.user.id) in UserDict.keys():
                    CurrentUser = UserDict[str(interaction.user.id)]
        
        #** Otherwise Create Fresh User Object **       
        if CurrentUser is None:
            if self.client.database.connected:
                try:
                    CurrentUser = self.client.userClass.User(self.client, user=interaction.user)
                except:
                    pass
            else:
                raise app_commands.CheckFailure("Database")

        #** Get Last Song's Data if Listening History Isn't Empty **
        if len(CurrentUser.history) > 0:
            LastSongData = CurrentUser.history[0]

            #** Format Data For Song & Add Last Listened To Song To Embed As Field **
            emoji = self.client.utils.get_emoji(LastSongData['source'].title())
            artists = self.client.utils.format_artists(LastSongData['artists'], LastSongData['artistID'] if 'artistID' in LastSongData.keys() else None)
            description = f"{str(emoji)+' ' if emoji is not None else ''}[{LastSongData['name']}]({LastSongData['url']})\nBy: {artists}\n"
            ProfileEmbed.add_field(name="Last Listened To:", value=description, inline=False)

            #** Calculate Time Difference And Check What To Display **
            TimeDiff = relativedelta(datetime.now(), LastSongData['listenedAt'])
            if TimeDiff.years >= 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value=f"Over {f'{TimeDiff.years} years' if TimeDiff.years > 1 else 'a year'} ago")
            elif TimeDiff.months >= 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value=f"Over {f'{TimeDiff.months} months' if TimeDiff.months > 1 else 'a month'} ago")
            elif TimeDiff.days >= 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value=f"{f'{TimeDiff.days} days' if TimeDiff.days > 1 else 'A day'} ago")
            elif TimeDiff.hours >= 1:
                ProfileEmbed.add_field(name="Last Listening Session:", value=f"{f'{TimeDiff.hours} hours' if TimeDiff.days > 1 else 'An hour'} ago")
            else:
                ProfileEmbed.add_field(name="Last Listening Session:", value="Less than an hour ago")
        
        #** Add Blank Fields If Listening History Empty **
        else:
            ProfileEmbed.add_field(name="Last Listened To:", value="No Listening History", inline=False)
            ProfileEmbed.add_field(name="Last Listening Session:", value="N/A")

        #** Calculate Total Song Count & Add As Field To Embed **
        ProfileEmbed.add_field(name="Lifetime Song Count:", value=f"{CurrentUser.songs} Songs")
        
        #** Send Profile Embed To User **
        await interaction.response.send_message(embed=ProfileEmbed)


    @app_commands.command(description="Displays your 20 last listened to songs through the bot.")
    async def history(self, interaction: discord.Interaction):
        
        #** Setup Base History Embed With Title, User's Colour & Profile Picture **
        embed = discord.Embed(title=interaction.user.display_name+"'s Listening History",
                              colour=discord.Colour.blue())
        if interaction.user.avatar is not None:
            embed.set_thumbnail(url=interaction.user.avatar.url)
        
        #** Try Getting User Object From Player If User Is In VC **
        currentUser = None
        if (interaction.user.voice is not None) and (interaction.user.voice.channel is not None):
            Player = self.client.lavalink.player_manager.get(interaction.user.voice.channel.guild.id)
            if Player is not None:
                UserDict = Player.fetch('Users')
                if str(interaction.user.id) in UserDict.keys():
                    currentUser = UserDict[str(interaction.user.id)]
        
        #** Otherwise Create Fresh User Object **       
        if currentUser is None:
            if self.client.database.connected:
                try:
                    currentUser = self.client.userClass.User(self.client, user=interaction.user)
                except:
                    pass
            else:
                raise app_commands.CheckFailure("Database")

        # Check if user has history
        if len(currentUser.history) > 0:
            print(currentUser.history)
            history = iter(currentUser.history)
            pages = []
            
            date = None
            while True:
                
                song = next(history, None)
                if song is None:
                    break
                
                if date is None:
                    description = f"**{song['listenedAt'].strftime('%d %B %Y')}**\n"
                    date = song['listenedAt']
                elif (song['listenedAt'].day != date.day or song['listenedAt'].month != date.month or song['listenedAt'].year != date.year):
                    date = song['listenedAt']
                    embed.description = description
                    embed.set_footer(text=f"Page {len(pages)+1}/{math.ceil(len(currentUser.history) / 5)}")
                    dict = copy.deepcopy(embed.to_dict())
                    pages.append(dict)
                    description = f"\n**{song['listenedAt'].strftime('%d %B %Y')}**\n"
                    
                emoji = self.client.utils.get_emoji(song['source'].title())
                artists = self.client.utils.format_artists(song['artists'], song['artistID'] if 'artistID' in song.keys() else None)
                description += f"{song['listenedAt'].strftime('%H:%M')}   {str(emoji)+' ' if emoji is not None else ''}[{song['name']}]({song['url']})"
                description += f"\n        *By:* {artists}\n"

            embed.description = description
            embed.set_footer(text=f"Page {len(pages)+1}/{math.ceil(len(currentUser.history) / 5)}")
            dict = copy.deepcopy(embed.to_dict())
            pages.append(dict)
            
            #** If More Than One Page Being Displayed, Add Back And Next Reactions & Add To Global Pagination System **
            await interaction.response.send_message(embed=discord.Embed.from_dict(pages[0]))
            if len(pages) > 1:
                message = await interaction.original_response()
                await self.pagination.setup(message, pages)
        
        #** Let User Know If They Have No Listening History To Display **
        else:
            await interaction.response.send_message("**You do not have any history to display!**\nGet listening today by joining a vc and running `/play`!", ephemeral=True)
    

    @app_commands.command(description="Displays 10 random song recommendations based on your listening history.")
    async def recommendations(self, interaction: discord.Interaction):
        
        #** Try Getting User Object From Player If User Is In VC **
        user = None
        if (interaction.user.voice is not None) and (interaction.user.voice.channel is not None):
            player = self.client.lavalink.player_manager.get(interaction.user.voice.channel.guild.id)
            if player is not None:
                userDict = player.fetch('Users')
                if str(interaction.user.id) in userDict.keys():
                    user = userDict[str(interaction.user.id)]
        
        #** Otherwise Create Fresh User Object **       
        if user is None:
            if self.client.database.connected:
                try:
                    user = self.client.userClass.User(self.client, user=interaction.user)
                except:
                    pass
            else:
                raise app_commands.CheckFailure("Database")
        
        #** Get Recommendations From Spotify API Through User Class If User Has Listened To At Least One Song **
        if user.recommendations['songcount'] > 0:
            try:
                tracks = user.getRecommendations()
            except:
                await interaction.response.send_message("**An Error Occurred Whilst Fetching Recommendations**!\nIf this error persists, contact `@sam_lolo` on Discord.", ephemeral=True)
        else:
            raise app_commands.CheckFailure("Recommendations")

        #** Randomly Choose 10 Songs From 50 Recomendations **
        if tracks is not None:
            recommendations = {}
            for i in range(10):
                track = random.choice(tracks)
                while track['id'] in recommendations.keys():
                    track = random.choice(tracks)
                recommendations[track['id']] = track

            #** Loop Through Data & Create Dictionary Of Embed Pages **
            pages = []
            count = 0
            for id, data in recommendations.items():

                #** Format Embed Sections **
                song = data['name'] + "\nBy: " + self.client.utils.format_artists(data['artists'], data['artistID'])
                links = f"{self.client.utils.get_emoji('Spotify')} Song: [Spotify](https://open.spotify.com/track/{id})\n"
                if data['preview'] is not None:
                    links += f'{self.client.utils.get_emoji("Preview")} Song: [Preview]({data["preview"]})\n'
                links += f"{self.client.utils.get_emoji('Album')} Album: [{data['album']}](https://open.spotify.com/album/{data['albumID']})"

                #** Create New Embed **
                page = discord.Embed(
                    title = interaction.user.display_name+"'s Recommendations")
                page.set_thumbnail(url=data['art'])
                page.add_field(name=f"Song {count+1}:", value=song, inline=False)
                page.add_field(name="Links:", value=links, inline=False)
                page.set_footer(text=f"({count+1}/10) React To See More Recommendations!")

                #** Display First Recomendation To User **
                if count == 0:
                    await interaction.response.send_message(embed=page)

                #** Convert Embed To Dictionary and Add To Data Dictionary & Increment Counter **
                pages.append(page.to_dict())
                count += 1

            #** Add Embed To Active Pages In Pagination Cog **
            message = await interaction.original_response()
            await self.pagination.setup(message, pages)
        
        #** Return Error To User If Failed To Get Recommendations **
        else:
            await interaction.response.send_message("**An Error Occurred Whilst Fetching Recommendations**!\nIf this error persists, contact `@sam_lolo` on Discord.", ephemeral=True)


    @app_commands.command(description="Deletes your user data where requested from our database.")
    @app_commands.choices(type=[app_commands.Choice(name="All", value="users, spotify, history, recommendations"),
                                app_commands.Choice(name="History", value="history"),
                                app_commands.Choice(name="User", value="users, history, recommendations")])
    async def delete(self, interaction: discord.Interaction, type: app_commands.Choice[str]):
        
        #** Get Tables That Would Need To Be Deleted **
        Tables = type.value.split(", ")

        #** Create Warning Embed & Check User Is Sure They Want To Delete Their Data **
        WarningEmbed = discord.Embed(title=f"New Request To Remove `{type.name}` Data!",
                                     description="The Requested data will be deleted and lost forever!\nYou may also lose access to certain bot features after this process!\n**Are you sure you want to continue?**",
                                     colour=discord.Colour.gold())
        WarningEmbed.set_footer(text="If you continue using the bot, new data will be stored!")

        #** Create DM Channel With User If One Doesn't Already Exist **
        if interaction.user.dm_channel == None:
            await interaction.user.create_dm()
        
        #** Try To Send Embed To User & Add Reaction If Successful**
        try:
            SentWarning = await interaction.user.dm_channel.send(embed=WarningEmbed)
            await SentWarning.add_reaction(self.client.utils.get_emoji('checkmark'))

        #** Raise Error If Can't Send Messages To DM Channel **
        except :
            raise app_commands.CheckFailure(message="DM")
        
        #** Let User Know To Check DM's If All Sucessful **
        await interaction.response.send_message("Please check your DMs!", ephemeral=True)

        #** Check Function To Be Called When Checking If Correct Reaction Has Taken Place **
        def ReactionAdd(Reaction):
            return (Reaction.message_id == SentWarning.id) and (Reaction.user_id != self.client.user.id)

        #** Wait For User To React To Tick & Remove Data When Done So **
        while True:
            Reaction = await self.client.wait_for("raw_reaction_add", check=ReactionAdd)
            if str(Reaction.emoji) == self.client.utils.get_emoji('checkmark'):
                self.client.database.RemoveData(interaction.user.id, Tables)
                await interaction.user.dm_channel.send("All requested data successfully removed!")


#!-------------------SETUP FUNCTION-------------------#


async def setup(client: discord.Client):
    await client.add_cog(AccountCog(client))