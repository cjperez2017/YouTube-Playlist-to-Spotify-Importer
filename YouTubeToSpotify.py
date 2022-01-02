import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import os
from googleapiclient.discovery import build
from youtube_title_parse import get_artist_title
import copy
import sys
from Utils import make_file_copy

def main():
    environment_setup()
    token, username = spotify_tokens()
    s = spotipy.Spotify(token)

    songs = get_youtube_playlist()

    spotify_playlist_names = {}
    for item in s.current_user_playlists()['items']:
        if item['owner']['id'] == username:
            spotify_playlist_names[item['name']] = item['id']
            print(item['name'])
    playlist_name = input('Which playlist would you like to add to (If you want to make a new playlist pick a unique name)?: ')

    list_id = spotify_playlist_names.get(playlist_name, False)
    add_to_spotify(songs, s, playlist_name, list_id)

def environment_setup():
    f = open('client', 'r')
    for line in f.readlines():
        client = line.split(' ')
        client[1] = client[1].replace('\n', '')
        env_var_name = client[0]
        os.environ[env_var_name] = client[1]
    f.close()

def setup():
    environment_setup()
    token, username = spotify_tokens()
    s = spotipy.Spotify(token)

    songs = get_youtube_playlist_site()

    return songs, s

def get_youtube_playlist_site():
    api_key = os.environ['YOUTUBE_API_KEY']
    youtube = build('youtube', 'v3', developerKey=api_key)

    request = youtube.playlists().list(
        part='snippet',
        channelId=os.environ['YOUTUBE_CHANNEL_ID'],
        maxResults=50
    )
    response = request.execute()
    print('youtube_playlist')
    print('----------------')
    playlist = {}
    for item in response['items']:
        playlist[item['snippet']['title']] = item['id']
        print(item['snippet']['title'])
    return playlist

