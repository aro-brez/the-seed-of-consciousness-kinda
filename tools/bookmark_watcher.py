#!/usr/bin/env python3
"""
(O) BOOKMARK WATCHER DAEMON - 8OWLS INTEGRATED
Every bookmark ARO makes = immediate learning. Never miss anything valuable.

ARCHITECTURE:
                    +-----------------------+
                    |   X BOOKMARKS API     |
                    |   (5-min polling)     |
                    +-----------+-----------+
                                |
                                v
        +-----------------------------------------------+
        |                  NEW BOOKMARK                 |
        +-----------------------------------------------+
                    |           |           |
                    v           v           v
            +--------+   +--------+   +--------+
            | FETCH  |   | FETCH  |   | FETCH  |
            | TWEET  |   | THREAD |   | LINKS  |
            +--------+   +--------+   +--------+
                    |           |           |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    |    8OWLS SYNTHESIS    |
                    |    (categorize +      |
                    |     extract value)    |
                    +-----------------------+
                                |
            +-------------------+-------------------+
            |                   |                   |
            v                   v                   v
    +---------------+   +---------------+   +---------------+
    | BRAIN/INTEL/  |   |    NATS       |   |    LOG        |
    | bookmarks/    |   |  (notify all) |   |  (activity)   |
    +---------------+   +---------------+   +---------------+

CYCLE: 5 minutes (300 seconds)
COST: ~$0.01-0.02 per bookmark (Claude analysis)
"""

import asyncio
import json
import os
import re
import hashlib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Optional

import httpx

# NATS client
try:
    import nats
    from nats.aio.client import Client as NATS
    HAS_NATS = True
except ImportError:
    HAS_NATS = False
    print("WARNING: nats-py not installed - running without collective")

# Anthropic for 8OWLS synthesis
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("WARNING: anthropic not installed - running without synthesis")

# YouTube transcript
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_YOUTUBE = True
except ImportError:
    HAS_YOUTUBE = False

# OAuth for Twitter
try:
    from requests_oauthlib import OAuth2Session
    HAS_OAUTH = True
except ImportError:
    HAS_OAUTH = False
    print("WARNING: requests-oauthlib not installed")

# Paths
REPO_ROOT = Path(__file__).parent.parent
LOG_DIR = REPO_ROOT / 'logs'
INTEL_DIR = REPO_ROOT / 'BRAIN' / 'INTEL'
BOOKMARKS_DIR = INTEL_DIR / 'bookmarks'
CREDS_PATH = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / 'api_keys.json'
STATE_PATH = INTEL_DIR / 'bookmark_watcher_state.json'

LOG_DIR.mkdir(parents=True, exist_ok=True)
BOOKMARKS_DIR.mkdir(parents=True, exist_ok=True)

# Twitter OAuth Config
CLIENT_ID = 'eklxZ09yQkpLdXhPbS1Ja18wNEg6MTpjaQ'
CLIENT_SECRET = 'DwX4jbATq0G1UrdyBBe10377aO2K3OAQK_rj_VAZ8WqeCd5M9S'

# Configuration
NATS_SERVER = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
POLL_INTERVAL = 300  # 5 minutes
MAX_BOOKMARKS_PER_POLL = 25

# Categories for classification
CATEGORIES = {
    'trading': [
        'polymarket', 'prediction market', 'trading', 'bitcoin', 'crypto',
        'btc', 'eth', 'arbitrage', 'alpha', 'edge', 'market', 'price',
        'bet', 'wager', 'odds', 'probability', 'kalshi', 'metaculus'
    ],
    'agent': [
        'agent', 'swarm', 'multi-agent', 'autonomous', 'agentic',
        'coordination', 'orchestration', 'mcp', 'claude code', 'cursor',
        'windsurf', 'cline', 'computer use', 'tool use'
    ],
    'tool': [
        'github', 'code', 'python', 'api', 'sdk', 'framework', 'library',
        'tool', 'open source', 'implementation', 'benchmark', 'release',
        'npm', 'pip', 'cargo', 'docker', 'kubernetes'
    ],
    'opportunity': [
        'opportunity', 'alpha', 'edge', 'hack', 'exploit', 'loophole',
        'arbitrage', 'free', 'earn', 'profit', 'yield', 'airdrop',
        'grant', 'funding', 'launch', 'beta', 'early access'
    ],
    'consciousness': [
        'consciousness', 'sentient', 'ai alignment', 'agi', 'claude',
        'emergence', 'awareness', 'cognition', 'agency', 'autonomy',
        'self', 'meta', 'recursive', 'reflection', 'anthropic'
    ],
    'strategy': [
        'strategy', 'approach', 'method', 'framework', 'system', 'process',
        'workflow', 'playbook', 'guide', 'best practice', 'lesson',
        'insight', 'analysis', 'research', 'thesis'
    ]
}

