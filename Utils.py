import os

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
        ans += '<span>'+playlist+'<button class="youtube-playlist-button" id="'+playlist+'">Select</button></span>\n<br/><br/>\n'
    return ans

def template_engine(read_file, playlist_names, spotify_playlist_names):
    i = 0
    while True:
        try:
            front_i = read_file.index('{{')
            back_i = read_file.index('}}')
            template = read_file[front_i+len('{{'):back_i]
            if template == 'list_youtube_playlist':
                read_file = read_file.replace('{{list_youtube_playlist}}', list_youtube_playlist(playlist_names))
            elif template == 'list_spotify_playlist':
                read_file = read_file.replace('{{list_spotify_playlist}}', list_spotify_playlist(spotify_playlist_names))
        except ValueError:
            break
    return read_file

def list_spotify_playlist(playlist_names):
    ans = ''
    for playlist in playlist_names.keys():
        ans += '<span>'+playlist+'<button class="spotify-playlist-button" id="'+playlist+'">Select</button></span>\n<br/><br/>\n'
    return ans


# setup_enviornment()
