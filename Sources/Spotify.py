
#!--------------------IMPORT MODULES-----------------------#


from lavalink.errors import LoadError
from lavalink.models import Source, LoadResult, LoadType, PlaylistInfo, DeferredAudioTrack


#!-------------------DEFERED AUDIO TRACK---------------------#


class SpotifyDeferredTrack(DeferredAudioTrack):

    async def load(self, client):
        result = await client.get_tracks(f"ytsearch:{self.title} {self.extra['spotify']['artists'][0]}")

        if (result.load_type != LoadType.SEARCH) or (result.tracks is None):
            raise LoadError

        first_track = result.tracks[0]
        base64 = first_track.track
        self.track = base64

        return base64


#!---------------------SPOTIFY CUSTOM SOURCE----------------------#


class SpotifySource(Source):
    
    def __init__(self, discord):
        super().__init__('spotify')
        self.discord = discord

    async def load_item(self, client, query):
        
        if query.startswith('spsearch:') or query.startswith('https://open.spotify.com/'):
            
            try:
                if query.startswith('spsearch:'):
                    info = self.discord.music.SearchSpotify(query.strip("spsearch:"))
                
                elif query.startswith('https://open.spotify.com/'):
                    
                    spotifyID = (query.split("/"))[4].split("?")[0]
                    if len(spotifyID) != 22:
                        raise Exception(f"Invalid URL: {query}")

                    if "track" in query:
                        info = self.discord.music.GetSongInfo(spotifyID)
                    elif "playlist" in query:
                        info = self.discord.music.GetPlaylistSongs(spotifyID)
                    elif "album" in query:
                        info = self.discord.music.GetAlbumInfo(spotifyID)
                    else:
                        raise Exception(f"Unsupported Input: {query}")
            
            except Exception as e:
                raise LoadError
            
            else:
                tracks = []
                for track in info["tracks"]:
                    trackObj = SpotifyDeferredTrack({'identifier': track['id'],  
                                                    'isSeekable': True,
                                                    'author': None,
                                                    'length': track['duration'],
                                                    'isStream': False,
                                                    'title': track['name'],
                                                    'sourceName': 'spotify',
                                                    'uri': f"https://open.spotify.com/track/{track['id']}"}, 
                                                    requester=0,
                                                    spotify={'artists': track['artists'],
                                                            'artistID': track['artistID'],
                                                            'art': track['art'],
                                                            'album': track['album'],
                                                            'albumID': track['albumID'],
                                                            'release': track['release'],
                                                            'popularity': track['popularity'],
                                                            'explicit': track['explicit'],
                                                            'preview': track['preview']})
                    tracks.append(trackObj)
                
                if not("playlistInfo" in info.keys()):
                    return LoadResult(LoadType.TRACK, tracks, playlist_info=PlaylistInfo.none())

                else:
                    return LoadResult(LoadType.PLAYLIST, tracks, playlist_info=PlaylistInfo(info['playlistInfo']['name']))