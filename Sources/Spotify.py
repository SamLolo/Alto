
#!--------------------IMPORT MODULES-----------------------#


import lavalink
from discord.ext import commands
from lavalink.errors import LoadError
from lavalink.models import Source, LoadResult, LoadType, PlaylistInfo, DeferredAudioTrack


#!-------------------DEFERED AUDIO TRACK---------------------#


class SpotifyDeferredTrack(DeferredAudioTrack):

    async def load(self, client: lavalink.Client):
        # Search youtube for spotify track
        results = await client.get_tracks(f"ytsearch:{self.title} by {self.extra['metadata']['artists'][0]}")

        # If odd load result, or no tracks, raise a LoadError
        if (results.load_type != LoadType.SEARCH) or (results.tracks is None):
            raise LoadError
        
        # Get match score for each search result
        tracks = {}
        for track in results['tracks']:
            score = self.check_match(track)
            tracks[track] = score
        
        # Sort tracks based on their score so best score is first in dict
        tracks = sorted(tracks.items(), key=lambda x: x[1], reverse=True)
        top = tracks[0][0]
        
        # Cache top track metadata & base64 track
        data = {'track': top.track,
                'source': 'spotify',
                'id': self.identifier,
                'name': self.title,
                'url': self.uri,
                'duration': self.duration}
        data.update(self.extra['metadata'])
        client.database.cacheSong(data)

        # Return base64 track code from best search result
        self.track = top.track
        return self.track
    
    
    def check_match(self, track: lavalink.AudioTrack):
        # Assign track an int score (higher=better)
        match = 0
        
        # If title of track is found in Youtube title
        if self.title in track['title']:
            match += 2
        
        # If spotify author name is found in Youtube channel name or Youtube title
        if self.extra['metadata']['artists'][0] in track['author'] or self.extra['metadata']['artists'][0] in track['title']:
            match += 1
        
        # Duration is within 5 seconds of actual track duration (favours audio only vs music videos)
        if (self.duration - track['duration']) <= 5000 or (self.duration - track['duration']) >= -5000:
            match += 2
        
        # If VEVO in youtube channel name, then likely official channel
        if "VEVO" in track['author']:
            match += 1
        
        # Audio or lyric versions of tracks should be preferred
        if "audio" in track['title'] or "lyric" in track['title']:
            match += 2
        
        # Prefer unslowed tracks unless specified otherwise
        if "slowed" in track['title'] and not("slowed" in self.title):
            match -= 1
        
        # Prefer original track unless specified otherwise
        if "reverb" in track['title'] and not("reverb" in self.title):
            match -= 1
        
        # Prefer original version over remixes unless remix is explicitly specified
        if "remix" in track['title'] and not("remix" in self.title):
            match -= 2
        
        return match


#!---------------------SPOTIFY CUSTOM SOURCE----------------------#


class SpotifySource(Source):
    
    def __init__(self, discord: commands.Bot):
        super().__init__('spotify')
        # Set discord client as attribute for access during loading songs
        self.discord = discord


    async def load_item(self, client: lavalink.Client, query: str):
        # Types of queries to be caught by SpotifySource
        if query.startswith('spsearch:') or query.startswith('https://open.spotify.com/'):
            cache = None
            try:
                # If request to search spotify, call Spotify search for query
                if query.startswith('spsearch:'):
                    info = self.discord.music.SearchSpotify(query.strip("spsearch:"))
                    
                    # Query cache for returned spotifyID
                    cache = client.database.searchCache(info['tracks'][0]['id'])
                
                # If url entered, get spotifyID by splitting up url
                elif query.startswith('https://open.spotify.com/'):
                    spotifyID = (query.split("/"))[4].split("?")[0]
                    if len(spotifyID) != 22:
                        raise Exception(f"Invalid URL: {query}")

                    # If just track, query cache for spotifyID
                    if "track" in query:
                        cache = client.database.searchCache(spotifyID)
                        
                        # If no track found, get new song info from Spotify
                        if cache is None:
                            info = self.discord.music.GetSongInfo(spotifyID)
                    
                    # If playlist/album, load track metadata from Spotify
                    elif "playlist" in query:
                        info = self.discord.music.GetPlaylistSongs(spotifyID)
                    elif "album" in query:
                        info = self.discord.music.GetAlbumInfo(spotifyID)
                    else:
                        raise Exception(f"Unsupported Input: {query}")
            
            # Deal with errors raised whilst fetching track information
            except LoadError as e:
                client.logger.debug(f"LoadError for query: {query}")
                raise e
            except Exception as e:
                client.logger.exception(e)
                raise LoadError
            
            # If cached (single) track found, load track as standard AudioTrack
            else:
                if cache is not None:
                    tracks = [lavalink.AudioTrack({'track': cache['track'],
                                                   'identifier': cache['id'],  
                                                   'isSeekable': True,
                                                   'author': cache['artists'][0],
                                                   'length': cache['duration'],
                                                   'isStream': False,
                                                   'title': cache['name'],
                                                   'sourceName': 'spotify',
                                                   'uri': cache['url']},
                                                   requester = 0,
                                                   metadata={k:cache[k] for k in ('cacheID', 'artists', 'artistID', 'album', 'albumID', 'art', 'colour', 'release', 'popularity', 'explicit', 'preview')})]                
                    return LoadResult(LoadType.TRACK, tracks, playlist_info=PlaylistInfo.none())
                
                # Otherwise load a list of deferred Spotify tracks
                else:
                    tracks = []
                    for track in info["tracks"]:
                        trackObj = SpotifyDeferredTrack({'identifier': track['id'],  
                                                        'isSeekable': True,
                                                        'author': track['artists'][0],
                                                        'length': track['duration'],
                                                        'isStream': False,
                                                        'title': track['name'],
                                                        'sourceName': 'spotify',
                                                        'uri': f"https://open.spotify.com/track/{track['id']}"}, 
                                                        requester=0,
                                                        metadata={'cacheID': None,
                                                                'artists': track['artists'],
                                                                'artistID': track['artistID'],
                                                                'album': track['album'],
                                                                'albumID': track['albumID'],
                                                                'art': track['art'],
                                                                'colour': None,
                                                                'release': track['release'],
                                                                'popularity': track['popularity'],
                                                                'explicit': track['explicit'],
                                                                'preview': track['preview']})
                        tracks.append(trackObj)
                
                    # Return LoadResult with playlist metadata if available
                    if not("playlistInfo" in info.keys()):
                        return LoadResult(LoadType.TRACK, tracks, playlist_info=PlaylistInfo.none())
                    else:
                        return LoadResult(LoadType.PLAYLIST, tracks, playlist_info=PlaylistInfo(info['playlistInfo']['name']))