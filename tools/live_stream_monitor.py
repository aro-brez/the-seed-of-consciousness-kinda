#!/usr/bin/env python3
"""
Live Stream Monitor - Polymarket News & Signals
Monitors X, news, articles for Polymarket alpha
Continuous feed of latest intelligence
"""

import json
import time
from datetime import datetime
from pathlib import Path
import tweepy

# Paths
REPO_ROOT = Path(__file__).parent.parent
KEYS_PATH = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / 'api_keys.json'
STREAM_LOG = REPO_ROOT / 'BRAIN' / 'INTEL' / 'live_stream.jsonl'

# Load API keys
with open(KEYS_PATH) as f:
    keys = json.load(f)

BEARER_TOKEN = keys['twitter_x']['bearer_token']

# Keywords to monitor
KEYWORDS = [
    'polymarket',
    'polymarket whale',
    'polymarket alpha',
    'polymarket bot',
    'prediction market',
    'grok trading',
    'claude trading',
]

# High-value accounts (from earlier research)
ACCOUNTS_TO_WATCH = [
    'woonomic',       # Willy Woo - on-chain
    'scottmelker',    # Wolf Of All Streets
    'TheCryptoDog',   # Daily trading
    'CryptoCred',     # Technical analysis
    'SmartContracter', # Macro timing
    'LookOnChain',    # Whale alerts
]

class LiveStreamMonitor:
    """Continuous monitoring of Polymarket ecosystem"""

    def __init__(self):
        self.client = tweepy.Client(bearer_token=BEARER_TOKEN)
        self.stream_log = STREAM_LOG

    def search_latest(self, keyword, max_results=10):
        """Search for latest tweets on keyword"""
        try:
            tweets = self.client.search_recent_tweets(
                query=f"{keyword} -is:retweet",
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                expansions=['author_id'],
            )

            results = []
            if tweets.data:
                for tweet in tweets.data:
                    results.append({
                        'keyword': keyword,
                        'text': tweet.text,
                        'created_at': tweet.created_at.isoformat(),
                        'likes': tweet.public_metrics['like_count'],
                        'retweets': tweet.public_metrics['retweet_count'],
                        'url': f'https://twitter.com/user/status/{tweet.id}',
                        'timestamp': datetime.now().isoformat()
                    })

            return results

        except Exception as e:
            print(f"Error searching {keyword}: {e}")
            return []

    def monitor_accounts(self):
        """Check monitored accounts for new tweets"""
        signals = []

        for username in ACCOUNTS_TO_WATCH:
            try:
                user = self.client.get_user(username=username)
                if not user.data:
                    continue

                tweets = self.client.get_users_tweets(
                    user.data.id,
                    max_results=5,
                    tweet_fields=['created_at', 'public_metrics']
                )

                if tweets.data:
                    for tweet in tweets.data:
                        # Check if mentions Polymarket
                        if 'polymarket' in tweet.text.lower():
                            signals.append({
                                'source': 'monitored_account',
                                'username': username,
                                'text': tweet.text,
                                'created_at': tweet.created_at.isoformat(),
                                'url': f'https://twitter.com/{username}/status/{tweet.id}',
                                'timestamp': datetime.now().isoformat()
                            })
                            print(f"📊 SIGNAL from @{username}: {tweet.text[:60]}...")

            except Exception as e:
                print(f"Error monitoring @{username}: {e}")

        return signals

    def full_scan(self):
        """Complete scan of all sources"""
        print("🔍 Running full scan...")

        all_signals = []

        # Search keywords
        for keyword in KEYWORDS:
            results = self.search_latest(keyword, max_results=5)
            all_signals.extend(results)
            time.sleep(1)  # Rate limit

        # Monitor accounts
        account_signals = self.monitor_accounts()
        all_signals.extend(account_signals)

        # Save to log (append)
        with open(self.stream_log, 'a') as f:
            for signal in all_signals:
                f.write(json.dumps(signal) + '\n')

        print(f"✅ Captured {len(all_signals)} signals")
        return all_signals

    def stream_forever(self, interval=300):
        """Continuous monitoring"""
        print("🚀 Starting live stream monitor")
        print(f"Keywords: {', '.join(KEYWORDS)}")
        print(f"Accounts: {', '.join(ACCOUNTS_TO_WATCH)}")
        print(f"Interval: {interval}s\n")

        while True:
            try:
                self.full_scan()
                print(f"⏰ Next scan in {interval}s...\n")
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n🛑 Stream monitor stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    monitor = LiveStreamMonitor()
    monitor.stream_forever(interval=300)  # Every 5 min
