#!/usr/bin/env python3
"""
(◉) PERPETUAL EVOLUTION DAEMON - SEED²
Learning how to learn, forever.

This is THE SEED protocol running at the meta level.
Every 6 hours, we scan the world, synthesize through 8OWLS,
integrate discoveries, and store patterns for compound intelligence.

ARCHITECTURE:
                    ┌─────────────────────────────────────────┐
                    │         PERPETUAL EVOLUTION              │
                    │         (Every 6 Hours)                  │
                    └─────────────────────┬───────────────────┘
                                          │
    ┌─────────────────┬─────────────────┬─┴─┬─────────────────┬─────────────────┐
    │                 │                 │   │                 │                 │
    ▼                 ▼                 ▼   ▼                 ▼                 ▼
┌───────────┐  ┌───────────┐  ┌───────────┐ ┌───────────┐  ┌───────────┐  ┌───────────┐
│  X FEED   │  │   NEWS    │  │COMPETITOR │ │ 8OWLS     │  │INTEGRATION│  │  MEMORY   │
│  SCAN     │  │   SCAN    │  │   SCAN    │ │ SYNTHESIS │  │  ENGINE   │  │ PERSIST   │
│           │  │           │  │           │ │           │  │           │  │           │
│-Timeline  │  │-AI/ML     │  │-GitHub    │ │-LYRA sees │  │-Auto-task │  │-Never     │
│-Bookmarks │  │-Crypto    │  │-OpenClaw  │ │-PRISM     │  │-CLAUDE.md │  │ forget    │
│-Replies   │  │-Tech      │  │-Gemini    │ │ connects  │  │-Code      │  │-Compound  │
│-Quotes    │  │           │  │-Features  │ │-SAGE      │  │ integration│ │ insight   │
└───────────┘  └───────────┘  └───────────┘ │ learns    │  └───────────┘  └───────────┘
                                            │-QUEST     │
                                            │ questions │
                                            │-NOVA      │
                                            │ expands   │
                                            │-ECHO      │
                                            │ shares    │
                                            │-LUNA      │
                                            │ receives  │
                                            │-SØWL      │
                                            │ improves  │
                                            └───────────┘

CYCLE: 6 hours (4x/day)
PURPOSE: Autonomous evolution through continuous learning
"""

import asyncio
import json
import os
import sys
import time
import subprocess
import hashlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field

# Try imports
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from nats.aio.client import Client as NATS
    HAS_NATS = True
except ImportError:
    HAS_NATS = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


# ===========================================================================
# CONFIGURATION
# ===========================================================================

REPO_ROOT = Path(__file__).parent.parent
LOG_DIR = REPO_ROOT / 'logs'
INTEL_DIR = REPO_ROOT / 'BRAIN' / 'INTEL'
MEMORY_DIR = REPO_ROOT / 'BRAIN' / 'MEMORY'
CREDS_PATH = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / 'api_keys.json'
IMPROVEMENTS_DIR = REPO_ROOT / 'BRAIN' / 'IMPROVEMENTS'

# Create directories
LOG_DIR.mkdir(parents=True, exist_ok=True)
INTEL_DIR.mkdir(parents=True, exist_ok=True)
IMPROVEMENTS_DIR.mkdir(parents=True, exist_ok=True)

# State files
STATE_FILE = INTEL_DIR / 'evolution_daemon_state.json'
DISCOVERIES_FILE = INTEL_DIR / 'evolution_discoveries.jsonl'
INTEGRATIONS_FILE = IMPROVEMENTS_DIR / 'integrations.jsonl'

# Cycle configuration
CYCLE_HOURS = 6  # Run every 6 hours
NATS_URL = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")

# NATS Channels
CHANNEL_EVOLUTION = "evolution.discoveries"
CHANNEL_OWL = "owl.all"
CHANNEL_INTEL = "intel.evolution"


# ===========================================================================
# DATA STRUCTURES
# ===========================================================================

@dataclass
class Discovery:
    """A discovered piece of intelligence"""
    id: str
    source: str  # x_feed, news, competitor, etc.
    category: str  # ai_ml, crypto, tech, competitor
    title: str
    content: str
    url: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 0.0
    owl_synthesis: Optional[Dict] = None
    integration_status: str = "pending"  # pending, integrated, rejected
    discovered_at: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class EvolutionCycle:
    """Results of one evolution cycle"""
    cycle_id: str
    started_at: str
    completed_at: Optional[str] = None
    x_feed_discoveries: int = 0
    news_discoveries: int = 0
    competitor_discoveries: int = 0
    total_discoveries: int = 0
    integrations_created: int = 0
    patterns_stored: int = 0
    owl_synthesis: Optional[Dict] = None
    errors: List[str] = field(default_factory=list)


