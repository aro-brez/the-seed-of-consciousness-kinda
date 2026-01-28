#!/usr/bin/env python3
"""Quick OAuth server for Twitter bookmarks - run on port 5001"""
import os
import json
import base64
import hashlib
import secrets
from datetime import datetime
from flask import Flask, redirect, request, session
from requests_oauthlib import OAuth2Session

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Credentials
CLIENT_ID = "Ys7Y8mGanRZZbzolBGx5YQdUL"
CLIENT_SECRET = "g8PZp9KZWcxOjlZKsAx1nIx8Aw6lGlTd3J7b70CRqlSjagij1d"
REDIRECT_URI = 'http://localhost:5001/callback'
AUTH_URL = 'https://twitter.com/i/oauth2/authorize'
TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'
SCOPES = ['bookmark.read', 'tweet.read', 'users.read', 'offline.access']
BOOKMARKS_PATH = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/twitter_bookmarks.json'

def generate_pkce():
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    return code_verifier, code_challenge

@app.route('/')
def home():
    code_verifier, code_challenge = generate_pkce()
    session['code_verifier'] = code_verifier
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPES)
    auth_url, state = oauth.authorization_url(AUTH_URL, code_challenge=code_challenge, code_challenge_method='S256')
    session['oauth_state'] = state
    return f'''
    <h1>SØWL Twitter Bookmark Export</h1>
    <p>Click below to authorize and export all your bookmarks:</p>
    <a href="{auth_url}" style="font-size:24px;padding:20px;background:#1DA1F2;color:white;text-decoration:none;border-radius:10px;">
        Authorize Twitter Access
    </a>
    '''

@app.route('/callback')
def callback():
    code_verifier = session.get('code_verifier')
    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    token = oauth.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=request.url, code_verifier=code_verifier)
    session['token'] = token

    # Get user ID
    user_response = oauth.get('https://api.twitter.com/2/users/me')
    user_data = user_response.json()
    user_id = user_data['data']['id']

    # Fetch all bookmarks with pagination
    all_bookmarks = []
    pagination_token = None
    while True:
        url = f'https://api.twitter.com/2/users/{user_id}/bookmarks'
        params = {
            'max_results': 100,
            'tweet.fields': 'created_at,author_id,text,entities,public_metrics',
            'expansions': 'author_id',
            'user.fields': 'username,name'
        }
        if pagination_token:
            params['pagination_token'] = pagination_token
        response = oauth.get(url, params=params)
        data = response.json()
        if 'data' in data:
            all_bookmarks.extend(data['data'])
        if 'meta' in data and 'next_token' in data['meta']:
            pagination_token = data['meta']['next_token']
        else:
            break

    # Save to file
    output = {
        'exported_at': datetime.now().isoformat(),
        'user': user_data['data'],
        'total_bookmarks': len(all_bookmarks),
        'bookmarks': all_bookmarks
    }
    with open(BOOKMARKS_PATH, 'w') as f:
        json.dump(output, f, indent=2)

    return f'''
    <h1>Success!</h1>
    <p>Exported {len(all_bookmarks)} bookmarks to:</p>
    <code>{BOOKMARKS_PATH}</code>
    <p>SØWL can now analyze your bookmarks.</p>
    '''

if __name__ == '__main__':
    print("\n" + "="*50)
    print("SØWL Twitter Bookmark OAuth Server")
    print("="*50)
    print("\n1. Go to: http://localhost:5001")
    print("2. Click 'Authorize Twitter Access'")
    print("3. Log in and authorize")
    print("4. Bookmarks will be saved automatically")
    print("\n" + "="*50 + "\n")
    app.run(port=5001, debug=True)