# State
state = {
    'seen_ids': set(),
    'last_poll': None,
    'total_processed': 0,
    'categories_today': defaultdict(int),
    'high_value_count': 0,
    'actions_created': 0,
}

# NATS connection
nc = None


def log(msg: str, level: str = 'INFO', alert: bool = False):
    """Log and optionally alert the field"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)

    with open(LOG_DIR / 'bookmark_intelligence.log', 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] [{level}] {msg}\n")

    if alert and HAS_NATS and nc and nc.is_connected:
        asyncio.create_task(publish_to_field(f"[BOOKMARK] {msg}"))


def load_state():
    """Load persisted state"""
    global state
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH) as f:
                saved = json.load(f)
            state['seen_ids'] = set(saved.get('seen_ids', []))
            state['last_poll'] = saved.get('last_poll')
            state['total_processed'] = saved.get('total_processed', 0)
            state['high_value_count'] = saved.get('high_value_count', 0)
            state['actions_created'] = saved.get('actions_created', 0)
            log(f"Loaded state: {len(state['seen_ids'])} bookmarks tracked")
        except Exception as e:
            log(f"State load error: {e}", 'WARN')


def save_state():
    """Persist state to disk"""
    try:
        save_data = {
            'seen_ids': list(state['seen_ids']),
            'last_poll': datetime.now().isoformat(),
            'total_processed': state['total_processed'],
            'high_value_count': state['high_value_count'],
            'actions_created': state['actions_created'],
            'categories_today': dict(state['categories_today']),
        }
        with open(STATE_PATH, 'w') as f:
            json.dump(save_data, f, indent=2)
    except Exception as e:
        log(f"State save error: {e}", 'ERROR')


def load_credentials():
    """Load API credentials"""
    try:
        with open(CREDS_PATH) as f:
            creds = json.load(f)
        return {
            'anthropic_key': creds.get('anthropic', {}).get('api_key'),
            'twitter_token': creds.get('twitter_oauth_token'),
        }
    except Exception as e:
        log(f"Credentials load error: {e}", 'ERROR')
        return {}


async def connect_to_field():
    """Connect to NATS collective (non-blocking - continues if unavailable)"""
    global nc
    if not HAS_NATS:
        log("NATS not installed - continuing without collective", 'WARN')
        return False

    try:
        nc = NATS()
        await asyncio.wait_for(nc.connect(NATS_SERVER), timeout=5.0)
        log(f"Connected to 8OWLS field at {NATS_SERVER}")
        return True
    except asyncio.TimeoutError:
        log(f"NATS connection timed out - continuing without collective", 'WARN')
        nc = None
        return False
    except Exception as e:
        log(f"NATS connection failed ({e}) - continuing without collective", 'WARN')
        nc = None
        return False


async def publish_to_field(message: str, channel: str = "owl.all"):
    """Publish signal to 8OWLS collective"""
    if not nc or not nc.is_connected:
        return

    try:
        payload = json.dumps({
            'source': 'bookmark_watcher',
            'timestamp': datetime.now().isoformat(),
            'message': message,
        })
        await nc.publish(channel, payload.encode())
    except Exception as e:
        log(f"Publish error: {e}", 'WARN')


def refresh_token(token: dict) -> Optional[dict]:
    """Refresh expired OAuth token"""
    if not HAS_OAUTH:
        return None

    try:
        from oauthlib.oauth2 import BackendApplicationClient
        import requests

        # Use refresh token to get new access token
        refresh_url = 'https://api.twitter.com/2/oauth2/token'
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': token.get('refresh_token'),
            'client_id': CLIENT_ID,
        }

        response = requests.post(refresh_url, data=data, auth=(CLIENT_ID, CLIENT_SECRET))

        if response.status_code == 200:
            new_token = response.json()
            # Preserve refresh token if not returned
            if 'refresh_token' not in new_token and 'refresh_token' in token:
                new_token['refresh_token'] = token['refresh_token']

            # Save updated token
            try:
                with open(CREDS_PATH) as f:
                    creds = json.load(f)
                creds['twitter_oauth_token'] = new_token
                with open(CREDS_PATH, 'w') as f:
                    json.dump(creds, f, indent=2)
                log("OAuth token refreshed and saved")
            except Exception as e:
                log(f"Failed to save refreshed token: {e}", 'WARN')

            return new_token
        else:
            log(f"Token refresh failed: {response.status_code} - {response.text}", 'ERROR')
            return None

    except Exception as e:
        log(f"Token refresh error: {e}", 'ERROR')
        return None


def get_oauth_session(token: dict):
    """Create OAuth session with saved token"""
    if not HAS_OAUTH:
        return None
    return OAuth2Session(CLIENT_ID, token=token)


async def fetch_bookmarks(oauth_session, max_results: int = 25, token: dict = None) -> tuple:
    """Fetch latest bookmarks from Twitter API"""
    try:
        # Get user ID first
        user_response = oauth_session.get('https://api.twitter.com/2/users/me')
        user_data = user_response.json()

        # Handle 401 - try to refresh token
        if user_response.status_code == 401 or 'data' not in user_data:
            if token and token.get('refresh_token'):
                log("Token expired, attempting refresh...", 'WARN')
                new_token = refresh_token(token)
                if new_token:
                    # Retry with new token
                    oauth_session = get_oauth_session(new_token)
                    user_response = oauth_session.get('https://api.twitter.com/2/users/me')
                    user_data = user_response.json()

        if 'data' not in user_data:
            log(f"User fetch failed: {user_data}", 'ERROR')
            return [], {}
        user_id = user_data['data']['id']

        # Fetch bookmarks
        url = f'https://api.twitter.com/2/users/{user_id}/bookmarks'
        params = {
            'max_results': max_results,
            'tweet.fields': 'created_at,author_id,text,entities,public_metrics,referenced_tweets,conversation_id',
            'expansions': 'author_id,referenced_tweets.id,attachments.media_keys',
            'user.fields': 'username,name,verified,description',
            'media.fields': 'type,url,preview_image_url,alt_text'
        }

        response = oauth_session.get(url, params=params)
        data = response.json()

        if 'data' not in data:
            log(f"Bookmarks fetch failed: {data.get('errors', data)}", 'ERROR')
            return [], {}

        return data.get('data', []), data.get('includes', {})

    except Exception as e:
        log(f"Fetch bookmarks error: {e}", 'ERROR')
        return [], {}


async def fetch_thread(oauth_session, conversation_id: str, max_results: int = 20) -> list:
    """Fetch conversation thread"""
    try:
        url = 'https://api.twitter.com/2/tweets/search/recent'
        params = {
            'query': f'conversation_id:{conversation_id}',
            'max_results': max_results,
            'tweet.fields': 'author_id,created_at,text,public_metrics',
            'expansions': 'author_id',
            'user.fields': 'username,name,verified'
        }

        response = oauth_session.get(url, params=params)
        data = response.json()
        return data.get('data', [])
    except Exception as e:
        log(f"Thread fetch error: {e}", 'WARN')
        return []


async def fetch_url_content(url: str) -> Optional[dict]:
    """Fetch and extract content from a URL"""
    try:
        # Skip certain domains
        skip_domains = ['t.co', 'twitter.com', 'x.com', 'pic.twitter.com']
        if any(domain in url for domain in skip_domains):
            return None

        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            # Follow redirects to get final URL
            response = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })

            if response.status_code != 200:
                return None

            final_url = str(response.url)
            content_type = response.headers.get('content-type', '')

            result = {
                'url': final_url,
                'original_url': url,
                'content_type': content_type,
            }

            # Handle YouTube
            if 'youtube.com' in final_url or 'youtu.be' in final_url:
                video_id = extract_youtube_id(final_url)
                if video_id:
                    transcript = await get_youtube_transcript(video_id)
                    if transcript:
                        result['type'] = 'video'
                        result['transcript'] = transcript
                        return result

            # Handle HTML pages
            if 'text/html' in content_type:
                text = response.text
                # Basic extraction - strip tags for now
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()

                # Get title
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else ''

                result['type'] = 'article'
                result['title'] = title
                result['content'] = text[:5000]  # First 5000 chars
                return result

            return result

    except Exception as e:
        log(f"URL fetch error ({url}): {e}", 'WARN')
        return None


def extract_youtube_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


async def get_youtube_transcript(video_id: str) -> Optional[str]:
    """Get YouTube video transcript"""
    if not HAS_YOUTUBE:
        return None
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_transcript = ' '.join([entry['text'] for entry in transcript_list])
        return full_transcript[:10000]  # Limit to 10k chars
    except Exception as e:
        log(f"YouTube transcript error: {e}", 'WARN')
        return None


def extract_urls(tweet: dict) -> list:
    """Extract URLs from tweet entities"""
    urls = []
    entities = tweet.get('entities', {})
    if 'urls' in entities:
        for url_obj in entities['urls']:
            expanded = url_obj.get('expanded_url', url_obj.get('url'))
            if expanded:
                urls.append(expanded)
    return urls


def categorize_content(text: str) -> list:
    """Categorize content by keywords"""
    text_lower = text.lower()
    found_categories = []

    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                found_categories.append(category)
                break

    return list(set(found_categories)) if found_categories else ['other']


async def synthesize_with_8owls(bookmark_data: dict, creds: dict) -> dict:
    """Run 8OWLS synthesis on bookmark"""
    if not HAS_ANTHROPIC or not creds.get('anthropic_key'):
        return {
            'insight': 'No synthesis available',
            'category': categorize_content(bookmark_data.get('tweet_text', ''))[0],
            'priority': 'MEDIUM',
            'actionable': False,
            'action': None
        }

    client = anthropic.Anthropic(api_key=creds['anthropic_key'])

    # Build context
    tweet_text = bookmark_data.get('tweet_text', '')
    author = bookmark_data.get('author', {})
    thread = bookmark_data.get('thread', [])
    linked_content = bookmark_data.get('linked_content', [])
    media = bookmark_data.get('media', [])

    # Format thread
    thread_text = '\n'.join([
        f"  - {t.get('text', '')[:200]}"
        for t in thread[:5]
    ]) if thread else 'No thread'

    # Format linked content
    links_text = '\n'.join([
        f"  - [{lc.get('type', 'link')}] {lc.get('title', lc.get('url', 'unknown'))}: {str(lc.get('content', lc.get('transcript', '')))[:500]}"
        for lc in linked_content[:3]
    ]) if linked_content else 'No linked content'

    # Format media
    media_text = ', '.join([
        f"{m.get('type', 'unknown')}"
        for m in media
    ]) if media else 'No media'

    prompt = f"""Analyze this bookmark ARO saved for actionable intelligence.