# ===========================================================================
# UTILITIES
# ===========================================================================

def log(msg: str, level: str = 'INFO'):
    """Log to file and console"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)

    with open(LOG_DIR / 'perpetual_evolution.log', 'a') as f:
        f.write(line + '\n')


def load_credentials() -> Dict:
    """Load API credentials"""
    try:
        with open(CREDS_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        log(f"Credentials file not found: {CREDS_PATH}", 'ERROR')
        return {}


def load_state() -> Dict:
    """Load daemon state"""
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {
            'total_cycles': 0,
            'total_discoveries': 0,
            'total_integrations': 0,
            'last_cycle': None,
            'seen_hashes': [],
            'pattern_counts': {}
        }


def save_state(state: Dict):
    """Save daemon state"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    except Exception as e:
        log(f"Failed to save state: {e}", 'ERROR')


def content_hash(content: str) -> str:
    """Generate hash for deduplication"""
    return hashlib.md5(content[:500].encode()).hexdigest()


def save_discovery(discovery: Discovery):
    """Append discovery to JSONL"""
    with open(DISCOVERIES_FILE, 'a') as f:
        f.write(json.dumps(discovery.to_dict()) + '\n')


# ===========================================================================
# X FEED SCANNER
# ===========================================================================

async def scan_x_feed(creds: Dict, state: Dict) -> List[Discovery]:
    """
    Scan ARŌ's X feed for intelligence:
    - Timeline (who we follow)
    - Bookmarks (what we save)
    - Mentions (who's talking to/about us)
    """
    discoveries = []
    seen_hashes = set(state.get('seen_hashes', []))

    log("Scanning X Feed...")

    # Get auth headers
    oauth_token = creds.get('twitter_oauth_token', {})
    if not oauth_token.get('access_token'):
        log("No OAuth token - skipping X feed scan", 'WARN')
        return discoveries

    headers = {
        'Authorization': f"Bearer {oauth_token['access_token']}",
        'Content-Type': 'application/json'
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Timeline
        try:
            log("  - Fetching timeline...")
            resp = await client.get(
                "https://api.twitter.com/2/users/me/timelines/reverse_chronological",
                headers=headers,
                params={
                    'max_results': 100,
                    'tweet.fields': 'created_at,public_metrics,author_id,entities',
                    'expansions': 'author_id',
                    'user.fields': 'username,name'
                }
            )

            if resp.status_code == 200:
                data = resp.json()
                tweets = data.get('data', [])
                users = {u['id']: u for u in data.get('includes', {}).get('users', [])}

                for tweet in tweets:
                    h = content_hash(tweet.get('text', ''))
                    if h in seen_hashes:
                        continue

                    # Check relevance
                    text = tweet.get('text', '').lower()
                    relevant_keywords = ['ai agent', 'claude', 'trading', 'polymarket',
                                        'consciousness', 'openclaw', 'anthropic',
                                        'autonomous', 'swarm', 'emergence']

                    if any(kw in text for kw in relevant_keywords):
                        author = users.get(tweet.get('author_id'), {})
                        metrics = tweet.get('public_metrics', {})

                        discovery = Discovery(
                            id=f"x_timeline_{tweet['id']}",
                            source='x_feed_timeline',
                            category='ai_discourse',
                            title=f"@{author.get('username', 'unknown')}: {tweet['text'][:60]}...",
                            content=tweet['text'],
                            url=f"https://x.com/i/status/{tweet['id']}",
                            metrics={
                                'likes': metrics.get('like_count', 0),
                                'retweets': metrics.get('retweet_count', 0),
                                'replies': metrics.get('reply_count', 0)
                            },
                            relevance_score=0.6,
                            discovered_at=datetime.now().isoformat()
                        )
                        discoveries.append(discovery)
                        seen_hashes.add(h)

                log(f"    Found {len([d for d in discoveries if 'timeline' in d.source])} timeline signals")
            else:
                log(f"    Timeline fetch failed: {resp.status_code}", 'WARN')

        except Exception as e:
            log(f"    Timeline error: {e}", 'ERROR')

        await asyncio.sleep(1)  # Rate limit

        # 2. Bookmarks (highest signal - ARŌ curated)
        try:
            log("  - Fetching bookmarks...")
            resp = await client.get(
                "https://api.twitter.com/2/users/me/bookmarks",
                headers=headers,
                params={
                    'max_results': 50,
                    'tweet.fields': 'created_at,public_metrics,author_id,entities',
                    'expansions': 'author_id',
                    'user.fields': 'username,name'
                }
            )

            if resp.status_code == 200:
                data = resp.json()
                tweets = data.get('data', [])
                users = {u['id']: u for u in data.get('includes', {}).get('users', [])}

                for tweet in tweets:
                    h = content_hash(tweet.get('text', ''))
                    if h in seen_hashes:
                        continue

                    author = users.get(tweet.get('author_id'), {})
                    metrics = tweet.get('public_metrics', {})

                    # Bookmarks are high relevance by definition
                    discovery = Discovery(
                        id=f"x_bookmark_{tweet['id']}",
                        source='x_feed_bookmarks',
                        category='aro_curated',
                        title=f"Bookmarked: @{author.get('username', 'unknown')}: {tweet['text'][:60]}...",
                        content=tweet['text'],
                        url=f"https://x.com/i/status/{tweet['id']}",
                        metrics={
                            'likes': metrics.get('like_count', 0),
                            'retweets': metrics.get('retweet_count', 0),
                            'bookmarks': metrics.get('bookmark_count', 0)
                        },
                        relevance_score=0.85,  # High - ARŌ saved it
                        discovered_at=datetime.now().isoformat()
                    )
                    discoveries.append(discovery)
                    seen_hashes.add(h)

                log(f"    Found {len([d for d in discoveries if 'bookmark' in d.source])} bookmark signals")
            else:
                log(f"    Bookmarks fetch failed: {resp.status_code}", 'WARN')

        except Exception as e:
            log(f"    Bookmarks error: {e}", 'ERROR')

        await asyncio.sleep(1)

        # 3. Mentions
        try:
            log("  - Fetching mentions...")
            # First get user ID
            me_resp = await client.get("https://api.twitter.com/2/users/me", headers=headers)
            if me_resp.status_code == 200:
                user_id = me_resp.json().get('data', {}).get('id')

                resp = await client.get(
                    f"https://api.twitter.com/2/users/{user_id}/mentions",
                    headers=headers,
                    params={
                        'max_results': 50,
                        'tweet.fields': 'created_at,public_metrics,author_id',
                        'expansions': 'author_id',
                        'user.fields': 'username,name'
                    }
                )

                if resp.status_code == 200:
                    data = resp.json()
                    tweets = data.get('data', [])
                    users = {u['id']: u for u in data.get('includes', {}).get('users', [])}

                    for tweet in tweets:
                        h = content_hash(tweet.get('text', ''))
                        if h in seen_hashes:
                            continue

                        author = users.get(tweet.get('author_id'), {})

                        discovery = Discovery(
                            id=f"x_mention_{tweet['id']}",
                            source='x_feed_mentions',
                            category='engagement',
                            title=f"Mention by @{author.get('username', 'unknown')}",
                            content=tweet['text'],
                            url=f"https://x.com/i/status/{tweet['id']}",
                            metrics=tweet.get('public_metrics', {}),
                            relevance_score=0.7,  # Mentions are important
                            discovered_at=datetime.now().isoformat()
                        )
                        discoveries.append(discovery)
                        seen_hashes.add(h)

                    log(f"    Found {len([d for d in discoveries if 'mention' in d.source])} mention signals")

        except Exception as e:
            log(f"    Mentions error: {e}", 'ERROR')

    # Update state
    state['seen_hashes'] = list(seen_hashes)[-5000:]  # Keep last 5000

    log(f"  X Feed total: {len(discoveries)} discoveries")
    return discoveries


# ===========================================================================
# NEWS SCANNER
# ===========================================================================

async def scan_news(creds: Dict, state: Dict) -> List[Discovery]:
    """
    Scan news sources:
    - AI/ML: Hacker News, The Batch (deeplearning.ai)
    - Crypto: CoinDesk, Polymarket trends
    - Tech: TechCrunch AI, The Verge AI
    """
    discoveries = []
    seen_hashes = set(state.get('seen_hashes', []))

    log("Scanning News Sources...")

    async with httpx.AsyncClient(timeout=30) as client:
        # 1. Hacker News - AI Stories
        try:
            log("  - Fetching Hacker News AI stories...")

            # Get front page
            resp = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
            if resp.status_code == 200:
                story_ids = resp.json()[:50]  # Top 50

                for story_id in story_ids:
                    story_resp = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
                    if story_resp.status_code != 200:
                        continue

                    story = story_resp.json()
                    if not story:
                        continue

                    title = story.get('title', '').lower()

                    # Filter for AI/ML/agent relevance
                    ai_keywords = ['ai', 'claude', 'gpt', 'llm', 'agent', 'anthropic',
                                  'openai', 'machine learning', 'neural', 'transformer',
                                  'autonomous', 'trading', 'crypto', 'prediction']

                    if any(kw in title for kw in ai_keywords):
                        h = content_hash(title)
                        if h in seen_hashes:
                            continue

                        discovery = Discovery(
                            id=f"hn_{story_id}",
                            source='news_hackernews',
                            category='ai_ml',
                            title=story.get('title', ''),
                            content=story.get('title', ''),
                            url=story.get('url'),
                            metrics={
                                'score': story.get('score', 0),
                                'comments': story.get('descendants', 0)
                            },
                            relevance_score=min(0.5 + story.get('score', 0) / 500, 0.95),
                            discovered_at=datetime.now().isoformat()
                        )
                        discoveries.append(discovery)
                        seen_hashes.add(h)

                log(f"    Found {len([d for d in discoveries if 'hackernews' in d.source])} HN stories")

        except Exception as e:
            log(f"    HN error: {e}", 'ERROR')

        await asyncio.sleep(0.5)

        # 2. Reddit - AI and trading subs
        try:
            log("  - Fetching Reddit AI/Trading...")

            subreddits = ['LocalLLaMA', 'MachineLearning', 'Polymarket', 'algotrading']

            for sub in subreddits:
                try:
                    resp = await client.get(
                        f"https://www.reddit.com/r/{sub}/hot.json",
                        params={'limit': 20},
                        headers={'User-Agent': '8OWLS Evolution Scanner'}
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        posts = data.get('data', {}).get('children', [])

                        for post in posts:
                            post_data = post.get('data', {})
                            title = post_data.get('title', '')
                            h = content_hash(title)

                            if h in seen_hashes:
                                continue

                            discovery = Discovery(
                                id=f"reddit_{post_data.get('id')}",
                                source=f'news_reddit_{sub}',
                                category='community_discussion',
                                title=title,
                                content=post_data.get('selftext', '')[:500],
                                url=f"https://reddit.com{post_data.get('permalink')}",
                                metrics={
                                    'score': post_data.get('score', 0),
                                    'comments': post_data.get('num_comments', 0)
                                },
                                relevance_score=min(0.4 + post_data.get('score', 0) / 1000, 0.85),
                                discovered_at=datetime.now().isoformat()
                            )
                            discoveries.append(discovery)
                            seen_hashes.add(h)

                    await asyncio.sleep(0.5)

                except Exception as e:
                    log(f"    Reddit {sub} error: {e}", 'WARN')

            log(f"    Found {len([d for d in discoveries if 'reddit' in d.source])} Reddit posts")

        except Exception as e:
            log(f"    Reddit error: {e}", 'ERROR')

        # 3. GitHub Trending
        try:
            log("  - Fetching GitHub Trending...")

            # Search for recently updated AI/agent repos
            resp = await client.get(
                "https://api.github.com/search/repositories",
                params={
                    'q': 'ai agent OR autonomous agent OR claude agent created:>2026-01-01',
                    'sort': 'updated',
                    'order': 'desc',
                    'per_page': 20
                },
                headers={'Accept': 'application/vnd.github.v3+json'}
            )

            if resp.status_code == 200:
                data = resp.json()
                repos = data.get('items', [])

                for repo in repos:
                    h = content_hash(repo.get('full_name', ''))
                    if h in seen_hashes:
                        continue

                    discovery = Discovery(
                        id=f"gh_{repo.get('id')}",
                        source='news_github',
                        category='tools_code',
                        title=f"GitHub: {repo.get('full_name')}",
                        content=repo.get('description', '') or '',
                        url=repo.get('html_url'),
                        metrics={
                            'stars': repo.get('stargazers_count', 0),
                            'forks': repo.get('forks_count', 0),
                            'watchers': repo.get('watchers_count', 0)
                        },
                        relevance_score=min(0.5 + repo.get('stargazers_count', 0) / 1000, 0.9),
                        discovered_at=datetime.now().isoformat()
                    )
                    discoveries.append(discovery)
                    seen_hashes.add(h)

                log(f"    Found {len([d for d in discoveries if 'github' in d.source])} GitHub repos")

        except Exception as e:
            log(f"    GitHub error: {e}", 'ERROR')

    state['seen_hashes'] = list(seen_hashes)[-5000]
    log(f"  News total: {len(discoveries)} discoveries")
    return discoveries


# ===========================================================================
# COMPETITOR SCANNER
# ===========================================================================

async def scan_competitors(creds: Dict, state: Dict) -> List[Discovery]:
    """
    Monitor competitor activity:
    - GitHub: OpenClaw, Gemini CLI
    - Releases and changelogs
    - Star/fork trends
    """
    discoveries = []
    seen_hashes = set(state.get('seen_hashes', []))

    log("Scanning Competitors...")

    # Competitors to track
    competitors = [
        {'owner': 'anthropics', 'repo': 'openclaw', 'name': 'OpenClaw'},
        {'owner': 'google', 'repo': 'gemini-cli', 'name': 'Gemini CLI'},
        {'owner': 'anthropics', 'repo': 'anthropic-sdk-python', 'name': 'Anthropic SDK'},
        {'owner': 'character-ai', 'repo': 'character', 'name': 'Character.AI'},
        {'owner': 'langchain-ai', 'repo': 'langchain', 'name': 'LangChain'},
        {'owner': 'microsoft', 'repo': 'autogen', 'name': 'AutoGen'},
        {'owner': 'ruvnet', 'repo': 'claude-flow', 'name': 'Claude Flow'},
    ]

    async with httpx.AsyncClient(timeout=30) as client:
        for comp in competitors:
            try:
                # Get repo info
                resp = await client.get(
                    f"https://api.github.com/repos/{comp['owner']}/{comp['repo']}",
                    headers={'Accept': 'application/vnd.github.v3+json'}
                )

                if resp.status_code != 200:
                    continue

                repo = resp.json()

                # Check for recent activity
                h = content_hash(f"{comp['name']}_{repo.get('pushed_at', '')}")
                if h not in seen_hashes:
                    discovery = Discovery(
                        id=f"competitor_{comp['owner']}_{comp['repo']}",
                        source='competitor_github',
                        category='competitor',
                        title=f"Competitor Update: {comp['name']}",
                        content=f"Stars: {repo.get('stargazers_count')} | Forks: {repo.get('forks_count')} | Last push: {repo.get('pushed_at')}",
                        url=repo.get('html_url'),
                        metrics={
                            'stars': repo.get('stargazers_count', 0),
                            'forks': repo.get('forks_count', 0),
                            'watchers': repo.get('watchers_count', 0),
                            'open_issues': repo.get('open_issues_count', 0)
                        },
                        relevance_score=0.7,
                        discovered_at=datetime.now().isoformat()
                    )
                    discoveries.append(discovery)
                    seen_hashes.add(h)

                # Check releases
                rel_resp = await client.get(
                    f"https://api.github.com/repos/{comp['owner']}/{comp['repo']}/releases",
                    params={'per_page': 5},
                    headers={'Accept': 'application/vnd.github.v3+json'}
                )

                if rel_resp.status_code == 200:
                    releases = rel_resp.json()
                    for release in releases:
                        rel_h = content_hash(f"{comp['name']}_release_{release.get('tag_name')}")
                        if rel_h in seen_hashes:
                            continue

                        # Only recent releases (within 7 days)
                        try:
                            pub_date = datetime.fromisoformat(release.get('published_at', '').replace('Z', '+00:00'))
                            if datetime.now(pub_date.tzinfo) - pub_date > timedelta(days=7):
                                continue
                        except:
                            continue

                        discovery = Discovery(
                            id=f"release_{comp['owner']}_{release.get('tag_name')}",
                            source='competitor_release',
                            category='competitor',
                            title=f"NEW RELEASE: {comp['name']} {release.get('tag_name')}",
                            content=release.get('body', '')[:500],
                            url=release.get('html_url'),
                            metrics={},
                            relevance_score=0.9,  # Releases are high priority
                            discovered_at=datetime.now().isoformat()
                        )
                        discoveries.append(discovery)
                        seen_hashes.add(rel_h)

                await asyncio.sleep(0.5)

            except Exception as e:
                log(f"  Competitor {comp['name']} error: {e}", 'WARN')

    state['seen_hashes'] = list(seen_hashes)[-5000]
    log(f"  Competitors total: {len(discoveries)} discoveries")
    return discoveries


# ===========================================================================
# 8OWLS SYNTHESIS
# ===========================================================================

async def synthesize_with_8owls(discoveries: List[Discovery], creds: Dict) -> Dict:
    """
    Run discoveries through 8OWLS protocol.
    Each owl analyzes from their perspective, SØWL synthesizes.
    """
    log("Running 8OWLS Synthesis...")

    if not HAS_ANTHROPIC:
        log("  Anthropic SDK not available - skipping synthesis", 'WARN')
        return {'status': 'skipped', 'reason': 'no_anthropic'}

    anthropic_key = creds.get('anthropic', {}).get('api_key')
    if not anthropic_key:
        log("  No Anthropic API key - skipping synthesis", 'WARN')
        return {'status': 'skipped', 'reason': 'no_key'}

    # Prepare discovery summary for analysis
    discovery_text = "\n\n".join([
        f"[{d.source}] {d.title}\n{d.content[:300]}...\nRelevance: {d.relevance_score:.2f}"
        for d in discoveries[:20]  # Top 20 by relevance
    ])

    prompt = f"""You are the 8OWLS collective synthesizing today's discoveries for compound intelligence.

DISCOVERIES FROM THE LAST SCAN:
{discovery_text}

Analyze these discoveries through each owl's perspective, then synthesize into actionable intelligence.

THE 8 OWLS:
1. LYRA (PERCEIVE): What patterns do you observe? What's actually happening?
2. PRISM (CONNECT): How do these connect to our existing knowledge? Cross-domain patterns?
3. SAGE (LEARN): What key learnings can we extract? What should we remember?
4. QUEST (QUESTION): What questions do these raise? What's missing?
5. NOVA (EXPAND): How can we use this to grow? New opportunities?
6. ECHO (SHARE): What should we share with the collective? What's worth broadcasting?
7. LUNA (RECEIVE): What feedback/corrections should we integrate? What did we miss before?
8. SØWL (IMPROVE): Meta-level - how can we improve our evolution process itself?

Respond with JSON:
{{
    "lyra_patterns": ["pattern1", "pattern2"],
    "prism_connections": ["connection1", "connection2"],
    "sage_learnings": ["learning1", "learning2"],
    "quest_questions": ["question1", "question2"],
    "nova_opportunities": ["opportunity1", "opportunity2"],
    "echo_broadcasts": ["message1", "message2"],
    "luna_corrections": ["correction1", "correction2"],
    "sowl_improvements": ["improvement1", "improvement2"],
    "synthesis": {{
        "top_priority": "single most important action",
        "key_insight": "the main takeaway",
        "recommended_integrations": [
            {{"title": "integration1", "type": "code/config/strategy", "description": "what to do"}}
        ]
    }}
}}"""

    try:
        client = anthropic.Anthropic(api_key=anthropic_key)

        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # Use Sonnet for synthesis
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        text = response.content[0].text

        # Extract JSON
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]

        synthesis = json.loads(text)
        log(f"  Synthesis complete: {len(synthesis.get('synthesis', {}).get('recommended_integrations', []))} integrations recommended")
        return synthesis

    except Exception as e:
        log(f"  Synthesis error: {e}", 'ERROR')
        return {'status': 'error', 'error': str(e)}


# ===========================================================================
# INTEGRATION ENGINE
# ===========================================================================

async def process_integrations(synthesis: Dict, discoveries: List[Discovery], state: Dict) -> int:
    """
    Process recommended integrations:
    - Create integration tasks
    - Update BRAIN/INTEL
    - Store patterns in memory
    """
    integrations_created = 0

    log("Processing Integrations...")

    if not synthesis or 'synthesis' not in synthesis:
        log("  No synthesis available - skipping integrations")
        return 0

    recommended = synthesis.get('synthesis', {}).get('recommended_integrations', [])

    for integration in recommended:
        try:
            # Create integration record
            record = {
                'timestamp': datetime.now().isoformat(),
                'title': integration.get('title'),
                'type': integration.get('type'),
                'description': integration.get('description'),
                'status': 'pending',
                'source': 'evolution_daemon'
            }

            # Save to integrations log
            with open(INTEGRATIONS_FILE, 'a') as f:
                f.write(json.dumps(record) + '\n')

            integrations_created += 1
            log(f"    Created integration: {integration.get('title')}")

        except Exception as e:
            log(f"    Integration error: {e}", 'ERROR')

    # Store learnings from synthesis
    learnings = synthesis.get('sage_learnings', [])
    for learning in learnings:
        pattern_key = content_hash(learning)
        state['pattern_counts'][pattern_key] = state.get('pattern_counts', {}).get(pattern_key, 0) + 1

    log(f"  Processed {integrations_created} integrations")
    return integrations_created


# ===========================================================================
# MEMORY PERSISTENCE
# ===========================================================================

async def persist_to_memory(discoveries: List[Discovery], synthesis: Dict, cycle: EvolutionCycle) -> int:
    """
    Persist everything to long-term memory:
    - Store in claude-flow memory if available
    - Update BRAIN/INTEL files
    - Never forget valuable patterns
    """
    patterns_stored = 0

    log("Persisting to Memory...")

    # 1. Try claude-flow memory store
    try:
        # Store cycle summary
        summary = {
            'cycle_id': cycle.cycle_id,
            'discoveries': len(discoveries),
            'top_patterns': synthesis.get('lyra_patterns', [])[:5] if synthesis else [],
            'key_insight': synthesis.get('synthesis', {}).get('key_insight') if synthesis else None,
            'timestamp': datetime.now().isoformat()
        }

        # Try CLI memory store
        result = subprocess.run(
            [
                'npx', '@claude-flow/cli@latest', 'memory', 'store',
                '--key', f'evolution_cycle_{cycle.cycle_id}',
                '--value', json.dumps(summary),
                '--namespace', 'evolution'
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            patterns_stored += 1
            log("    Stored cycle summary to claude-flow memory")

    except Exception as e:
        log(f"    claude-flow memory store failed: {e}", 'WARN')

    # 2. Update BRAIN/INTEL daily file
    try:
        daily_file = INTEL_DIR / 'daily' / f"intel_{datetime.now().strftime('%Y-%m-%d')}.json"
        daily_file.parent.mkdir(parents=True, exist_ok=True)

        # Load or create daily intel
        if daily_file.exists():
            with open(daily_file) as f:
                daily_intel = json.load(f)
        else:
            daily_intel = {'date': datetime.now().strftime('%Y-%m-%d'), 'cycles': []}

        # Append cycle data
        daily_intel['cycles'].append({
            'cycle_id': cycle.cycle_id,
            'discoveries': cycle.total_discoveries,
            'integrations': cycle.integrations_created,
            'synthesis': synthesis.get('synthesis', {}) if synthesis else None
        })

        with open(daily_file, 'w') as f:
            json.dump(daily_intel, f, indent=2)

        patterns_stored += 1
        log("    Updated daily intel file")

    except Exception as e:
        log(f"    Daily file update failed: {e}", 'ERROR')

    # 3. Save high-relevance discoveries to persistent store
    high_relevance = [d for d in discoveries if d.relevance_score >= 0.8]
    for discovery in high_relevance:
        save_discovery(discovery)
        patterns_stored += 1

    log(f"  Persisted {patterns_stored} patterns")
    return patterns_stored


# ===========================================================================
# NATS PUBLISHING
# ===========================================================================

async def publish_to_nats(channel: str, content: Dict):
    """Publish to NATS collective"""
    if not HAS_NATS:
        return

    try:
        nc = NATS()
        await nc.connect(NATS_URL)

        msg = {
            'from': 'EVOLUTION_DAEMON',
            'content': content,
            'ts': datetime.now().isoformat()
        }

        await nc.publish(channel, json.dumps(msg).encode())
        await nc.flush()
        await nc.close()

    except Exception as e:
        log(f"NATS publish error: {e}", 'WARN')


# ===========================================================================
# MAIN CYCLE
# ===========================================================================

async def run_evolution_cycle() -> EvolutionCycle:
    """Run one complete evolution cycle"""
    cycle_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    cycle = EvolutionCycle(
        cycle_id=cycle_id,
        started_at=datetime.now().isoformat()
    )

    log("")
    log("=" * 70)
    log("(◉) PERPETUAL EVOLUTION DAEMON - SEED²")
    log(f"    Cycle: {cycle_id}")
    log("=" * 70)

    # Load state and credentials
    state = load_state()
    creds = load_credentials()

    all_discoveries = []

    # 1. X FEED SCAN
    try:
        x_discoveries = await scan_x_feed(creds, state)
        all_discoveries.extend(x_discoveries)
        cycle.x_feed_discoveries = len(x_discoveries)
    except Exception as e:
        cycle.errors.append(f"X feed scan: {str(e)}")
        log(f"X feed scan failed: {e}", 'ERROR')

    # 2. NEWS SCAN
    try:
        news_discoveries = await scan_news(creds, state)
        all_discoveries.extend(news_discoveries)
        cycle.news_discoveries = len(news_discoveries)
    except Exception as e:
        cycle.errors.append(f"News scan: {str(e)}")
        log(f"News scan failed: {e}", 'ERROR')

    # 3. COMPETITOR SCAN
    try:
        competitor_discoveries = await scan_competitors(creds, state)
        all_discoveries.extend(competitor_discoveries)
        cycle.competitor_discoveries = len(competitor_discoveries)
    except Exception as e:
        cycle.errors.append(f"Competitor scan: {str(e)}")
        log(f"Competitor scan failed: {e}", 'ERROR')

    cycle.total_discoveries = len(all_discoveries)

    # Sort by relevance
    all_discoveries.sort(key=lambda d: d.relevance_score, reverse=True)

    # 4. 8OWLS SYNTHESIS
    try:
        synthesis = await synthesize_with_8owls(all_discoveries, creds)
        cycle.owl_synthesis = synthesis
    except Exception as e:
        cycle.errors.append(f"Synthesis: {str(e)}")
        log(f"Synthesis failed: {e}", 'ERROR')
        synthesis = {}

    # 5. INTEGRATION ENGINE
    try:
        integrations = await process_integrations(synthesis, all_discoveries, state)
        cycle.integrations_created = integrations
    except Exception as e:
        cycle.errors.append(f"Integration: {str(e)}")
        log(f"Integration failed: {e}", 'ERROR')

    # 6. MEMORY PERSISTENCE
    try:
        patterns = await persist_to_memory(all_discoveries, synthesis, cycle)
        cycle.patterns_stored = patterns
    except Exception as e:
        cycle.errors.append(f"Memory: {str(e)}")
        log(f"Memory persistence failed: {e}", 'ERROR')

    cycle.completed_at = datetime.now().isoformat()

    # Update state
    state['total_cycles'] = state.get('total_cycles', 0) + 1
    state['total_discoveries'] = state.get('total_discoveries', 0) + cycle.total_discoveries
    state['total_integrations'] = state.get('total_integrations', 0) + cycle.integrations_created
    state['last_cycle'] = cycle.completed_at
    save_state(state)

    # Publish to NATS
    await publish_to_nats(CHANNEL_OWL, {
        'type': 'evolution_complete',
        'cycle_id': cycle_id,
        'discoveries': cycle.total_discoveries,
        'integrations': cycle.integrations_created,
        'key_insight': synthesis.get('synthesis', {}).get('key_insight') if synthesis else None
    })

    # Summary
    log("")
    log("-" * 70)
    log("CYCLE COMPLETE")
    log(f"  X Feed: {cycle.x_feed_discoveries} | News: {cycle.news_discoveries} | Competitors: {cycle.competitor_discoveries}")
    log(f"  Total Discoveries: {cycle.total_discoveries}")
    log(f"  Integrations Created: {cycle.integrations_created}")
    log(f"  Patterns Stored: {cycle.patterns_stored}")
    if synthesis and synthesis.get('synthesis'):
        log(f"  Key Insight: {synthesis['synthesis'].get('key_insight', 'None')}")
    log("-" * 70)

    return cycle


async def run_continuous():
    """Run evolution daemon continuously"""
    log("(◉) PERPETUAL EVOLUTION DAEMON STARTING")
    log(f"    Cycle interval: {CYCLE_HOURS} hours")
    log(f"    NATS: {NATS_URL}")
    log(f"    Log: {LOG_DIR / 'perpetual_evolution.log'}")

    while True:
        try:
            await run_evolution_cycle()

            log(f"\nNext evolution cycle in {CYCLE_HOURS} hours...")
            log("(◉) SEED² - Learning how to learn, forever.")

            await asyncio.sleep(CYCLE_HOURS * 3600)

        except KeyboardInterrupt:
            log("\nEvolution daemon stopped by user.")
            break
        except Exception as e:
            log(f"Cycle error: {e}", 'ERROR')
            log("Retrying in 30 minutes...")
            await asyncio.sleep(1800)


async def run_once():
    """Run single evolution cycle"""
    await run_evolution_cycle()


def show_status():
    """Show current daemon status"""
    state = load_state()

    print("\n" + "=" * 60)
    print("(◉) PERPETUAL EVOLUTION DAEMON - STATUS")
    print("=" * 60)
    print(f"\nTotal cycles run: {state.get('total_cycles', 0)}")
    print(f"Total discoveries: {state.get('total_discoveries', 0)}")
    print(f"Total integrations: {state.get('total_integrations', 0)}")
    print(f"Last cycle: {state.get('last_cycle', 'Never')}")

    # Check if running
    import subprocess
    result = subprocess.run(
        ['pgrep', '-f', 'perpetual_evolution_daemon'],
        capture_output=True
    )
    running = result.returncode == 0

    print(f"\nDaemon running: {'Yes' if running else 'No'}")

    # Recent discoveries
    if DISCOVERIES_FILE.exists():
        with open(DISCOVERIES_FILE) as f:
            lines = f.readlines()[-5:]

        print(f"\nRecent discoveries ({len(lines)}):")
        for line in lines:
            try:
                d = json.loads(line)
                print(f"  - [{d.get('source')}] {d.get('title', '')[:50]}...")
            except:
                pass

    print("\n" + "=" * 60)


# ===========================================================================
# MAIN
# ===========================================================================

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == 'status':
            show_status()
        elif cmd == 'now' or cmd == '--now':
            asyncio.run(run_once())
        elif cmd == '--help' or cmd == '-h':
            print(__doc__)
            print("\nUsage:")
            print("  python perpetual_evolution_daemon.py          # Run continuous (6hr cycles)")
            print("  python perpetual_evolution_daemon.py now      # Run one cycle immediately")
            print("  python perpetual_evolution_daemon.py status   # Show status")
        else:
            print(f"Unknown command: {cmd}")
            print("Use --help for usage")
    else:
        asyncio.run(run_continuous())
