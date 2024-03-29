import pandas as pd
from argparse import ArgumentParser
import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
from spotipy import oauth2
from spotipy.oauth2 import SpotifyClientCredentials
import os
from datetime import datetime

## few thoughts:
#   1. use artists to pull songs that users haven't listened to but may be interested in
#       - using Spotify API to pull in songs from discography

## remaining work:
#   - set-up autehntication key/register app for API key
#       - this will be used for all users/friends, I guess
#   - figure out how to create playlists
#       - will have to be public and send link via email

def shuffler(shuffle):
    """
    Main shuffling/random smapling function

    This aims to reduce the bias and weighting of heavy binging on certain artists and may help find 
    previously lost gems in listening history. Basically, an artist can only appear once, if they appear more
    than once, we randomly selct one and then move on, removing the rest. 
    """

    norm_dist = shuffle['artistName'].value_counts()
    for artist in norm_dist.index:
        if norm_dist[artist] > 1:
            artist_subsample = shuffle[shuffle['artistName'] == artist].reset_index().sample(replace=False, n=1, random_state=42)
            shuffle = shuffle[shuffle['artistName'] != artist]

            shuffle = pd.concat([shuffle,artist_subsample]).reset_index().drop(['index','level_0'],axis=1)

    return(shuffle)

def download_file_from_google_drive(file_id, destination):
    URL = "https://docs.google.com/uc?export=download&confirm=1"

    session = requests.Session()

    response = session.get(URL, params={"id": file_id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {"id": file_id, "confirm": token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value

    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

def get_spotify_ids(shuffle):

    track_dict = {}

    for tracks in shuffle.iterrows():

        album_track_id = ''
        single_track_id = ''
        compilation_track_id = ''
        
        has_album_version = 0
        has_single = 0

        artist = tracks[1]['artistName']
        song_name = tracks[1]['trackName'].replace("'","")

        track_dict['{}_{}'.format(artist,song_name)] = ''

        try:
            track_id = sp.search(q='artist:' + artist + ' track:' + song_name , type='track')
        except Exception as e:
            print(e)
        
        for item in track_id['tracks']['items']:
            if item['album']['album_type'] == 'album':
                has_album_version = 1
                album_track_id = item['id']
            elif item['album']['album_type'] == 'single':
                has_single = 1
                single_track_id = item['id']
            elif item['album']['album_type'] == 'compilation':
                compilation_track_id = item['id']

        if has_album_version == 1:
            track_dict['{}_{}'.format(artist,song_name)] = album_track_id
        elif (has_album_version == 0) & (has_single == 1):
            track_dict['{}_{}'.format(artist,song_name)] = single_track_id
        elif (has_album_version == 0) & (has_single == 0):
            track_dict['{}_{}'.format(artist,song_name)] = compilation_track_id

    return(track_dict)

def main():
    parser = ArgumentParser(
        description="Daily Data Savvy metric calculation pipeline"
    )
    parser.add_argument(
        "--num_songs",
        "-n",
        help="Specify playlist length -- default is 250",
    )

    extended_history = True

    settings = parser.parse_args()

    # Date

    if settings.num_songs is None:
        num_songs = 250
    else:
        num_songs = int(settings.num_songs)

    ## load library data
        
    print("Loading library...")

    if not extended_history:
        file_id = os.environ["FILE_ID"]
        destination = "./StreamingHistory_music_0.json"

        download_file_from_google_drive(file_id, destination)

        library = pd.read_json("StreamingHistory_music_0.json")

    else:
        library = pd.DataFrame()

        if type(os.environ["FILE_ID_LIST"]) is list:
            file_list = os.environ["FILE_ID_LIST"]
        else:
            file_list = json.loads(os.environ["FILE_ID_LIST"])

        for file in file_list:

            file_id = file
            destination = "./StreamingHistory_music_0.json"

            download_file_from_google_drive(file_id, destination)
            temp_df = pd.read_json("StreamingHistory_music_0.json")

            os.remove(destination)

            temp_df = temp_df[['master_metadata_track_name','master_metadata_album_artist_name','spotify_track_uri']]
            temp_df['spotify_track_uri'] = temp_df['spotify_track_uri'].str.replace('spotify:track:','')
            temp_df['artistName'] = temp_df['master_metadata_album_artist_name']

            library = pd.concat([library,temp_df])

    print("Shuffling...")

    shuffle = library.sample(replace=False, 
                                n=num_songs, 
                                random_state=None)

    ## initial sampling to get num_songs length songs

    shuffle = shuffler(shuffle)

    while len(shuffle) < num_songs:
        
        extra_shuffle = library.sample(replace=False, n=num_songs - len(shuffle), random_state=None)

        shuffle = pd.concat([shuffle,extra_shuffle]).reset_index().drop(['index'],axis=1)

        shuffle = shuffler(shuffle)

    print("Creating Playlist: Shuffler {}...".format(datetime.now().strftime('%Y-%m-%d')))

    username = 'kicsikicsi'

    # os.environ["SPOTIPY_CLIENT_ID"] = '' # client id
    # os.environ["SPOTIPY_CLIENT_SECRET"] = '' # Secret ID
    # os.environ["SPOTIPY_REDIRECT_URI"] = '' # Redirect URI

    scope = 'playlist-modify-public'

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.environ["SPOTIPY_CLIENT_ID"], 
        client_secret=os.environ["SPOTIPY_CLIENT_SECRET"], 
        redirect_uri="http://localhost:8888/callback", 
        scope=scope, 
        open_browser=False,))

    new_playlist = sp.user_playlist_create(username, 'Shuffler {}'.format(datetime.now().strftime('%Y-%m-%d')), public=True, collaborative=False, description='')

    if not extended_history:
        print('Getting Spotify song identifiers...')
        track_dict = get_spotify_ids(shuffle)
    else:
        track_dict = shuffle['spotify_track_uri'].to_dict()

    print('Uploading songs to playlist')

    track_list = []

    for item in track_dict:
        track_list.append(track_dict[item])

    for track in track_list:
        try:
            print(track)
            sp.user_playlist_add_tracks(username, new_playlist['id'], tracks = [track], position=None)
        except Exception as e:
            print("Error uploading track {}".format(track_dict[track]))

if __name__ == '__main__':
    main()