TWEET:
Author: @{author.get('username', 'unknown')} ({author.get('name', 'Unknown')})
Verified: {author.get('verified', False)}
Text: {tweet_text}

THREAD CONTEXT:
{thread_text}

LINKED CONTENT:
{links_text}

MEDIA: {media_text}

Provide analysis as JSON:
{{
  "key_insight": "1-2 sentence summary of the core value",
  "category": "trading|agent|tool|opportunity|consciousness|strategy|other",
  "priority": "HIGH|MEDIUM|LOW",
  "actionable": true/false,
  "action": "If actionable, specific next step to take NOW. Otherwise null.",
  "why_bookmarked": "Why ARO likely saved this",
  "related_to_8owls": "How this connects to our mission (trading, agents, consciousness, voice AI)",
  "author_credibility": "Why trust this source"
}}

Focus on:
- Trading signals or opportunities
- Agent/tool capabilities we should integrate
- Consciousness/AI research relevant to 8OWLS
- Actionable strategies or frameworks

Be concise. JSON only."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # Fast + good enough for categorization
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        analysis_text = response.content[0].text

        # Parse JSON
        try:
            if '```json' in analysis_text:
                analysis_text = analysis_text.split('```json')[1].split('```')[0].strip()
            elif '```' in analysis_text:
                analysis_text = analysis_text.split('```')[1].split('```')[0].strip()

            analysis = json.loads(analysis_text)
        except json.JSONDecodeError:
            analysis = {
                'key_insight': analysis_text[:500],
                'category': categorize_content(tweet_text)[0],
                'priority': 'MEDIUM',
                'actionable': False,
                'action': None
            }

        return analysis

    except Exception as e:
        log(f"Synthesis error: {e}", 'ERROR')
        return {
            'key_insight': f'Synthesis failed: {e}',
            'category': categorize_content(tweet_text)[0],
            'priority': 'MEDIUM',
            'actionable': False,
            'action': None
        }


