
#!--------------------IMPORT MODULES-----------------------#


from lavalink.errors import LoadError
from lavalink.models import Source, LoadResult, LoadType, PlaylistInfo, DeferredAudioTrack


#!-------------------DEFERED AUDIO TRACK---------------------#


class SpotifyDeferredTrack(DeferredAudioTrack):

    async def load(self, client):
        results = await client.get_tracks(f"ytsearch:{self.title} {self.extra['spotify']['artists'][0]}")
        print(results["tracks"][0])

        if (results.load_type != LoadType.SEARCH) or (results.tracks is None):
            raise LoadError
        
        tracks = {}
        for track in results['tracks']:
            match = 1
            if self.title in track['title']:
                match += 1
            if self.extra['spotify']['artists'][0] in track['author']:
                match += 1
            if (self.duration - track['duration']) <= 5000 or (self.duration - track['duration']) >= -5000:
                match += 1
            if "VEVO" in track['author']:
                match += 1
            if "audio" in track['title'] or "lyric" in track['title']:
                match += 1
                
            tracks[track] = match
            
        tracks = sorted(tracks.items(), key=lambda x: x[1], reverse=True)
        print(tracks[0][0])

        base64 = tracks[0][0].track
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
                
                if not("playlistInfo" in info.keys()):
                    return LoadResult(LoadType.TRACK, tracks, playlist_info=PlaylistInfo.none())

                else:
                    return LoadResult(LoadType.PLAYLIST, tracks, playlist_info=PlaylistInfo(info['playlistInfo']['name']))