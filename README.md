# Alto | Discord Music Bot
[![](https://dcbadge.vercel.app/api/shield/803939964092940308?bot=true&style=flat)](https://discord.com/api/oauth2/authorize?client_id=803939964092940308&permissions=414836976704&scope=bot)
![Static Badge](https://img.shields.io/badge/Version-1.1-blue?style=flat)
[![wakatime](https://wakatime.com/badge/user/aa966dfd-2ee1-42d6-8b74-530c65d62ac0/project/5377707e-5dac-4307-aef2-e8dcb24ec022.svg)](https://wakatime.com/@aa966dfd-2ee1-42d6-8b74-530c65d62ac0/projects/tqfoalvzth)

## About The Project
The music bot was originally created as part of my A-Level coursework, and is currently maintained as a passion project. If you'd like to use the bot, you can invite the offical bot [here](https://discord.com/api/oauth2/authorize?client_id=803939964092940308&permissions=414836976704&scope=bot) or you can setup the code yourself using the information below! If you'd like to contribute, please do so on the [dev branch](https://github.com/SamLolo/Alto/tree/dev)! To track development, you can visit the [Trello Board](https://trello.com/b/nghSiaQg/development) which is used to track issues, and update progress, as well as future update plans! If you'd like to learn more, you can contact me on Discord *@sam_lolo*!

### Technical Information
- ![Python](https://img.shields.io/badge/python-3670A0?style=flat-square&logo=python&logoColor=ffdd54) Coded in Python using [Discord.py](https://github.com/Rapptz/discord.py) & [Lavalink.py](https://github.com/Devoxin/Lavalink.py)
- ![Oracle](https://img.shields.io/badge/Oracle-F80000?style=flat-square&logo=oracle&logoColor=white)  Uses an ARM-Based instance on [Oracle Cloud Infrastructure (OCI)](https://www.oracle.com/cloud/) running Oracle Linux 9
- ![MySQL](https://img.shields.io/badge/mysql-%2300f.svg?style=flat-squaree&logo=mysql&logoColor=white) Hosted alongside a MySQL database, storing both user & track information
- ![Trello](https://img.shields.io/badge/Trello-%23026AA7.svg?style=flat-square&logo=Trello&logoColor=white) Planning done using a [Trello board](https://trello.com/b/nghSiaQg/development)

### Supported Platforms
Alto supports playing audio from a range of sources, including but not limited to:

![Sound Cloud](https://img.shields.io/badge/sound%20cloud-FF5500?style=for-the-badge&logo=soundcloud&logoColor=white)
![Spotify](https://img.shields.io/badge/Spotify-1ED760?style=for-the-badge&logo=spotify&logoColor=white)
![Twitch](https://img.shields.io/badge/Twitch-9347FF?style=for-the-badge&logo=twitch&logoColor=white)
![YouTube](https://img.shields.io/badge/YouTube-%23FF0000.svg?style=for-the-badge&logo=YouTube&logoColor=white)

### Using The Bot
If you would like to self-host the bot, you will need to setup your own MySQL database, and download [lavalink](https://github.com/lavalink-devs/Lavalink) for the bot to work! You can find templates for all the required tables inside the [Database](https://github.com/SamLolo/Alto/tree/main/Database) folder, allowing for easy setup using the "import data" function of MySQL workbench!

**The bot will also require two accounts to be made:**
- An application on the [Discord developer portal](https://discord.com/developers). This will allow you to create the bot that the code will run through.
  - The bot token will need to be stored in enviroment variables using the key "BOT_TOKEN".
- An application registered on the [Spotify Web API](https://developer.spotify.com/documentation/web-api). This provides the Spotify metadata used for multiple commands!
  - The secret will needed to be stored as "SPOTIFY_SECRET" in environment variables, and the client id should be copied into the config.toml file!
  - The bot will work without this, although Spotify playback and commands using the web api will be disabled!