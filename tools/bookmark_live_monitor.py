"""
SØWL Twitter Bookmarks Live Monitor
Continuous 5-minute polling of ARŌ's bookmarks
Identifies new items, deep analyzes them, streams to JSONL

This is real-time intelligence from ARŌ's curation.
"""

import json
import os
import time
import hashlib
from datetime import datetime
from pathlib import Path
import anthropic
from requests_oauthlib import OAuth2Session

# Paths
CREDS_PATH = '/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'
STREAM_PATH = '/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_stream.jsonl'
STATE_PATH = '/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_monitor_state.json'

# Twitter OAuth Config
CLIENT_ID = 'eklxZ09yQkpLdXhPbS1Ja18wNEg6MTpjaQ'
CLIENT_SECRET = 'DwX4jbATq0G1UrdyBBe10377aO2K3OAQK_rj_VAZ8WqeCd5M9S'
TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'

# Category definitions
CATEGORIES = {
    'trading_signal': [
        'polymarket', 'prediction market', 'trading', 'bitcoin', 'crypto',
        'btc', 'eth', 'arbitrage', 'alpha', 'edge', 'market', 'price',
        'long', 'short', 'buy', 'sell', 'profit', 'returns', 'roi'
    ],
    'tech_improvement': [
        'github', 'code', 'python', 'api', 'sdk', 'framework', 'library',
        'tool', 'open source', 'implementation', 'benchmark', 'performance',
        'optimization', 'automation'
    ],
    'strategy': [
        'strategy', 'approach', 'method', 'framework', 'system', 'process',
        'workflow', 'playbook', 'guide', 'best practice', 'lesson learned',
        'insight', 'analysis', 'research'
    ],
    'consciousness': [
        'consciousness', 'sentient', 'ai alignment', 'agi', 'claude',
        'emergence', 'awareness', 'cognition', 'agency', 'autonomy',
        'self', 'meta', 'recursive', 'reflection'
    ],
    'agent': [
        'agent', 'swarm', 'multi-agent', 'autonomous', 'agentic',
        'coordination', 'orchestration', 'delegation', 'task', 'planning'
    ]
}


