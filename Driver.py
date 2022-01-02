import YouTube as youtube
import Spotify as spotify
import Utils
if __name__ == "__main__":

    yt = youtube.YouTube()
    yt.get_youtube_playlist()
    p = input('Playlist Name: ')
    yt.set_youtube_playlist_id(yt.youtube_playlist[p])
    yt.get_songs_from_playlist_id()
    Utils.print_spreadsheet(yt.songs)

    s = spotify.Spotify(yt)
    s.get_spotify_playlists()
    p = input('Playlist to add songs to: ')
    s.add_to_spotify(p)