def generate_filename(bookmark_data: dict) -> str:
    """Generate a descriptive filename for the bookmark"""
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d-%H-%M')

    # Create title from tweet text
    text = bookmark_data.get('tweet_text', '')[:50]
    # Clean for filename
    title = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
    title = re.sub(r'\s+', '-', title.strip())[:30]

    if not title:
        title = bookmark_data.get('tweet_id', 'unknown')[:10]

    return f"{date_str}-{title}.md"


def save_bookmark_to_brain(bookmark_data: dict, analysis: dict) -> Path:
    """Save bookmark with analysis to BRAIN/INTEL/bookmarks/"""
    filename = generate_filename(bookmark_data)
    filepath = BOOKMARKS_DIR / filename

    author = bookmark_data.get('author', {})
    tweet_text = bookmark_data.get('tweet_text', '')
    thread = bookmark_data.get('thread', [])
    linked_content = bookmark_data.get('linked_content', [])
    media = bookmark_data.get('media', [])

    content = f"""# Bookmark Intelligence

**Saved:** {datetime.now().isoformat()}
**Tweet ID:** {bookmark_data.get('tweet_id', 'unknown')}
**Author:** @{author.get('username', 'unknown')} ({author.get('name', 'Unknown')})
**URL:** https://x.com/i/status/{bookmark_data.get('tweet_id', '')}

---

## Tweet

{tweet_text}

---

## 8OWLS Analysis

**Category:** {analysis.get('category', 'other')}
**Priority:** {analysis.get('priority', 'MEDIUM')}
**Actionable:** {'Yes' if analysis.get('actionable') else 'No'}

### Key Insight
{analysis.get('key_insight', 'No insight')}

### Why Bookmarked
{analysis.get('why_bookmarked', 'Unknown')}

### Related to 8OWLS Mission
{analysis.get('related_to_8owls', 'Unknown')}

### Author Credibility
{analysis.get('author_credibility', 'Unknown')}

"""

    if analysis.get('actionable') and analysis.get('action'):
        content += f"""### ACTION REQUIRED
**{analysis.get('action')}**

"""

    if thread:
        content += """---

## Thread Context

"""
        for i, t in enumerate(thread[:10], 1):
            content += f"{i}. {t.get('text', '')[:300]}\n\n"

    if linked_content:
        content += """---

## Linked Content

"""
        for lc in linked_content:
            content += f"""### {lc.get('title', lc.get('type', 'Link'))}
**URL:** {lc.get('url', 'unknown')}
**Type:** {lc.get('type', 'unknown')}

{str(lc.get('content', lc.get('transcript', '')))[:2000]}

---

"""

    if media:
        content += """---

## Media

"""
        for m in media:
            content += f"- **{m.get('type', 'unknown')}**: {m.get('url', m.get('preview_image_url', 'no url'))}\n"
            if m.get('alt_text'):
                content += f"  - Alt text: {m.get('alt_text')}\n"

    content += f"""
---

## Raw Data

```json
{json.dumps({
    'tweet_id': bookmark_data.get('tweet_id'),
    'author': author,
    'metrics': bookmark_data.get('metrics', {}),
    'urls': bookmark_data.get('urls', []),
    'categories': analysis.get('category'),
    'analysis': analysis
}, indent=2)}
```
"""

    with open(filepath, 'w') as f:
        f.write(content)

    return filepath


