import os
import pykakasi
import romajitable
from fuzzywuzzy import process, fuzz
import cutlet
# from googletrans import Translator


def make_file_copy(file_name):
    file = open(file_name, 'rt')
    if '.' in file_name:
        file_info = file_name.split('.')
        path = file_info[0] + '_copy.' + file_info[1]
    else:
        path = file_name + '_copy'

    file_copy = open(path, 'w')

    for line in file.readlines():
        file_copy.write(line)

    file.close()

    return open(path, 'rt'), path


def setup_enviornment():
    # os.system('python3 -m pip install --user virtualenv')
    os.system('python3 -m venv env')
    os.system('source env/bin/activate')
    os.system('pip3 install -r requirments.txt')


def list_youtube_playlist(playlist_names):
    ans = ''
    for playlist in playlist_names.keys():
        ans += '<form action="/' + playlist + '" class="youtube-playlist-form" id="' + playlist + '">' \
               + playlist + '<button name="' + playlist + '" type="submit">Select</button>' + \
               '</form>\n<br/><br/>\n'
        # ans += '<span>' + playlist + '<button class="youtube-playlist-button" id="' + playlist + '">Select</button></span>\n<br/><br/>\n'
    return ans


def template_engine(read_file, playlist_names, spotify_playlist_names):
    i = 0
    while True:
        try:
            front_i = read_file.index('{{')
            back_i = read_file.index('}}')
            template = read_file[front_i + len('{{'):back_i]
            if template == 'list_youtube_playlist':
                read_file = read_file.replace('{{list_youtube_playlist}}', list_youtube_playlist(playlist_names))
            elif template == 'list_spotify_playlist':
                read_file = read_file.replace('{{list_spotify_playlist}}',
                                              list_spotify_playlist(spotify_playlist_names))
        except ValueError:
            break
    return read_file


def list_spotify_playlist(playlist_names):
    ans = ''
    for playlist in playlist_names.keys():
        ans += '<span>' + playlist + '<button class="spotify-playlist-button" id="' + playlist + '">Select</button></span>\n<br/><br/>\n'
    return ans


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


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


def print_spreadsheet(songs, append=False):
    if append:
        f = open('song_list.csv', 'a')
    else:
        f = open('song_list.csv', 'w')
    f.writelines('Title, Channel Name, Song, Artist\n')
    for x in songs.keys():
        parts = (x[0], x[1], songs[x][1], songs[x][0])
        ex = ''
        for part in parts:
            if ',' in part:
                ex = ex + '"' + part + '", '
            else:
                ex = ex + part + ', '
            ex = ex[:-1]
        ex = ex + '\n'
        f.writelines(ex)


def to_kana(word):
    if type(word)==list:
        ans = []
        for w in word:
            ans.append(to_kana(w))
        return ans
    else:
        word = word.replace(' ', '')
        result = romajitable.to_kana(word)
        return result.katakana


def to_rnji(word):
    if type(word) == list:
        ans = []
        for w in word:
            ans.append(to_rnji(w))
        return ans
    else:
        katsu = cutlet.Cutlet()
        rnji = katsu.romaji(word)
        return rnji


def get_match_ratio(string1: str, string2: str):
    """

    :param string1: first string to compare
    :param string2: second string to compare
    :return: The match ratio
    """
    return fuzz.WRatio(string1,string2)

# def translate_to_eng(word):
#     if type(word)==list:
#         ans = []
#         for w in word:
#             ans.append(translate_to_eng(w))
#         return ans
#     else:
#         translator = Translator()
#         result = translator.translate(word)
#         return result.text
