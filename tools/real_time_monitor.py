#!/usr/bin/env python3
"""
Real-Time X Monitor for Trading Signals
Monitors specific accounts for breaking signals
Feeds fresh intelligence into trading loop
"""

import json
import time
from datetime import datetime
from pathlib import Path
import tweepy

# Load API keys
REPO_ROOT = Path(__file__).parent.parent
api_keys_path = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / 'api_keys.json'

with open(api_keys_path) as f:
    keys = json.load(f)

BEARER_TOKEN = keys['twitter_x']['bearer_token']

# High-value accounts to monitor (verified signal quality)
MONITOR_ACCOUNTS = [
    'woonomic',          # Willy Woo - On-chain analysis
    'scottmelker',       # Wolf Of All Streets - Technical analysis
    'TheCryptoDog',      # Daily trading updates
    'CryptoCred',        # Technical patterns, called BTC bottom
    'SmartContracter',   # Macro cycles, precision timing
    'LookOnChain',       # Whale alerts
    'elonmusk',          # Market moving tweets
]

# Output
SIGNALS_PATH = REPO_ROOT / 'BRAIN' / 'INTEL' / 'live_signals.json'

def monitor_forever():
    """Monitor Twitter for breaking signals"""
    client = tweepy.Client(bearer_token=BEARER_TOKEN)

    print("🔴 LIVE MONITORING STARTED")
    print(f"Tracking: {', '.join(MONITOR_ACCOUNTS)}")

    signals = []

    while True:
        try:
            for username in MONITOR_ACCOUNTS:
                # Get latest tweets
                user = client.get_user(username=username)
                tweets = client.get_users_tweets(
                    user.data.id,
                    max_results=5,
                    tweet_fields=['created_at', 'public_metrics']
                )

                if tweets.data:
                    for tweet in tweets.data:
                        # Check if tweet is fresh (last 15 min)
                        age_minutes = (datetime.now() - tweet.created_at).total_seconds() / 60

                        if age_minutes < 15:
                            signal = {
                                'username': username,
                                'tweet_id': tweet.id,
                                'text': tweet.text,
                                'created_at': tweet.created_at.isoformat(),
                                'age_minutes': age_minutes,
                                'likes': tweet.public_metrics['like_count'],
                                'retweets': tweet.public_metrics['retweet_count'],
                                'url': f'https://twitter.com/{username}/status/{tweet.id}'
                            }

                            signals.append(signal)
                            print(f"📊 NEW SIGNAL: @{username} - {tweet.text[:50]}...")

            # Save signals
            with open(SIGNALS_PATH, 'w') as f:
                json.dump(signals, f, indent=2)

            # Check every 5 minutes
            time.sleep(300)

        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    monitor_forever()
