from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
from Utils import make_file_copy, template_engine
import YouTubeToSpotify as yts
from YouTubeToSpotify import setup, get_spotify_playlist
host = 'localhost'
port = 8000


url_dict = {'/spotify-client-id':'SPOTIPY_CLIENT_ID', '/spotify-secert-id':'SPOTIPY_CLIENT_SECRET', '/spotify-username':'SPOTIFY_USERNAME', '/youtube-api-key':'YOUTUBE_API_KEY', '/youtube-channel-id':'YOUTUBE_CHANNEL_ID'};


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if '.' not in str(self.path):
            file_type = [str(self.path), '']
        else:
            file_type = str(self.path).split('.')

        print('path is %s' % (self.path))

        if self.path.endswith('/'):
            self.send_response(200)
            self.send_header("content-type", "text/html")
            self.end_headers()
            f = open('Index.html', 'r').read()
            try:
                playlist_names, spotify_token = setup()
                print('setup complete')
                spotify_playlist_names = get_spotify_playlist(spotify_token)
                print('spotify playlist obtained')
                f = template_engine(f, playlist_names, spotify_playlist_names)
                print('template engine applied')
                f = unicode(f, "utf-8")
            except:
                print('oops')
            self.wfile.write(f.encode())
        elif file_type[1] == 'html' and str(self.path)[1:] in os.listdir():
            prinr(file_type[1])
            self.send_response(200)
            self.send_header("content-type", "text/html")
            self.end_headers()
            f = open(file_type[0][1:] + '.html', 'r').read()
            self.wfile.write(f.encode())
        elif self.path.endswith('/Style.css'):
            self.send_response(200)
            self.send_header("content-type", "text/css")
            self.end_headers()
            f = open('Style.css', 'r').read()
            self.wfile.write(f.encode())
        elif file_type[1] == 'png' and str(self.path)[1:].split('/')[1] in os.listdir('logos'):
            self.send_response(200)
            self.send_header("content-type", "image/png")
            self.end_headers()
            f = open(file_type[0][1:] + '.png', 'rb').read()
            self.wfile.write(f)
        elif self.path.endswith('/Script.js'):
            self.send_response(200)
            self.send_header("content-type", "text/js")
            self.end_headers()
            f = open('script.js', 'r').read()
            self.wfile.write(f.encode())
        else:
            self.send_response(404)
            self.send_header("content-type", "text/html")
            self.end_headers()
            f = open('404_Error.html', 'r').read()
            self.wfile.write(f.encode())

    def do_POST(self):
        print()
        for path in url_dict.keys():
            if self.path.endswith(path):
                length = int(self.headers.get('content-length'))
                data = self.rfile.read(length).decode().split('=')
                data_type = data[0]
                key = data[1]
                print(data_type, key)
                yts.edit_client(url_dict['/'+data_type], key)
                self.send_response(200)
                self.send_header("content-type", "text/txt")
                response = json.dumps({'fail': False})
                print(response)
                self.send_header("content-length", str(len(bytes(str(response).encode()))))
                self.end_headers()
                self.wfile.write(bytes(str(response).encode()))
                break

if __name__ == "__main__":
    server = HTTPServer((host, port), handler)
    print('Server started on http://%s:%s' % (host, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

        server.server_close()
        print('server closed')
