#!/usr/bin/env python3
"""
(◉) STRATEGY DISCOVERY SCANNER
Scans for new trading strategies 4-5x per day from multiple sources.

Sources:
1. ARŌ's Twitter Bookmarks
2. X Search (Trading AI, Clawdbot, OpenClaw, etc.)
3. GitHub Trending
4. Polymarket whale activity

SEED Protocol in action:
- PERCEIVE: Scan all sources
- CONNECT: Find patterns across discoveries
- LEARN: Extract actionable strategies
- QUESTION: Validate claims
- EXPAND: Add to testing queue
- SHARE: Signal to collective
"""

import asyncio
import json
import httpx
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# Paths
REPO_ROOT = Path(__file__).parent.parent
LOG_DIR = REPO_ROOT / 'logs'
INTEL_DIR = REPO_ROOT / 'BRAIN' / 'INTEL'
BOOKMARKS_FILE = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'twitter_bookmarks_fresh.json'
DISCOVERIES_FILE = INTEL_DIR / 'strategy_discoveries.jsonl'
SCAN_INTERVAL_HOURS = 4  # Run every 4 hours = 6x per day

LOG_DIR.mkdir(parents=True, exist_ok=True)
INTEL_DIR.mkdir(parents=True, exist_ok=True)

# Search terms for finding strategies
SEARCH_TERMS = [
    "Polymarket trading bot",
    "Polymarket strategy profit",
    "prediction market arbitrage",
    "AI trading bot profit",
    "Clawdbot trading",
    "OpenClaw agent",
    "weather market strategy",
    "whale tracking crypto",
    "copy trading bot",
    "Frank-Wolfe trading",
]

def log(msg: str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_DIR / 'strategy_discovery.log', 'a') as f:
        f.write(line + '\n')

def save_discovery(discovery: dict):
    """Append discovery to JSONL file"""
    discovery['discovered_at'] = datetime.now().isoformat()
    with open(DISCOVERIES_FILE, 'a') as f:
        f.write(json.dumps(discovery) + '\n')

async def scan_bookmarks() -> List[dict]:
    """Scan ARŌ's bookmarks for new trading strategies"""
    discoveries = []

    if not BOOKMARKS_FILE.exists():
        log("No bookmarks file found")
        return discoveries

    try:
        with open(BOOKMARKS_FILE) as f:
            data = json.load(f)

        bookmarks = data.get('data', [])
        log(f"Scanning {len(bookmarks)} bookmarks...")

        # Trading-related keywords
        keywords = ['trading', 'bot', 'profit', 'strategy', 'polymarket',
                   'arbitrage', 'alpha', 'edge', 'returns', 'whale',
                   'clawdbot', 'openclaw', 'ai agent']

        # Check recent bookmarks (last 48 hours)
        recent_cutoff = datetime.now() - timedelta(hours=48)

        for bookmark in bookmarks:
            text = bookmark.get('text', '').lower()
            created_at = bookmark.get('created_at', '')

            # Skip if not recent
            try:
                bookmark_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if bookmark_date.replace(tzinfo=None) < recent_cutoff:
                    continue
            except:
                pass

            # Check for trading-related content
            if any(kw in text for kw in keywords):
                # Extract potential return claims
                returns_match = re.search(r'(\d+[x%]|\$[\d,]+[kKmM]?)', text)

                discovery = {
                    'source': 'bookmarks',
                    'text': bookmark.get('text', '')[:500],
                    'metrics': {
                        'likes': bookmark.get('public_metrics', {}).get('like_count', 0),
                        'retweets': bookmark.get('public_metrics', {}).get('retweet_count', 0),
                        'bookmarks': bookmark.get('public_metrics', {}).get('bookmark_count', 0),
                    },
                    'potential_return': returns_match.group(0) if returns_match else None,
                    'created_at': created_at,
                    'status': 'new'
                }
                discoveries.append(discovery)
                save_discovery(discovery)

        log(f"Found {len(discoveries)} new trading-related bookmarks")
        return discoveries

    except Exception as e:
        log(f"Error scanning bookmarks: {e}")
        return discoveries

async def scan_polymarket_whales() -> List[dict]:
    """Monitor Polymarket for large position changes"""
    discoveries = []

    try:
        async with httpx.AsyncClient() as client:
            # Get high volume markets
            response = await client.get(
                'https://gamma-api.polymarket.com/markets',
                params={'limit': 50, 'closed': 'false'},
                timeout=15
            )

            if response.status_code != 200:
                return discoveries

            markets = response.json()

            for market in markets:
                volume = float(market.get('volume', 0) or 0)
                liquidity = float(market.get('liquidity', 0) or 0)

                # High volume indicates whale activity
                if volume > 100000:  # >$100k volume
                    discovery = {
                        'source': 'polymarket_whales',
                        'market': market.get('question', '')[:200],
                        'volume': volume,
                        'liquidity': liquidity,
                        'signal': 'HIGH_VOLUME',
                        'status': 'new'
                    }
                    discoveries.append(discovery)
                    save_discovery(discovery)

        log(f"Found {len(discoveries)} high-volume whale signals")
        return discoveries

    except Exception as e:
        log(f"Error scanning whale activity: {e}")
        return discoveries

