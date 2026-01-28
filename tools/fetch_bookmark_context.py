#!/usr/bin/env python3
"""
Fetch full context for bookmarked tweets:
- Full thread/conversation
- Replies
- Linked articles
"""
import json
import requests
import time
from datetime import datetime

# Load credentials
with open('/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json') as f:
    creds = json.load(f)

BEARER_TOKEN = creds['twitter_x']['bearer_token']
BOOKMARKS_PATH = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/twitter_bookmarks.json'
OUTPUT_PATH = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/twitter_bookmarks_full.json'

headers = {
    'Authorization': f'Bearer {BEARER_TOKEN}',
    'User-Agent': 'v2TweetLookupPython'
}

def get_tweet_with_context(tweet_id):
    """Fetch tweet with full conversation context"""
    url = f'https://api.twitter.com/2/tweets/{tweet_id}'
    params = {
        'tweet.fields': 'author_id,conversation_id,created_at,entities,public_metrics,referenced_tweets,text',
        'expansions': 'author_id,referenced_tweets.id,entities.mentions.username',
        'user.fields': 'username,name,description'
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def get_conversation_thread(conversation_id, max_results=50):
    """Fetch all tweets in a conversation thread"""
    url = 'https://api.twitter.com/2/tweets/search/recent'
    params = {
        'query': f'conversation_id:{conversation_id}',
        'tweet.fields': 'author_id,created_at,entities,public_metrics,text,in_reply_to_user_id',
        'expansions': 'author_id',
        'user.fields': 'username,name',
        'max_results': max_results
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def expand_url(short_url):
    """Expand t.co short URL"""
    try:
        response = requests.head(short_url, allow_redirects=True, timeout=5)
        return response.url
    except:
        return short_url

def process_bookmarks():
    """Process all bookmarks and fetch full context"""
    with open(BOOKMARKS_PATH) as f:
        bookmarks_data = json.load(f)

    enriched_bookmarks = []
    total = len(bookmarks_data['bookmarks'])

    print(f"Processing {total} bookmarks...")

    for i, bookmark in enumerate(bookmarks_data['bookmarks'], 1):
        tweet_id = bookmark['id']
        print(f"\n[{i}/{total}] Processing tweet {tweet_id}")

        enriched = {
            'original': bookmark,
            'thread': [],
            'replies': [],
            'expanded_urls': []
        }

        # Get tweet with context
        tweet_data = get_tweet_with_context(tweet_id)
        if 'data' in tweet_data:
            enriched['full_tweet'] = tweet_data['data']
            enriched['includes'] = tweet_data.get('includes', {})

            # Get conversation thread
            conv_id = tweet_data['data'].get('conversation_id')
            if conv_id:
                time.sleep(0.5)  # Rate limiting
                thread_data = get_conversation_thread(conv_id)
                if 'data' in thread_data:
                    enriched['replies'] = thread_data['data']
                    print(f"   Found {len(thread_data['data'])} replies")

        # Expand URLs in entities
        if 'entities' in bookmark and 'urls' in bookmark['entities']:
            for url_entity in bookmark['entities']['urls']:
                short_url = url_entity.get('url', '')
                expanded = url_entity.get('expanded_url', expand_url(short_url))
                enriched['expanded_urls'].append({
                    'short': short_url,
                    'expanded': expanded,
                    'display': url_entity.get('display_url', '')
                })

        enriched_bookmarks.append(enriched)

        # Rate limiting - Twitter API allows ~300 requests per 15 min
        time.sleep(1)

        # Save progress every 10 tweets
        if i % 10 == 0:
            print(f"\n   Saving progress... ({i}/{total})")
            output = {
                'exported_at': bookmarks_data['exported_at'],
                'enriched_at': datetime.now().isoformat(),
                'user': bookmarks_data['user'],
                'total_bookmarks': len(enriched_bookmarks),
                'bookmarks': enriched_bookmarks
            }
            with open(OUTPUT_PATH, 'w') as f:
                json.dump(output, f, indent=2)

    # Final save
    output = {
        'exported_at': bookmarks_data['exported_at'],
        'enriched_at': datetime.now().isoformat(),
        'user': bookmarks_data['user'],
        'total_bookmarks': len(enriched_bookmarks),
        'bookmarks': enriched_bookmarks
    }
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*50}")
    print(f"SUCCESS! Enriched {len(enriched_bookmarks)} bookmarks")
    print(f"Saved to: {OUTPUT_PATH}")
    print(f"{'='*50}")

if __name__ == '__main__':
    process_bookmarks()