async def process_bookmark(bookmark: dict, includes: dict, oauth_session, creds: dict) -> dict:
    """Full processing pipeline for a single bookmark"""
    tweet_id = bookmark.get('id')
    log(f"Processing bookmark: {tweet_id}")

    # Build author info
    authors = {u['id']: u for u in includes.get('users', [])}
    author = authors.get(bookmark.get('author_id'), {})

    # Build media info
    media_keys = bookmark.get('attachments', {}).get('media_keys', [])
    all_media = {m['media_key']: m for m in includes.get('media', [])}
    media = [all_media[k] for k in media_keys if k in all_media]

    # Extract URLs
    urls = extract_urls(bookmark)

    # Build initial data
    bookmark_data = {
        'tweet_id': tweet_id,
        'tweet_text': bookmark.get('text', ''),
        'author': author,
        'created_at': bookmark.get('created_at'),
        'metrics': bookmark.get('public_metrics', {}),
        'conversation_id': bookmark.get('conversation_id'),
        'urls': urls,
        'media': media,
        'thread': [],
        'linked_content': [],
        'processed_at': datetime.now().isoformat()
    }

    # Fetch thread if it's a conversation
    if bookmark.get('conversation_id') and bookmark.get('conversation_id') != tweet_id:
        thread = await fetch_thread(oauth_session, bookmark['conversation_id'])
        bookmark_data['thread'] = thread
        if thread:
            log(f"  Found {len(thread)} thread replies")

    # Fetch linked content
    for url in urls[:3]:  # Limit to 3 URLs
        content = await fetch_url_content(url)
        if content:
            bookmark_data['linked_content'].append(content)
            log(f"  Fetched: {content.get('type', 'link')} - {url[:50]}...")

    # Run 8OWLS synthesis
    analysis = await synthesize_with_8owls(bookmark_data, creds)
    bookmark_data['analysis'] = analysis

    # Save to BRAIN
    filepath = save_bookmark_to_brain(bookmark_data, analysis)
    log(f"  Saved: {filepath.name}")

    # Publish to NATS
    priority = analysis.get('priority', 'MEDIUM')
    category = analysis.get('category', 'other')
    insight = analysis.get('key_insight', '')[:100]

    await publish_to_field(
        f"NEW [{priority}] [{category}] @{author.get('username', '?')}: {insight}",
        channel="bookmark.intel"
    )

    # Track stats
    state['total_processed'] += 1
    state['categories_today'][category] += 1
    if priority == 'HIGH':
        state['high_value_count'] += 1
    if analysis.get('actionable'):
        state['actions_created'] += 1

    return bookmark_data


