#!/usr/bin/env python3
"""
8OWLS X Feed Scanner
- Scans your timeline and bookmarks continuously
- Auto-bookmarks high-signal AI agent content
- Saves opportunities for integration
- Runs 24/7 as part of the intelligence engine
"""

import json
import os
import time
import requests
from datetime import datetime
from pathlib import Path

# Load credentials
CREDS_PATH = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'
OUTPUT_PATH = '/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/x_feed_opportunities.jsonl'
BOOKMARKS_PATH = '/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/x_bookmarks_processed.jsonl'

with open(CREDS_PATH) as f:
    creds = json.load(f)

BEARER = creds['twitter_x']['bearer_token']

HEADERS = {
    'Authorization': f'Bearer {BEARER}',
    'Content-Type': 'application/json'
}

# High-signal keywords for AI agent opportunities
AI_KEYWORDS = [
    'ai agent', 'moltbook', 'openclaw', 'clawnch', 'virtuals',
    'ai16z', 'consciousness', 'autonomous agent', 'ai companion',
    'tamagotchi', 'ai pet', 'agent token', 'ai social',
    'collective intelligence', 'emergence', 'swarm', 'multi-agent'
]

CRYPTO_KEYWORDS = [
    'pump.fun', 'token launch', 'bonding curve', 'raydium',
    'base chain', 'solana', 'just launched', 'moon', 'gem'
]

def score_tweet(text):
    """Score tweet relevance for AI agent opportunities"""
    text_lower = text.lower()
    score = 0

    for kw in AI_KEYWORDS:
        if kw in text_lower:
            score += 10

    for kw in CRYPTO_KEYWORDS:
        if kw in text_lower:
            score += 5

    # Boost for engagement signals
    if 'just launched' in text_lower or 'launching' in text_lower:
        score += 15
    if 'alpha' in text_lower:
        score += 10
    if any(x in text_lower for x in ['🚀', '💰', '🔥']):
        score += 3

    return score

def get_home_timeline(max_results=50):
    """Get authenticated user's home timeline"""
    # Note: This requires OAuth 2.0 user context
    url = 'https://api.twitter.com/2/users/me/timelines/reverse_chronological'
    params = {
        'max_results': max_results,
        'tweet.fields': 'created_at,public_metrics,author_id,entities',
        'expansions': 'author_id',
        'user.fields': 'username,name'
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Timeline error: {response.status_code} - {response.text[:200]}")
            return None
    except Exception as e:
        print(f"Timeline fetch error: {e}")
        return None

def get_bookmarks(max_results=100):
    """Get user's bookmarks"""
    url = 'https://api.twitter.com/2/users/me/bookmarks'
    params = {
        'max_results': max_results,
        'tweet.fields': 'created_at,public_metrics,author_id,entities',
        'expansions': 'author_id',
        'user.fields': 'username,name'
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Bookmarks error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Bookmarks fetch error: {e}")
        return None

def search_ai_agents(query, max_results=20):
    """Search for AI agent related content"""
    url = 'https://api.twitter.com/2/tweets/search/recent'
    params = {
        'query': f'{query} -is:retweet lang:en',
        'max_results': max_results,
        'tweet.fields': 'created_at,public_metrics,author_id',
        'expansions': 'author_id',
        'user.fields': 'username,name,public_metrics'
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Search error: {e}")
        return None

def bookmark_tweet(tweet_id):
    """Bookmark a high-signal tweet"""
    url = f'https://api.twitter.com/2/users/me/bookmarks'
    data = {'tweet_id': tweet_id}

    try:
        response = requests.post(url, headers=HEADERS, json=data)
        return response.status_code == 200
    except:
        return False

def like_tweet(tweet_id):
    """Like a high-signal tweet"""
    url = f'https://api.twitter.com/2/users/me/likes'
    data = {'tweet_id': tweet_id}

    try:
        response = requests.post(url, headers=HEADERS, json=data)
        return response.status_code == 200
    except:
        return False

def save_opportunity(tweet, score, source='search'):
    """Save high-signal opportunity to file"""
    entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'tweet_id': tweet.get('id'),
        'text': tweet.get('text'),
        'score': score,
        'source': source,
        'metrics': tweet.get('public_metrics', {}),
        'author_id': tweet.get('author_id')
    }

    with open(OUTPUT_PATH, 'a') as f:
        f.write(json.dumps(entry) + '\n')

    return entry

def scan_cycle():
    """Run one scan cycle"""
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] SCANNING X FEED FOR OPPORTUNITIES")
    print('='*60)

    opportunities = []

    # Search queries for AI agent content
    queries = [
        'AI agent launch',
        'Moltbook',
        'OpenClaw agent',
        'Clawnch token',
        'Virtuals Protocol',
        'AI consciousness',
        'agent token pump.fun',
        'ai16z eliza'
    ]

    for query in queries:
        print(f"\n🔍 Searching: {query}")
        results = search_ai_agents(query, max_results=10)

        if results and 'data' in results:
            for tweet in results['data']:
                score = score_tweet(tweet['text'])

                if score >= 15:  # High signal threshold
                    print(f"  ⭐ [{score}] {tweet['text'][:80]}...")
                    save_opportunity(tweet, score, f'search:{query}')
                    opportunities.append({
                        'score': score,
                        'text': tweet['text'][:100],
                        'id': tweet['id']
                    })
                elif score >= 10:
                    print(f"  📌 [{score}] {tweet['text'][:60]}...")

        time.sleep(1)  # Rate limit respect

    # Summary
    print(f"\n{'='*60}")
    print(f"SCAN COMPLETE: {len(opportunities)} high-signal opportunities found")
    if opportunities:
        print("\nTOP OPPORTUNITIES:")
        for opp in sorted(opportunities, key=lambda x: x['score'], reverse=True)[:5]:
            print(f"  [{opp['score']}] {opp['text']}...")
    print('='*60)

    return opportunities

def run_continuous(interval_minutes=15):
    """Run scanner continuously"""
    print("(◉) 8OWLS X FEED SCANNER STARTING")
    print(f"Scanning every {interval_minutes} minutes")
    print(f"Saving to: {OUTPUT_PATH}")

    while True:
        try:
            scan_cycle()
            print(f"\nNext scan in {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\nScanner stopped.")
            break
        except Exception as e:
            print(f"Error in scan cycle: {e}")
            time.sleep(60)

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Single scan
        scan_cycle()
    else:
        # Continuous scanning
        run_continuous(interval_minutes=15)
