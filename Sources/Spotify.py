
#!--------------------IMPORT MODULES-----------------------#


import logging
import lavalink
from discord.ext import commands
from Classes.utils import get_colour
from Classes.database import Database
from lavalink.errors import LoadError
from lavalink import Source, LoadResult, LoadType, PlaylistInfo, DeferredAudioTrack


#!-------------------DEFERED AUDIO TRACK---------------------#


class SpotifyDeferredTrack(DeferredAudioTrack):
    
    def __init__(self, database: Database, data: dict, requester: int = 0, **extra):
        self.database = database
        super().__init__(data, requester, **extra)


    async def load(self, client: lavalink.Client):
        # Search youtube for spotify track
        results = await client.get_tracks(f"ytsearch:{self.title} by {self.extra['metadata']['artists'][0]['name']}")

        # If odd load result, or no tracks, raise a LoadError
        if (results.load_type != LoadType.SEARCH) or (results.tracks is None):
            raise LoadError
        
        # Get match score for each search result
        tracks = {}
        for track in results['tracks']:
            score = self.check_match(track)
            tracks[track] = score
        
        # Sort tracks based on their score so best score is first in dict and chose top result as track
        tracks = sorted(tracks.items(), key=lambda x: x[1], reverse=True)
        top = tracks[0][0]
        self.track = top.track
        
        # Cache track metadata if not aleady cached
        if self.extra['metadata']['cacheID'] is None:
            try:
                cacheID = self.database.cacheSong(self)
                self.extra['metadata']['cacheID'] = cacheID
            except:
                pass
            
        # Return base64 track code from best search result
        return self.track
    
    
    def check_match(self, track: lavalink.AudioTrack):
        # Assign track an int score (higher=better)
        match = 0
        
        # If title of track is found in Youtube title
        if self.title in track['title']:
            match += 5
        
        # If spotify author name is found in Youtube channel name or Youtube title
        if self.extra['metadata']['artists'][0]['name'] in track['author']:
            match += 4 
        if self.extra['metadata']['artists'][0]['name'] in track['title']:
            match += 2
        
        # Duration is within 5 seconds of actual track duration (favours audio only vs music videos)
        if (self.duration - track['duration']) <= 5000 or (self.duration - track['duration']) >= -5000:
            match += 4
        
        # If VEVO in youtube channel name, then likely official channel
        if "VEVO" in track['author']:
            match += 1
        
        # Audio or lyric versions of tracks should be preferred
        if "audio" in track['title'] or "lyric" in track['title']:
            match += 3
        
        # Check keywords for match between found sound and original
        kwords = ["slowerd", "reverb", "sped-up", "acoustic", "stripped", "live"]
        for word in kwords:
            if word in track['title'] and word in self.title:
                match += 2
            elif (word in track['title'] and not(word in self.title)) or (not(word in track['title']) and word in self.title):
                match -= 1
        
        # Prefer original version over remixes unless remix is explicitly specified
        if "remix" in track['title'] and "remix" in self.title:
            match += 1
        elif ("remix" in track['title'] and not("remix" in self.title)) or (not("remix" in track['title']) and "remix" in self.title):
            match -= 2
        
        return match


#!---------------------SPOTIFY CUSTOM SOURCE----------------------#