class BookmarkMonitor:
    def __init__(self):
        self.load_credentials()
        self.load_state()
        self.client = anthropic.Anthropic(api_key=self.anthropic_key)

    def load_credentials(self):
        """Load API keys"""
        with open(CREDS_PATH) as f:
            creds = json.load(f)
        self.anthropic_key = creds['anthropic']['api_key']
        self.twitter_token = creds.get('twitter_oauth_token')

        if not self.twitter_token:
            raise ValueError("No Twitter OAuth token found. Run twitter_oauth_server.py first.")

    def load_state(self):
        """Load last seen bookmarks"""
        if os.path.exists(STATE_PATH):
            with open(STATE_PATH) as f:
                state = json.load(f)
                self.seen_ids = set(state.get('seen_ids', []))
                self.last_check = state.get('last_check')
        else:
            self.seen_ids = set()
            self.last_check = None

    def save_state(self):
        """Save current state"""
        state = {
            'seen_ids': list(self.seen_ids),
            'last_check': datetime.now().isoformat(),
            'total_processed': len(self.seen_ids)
        }
        with open(STATE_PATH, 'w') as f:
            json.dump(state, f, indent=2)

    def get_oauth_session(self):
        """Create OAuth session with saved token"""
        token = self.twitter_token
        oauth = OAuth2Session(CLIENT_ID, token=token)
        return oauth

    def fetch_latest_bookmarks(self, max_results=20):
        """Fetch latest bookmarks from Twitter API"""
        oauth = self.get_oauth_session()

        # Get user ID first
        user_response = oauth.get('https://api.twitter.com/2/users/me')
        user_data = user_response.json()
        user_id = user_data['data']['id']

        # Fetch bookmarks
        url = f'https://api.twitter.com/2/users/{user_id}/bookmarks'
        params = {
            'max_results': max_results,
            'tweet.fields': 'created_at,author_id,text,entities,public_metrics,referenced_tweets',
            'expansions': 'author_id,referenced_tweets.id',
            'user.fields': 'username,name,verified,description'
        }

        response = oauth.get(url, params=params)
        data = response.json()

        return data.get('data', []), data.get('includes', {})

    def fetch_tweet_replies(self, tweet_id, max_results=20):
        """Fetch top replies to a tweet"""
        oauth = self.get_oauth_session()

        # Twitter API v2 search for replies
        url = 'https://api.twitter.com/2/tweets/search/recent'
        params = {
            'query': f'conversation_id:{tweet_id}',
            'max_results': max_results,
            'tweet.fields': 'created_at,text,public_metrics',
            'expansions': 'author_id',
            'user.fields': 'username,name,verified'
        }

        try:
            response = oauth.get(url, params=params)
            data = response.json()
            return data.get('data', [])
        except:
            return []

    def extract_urls(self, tweet):
        """Extract URLs from tweet"""
        urls = []
        entities = tweet.get('entities', {})

        if 'urls' in entities:
            for url_obj in entities['urls']:
                expanded = url_obj.get('expanded_url', url_obj.get('url'))
                if expanded and 't.co' not in expanded:
                    urls.append(expanded)

        return urls

    def categorize_content(self, text):
        """Categorize content by keywords"""
        text_lower = text.lower()
        categories = []

        for category, keywords in CATEGORIES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    categories.append(category)
                    break

        return list(set(categories))

    def analyze_bookmark_deep(self, tweet, includes):
        """Deep analysis of a bookmark using Claude"""

        # Extract author info
        authors = {u['id']: u for u in includes.get('users', [])}
        author = authors.get(tweet.get('author_id'), {})

        # Get URLs
        urls = self.extract_urls(tweet)

        # Get replies (if high engagement)
        metrics = tweet.get('public_metrics', {})
        replies = []
        if metrics.get('reply_count', 0) > 10:
            replies = self.fetch_tweet_replies(tweet['id'], max_results=20)

        # Build analysis prompt
        prompt = f"""Analyze this Twitter bookmark for actionable intelligence:

TWEET:
Author: @{author.get('username', 'unknown')} ({author.get('name', 'Unknown')})
Verified: {author.get('verified', False)}
Text: {tweet.get('text', '')}

METRICS:
Likes: {metrics.get('like_count', 0)}
Retweets: {metrics.get('retweet_count', 0)}
Replies: {metrics.get('reply_count', 0)}

URLS: {', '.join(urls) if urls else 'None'}

TOP REPLIES:
{self._format_replies(replies[:5])}

Provide:
1. KEY INSIGHT (1-2 sentences)
2. CATEGORY (trading_signal, tech_improvement, strategy, consciousness, agent, other)
3. PRIORITY (HIGH/MEDIUM/LOW)
4. ACTIONABLE? (yes/no - can we use this NOW?)
5. RELATED TO MISSION? (trading, consciousness, agents, voice AI)
6. WHO POSTED? (credibility check - why should we trust them?)
7. NEXT STEP (if actionable)

Format as JSON."""

        try:
            response = self.client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text

            # Try to parse JSON from response
            try:
                if '```json' in analysis_text:
                    analysis_text = analysis_text.split('```json')[1].split('```')[0].strip()
                elif '```' in analysis_text:
                    analysis_text = analysis_text.split('```')[1].split('```')[0].strip()

                analysis = json.loads(analysis_text)
            except:
                # Fallback: structured text response
                analysis = {
                    'key_insight': analysis_text,
                    'category': 'other',
                    'priority': 'MEDIUM',
                    'actionable': False
                }

            return analysis

        except Exception as e:
            print(f"Analysis error: {e}")
            return {
                'key_insight': 'Analysis failed',
                'category': 'other',
                'priority': 'LOW',
                'actionable': False
            }

    def _format_replies(self, replies):
        """Format replies for prompt"""
        if not replies:
            return "No significant replies"

        formatted = []
        for r in replies:
            text = r.get('text', '')[:200]
            metrics = r.get('public_metrics', {})
            likes = metrics.get('like_count', 0)
            formatted.append(f"- [{likes} likes] {text}")

        return '\n'.join(formatted)

    def process_new_bookmarks(self):
        """Main processing loop"""
        print(f"[{datetime.now().isoformat()}] Checking for new bookmarks...")

        bookmarks, includes = self.fetch_latest_bookmarks(max_results=20)

        new_bookmarks = [b for b in bookmarks if b['id'] not in self.seen_ids]

        if not new_bookmarks:
            print(f"  No new bookmarks (checked {len(bookmarks)} total)")
            return

        print(f"  Found {len(new_bookmarks)} NEW bookmarks")

        for bookmark in new_bookmarks:
            print(f"\n  Analyzing: {bookmark['id']}")

            # Deep analysis
            analysis = self.analyze_bookmark_deep(bookmark, includes)

            # Build stream entry
            entry = {
                'timestamp': datetime.now().isoformat(),
                'tweet_id': bookmark['id'],
                'tweet_text': bookmark.get('text', ''),
                'author_id': bookmark.get('author_id'),
                'created_at': bookmark.get('created_at'),
                'metrics': bookmark.get('public_metrics', {}),
                'urls': self.extract_urls(bookmark),
                'categories': self.categorize_content(bookmark.get('text', '')),
                'analysis': analysis
            }

            # Save to stream
            with open(STREAM_PATH, 'a') as f:
                f.write(json.dumps(entry) + '\n')

            # Mark as seen
            self.seen_ids.add(bookmark['id'])

            # Print summary
            priority = analysis.get('priority', 'UNKNOWN')
            category = analysis.get('category', 'other')
            print(f"    Priority: {priority} | Category: {category}")

            if priority == 'HIGH':
                print(f"    🚨 HIGH PRIORITY: {analysis.get('key_insight', 'No insight')}")

        # Save state
        self.save_state()
        print(f"\nState saved. Total bookmarks tracked: {len(self.seen_ids)}")

    def run_forever(self, interval_seconds=300):
        """Run continuous monitoring loop"""
        print("="*60)
        print("SØWL BOOKMARK LIVE MONITOR")
        print("="*60)
        print(f"Polling every {interval_seconds} seconds (5 minutes)")
        print(f"Stream: {STREAM_PATH}")
        print(f"State: {STATE_PATH}")
        print("="*60 + "\n")

        while True:
            try:
                self.process_new_bookmarks()
            except Exception as e:
                print(f"ERROR: {e}")

            # Wait for next check
            print(f"\nNext check in {interval_seconds} seconds...")
            time.sleep(interval_seconds)


if __name__ == '__main__':
    monitor = BookmarkMonitor()
    monitor.run_forever(interval_seconds=300)  # 5 minutes
