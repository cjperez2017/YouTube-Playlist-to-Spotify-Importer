
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
import os
from googleapiclient.discovery import build
from youtube_title_parse import get_artist_title
import copy
import sys
from Utils import make_file_copy, to_rnji, to_kana
import recordlinkage
from fuzzywuzzy import process, fuzz
import cutlet
import queue


class Spotify:

    def __init__(self, youtube):
        self.youtube = youtube
        self.environment_setup()
        self.spotify_token = None
        self.username = None
        self.create_spotify_token()
        self.spotify_playlist_id = None
        self.spotify_playlist = None
        self.song_not_found_queue = queue.Queue()
        self.unfound_songs = [] #(youtube title, channel name, song, artist)

    def set_spotify_token(self, spotify_token):
        self.spotify_token = spotify_token

    def set_spotify_playlist_id(self, spotify_playlist_id):
        self.spotify_playlist_id = spotify_playlist_id

    def set_spotify_playlist(self, spotify_playlist):
        self.spotify_playlist = spotify_playlist

    def set_username(self, username):
        self.username = username

    def environment_setup(self):
        f = open('client', 'r')
        for line in f.readlines():
            client = line.split(' ')
            client[1] = client[1].replace('\n', '')
            env_var_name = client[0]
            os.environ[env_var_name] = client[1]
        f.close()

    def get_spotify_playlists(self):
        """
        Gets all Spotify playlist which are owned by the user who's username is in the client file
        Puts dict {key: playlist_name, value: playlist_id}
        """
        spotify_playlist = {}
        for item in self.spotify_token.current_user_playlists()['items']:
            if item['owner']['id'] == self.username:
                spotify_playlist[item['name']] = item['id']
                print(item['name'])
        self.spotify_playlist = spotify_playlist

    def create_spotify_token(self):
        """
        Creates the spotify token and calls set_spotify_token
        """
        scope = 'playlist-read-private playlist-modify-private playlist-modify-public'
        with open('client', 'r') as f:
            username = f.readlines()[5].split(' ')[1]
            self.username = username.strip()
        prompt_token = util.prompt_for_user_token(username=username, scope=scope)
        token = spotipy.Spotify(prompt_token)
        self.set_spotify_token(token)

    def select_playlist(self, playlist_name):
        if playlist_name not in self.spotify_playlist.keys():
            description = ''
            self.spotify_token.user_playlist_create(self.username, playlist_name, public=True, description=description)

        for item in self.spotify_token.current_user_playlists()['items']:
            if item['owner']['id'] == self.username and item['name'] == playlist_name:
                list_id = item['id']
                self.set_spotify_playlist_id(list_id)
                break

    def add_songs_to_spotify_playlist(self):
        new_tracks = self.make_track_list()  # put song ids in here
        if len(self.spotify_token.user_playlist(self.username, playlist_id=self.spotify_playlist_id)['tracks']['items'])>0:
            tracks_in_playlist = [x['track']['id'] for x in
                                  self.spotify_token.user_playlist(self.username, playlist_id=self.spotify_playlist_id)['tracks']['items']]
            new_tracks = [track for track in new_tracks if track not in tracks_in_playlist]
        if len(new_tracks) > 0:
            self.spotify_token.user_playlist_add_tracks(self.username, self.spotify_playlist_id, new_tracks)
            tracks_in_playlist = [x['track']['id'] for x in
                                  self.spotify_token.user_playlist(self.username, playlist_id=self.spotify_playlist_id)[
                                      'tracks']['items']]
            not_found = [track for track in new_tracks if track not in tracks_in_playlist]
            print('not found:', not_found)

    def verify_match_score(self):
        pass

    def artist_parser(self, artist):
        """
                :param artist:
                :return: 1st val is the name of artist(s)
                         2nd val is a list of features
                """
        artist = artist.lower()
        feature_indicator_list = [' ft ', ' ft. ', ' feat ', ' feat. ', ' x ', '×', ' & ', ', ']
        for ft_type in feature_indicator_list:
            if ft_type in artist:
                artist = artist.split(ft_type)
                break
        # in case of layered features
        for ft_type in feature_indicator_list:
            if ft_type in artist[0]:
                temp = artist[0].split(ft_type)
                artist = artist[1:]
                artist.insert(0, temp[0])
                temp = temp[1:]
                for elem in temp:
                    artist.append(elem)
                break

        if type(artist) is list:
            main = artist[0]
            artist = ", ".join(artist[1:])
            artist = main + ' ft ' + artist
        artist = artist.strip()
        if ' ft ' in artist:
            artist_list = artist.split(' ft ')
            return artist_list[0].strip(), artist_list[1]
        return artist, []

    def get_list_of_artist_that_matches_youtube_artist(self, res, artist):
        artists_of_same_name_ids = []
        if len(res['artists']['items']) > 0:
            print('searching for artist:', artist)
            for artista in res['artists']['items']:
                # print('MULTI for:', artist, 'vs', artista['name'].lower())
                num_of_matches = 0
                if artista['name'].lower().strip() == artist.lower().strip() or artista['name'].replace(' ', '').lower().strip() == artist.replace(' ', '').lower().strip():
                    artists_of_same_name_ids.append(artista['id'])
                    # print('PERFECT', artista['name'])
                    num_of_matches += 1
            print(num_of_matches, 'potential match(es)')
        return artists_of_same_name_ids

    def get_track_list_from_artist_list(self, artists_of_same_name_ids):
        all_artist_tracks = {}
        for artist_id in artists_of_same_name_ids:
            for album in self.spotify_token.artist_albums(artist_id, limit=30)['items']:
                if 'US' not in album['available_markets']:
                    continue
                try:
                    for track in self.spotify_token.album_tracks(album['id'])['items']:
                        all_artist_tracks[track['name'].lower()] = track['id']
                except spotipy.exceptions.SpotifyException:
                    pass
        return all_artist_tracks

    def track_parser(self, track):
        if ' ft' in track or 'feat' in track:
            if 'ft.' in track:
                return track[:track.index('ft.')]
            elif 'feat.' in track:
                return track[:track.index('feat.')]
            elif 'ft' in track:
                return track[:track.index('ft')]
            elif 'feat' in track:
                return track[:track.index('feat')]
        return track

    def make_track_list(self):
        track_list = []
        for key in self.youtube.songs.keys():
            song = self.youtube.songs[key]
            track_adding = song[0].lower()
            artist = song[1].lower()
            print('SONG:', track_adding, 'by', artist)
            artist, features = self.artist_parser(artist)
            track_adding = self.track_parser(track_adding)
            artist = artist.strip()
            print('ARTIST: ', artist, 'FT', features)
            q = 'artist:' + artist
            res = self.spotify_token.search(q, limit=30, offset=0, type='artist')

            artists_of_same_name_ids = self.get_list_of_artist_that_matches_youtube_artist(res, artist)
            if len(artists_of_same_name_ids) == 0:
                print('Could not find artist:', artist)
                self.unfound_songs.append((key[0], key[1], song[0], song[1]))
                continue
            all_artist_tracks = self.get_track_list_from_artist_list(artists_of_same_name_ids)

            track_id, best_match = self.select_matching_track(all_artist_tracks, track_adding, features)

            if track_id is not None:
                # if int(best_match[0][0]) < 50:
                print('partial ratio:', fuzz.partial_ratio(track_adding, best_match[0][0]))
                if fuzz.partial_ratio(track_adding, best_match[0][0].lower()) <= 75 and int(best_match[0][1])<70:
                    print('not found:', key, best_match)
                    self.unfound_songs.append((key[0], key[1], song[0], song[1]))
                else:
                    print('guess:', key, best_match)
                    track_list.append(track_id)
        return track_list

    def add_to_spotify(self, playlist_name):
        self.select_playlist(playlist_name)
        self.add_songs_to_spotify_playlist()
        self.add_to_spotify_part2()

    def add_to_spotify_part2(self):
        print('round 1 unfound songs:', self.unfound_songs)

        self.youtube.songs = {}
        unfound_songs = self.unfound_songs
        self.unfound_songs = []
        for song in unfound_songs:
            self.youtube.songs[(song[0], song[1])] = (song[3], song[2])  #(youtube title, channel name, song, artist)
        self.add_songs_to_spotify_playlist()
        print('round 2 unfound songs:', self.unfound_songs)

        self.youtube.songs = {}
        unfound_songs = self.unfound_songs
        self.unfound_songs = []
        for song in unfound_songs:
            self.youtube.songs[(song[0], song[1])] = (song[0], song[1])
        self.add_songs_to_spotify_playlist()
        print('round 3 unfound songs:', self.unfound_songs)



    def select_matching_track(self, all_artist_tracks: dict, track_adding: str, features):
        """
        :param features:
        :param all_artist_tracks: dict{keys=all track names of the artist,value=track id associated with the key}
        :param track_adding: str the track name you are searching for
        :return: The song id of the best matched track
        """

        best_match = []
        list_of_all_artist_tracks = list(all_artist_tracks.keys())

        temp_list = list_of_all_artist_tracks + to_rnji(list_of_all_artist_tracks)
        best_match.append(process.extractOne(to_kana(track_adding), temp_list))

        temp_list += to_kana(list_of_all_artist_tracks)
        best_match.append(process.extractOne(track_adding, temp_list))

        temp_list = list_of_all_artist_tracks + to_kana(list_of_all_artist_tracks)
        best_match.append(process.extractOne(to_rnji(track_adding), temp_list))

        best_match.sort(key=lambda x: x[1], reverse=True)

        for item in list_of_all_artist_tracks:
            if item == best_match[0][0]:
                print(item, best_match[0][0])
                return all_artist_tracks[item], best_match
            elif to_rnji(item) == best_match[0][0]:
                print(item, best_match[0][0])
                return all_artist_tracks[item], best_match
            elif to_kana(item) == best_match[0][0]:
                print(item, best_match[0][0])
                return all_artist_tracks[item], best_match

        return all_artist_tracks[best_match[0][0]], best_match