class SpotifySource(Source):
    
    def __init__(self, discord: commands.Bot, database: Database):
        super().__init__('spotify')
        
        # Set discord client as attribute for access during loading songs
        self.discord = discord
        self.database = database
        self.logger = logging.getLogger('lavalink.spotify')


    async def load_item(self, client: lavalink.Client, query: str):
        
        # Types of queries to be caught by SpotifySource
        if query.startswith('spsearch:') or query.startswith('https://open.spotify.com/'):
            cache = None
            try:
                # If request to search spotify, call Spotify search for query
                if query.startswith('spsearch:'):
                    info = self.discord.music.SearchSpotify(query.strip("spsearch:"))
                    
                    # Query cache for returned spotifyID
                    try:
                        cache = self.database.searchCache(info['tracks'][0]['id'])
                    except Exception as ex:
                        if type(ex) != ConnectionError:
                            self.logger.debug(f"Failed to search cache for spotify ID: {info['tracks'][0]['id']}")
                            self.logger.exception(ex)
                    else:
                        if cache is None:
                            try:
                                features = self.discord.music.GetAudioFeatures([info['tracks'][0]['id']])
                            except:
                                features = None
                
                # If url entered, get spotifyID by splitting up url
                elif query.startswith('https://open.spotify.com/'):
                    spotifyID = (query.split("/"))[4].split("?")[0]
                    if len(spotifyID) != 22:
                        raise Exception(f"Invalid URL: {query}")

                    # If just track, query cache for spotifyID
                    if "track" in query:
                        try:
                            cache = self.database.searchCache(spotifyID)
                        except Exception as ex:
                            if type(ex) != ConnectionError:
                                self.logger.debug(f"Failed to search cache for spotify ID: {spotifyID}")
                                self.logger.exception(ex)
                        else:
                            if cache is None:
                                info = self.discord.music.GetSongInfo(spotifyID)
                                try:
                                    features = self.discord.music.GetAudioFeatures([spotifyID])
                                except:
                                    features = None
                    
                    # If playlist/album, load track metadata from Spotify
                    elif "playlist" in query:
                        info = self.discord.music.GetPlaylistSongs(spotifyID)
                        try:
                            features = self.discord.music.GetAudioFeatures([track['id'] for track in info['tracks']])
                        except:
                            features = None
                    elif "album" in query:
                        info = self.discord.music.GetAlbumInfo(spotifyID)
                        try:
                            features = self.discord.music.GetAudioFeatures([track['id'] for track in info['tracks']])
                        except:
                            features = None
                    else:
                        raise Exception(f"Unsupported Input: {query}")
            
            # Deal with errors raised whilst fetching track information
            except LoadError as ex:
                self.logger.error(f"LoadError for query: {query}")
                raise ex
            except Exception as ex:
                self.logger.error(f"Unexpected error whilst loading track: {ex.message}")
                self.logger.exception(ex)
                raise LoadError(ex.message)
            
            # If cached (single) track found, load track as standard AudioTrack
            if cache is not None:             
                return LoadResult(LoadType.TRACK, [cache], playlist_info=PlaylistInfo.none())
            
            # Otherwise load a list of deferred Spotify tracks
            else:
                tracks = []
                for index, data in enumerate(info["tracks"]):
                    tracks.append(SpotifyDeferredTrack(self.database,
                                                      {'identifier': data['id'],  
                                                       'isSeekable': True,
                                                       'author': data['artists'][0]['name'],
                                                       'length': data['duration'],
                                                       'isStream': False,
                                                       'title': data['name'],
                                                       'uri': f"https://open.spotify.com/track/{data['id']}",
                                                       'artworkURL': data['art'],
                                                       'sourceName': 'spotify'}, 
                                                        requester = 0,
                                                        metadata={
                                                            'cacheID': None,
                                                            'artists': data['artists'],
                                                            'colour': get_colour(data['art']),
                                                            'release': data['release'],
                                                            'popularity': data['popularity'],
                                                            'explicit': data['explicit'],
                                                            'preview': data['preview']
                                                        },
                                                        features = features[index] if features is not None else None,
                                                        album = info['albumInfo'] if 'albumInfo' in data.keys() else None))

                # Return LoadResult with playlist metadata if available
                if not("playlistInfo" in info.keys()):
                    return LoadResult(LoadType.TRACK, tracks, playlist_info=PlaylistInfo.none())
                else:
                    if not('album' in query):
                        return LoadResult(LoadType.PLAYLIST, tracks, playlist_info=PlaylistInfo(info['playlistInfo']['name']))
                    else:
                        return LoadResult(LoadType.PLAYLIST, tracks, playlist_info=PlaylistInfo(info['albumInfo']['name']))