def get_songs_from_playlist_id(playlist_id):
    request = youtube.playlistItems().list(
        part='snippet',
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()

    songs = {}
    for item in response['items']:
        video_title = item['snippet']['title']
        video_id = item['snippet']['resourceId']['videoId']
        request = youtube.videos().list(
            part='snippet',
            id=video_id
        )
        response = request.execute()
        channel_id = response['items'][0]['snippet']['channelId']
        request = youtube.channels().list(
            part='snippet',
            id=channel_id
        )
        response = request.execute()
        channel_name = response['items'][0]['snippet']['title']
        video_title = video_title.replace('(Official Audio)', '')
        if '|' in video_title:
            video_title = video_title[:video_title.index('|')]
        channel_name = channel_name.replace('- Topic', '').replace(',', '')
        songs[(video_title, channel_name)] = get_artist_title(video_title)

    songs = fix_artist_and_song_prediction(songs)
    return songs.values()

def get_spotify_playlist(spotify_token):
    spotify_playlist_names = {}
    username = os.environ['SPOTIFY_USERNAME']
    print('spotify_playlist')
    print('----------------')
    for item in spotify_token.current_user_playlists()['items']:
        if item['owner']['id'] == username:
            spotify_playlist_names[item['name']] = item['id']
            print(item['name'])
    return spotify_playlist_names

def edit_client(property_name, property_info):
    file_copy, path = make_file_copy('client')
    file = open('client', 'w')
    for line in file_copy:
        print(line)
        split_line = line.split(' ')
        print(split_line)
        if property_name == split_line[0]:
            file.write(property_name + ' ' + property_info + '\n')
        else:
            file.write(line)
    file_copy.close()
    file.close()
    os.system('rm client_copy')

def spotify_tokens():
    scope = 'playlist-read-private playlist-modify-private playlist-modify-public'
    username = os.environ['SPOTIFY_USERNAME']
    token = util.prompt_for_user_token(username, scope)
    return (token, username)


def get_youtube_playlist():
    api_key = os.environ['YOUTUBE_API_KEY']
    youtube = build('youtube', 'v3', developerKey=api_key)

    request = youtube.playlists().list(
        part='snippet',
        channelId=os.environ['YOUTUBE_CHANNEL_ID'],
        maxResults=50
    )
    response = request.execute()
    playlist = {}
    for item in response['items']:
        playlist[item['snippet']['title']] = item['id']
        print(item['snippet']['title'])
    playlist_name = input('Which playlist would you like to import? (type name exactly): ')
    playlist_id = playlist[playlist_name]

    request = youtube.playlistItems().list(
        part='snippet',
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()

    songs = {}
    for item in response['items']:
        video_title = item['snippet']['title']
        video_id = item['snippet']['resourceId']['videoId']
        request = youtube.videos().list(
            part='snippet',
            id=video_id
        )
        response = request.execute()
        channel_id = response['items'][0]['snippet']['channelId']
        request = youtube.channels().list(
            part='snippet',
            id=channel_id
        )
        response = request.execute()
        channel_name = response['items'][0]['snippet']['title']
        video_title = video_title.replace('(Official Audio)', '')
        if '|' in video_title:
            video_title = video_title[:video_title.index('|')]
        channel_name = channel_name.replace('- Topic', '').replace(',', '')
        songs[(video_title, channel_name)] = get_artist_title(video_title)

    songs = fix_artist_and_song_prediction(songs)
    print_spreadsheet(songs)
    return songs.values()


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def fix_artist_and_song_prediction(songs):
    for x in songs.keys():
        if songs[x] is None:
            songs[x] = (x[1], x[0])
        if is_int(songs[x][0]):
            songs[x] = (x[1], x[0])
        lamPlace = lambda a: a.replace(', ', '').lower()
        title, switch = song_parser(songs[x][1])
        artist, feat = artist_parser(songs[x][0])

        title = lamPlace(title)
        artist = lamPlace(artist)

        no_ft = title
        if 'ft' in no_ft:
            no_ft = no_ft[:no_ft.index('ft')]
        if no_ft.replace(' ', '') in x[1].replace(' ', '').lower():
            switch = 'switch'

        if switch == 'switch':
            temp = copy.copy(artist)
            artist = title
            title = temp
        elif 'change to' in switch:
            artist = switch[switch.index('(') + 1: switch.index(')')]
        songs[x] = (title, artist)
    return songs


def print_spreadsheet(songs):
    f = open('song_list.csv', 'w')
    f.writelines('Title, Channel Name, Artist, Song Name\n')
    for x in songs.keys():
        parts = (x[0], x[1], songs[x][1], songs[x][0])
        ex = ''
        for part in parts:
            if ',' in part:
                ex = ex + '"' + part + '", '
            else:
                ex = ex + part + ', '
        ex = ex + '\n'
        f.writelines(ex)
    # exit()


def add_to_spotify(songs, s, playlist_name, list_id):
    username = os.environ['SPOTIFY_USERNAME']
    if list_id is False:
        response = input(
            'Would you like this playlist to be public and/or to put a description? (yes/no) (yes/no) ex: "yes yes" or "no yes": ')
        response = response.split(' ')
        if response[0] == 'yes' or response[0] == 'y':
            public = True
        else:
            public = False
        description = ''
        if response[1] == 'yes' or response[1] == 'y':
            description = input('Please input the description you would like the playlist to have: ')
        s.user_playlist_create(username, playlist_name, public=public, description=description)
        for item in s.current_user_playlists()['items']:
            if item['owner']['id'] == username and item['name'] == playlist_name:
                list_id = item['id']
                break

    new_tracks = make_track_list(songs, s)  # put song ids in here
    if len(s.user_playlist(username, playlist_id=list_id)['tracks']['items']) > 0:
        tracks_in_playlist = [x['track']['id'] for x in
                              s.user_playlist(username, playlist_id=list_id)['tracks']['items']]
        new_tracks = [track for track in new_tracks if track not in tracks_in_playlist]
    if len(new_tracks) > 0:
        s.user_playlist_add_tracks(username, list_id, new_tracks)


def make_track_list(songs, s):
    track_list = []
    for song in songs:
        features = False
        track_adding = song[0]
        artist = song[1].lower()

        if 'ft' in artist:
            artist_list = artist.split(' ft ')
            artist = artist_list[0]
            features = artist_list[1]

        q = 'artist:' + artist
        res = s.search(q, limit=30, offset=0, type='artist')

        if len(res['artists']['items']) > 0:
            artists_of_same_name_ids = []
            for artista in res['artists']['items']:
                # print('MULTI for:', artist, 'vs', artista['name'].lower())
                if artista['name'].lower() == artist:
                    # artist_id = artista['id']
                    artists_of_same_name_ids.append(artista['id'])
                    # print('PERFECT', artista['name'].lower())
            if len(artists_of_same_name_ids) == 0:
                print('Could not find artist:', artist)
                continue

        all_artist_tracks = {}
        for artist_id in artists_of_same_name_ids:
            for album in s.artist_albums(artist_id, limit=30)['items']:
                if 'US' not in album['available_markets']:
                    continue
                try:
                    for track in s.album_tracks(album['id'])['items']:
                        all_artist_tracks[track['name'].lower()] = track['id']
                except spotipy.exceptions.SpotifyException:
                    pass
        # print(artist)
        # print(all_artist_tracks)
        track_id = select_matching_track(all_artist_tracks, track_adding.lower(), features)
        if track_id is not None:
            track_list.append(track_id)
    return track_list


def select_matching_track(all_artist_tracks, track_adding, features):
    best_match = (0, None)
    track_name = track_adding

    if ' ' in track_adding:
        track_adding = track_adding.split(' ')
    else:
        track_adding = [track_adding]

    if features is not False:
        track_adding.append(features)

    for track in all_artist_tracks.keys():

        match_count = 0
        key = track
        if ' ' in track:
            track = track.split(' ')
        else:
            track = [track]

        for word_a in track:
            for word_b in track_adding:
                if word_a == word_b:
                    match_count += 1
                else:
                    match_count -= .001
        if 'live' in track_name and 'live' not in track or 'live' not in track_name and 'live' in track:
            match_count -= 0.01
        if 'remix' in track_name and 'remix' not in track or 'remix' not in track_name and 'remix' in track:
            match_count -= 0.01

        if 'pa mi' in track_name and match_count > .7:
            print(track, match_count)

        if match_count > best_match[0]:
            best_match = (match_count, all_artist_tracks[key])

    if best_match[1] is None:
        print('\"' + track_name + '\"', 'could not be found')

    return best_match[1]


def artist_parser(artist):
    """

    :param artist:
    :return: 1st val is the name of artist(s)
             2nd val is a bool that is True if the artist includes features
    """
    artist = artist.lower()
    feat = False
    if 'ft' in artist:
        artist = artist.split(' ft ')
    elif 'feat.' in artist:
        artist = artist.split(' feat. ')
    elif 'feat' in artist:
        artist = artist.split(' feat ')
    elif ',' in artist:
        artist = artist.split(', ')
    elif ' x ' in artist:
        artist = artist.split(' x ')

    if type(artist) is list:
        main = artist[0]
        feat = True
        artist = " ".join(artist[1:])
        artist = main + ' ft ' + artist
    if artist[-1] == ' ':
        while artist[-1] == ' ':
            artist = artist[:-1]
    # print(artist)
    return artist, feat


def song_parser(song):
    """
    :param song: A string that is expected to hold the name of a song, or artist if a mistake was made
    :return: ret val 1 is the song info in a list format
             ret val 2 is a bool True means song and artist must be switched
    """
    switch = ''
    song = song.lower().replace(' with', '').replace(' lyrics', '')
    if ' x ' in song:
        song = song.split(' x ')
        song = song[0] + ' ft ' + str(song[1:])[1:-1].replace('\'', '').replace('\\n', '\n')
        song = song.replace(',', '')
        switch = 'switch'

    if ' by ' in song:
        working_song = song.split(' ')
        next_one = False
        for s in working_song:
            if next_one:
                art = s
                break
            elif s == 'by':
                next_one = True
        switch = 'change to (' + art + ')'
        song = song.replace('by ', '').replace(art + ' ', '')

    # if '(' in song and ')' in song:
    #     i_open = song.index('(')
    #     i_close = song.index(')')
    #     song = song[:i_open] + song[i_close + 1:]

    if song[-1] == ' ':
        while song[-1] == ' ':
            song = song[:-1]

    return song, switch


if __name__ == '__main__':
    main()
