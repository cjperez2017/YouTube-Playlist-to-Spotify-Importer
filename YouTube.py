import os
from googleapiclient.discovery import build
from youtube_title_parse import get_artist_title
from googleapiclient.errors import HttpError
import copy
from Utils import is_int
from difflib import SequenceMatcher


def simplify_channel_name(channel_name):
    channel_name = channel_name.lower()
    channel_name = channel_name.replace('- topic', '').replace(',', '').replace('official', '').replace('vevo', '')
    channel_name = channel_name.replace('youtube channel', '').replace('youtube', '')
    return channel_name.strip()


def simplify_video_title(title):
    title = title.lower()
    title = title.replace('(Official Audio)', '').replace('(Music Video)', '')
    if '|' in title:
        title = title[:title.index('|')]
    return title.strip()


class YouTube:

    def __init__(self):
        self.youtube_playlist = None
        self.youtube_token = None
        self.youtube_channel_id = None
        with open('client', 'r') as f:
            f = f.readlines()
            youtube_api_key = f[3].split(' ')[1].strip()
            self.create_youtube_token(youtube_api_key)
            self.youtube_channel_id = f[4].split(' ')[1].strip()
        self.songs = None
        self.youtube_playlist_id = None

    def set_youtube_playlist_id(self, youtube_playlist_id):
        self.youtube_playlist_id = youtube_playlist_id

    def create_youtube_token(self, youtube_api_key):
        try:
            self.youtube_token = build('youtube', 'v3', developerKey=youtube_api_key)
        except HttpError:
            print('Youtube API Key not accepted')
            self.youtube_token = None

    def set_playlist_dict(self, playlist_names):
        self.youtube_playlist = playlist_names

    def set_songs(self, songs):
        if self.songs is None:
            self.songs = songs
        else:
            self.songs.update(songs)

    def get_youtube_playlist(self):
        youtube = self.youtube_token

        request = youtube.playlists().list(
            part='snippet',
            channelId=self.youtube_channel_id,
            maxResults=50
        )

        response = request.execute()
        print('youtube_playlist')
        print('----------------')
        playlist = {}
        for item in response['items']:
            playlist[item['snippet']['title']] = item['id']
            print(item['snippet']['title'])

        self.set_playlist_dict(playlist)

    def get_channel_name(self, channel_id):
        response = self.youtube_token.channels().list(
            part='snippet',
            id=channel_id
        ).execute()
        channel_name = simplify_channel_name(response['items'][0]['snippet']['title'])
        return simplify_channel_name(channel_name)

    def get_songs_from_playlist_id(self, nextPageToken=None):
        if nextPageToken is None:
            request = self.youtube_token.playlistItems().list(
                part='snippet',
                playlistId=self.youtube_playlist_id,
                maxResults=50
            )
        else:
            request = self.youtube_token.playlistItems().list(
                part='snippet',
                playlistId=self.youtube_playlist_id,
                maxResults=50,
                pageToken=nextPageToken
            )
        playlist_list_response = request.execute()

        songs = {}
        for item in playlist_list_response['items']:
            video_title = item['snippet']['title']
            video_title = simplify_video_title(video_title)
            video_id = item['snippet']['resourceId']['videoId']
            request = self.youtube_token.videos().list(
                part='snippet',
                id=video_id
            )
            response = request.execute()

            if len(response['items']) == 0:
                continue

            channel_name = self.get_channel_name(response['items'][0]['snippet']['channelId'])

            songs[(video_title, channel_name)] = get_artist_title(video_title)
        for x in songs.keys():
            video_title = x[0]
            channel_name = x[1]
            if songs[x] is None:
                # If no prediction for key -> channel_name is artist and title is song name
                songs[x] = (video_title, channel_name)
        self.set_songs(songs)

        # self.fix_artist_and_song_prediction()
        if 'nextPageToken' in playlist_list_response:
            nextPageToken = playlist_list_response.get('nextPageToken')
            self.get_songs_from_playlist_id(nextPageToken)

    def artist_parser(self, artist):
        """
        :param artist:
        :return: 1st val is the name of artist(s)
                 2nd val is a bool that is True if the artist includes features
        """
        artist = artist.lower()
        feat = False
        feature_indicator_list = [' ft ', ' ft. ', ' feat ', ' feat. ', ' x ', ' & ', ', ']

        for ft_type in feature_indicator_list:
            if ft_type in artist:
                artist = artist.split(ft_type)
                break

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
            feat = True
            artist = " ".join(artist[1:])
            artist = main + ' ft ' + artist
        artist = artist.strip()

        return artist, feat

    def song_parser(self, song):
        """
        :param song: A string that is expected to hold the name of a song, or artist if a mistake was made
        :return: ret val 1 is the song info in a list format
                 ret val 2 is a bool True means song and artist must be switched
        """
        switch = False
        song = song.lower()

        if ' by ' in song:
            i = song.index(' by ')
            art = song[i + len(' by '):]
            switch = art
            song = song[:i]

        song = song.strip()
        return song, switch

    def fix_artist_and_song_prediction(self):
        songs = self.songs
        # songs[(video_title, channel_name)] = (artist, title)
        for x in songs.keys():
            video_title = x[0]
            channel_name = x[1]
            if songs[x] is None:
                # If no prediction for key -> channel_name is artist and title is song name
                songs[x] = (channel_name, video_title)
            lamPlace = lambda a: a.replace(',', '').lower()
            print(songs)
            title, switch = self.song_parser(songs[x][1])
            artist, feat = self.artist_parser(songs[x][0])

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
            else:
                artist = switch

            songs[x] = (title, artist)
        self.set_songs(songs)
# 90%
