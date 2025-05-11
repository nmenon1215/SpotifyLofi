import os
import base64
import urllib.parse
import requests
import json
from dotenv import load_dotenv

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

def populate_lofi_playlist(access_token, new_playlist_id):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    url = f'https://api.spotify.com/v1/playlists/{new_playlist_id}/tracks'
    body = {
        "uris": ["spotify:track:72iqZG1zy55rXQPBBB4a21"]
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print(f"Request failed with status code {response.status_code}")
        SystemError
access_token = get_access_token()
playlist_to_modify_name, playlist_to_modify_id= get_playlist_to_modify(access_token)
#song_names = get_song_names(playlist_to_modify_id)
new_playlist_id=create_new_playlist(access_token, playlist_to_modify_name, playlist_to_modify_id, get_usr_id(access_token))
populate_lofi_playlist(access_token, new_playlist_id)