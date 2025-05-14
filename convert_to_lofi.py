import os
import base64
import urllib.parse
import requests
import json
from dotenv import load_dotenv
import pandas as pd

# Load environment variables from .env file
load_dotenv()
def get_access_token():
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
    scope = 'playlist-read-private playlist-read-collaborative playlist-modify-private playlist-modify-public'
    credentials = f"{client_id}:{os.getenv('SPOTIFY_CLIENT_SECRET')}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    encoded_scope = urllib.parse.quote(scope)
    auth_url = (
        f"https://accounts.spotify.com/authorize?response_type=code"
        f"&client_id={client_id}&scope={encoded_scope}&redirect_uri={redirect_uri}"
    )
    print(f"Please go to this URL and authorize the application: {auth_url}")
    code = input("Input code from URL")
    auth_str = f"{client_id}:{os.getenv('SPOTIFY_CLIENT_SECRET')}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    token_url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    response = requests.post(token_url, headers=headers, data=data)
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens['access_token']
        refresh_token = tokens.get('refresh_token')
        print(f"Access Token: {access_token}")
        print(f"Refresh Token: {refresh_token}")
    else:
        print(f"Failed to obtain access token. Status code: {response.status_code}")
        print(response.text)
        SystemError
    return access_token

def get_playlist_to_modify(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    playlists = {}
    url = 'https://api.spotify.com/v1/me/playlists'
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}")
            break
        data = response.json()
        for item in data['items']:
            playlists[item['name']] = item['id']
        url = data.get('next')
    playlist_to_modify = input("Please input a playlist you would like to convert to lofi!")
    while playlist_to_modify not in playlists:
        playlist_to_modify = input("Sorry I could not find this playlist. Try double checking your spelling.")
    return playlist_to_modify, playlists[playlist_to_modify]

def get_usr_id(access_token):
    headers = {
        'Authorization' : f'Bearer {access_token}'
    }
    url = 'https://api.spotify.com/v1/me'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data['id']
    else:
        print(f"Request failed with status code {response.status_code}")
        SystemError

def get_song_names(playlist_id):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    song_names = []
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    params = {
        'fields': 'items(track(name)),next',
        'limit': 100  # Optional: specify the number of items per page
    }
    while url:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Failed to retrieve tracks: {response.status_code}")
            break
        data = response.json()
        for item in data['items']:
            track = item.get('track')
            if track:
                song_names.append(track.get('name'))
        url = data.get('next')  # Get the URL for the next page of results

    return song_names

def create_new_playlist(access_token, playlist_to_modify_name, playlist_to_modify_id, usr_id):
    headers = {
        'Authorization' : f'Bearer {access_token}'
    }
    user_id = urllib.parse.quote(usr_id)
    url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
    body = {
        "name": f'{playlist_to_modify_name} lofi',
        "description": f'Lofi version of {playlist_to_modify_name}',
        "public": False
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.status_code == 200 or response.status_code == 201:
        data = response.json()
        return data['id']
    else:
        print(f"Request failed with status code {response.status_code}")
        SystemError

def verify_name(actual_name, exp_name, artists_data, artist):
    actual_artists = []
    for a in artists_data:
        actual_artists.append(a['name'].lower())
    if artist.lower() not in actual_artists:
        return False
    match artist:
        case 'laurent':
            return actual_name.lower() == exp_name.lower() + " - lofi"
        case _:
            return actual_name.lower() == exp_name.lower()

def search_lofi(access_token, name):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    url = 'https://api.spotify.com/v1/search'
    df = pd.read_csv('trusted_lofi_artists.csv', header=None)
    trusted_artists = df.iloc[0].tolist()
    uris=[]
    for artist in trusted_artists:
        params = {
            'q': f'track:{name} artist:{artist}',
            'type': 'track',
            'market': 'US',
            'limit': 1
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['tracks']['items'] != []:
                if verify_name(data['tracks']['items'][0]['name'], name, data['tracks']['items'][0]['artists'], artist):
                    found_song = data['tracks']['items'][0]['name']
                    print(f'Found song {found_song} by {artist} while searching for {name}')
                    return data['tracks']['items'][0]['uri']
        else:
            print(f"Failed to search for song {name} under artist {artist}: {response.status_code}")
    return None

def search_lofi_uris(access_token, song_names):
    uris = []
    skipped = 0
    for name in song_names:
        uri = search_lofi(access_token, name)
        if uri == None:
            skipped += 1
            print(f'Couldn\'t find any lofi songs for "{name}"')
        else:
            uris.append(uri)
    print(f'{skipped} songs skipped')
    return uris

def populate_lofi_playlist(access_token, new_playlist_id, song_names):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    url = f'https://api.spotify.com/v1/playlists/{new_playlist_id}/tracks'
    uris = search_lofi_uris(access_token, song_names)
    uris = list(set(uris))
    print(uris)
    body = {
        "uris": uris
    }
    response = requests.post(url, headers=headers, data = json.dumps(body))
    if response.status_code == 201:
        data = response.json()
        print(data)
    else:
        print(f"Request failed with status code {response.status_code}")
        SystemError
#access_token = get_access_token()
access_token = 'BQA6Pq3ZCeBfhR30twrKZiAUH-k6zXx2GjjvG_uDfYofoAGZQ2vXZ3kpShatfvrVxvUjf-br25DuK0XMl9w3JOkhy5fOKmZgAgQ9T0cXc6j8jPnCAMow3DSiKZEGL--WIsk08x4TJ2EgZROi8e-bFOG_EZJDoEz0coS1skz_4QOoKN9KRapRRDwTb0iI5Y0qMx_nDDbgXWlflebOuh3Y0ZtVeVxYS5kYjJoMdCHPzs3DWsgAUz24KMG5bIm3aaMaoE95h9drNX93_Lx-rNYv6HgRbzQc5c9WS7TBLc-Urged7ImxB09Mihao'
playlist_to_modify_name, playlist_to_modify_id= get_playlist_to_modify(access_token)
song_names = get_song_names(playlist_to_modify_id)
new_playlist_id=create_new_playlist(access_token, playlist_to_modify_name, playlist_to_modify_id, get_usr_id(access_token))
populate_lofi_playlist(access_token, new_playlist_id, song_names)