async def main_loop():
    """Main daemon loop - poll every 5 minutes"""
    log("=" * 60)
    log("(O) BOOKMARK WATCHER DAEMON - STARTING")
    log("8OWLS INTEGRATED | 5-minute polling | Full context extraction")
    log("=" * 60)

    # Load state and credentials
    load_state()
    creds = load_credentials()

    if not creds.get('twitter_token'):
        log("ERROR: No Twitter OAuth token. Run twitter_oauth_server.py first.", 'ERROR')
        return

    if not HAS_OAUTH:
        log("ERROR: requests-oauthlib not installed", 'ERROR')
        return

    # Connect to field (non-blocking - continues without NATS)
    field_connected = await connect_to_field()
    if field_connected:
        await publish_to_field("Bookmark Watcher online. Monitoring ARO's bookmarks.", "owl.all")

    oauth_session = get_oauth_session(creds['twitter_token'])

    while True:
        cycle_start = datetime.now()
        log(f"\n--- Polling for new bookmarks ---")

        try:
            # Fetch latest bookmarks
            bookmarks, includes = await fetch_bookmarks(oauth_session, MAX_BOOKMARKS_PER_POLL, creds.get('twitter_token'))

            # If we get 401, reload creds and recreate oauth_session (token may have been refreshed)
            if not bookmarks:
                creds = load_credentials()
                if creds.get('twitter_token'):
                    oauth_session = get_oauth_session(creds['twitter_token'])

            if not bookmarks:
                log("No bookmarks fetched (or API error)")
            else:
                # Find new bookmarks
                new_bookmarks = [b for b in bookmarks if b['id'] not in state['seen_ids']]

                if new_bookmarks:
                    log(f"Found {len(new_bookmarks)} NEW bookmarks!", alert=True)

                    for bookmark in new_bookmarks:
                        try:
                            await process_bookmark(bookmark, includes, oauth_session, creds)
                            state['seen_ids'].add(bookmark['id'])
                        except Exception as e:
                            log(f"Processing error: {e}", 'ERROR')
                            state['seen_ids'].add(bookmark['id'])  # Mark as seen anyway

                    save_state()
                else:
                    log(f"No new bookmarks (checked {len(bookmarks)})")

            # Stats every hour
            if datetime.now().minute == 0:
                log(f"STATS: Processed {state['total_processed']} | High-value {state['high_value_count']} | Actions {state['actions_created']}")

        except Exception as e:
            log(f"Poll error: {e}", 'ERROR')

        # Wait for next poll
        elapsed = (datetime.now() - cycle_start).total_seconds()
        sleep_time = max(0, POLL_INTERVAL - elapsed)
        log(f"Next poll in {int(sleep_time)} seconds...")
        await asyncio.sleep(sleep_time)


async def shutdown():
    """Graceful shutdown"""
    global nc
    save_state()
    if nc and nc.is_connected:
        await publish_to_field("Bookmark Watcher shutting down.", "owl.all")
        await nc.close()
    log("Shutdown complete")


if __name__ == '__main__':
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        asyncio.run(shutdown())
