# YouTube-Playlist-to-Spotify-Importer
Converts a public YouTube playlist which contains songs to a Spotify Playlist linked to your account.

# What you will need:
  - A **SPOTIPY_CLIENT_ID** which you can get from the developers page from Spotify
  - A **SPOTIPY_CLIENT_SECRET** which you can get from the developers page from Spotify
  - A **YOUTUBE_API_KEY** which you can get from google apis. You want the one for youtube data
  - A **YOUTUBE_CHANNEL_ID** which you can get from YouTube. Just copy the channel id from the URL

# How to use
  1. Fill in the needed information in the **client** file
  2. Then run **python3 YouTubeToSpotify.py**
  3. Respond to the prompts in the console (make sure you spell the playlist names correctly)

# Notes
  - You must pick an existing YouTube playlist to import
  - The YouTube playlist must be **public**
  - If you want to create a new Spotify Playlist you must enter a name for the playlist that is different from the other play list you own 
    
    - EX: If you have 2 playlist **songs** and **favorites** and you want to create a listlist call **youtube** type **youtube** when asked to select  
           a spotify playlist
  - If you want to add to an existing playlist select a playlist name which you already own
  - Playlist in spotify can be public or private but must be owned by you
  - If a song is already in the playlist it will not be added again (one copy of a song for playlist)
  - Playlist are made based on the name of the song from youtube and sometimes the channel name. For best results please use the official versions of the songs and/or videos with straight forward titles
  - Mistakes are possible, double checking the playlist is encouraged 
  