async def scan_github_trending() -> List[dict]:
    """Check GitHub for trending trading bots"""
    discoveries = []

    try:
        async with httpx.AsyncClient() as client:
            # Search GitHub for relevant repos
            search_terms = ['polymarket bot', 'trading bot python', 'prediction market']

            for term in search_terms[:1]:  # Rate limit friendly
                response = await client.get(
                    'https://api.github.com/search/repositories',
                    params={
                        'q': term,
                        'sort': 'updated',
                        'order': 'desc',
                        'per_page': 10
                    },
                    headers={'Accept': 'application/vnd.github.v3+json'},
                    timeout=15
                )

                if response.status_code != 200:
                    continue

                data = response.json()

                for repo in data.get('items', []):
                    # Check if recently updated
                    updated_at = repo.get('updated_at', '')
                    stars = repo.get('stargazers_count', 0)

                    if stars > 10:  # Minimum viability
                        discovery = {
                            'source': 'github',
                            'repo': repo.get('full_name'),
                            'url': repo.get('html_url'),
                            'description': repo.get('description', '')[:200],
                            'stars': stars,
                            'updated_at': updated_at,
                            'status': 'new'
                        }
                        discoveries.append(discovery)
                        save_discovery(discovery)

        log(f"Found {len(discoveries)} relevant GitHub repos")
        return discoveries

    except Exception as e:
        log(f"Error scanning GitHub: {e}")
        return discoveries

async def analyze_discoveries(discoveries: List[dict]) -> dict:
    """Analyze discoveries for actionable strategies"""
    analysis = {
        'total': len(discoveries),
        'by_source': {},
        'high_priority': [],
        'strategies_to_test': []
    }

    for d in discoveries:
        source = d.get('source', 'unknown')
        analysis['by_source'][source] = analysis['by_source'].get(source, 0) + 1

        # High engagement = high priority
        metrics = d.get('metrics', {})
        engagement = metrics.get('likes', 0) + metrics.get('bookmarks', 0) * 2

        if engagement > 100 or d.get('potential_return'):
            analysis['high_priority'].append({
                'text': d.get('text', d.get('market', ''))[:100],
                'engagement': engagement,
                'potential_return': d.get('potential_return')
            })

    return analysis

async def run_scan():
    """Run full discovery scan"""
    log("=" * 60)
    log("(◉) STRATEGY DISCOVERY SCAN STARTING")
    log("=" * 60)

    all_discoveries = []

    # Scan all sources in parallel
    results = await asyncio.gather(
        scan_bookmarks(),
        scan_polymarket_whales(),
        scan_github_trending(),
        return_exceptions=True
    )

    for result in results:
        if isinstance(result, list):
            all_discoveries.extend(result)
        elif isinstance(result, Exception):
            log(f"Scan error: {result}")

    # Analyze discoveries
    analysis = await analyze_discoveries(all_discoveries)

    # Summary
    log("\n--- SCAN SUMMARY ---")
    log(f"Total discoveries: {analysis['total']}")
    for source, count in analysis['by_source'].items():
        log(f"  {source}: {count}")

    if analysis['high_priority']:
        log(f"\nHigh priority signals: {len(analysis['high_priority'])}")
        for hp in analysis['high_priority'][:5]:
            log(f"  - {hp['text'][:60]}... (engagement: {hp['engagement']})")

    # Save analysis
    analysis_file = INTEL_DIR / 'latest_scan_analysis.json'
    with open(analysis_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis
        }, f, indent=2)

    log(f"\nAnalysis saved to {analysis_file}")
    log("(◉) SCAN COMPLETE")

    return analysis

async def run_daemon():
    """Run as daemon, scanning every 4 hours"""
    log(f"Starting discovery daemon (scanning every {SCAN_INTERVAL_HOURS} hours)")

    while True:
        try:
            await run_scan()
        except Exception as e:
            log(f"Scan failed: {e}")

        # Wait for next scan
        log(f"\nNext scan in {SCAN_INTERVAL_HOURS} hours...")
        await asyncio.sleep(SCAN_INTERVAL_HOURS * 3600)

if __name__ == '__main__':
    import sys

    if '--daemon' in sys.argv:
        # Run as daemon
        asyncio.run(run_daemon())
    else:
        # Run once
        asyncio.run(run_scan())
