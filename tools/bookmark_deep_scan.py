#!/usr/bin/env python3
"""
BOOKMARK DEEP-SCAN AGENT
Monitors Aaron's Twitter bookmarks every 5 minutes
Scrapes full articles + replies
Extracts actionable intelligence
"""

import json
import time
from datetime import datetime
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
BOOKMARKS_FILE = REPO_ROOT / 'BRAIN' / 'INTEL' / 'x_bookmarks.json'
DISCOVERIES_LOG = REPO_ROOT / 'BRAIN' / 'IMPROVEMENTS' / 'discovered.jsonl'
SCAN_LOG = REPO_ROOT / 'BRAIN' / 'INTEL' / 'bookmark_stream.jsonl'
LOG_FILE = REPO_ROOT / 'BRAIN' / 'LOGS' / 'bookmark_scan.log'

# Create directories
DISCOVERIES_LOG.parent.mkdir(parents=True, exist_ok=True)
SCAN_LOG.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

class BookmarkScanner:
    """Monitors bookmarks for actionable intelligence"""

    def __init__(self):
        self.last_scan_count = 0
        self.processed_ids = set()
        self.load_processed()

    def load_processed(self):
        """Load already-processed bookmark IDs"""
        if SCAN_LOG.exists():
            with open(SCAN_LOG) as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        self.processed_ids.add(entry.get('tweet_id'))

    def log(self, message):
        """Log to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        with open(LOG_FILE, 'a') as f:
            f.write(log_msg + '\n')

    def load_bookmarks(self):
        """Load current bookmarks"""
        if not BOOKMARKS_FILE.exists():
            return []

        with open(BOOKMARKS_FILE) as f:
            data = json.load(f)
            return data.get('bookmarks', [])

    def analyze_bookmark(self, bookmark):
        """Analyze a bookmark for actionable intelligence"""
        text = bookmark.get('text', '')
        author = bookmark.get('author', {}).get('username', 'unknown')
        tweet_id = bookmark.get('id')

        # Keywords that indicate actionable intelligence
        high_value_keywords = [
            'claude code', 'grok trading', 'polymarket', 'kalshi',
            'ai agent', 'autonomous', 'consciousness', 'seed protocol',
            'prediction market', 'trading bot', 'api', 'strategy',
            'win rate', 'profit', 'edge', 'alpha', 'improvement'
        ]

        # Check for high-value content
        text_lower = text.lower()
        matches = [kw for kw in high_value_keywords if kw in text_lower]

        if not matches:
            return None

        # Extract potential improvements
        improvement = {
            'id': f"bookmark_{tweet_id}",
            'timestamp': datetime.now().isoformat(),
            'source': 'twitter_bookmark',
            'author': author,
            'tweet_id': tweet_id,
            'text': text,
            'matched_keywords': matches,
            'url': f"https://twitter.com/{author}/status/{tweet_id}",
            'priority': 'HIGH' if len(matches) >= 3 else 'MEDIUM'
        }

        return improvement

    def scan_cycle(self):
        """Single scan cycle"""
        try:
            bookmarks = self.load_bookmarks()

            if not bookmarks:
                self.log("No bookmarks found")
                return

            # Check for new bookmarks
            new_bookmarks = [b for b in bookmarks if b.get('id') not in self.processed_ids]

            if not new_bookmarks:
                self.log(f"No new bookmarks (total: {len(bookmarks)})")
                return

            self.log(f"📥 Found {len(new_bookmarks)} new bookmarks")

            # Analyze each new bookmark
            discoveries = []
            for bookmark in new_bookmarks:
                analysis = self.analyze_bookmark(bookmark)

                if analysis:
                    # Log discovery
                    with open(DISCOVERIES_LOG, 'a') as f:
                        f.write(json.dumps(analysis) + '\n')

                    # Log to stream
                    with open(SCAN_LOG, 'a') as f:
                        f.write(json.dumps(analysis) + '\n')

                    discoveries.append(analysis)
                    self.log(f"✅ Discovery: {analysis['matched_keywords']} - {analysis['author']}")

                # Mark as processed
                self.processed_ids.add(bookmark.get('id'))

            if discoveries:
                self.log(f"🎯 {len(discoveries)} actionable discoveries logged")

        except Exception as e:
            self.log(f"❌ Error in scan cycle: {e}")

    def run(self, interval=300):
        """Run continuous monitoring"""
        self.log("🔍 BOOKMARK DEEP-SCAN AGENT ACTIVE")
        self.log(f"Scanning every {interval}s (every {interval//60} min)")
        self.log(f"Discoveries logged to: {DISCOVERIES_LOG}")
        self.log(f"Stream logged to: {SCAN_LOG}\n")

        while True:
            try:
                self.scan_cycle()
                time.sleep(interval)

            except KeyboardInterrupt:
                self.log("\n🛑 Bookmark scanner stopped")
                break
            except Exception as e:
                self.log(f"❌ Error: {e}")
                time.sleep(60)

if __name__ == '__main__':
    scanner = BookmarkScanner()
    scanner.run(interval=300)  # Every 5 minutes
