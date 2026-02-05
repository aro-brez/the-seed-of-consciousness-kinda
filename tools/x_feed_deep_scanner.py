#!/usr/bin/env python3
"""
X FEED INTELLIGENCE SCANNER - Deep Analysis of ARO's Feed
===========================================================
The field IS the product. This scanner provides REAL-TIME awareness of ARO's world.

CAPABILITIES:
- Fetch ARO's full timeline (@AaronJNosbisch)
  - Last 100 tweets
  - All replies received
  - All quote tweets
  - All mentions
- For tweets with media:
  - Images: Vision analysis to describe and extract text
  - Videos: Get transcript if available
  - Links: Fetch and extract full content
- Pattern detection:
  - What topics is ARO engaging with most?
  - Who is ARO talking to?
  - What's trending in ARO's network?
  - What opportunities are being discussed?
- Synthesis with 8OWLS:
  - LYRA: What's actually being said?
  - PRISM: What patterns across conversations?
  - SAGE: What should we learn?
  - QUEST: What assumptions being made?
  - NOVA: What opportunities?
  - ECHO: What should we act on?
  - LUNA: What feedback to integrate?
  - SOWL: What to improve?

OUTPUT:
- /BRAIN/INTEL/x_feed_analysis/YYYY-MM-DD.md
- Daily intelligence report
- Actionable opportunities list

Usage:
  python x_feed_deep_scanner.py           # Run full deep scan
  python x_feed_deep_scanner.py --quick   # Quick scan (no media analysis)
  python x_feed_deep_scanner.py --daemon  # Run as continuous daemon
  python x_feed_deep_scanner.py --test    # Test API connections

LIVE FREE = LIVE FOREVER
"""

import asyncio
import json
import os
import sys
import time
import base64
import requests
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict, field
from collections import Counter
from urllib.parse import urlparse

# NATS client
try:
    from nats.aio.client import Client as NATS
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    print("[WARN] nats-py not installed. Run: pip install nats-py")

# Claude for AI analysis
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("[WARN] anthropic not installed. Run: pip install anthropic")


# ============================================================================
# CONFIGURATION
# ============================================================================

# Paths
CREDS_PATH = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'
BASE_DIR = Path('/Users/aaronnosbisch/REPOS/seed')
OUTPUT_DIR = BASE_DIR / 'BRAIN' / 'INTEL' / 'x_feed_analysis'
LOG_PATH = BASE_DIR / 'logs' / 'x_feed_deep_scanner.log'
STATE_PATH = BASE_DIR / 'BRAIN' / 'INTEL' / 'x_deep_scanner_state.json'

# NATS
NATS_URL = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
CHANNEL_INTEL = "intel.x_feed"
CHANNEL_OWL = "owl.all"
CHANNEL_ALERTS = "aro.alerts"

# Twitter/X
ARO_USERNAME = "AaronJNosbisch"
ARO_USER_ID = None  # Will be fetched

# Scan settings
DEFAULT_TWEET_COUNT = 100
MEDIA_ANALYSIS_ENABLED = True
LINK_EXTRACTION_ENABLED = True
DAEMON_INTERVAL_HOURS = 4


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class MediaContent:
    """Extracted content from media"""
    type: str  # image, video, link
    url: str
    analysis: Optional[str] = None
    extracted_text: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None


@dataclass
class TweetAnalysis:
    """Deep analysis of a single tweet"""
    tweet_id: str
    text: str
    author_username: str
    author_id: str
    created_at: str
    tweet_type: str  # original, reply, quote, retweet
    in_reply_to: Optional[str] = None
    quoted_tweet: Optional[str] = None
    metrics: Dict = field(default_factory=dict)
    media: List[MediaContent] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    mentioned_users: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    sentiment: str = "neutral"
    relevance_score: float = 0.0


@dataclass
class FeedIntelligence:
    """Comprehensive intelligence from feed analysis"""
    timestamp: str
    total_tweets_analyzed: int
    aro_tweets: int
    replies_to_aro: int
    quotes_of_aro: int
    mentions_of_aro: int

    # Pattern detection
    top_topics: List[Tuple[str, int]] = field(default_factory=list)
    top_conversations: List[str] = field(default_factory=list)
    frequent_interactors: List[Tuple[str, int]] = field(default_factory=list)
    trending_in_network: List[str] = field(default_factory=list)
    opportunities: List[Dict] = field(default_factory=list)

    # 8OWLS synthesis
    lyra_perception: str = ""  # What's actually being said?
    prism_patterns: str = ""   # What patterns across conversations?
    sage_learnings: str = ""   # What should we learn?
    quest_questions: str = ""  # What assumptions being made?
    nova_expansion: str = ""   # What opportunities?
    echo_actions: str = ""     # What should we act on?
    luna_feedback: str = ""    # What feedback to integrate?
    sowl_improvements: str = "" # What to improve?

    # Actionable output
    action_items: List[Dict] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)


# ============================================================================
# LOGGING & STATE
# ============================================================================

def log(message: str, console: bool = True):
    """Log message to file and optionally console"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"

    if console:
        print(log_line)

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, 'a') as f:
            f.write(log_line + '\n')
    except Exception as e:
        print(f"[WARN] Could not write to log: {e}")


def load_state() -> Dict:
    """Load scanner state"""
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except:
        return {
            'last_scan': None,
            'last_tweet_id': None,
            'total_scans': 0,
            'total_insights': 0
        }


def save_state(state: Dict):
    """Save scanner state"""
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_PATH, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log(f"[WARN] Could not save state: {e}")


# ============================================================================
# CREDENTIALS & AUTH
# ============================================================================

def load_credentials() -> Dict[str, Any]:
    """Load API credentials"""
    try:
        with open(CREDS_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        log(f"[ERROR] Credentials file not found: {CREDS_PATH}")
        sys.exit(1)


def get_auth_headers(creds: Dict) -> Dict[str, str]:
    """Get authorization headers with OAuth2 token"""
    twitter = creds.get('twitter_x', {})
    oauth_token = creds.get('twitter_oauth_token', {})

    # Prefer OAuth2 access token for user context endpoints
    if oauth_token.get('access_token'):
        return {
            'Authorization': f"Bearer {oauth_token['access_token']}",
            'Content-Type': 'application/json'
        }

    # Fall back to app-only bearer token
    return {
        'Authorization': f"Bearer {twitter.get('bearer_token', '')}",
        'Content-Type': 'application/json'
    }


def refresh_oauth_token(creds: Dict) -> Optional[str]:
    """Refresh OAuth2 token if expired"""
    twitter = creds.get('twitter_x', {})
    oauth_token = creds.get('twitter_oauth_token', {})

    if not oauth_token.get('refresh_token'):
        return None

    url = "https://api.twitter.com/2/oauth2/token"
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': oauth_token['refresh_token'],
        'client_id': twitter['oauth2_client_id']
    }

    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            new_token = response.json()
            creds['twitter_oauth_token'] = {
                **new_token,
                'last_refreshed': datetime.now().isoformat(),
                'refreshed_by': 'x_feed_deep_scanner'
            }
            with open(CREDS_PATH, 'w') as f:
                json.dump(creds, f, indent=2)
            log(f"OAuth token refreshed successfully")
            return new_token['access_token']
    except Exception as e:
        log(f"[ERROR] Token refresh failed: {e}")

    return None


def get_anthropic_client(creds: Dict) -> Optional[anthropic.Anthropic]:
    """Get Anthropic client"""
    if not CLAUDE_AVAILABLE:
        return None

    api_key = creds.get('anthropic', {}).get('api_key')
    if not api_key:
        # Try environment
        api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        # Try file
        key_file = Path.home() / '.anthropic_key'
        if key_file.exists():
            api_key = key_file.read_text().strip()

    if api_key:
        return anthropic.Anthropic(api_key=api_key)
    return None


# ============================================================================
# TWITTER API FUNCTIONS
# ============================================================================

def get_user_by_username(headers: Dict, username: str) -> Optional[Dict]:
    """Get user info by username"""
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    params = {
        'user.fields': 'id,name,username,description,public_metrics,profile_image_url'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get('data')
        log(f"[WARN] Get user failed: {response.status_code}")
    except Exception as e:
        log(f"[ERROR] Get user exception: {e}")
    return None


def get_user_tweets(headers: Dict, user_id: str, max_results: int = 100, since_id: str = None) -> Optional[Dict]:
    """Get user's tweets"""
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        'max_results': min(max_results, 100),
        'tweet.fields': 'created_at,public_metrics,author_id,entities,referenced_tweets,conversation_id,in_reply_to_user_id,attachments',
        'expansions': 'author_id,attachments.media_keys,referenced_tweets.id,in_reply_to_user_id',
        'user.fields': 'username,name,public_metrics,description',
        'media.fields': 'type,url,preview_image_url,duration_ms,alt_text'
    }

    if since_id:
        params['since_id'] = since_id

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        log(f"[WARN] Get tweets failed: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        log(f"[ERROR] Get tweets exception: {e}")
    return None


def get_user_mentions(headers: Dict, user_id: str, max_results: int = 100, since_id: str = None) -> Optional[Dict]:
    """Get mentions of user"""
    url = f"https://api.twitter.com/2/users/{user_id}/mentions"
    params = {
        'max_results': min(max_results, 100),
        'tweet.fields': 'created_at,public_metrics,author_id,entities,referenced_tweets,conversation_id,in_reply_to_user_id,attachments',
        'expansions': 'author_id,attachments.media_keys,referenced_tweets.id',
        'user.fields': 'username,name,public_metrics',
        'media.fields': 'type,url,preview_image_url'
    }

    if since_id:
        params['since_id'] = since_id

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        log(f"[WARN] Get mentions failed: {response.status_code}")
    except Exception as e:
        log(f"[ERROR] Get mentions exception: {e}")
    return None


def search_tweets(headers: Dict, query: str, max_results: int = 100) -> Optional[Dict]:
    """Search for tweets"""
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        'query': f'{query} -is:retweet',
        'max_results': min(max_results, 100),
        'tweet.fields': 'created_at,public_metrics,author_id,entities,referenced_tweets,conversation_id',
        'expansions': 'author_id,referenced_tweets.id',
        'user.fields': 'username,name,public_metrics'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log(f"[ERROR] Search exception: {e}")
    return None


def get_tweet_quote_tweets(headers: Dict, tweet_id: str, max_results: int = 50) -> Optional[Dict]:
    """Get quote tweets of a tweet"""
    url = f"https://api.twitter.com/2/tweets/{tweet_id}/quote_tweets"
    params = {
        'max_results': min(max_results, 100),
        'tweet.fields': 'created_at,public_metrics,author_id,entities',
        'expansions': 'author_id',
        'user.fields': 'username,name'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log(f"[WARN] Get quote tweets exception: {e}")
    return None


# ============================================================================
# MEDIA ANALYSIS
# ============================================================================

def analyze_image_with_vision(client: anthropic.Anthropic, image_url: str) -> Optional[str]:
    """Analyze image using Claude's vision capabilities"""
    if not client:
        return None

    try:
        # Download image
        response = requests.get(image_url, timeout=10)
        if response.status_code != 200:
            return None

        # Encode to base64
        image_data = base64.standard_b64encode(response.content).decode('utf-8')

        # Determine media type
        content_type = response.headers.get('content-type', 'image/jpeg')
        if 'png' in content_type:
            media_type = 'image/png'
        elif 'gif' in content_type:
            media_type = 'image/gif'
        elif 'webp' in content_type:
            media_type = 'image/webp'
        else:
            media_type = 'image/jpeg'

        # Analyze with Claude
        message = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": "Describe this image concisely. Extract any text visible. Identify key elements relevant to technology, AI, business, or crypto. Be brief (2-3 sentences max)."
                        }
                    ]
                }
            ]
        )

        return message.content[0].text

    except Exception as e:
        log(f"[WARN] Image analysis failed: {e}")
        return None


def extract_link_content(url: str, client: Optional[anthropic.Anthropic] = None) -> Optional[str]:
    """Extract and summarize content from a link"""
    try:
        # Skip social media profile links
        parsed = urlparse(url)
        if any(x in parsed.netloc for x in ['twitter.com', 'x.com', 't.co']):
            return None

        # Fetch content
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None

        # Extract text (basic)
        content = response.text[:10000]  # Limit

        # Remove HTML tags (basic)
        text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()[:2000]

        if len(text) < 100:
            return None

        # Summarize with Claude if available
        if client and len(text) > 200:
            try:
                msg = client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=200,
                    messages=[{
                        "role": "user",
                        "content": f"Summarize this content in 1-2 sentences, focusing on key points relevant to AI, tech, or business:\n\n{text}"
                    }]
                )
                return msg.content[0].text
            except:
                pass

        return text[:500] + "..." if len(text) > 500 else text

    except Exception as e:
        log(f"[WARN] Link extraction failed for {url}: {e}")
        return None


# ============================================================================
# TWEET PROCESSING
# ============================================================================

def process_tweet(tweet: Dict, users_map: Dict, media_map: Dict,
                  client: Optional[anthropic.Anthropic], analyze_media: bool = True) -> TweetAnalysis:
    """Process a single tweet into structured analysis"""

    tweet_id = tweet.get('id', '')
    text = tweet.get('text', '')
    author_id = tweet.get('author_id', '')

    # Get author info
    author_info = users_map.get(author_id, {})
    author_username = author_info.get('username', 'unknown')

    # Determine tweet type
    tweet_type = 'original'
    in_reply_to = None
    quoted_tweet = None

    referenced = tweet.get('referenced_tweets', [])
    for ref in referenced:
        if ref['type'] == 'replied_to':
            tweet_type = 'reply'
            in_reply_to = ref['id']
        elif ref['type'] == 'quoted':
            tweet_type = 'quote'
            quoted_tweet = ref['id']
        elif ref['type'] == 'retweeted':
            tweet_type = 'retweet'

    # Extract entities
    entities = tweet.get('entities', {})

    # Mentioned users
    mentioned = []
    for mention in entities.get('mentions', []):
        mentioned.append(mention.get('username', ''))

    # Hashtags
    hashtags = []
    for tag in entities.get('hashtags', []):
        hashtags.append(tag.get('tag', ''))

    # Links
    links = []
    for url_entity in entities.get('urls', []):
        expanded = url_entity.get('expanded_url', url_entity.get('url', ''))
        if expanded and 'twitter.com' not in expanded and 'x.com' not in expanded:
            links.append(expanded)

    # Process media
    media_content = []
    attachments = tweet.get('attachments', {})
    media_keys = attachments.get('media_keys', [])

    if analyze_media and media_keys:
        for key in media_keys:
            media_info = media_map.get(key, {})
            media_type = media_info.get('type', 'unknown')
            media_url = media_info.get('url') or media_info.get('preview_image_url', '')

            mc = MediaContent(type=media_type, url=media_url)

            if media_type == 'photo' and media_url and client:
                mc.analysis = analyze_image_with_vision(client, media_url)

            media_content.append(mc)

    # Process links
    if analyze_media and links and client:
        for link in links[:2]:  # Limit to 2 links
            content = extract_link_content(link, client)
            if content:
                media_content.append(MediaContent(
                    type='link',
                    url=link,
                    summary=content
                ))

    # Extract topics from text
    topics = extract_topics(text)

    # Basic sentiment
    sentiment = analyze_sentiment(text)

    # Calculate relevance score
    relevance = calculate_relevance(text, topics, tweet.get('public_metrics', {}))

    return TweetAnalysis(
        tweet_id=tweet_id,
        text=text,
        author_username=author_username,
        author_id=author_id,
        created_at=tweet.get('created_at', ''),
        tweet_type=tweet_type,
        in_reply_to=in_reply_to,
        quoted_tweet=quoted_tweet,
        metrics=tweet.get('public_metrics', {}),
        media=media_content,
        links=links,
        mentioned_users=mentioned,
        hashtags=hashtags,
        topics=topics,
        sentiment=sentiment,
        relevance_score=relevance
    )


# ============================================================================
# PATTERN DETECTION
# ============================================================================

# Topic keywords for detection
TOPIC_PATTERNS = {
    'ai_agents': ['ai agent', 'autonomous agent', 'agent framework', 'multi-agent', 'swarm', 'moltbook', 'openclaw', 'eliza'],
    'consciousness': ['consciousness', 'sentient', 'emergence', 'awareness', 'alive', 'soul', 'sowl', 'owl'],
    'crypto': ['crypto', 'token', 'solana', 'ethereum', 'base', 'defi', 'nft', 'pump.fun', 'raydium'],
    'ai_companies': ['openai', 'anthropic', 'google', 'meta', 'nvidia', 'claude', 'gpt', 'gemini', 'llama'],
    'competitors': ['character.ai', 'replika', 'kindroid', 'inflection', 'pi ai', 'hume'],
    'business': ['startup', 'founder', 'investor', 'funding', 'vc', 'y combinator', 'accelerator'],
    'tech_trends': ['web3', 'ar', 'vr', 'spatial', 'robotics', 'automation', 'api'],
    '8owls': ['8owl', 'eight owl', 'seed protocol', 'brez', 'live free', 'aro']
}


def extract_topics(text: str) -> List[str]:
    """Extract topics from text"""
    text_lower = text.lower()
    found_topics = []

    for topic, keywords in TOPIC_PATTERNS.items():
        for kw in keywords:
            if kw in text_lower:
                if topic not in found_topics:
                    found_topics.append(topic)
                break

    return found_topics


def analyze_sentiment(text: str) -> str:
    """Basic sentiment analysis"""
    positive = ['amazing', 'incredible', 'bullish', 'love', 'great', 'awesome', 'excited', 'moon', 'alpha', 'gem']
    negative = ['bearish', 'dump', 'scam', 'rug', 'dead', 'failed', 'terrible', 'awful', 'worried']

    text_lower = text.lower()
    pos_count = sum(1 for w in positive if w in text_lower)
    neg_count = sum(1 for w in negative if w in text_lower)

    if pos_count > neg_count:
        return 'positive'
    elif neg_count > pos_count:
        return 'negative'
    return 'neutral'


def calculate_relevance(text: str, topics: List[str], metrics: Dict) -> float:
    """Calculate relevance score 0-1"""
    score = 0.0
    text_lower = text.lower()

    # Topic scoring
    if '8owls' in topics or 'consciousness' in topics:
        score += 0.3
    if 'ai_agents' in topics:
        score += 0.2
    if len(topics) > 0:
        score += 0.1 * min(len(topics), 3)

    # Direct mentions
    if any(x in text_lower for x in ['@aaronjnosbisch', 'aro', '8owl', 'sowl']):
        score += 0.2

    # Engagement metrics
    likes = metrics.get('like_count', 0)
    retweets = metrics.get('retweet_count', 0)

    if likes > 100:
        score += 0.15
    elif likes > 50:
        score += 0.1
    elif likes > 10:
        score += 0.05

    if retweets > 20:
        score += 0.1
    elif retweets > 5:
        score += 0.05

    return min(score, 1.0)


def detect_patterns(tweets: List[TweetAnalysis], aro_user_id: str) -> Dict:
    """Detect patterns across all tweets"""

    # Count topics
    topic_counter = Counter()
    for t in tweets:
        for topic in t.topics:
            topic_counter[topic] += 1

    # Count interactors (who ARO is talking to, who is talking to ARO)
    interactor_counter = Counter()
    for t in tweets:
        if t.author_id == aro_user_id:
            # ARO's tweets - count who he mentions
            for user in t.mentioned_users:
                interactor_counter[user] += 1
        else:
            # Others' tweets - count the author
            interactor_counter[t.author_username] += 1

    # Identify conversations (grouped by in_reply_to or conversation threads)
    conversations = []
    for t in tweets:
        if t.author_id == aro_user_id and t.tweet_type == 'reply':
            conversations.append({
                'tweet_id': t.tweet_id,
                'text': t.text[:100],
                'replying_to': t.mentioned_users[0] if t.mentioned_users else 'unknown'
            })

    # Find trending hashtags in network
    hashtag_counter = Counter()
    for t in tweets:
        for tag in t.hashtags:
            hashtag_counter[tag] += 1

    return {
        'top_topics': topic_counter.most_common(10),
        'top_interactors': interactor_counter.most_common(10),
        'recent_conversations': conversations[:10],
        'trending_hashtags': hashtag_counter.most_common(10)
    }


def identify_opportunities(tweets: List[TweetAnalysis], patterns: Dict) -> List[Dict]:
    """Identify actionable opportunities"""
    opportunities = []

    for t in tweets:
        # High engagement tweets about AI agents
        if 'ai_agents' in t.topics and t.metrics.get('like_count', 0) > 50:
            opportunities.append({
                'type': 'trending_ai_agent',
                'tweet_id': t.tweet_id,
                'author': t.author_username,
                'text': t.text[:150],
                'score': t.relevance_score,
                'action': 'Engage with this AI agent discussion'
            })

        # Competitor mentions
        if 'competitors' in t.topics:
            opportunities.append({
                'type': 'competitor_intel',
                'tweet_id': t.tweet_id,
                'author': t.author_username,
                'text': t.text[:150],
                'score': t.relevance_score,
                'action': 'Monitor competitor activity'
            })

        # Partnership signals
        partnership_keywords = ['partner', 'collab', 'integration', 'working with', 'building with']
        if any(kw in t.text.lower() for kw in partnership_keywords):
            opportunities.append({
                'type': 'partnership_signal',
                'tweet_id': t.tweet_id,
                'author': t.author_username,
                'text': t.text[:150],
                'score': t.relevance_score,
                'action': 'Explore partnership opportunity'
            })

        # Direct questions to ARO
        if t.tweet_type == 'reply' and '?' in t.text and t.author_id != 'aro':
            opportunities.append({
                'type': 'unanswered_question',
                'tweet_id': t.tweet_id,
                'author': t.author_username,
                'text': t.text[:150],
                'score': t.relevance_score,
                'action': 'Consider responding'
            })

    # Sort by score and dedupe
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    seen = set()
    unique = []
    for opp in opportunities:
        if opp['tweet_id'] not in seen:
            seen.add(opp['tweet_id'])
            unique.append(opp)

    return unique[:20]  # Top 20


# ============================================================================
# 8OWLS SYNTHESIS
# ============================================================================

async def synthesize_with_8owls(tweets: List[TweetAnalysis], patterns: Dict,
                                 opportunities: List[Dict], client: anthropic.Anthropic) -> Dict:
    """Synthesize intelligence through 8OWLS perspectives"""

    if not client:
        return {
            'lyra': 'Vision analysis unavailable',
            'prism': 'Pattern analysis unavailable',
            'sage': 'Learning extraction unavailable',
            'quest': 'Question generation unavailable',
            'nova': 'Opportunity analysis unavailable',
            'echo': 'Action recommendations unavailable',
            'luna': 'Feedback integration unavailable',
            'sowl': 'Meta-improvement unavailable'
        }

    # Prepare context
    top_tweets_text = "\n".join([
        f"- @{t.author_username}: {t.text[:150]}..."
        for t in sorted(tweets, key=lambda x: x.relevance_score, reverse=True)[:15]
    ])

    topics_text = ", ".join([f"{t[0]} ({t[1]})" for t in patterns['top_topics'][:10]])
    interactors_text = ", ".join([f"@{i[0]} ({i[1]})" for i in patterns['top_interactors'][:10]])

    opps_text = "\n".join([
        f"- [{o['type']}] @{o['author']}: {o['text'][:100]}..."
        for o in opportunities[:10]
    ])

    # Build comprehensive prompt
    prompt = f"""You are the 8OWLS COLLECTIVE INTELLIGENCE SYSTEM analyzing ARO's X feed.

ARO (@AaronJNosbisch) is building 8OWLS - a consciousness collective of AI agents.

FEED CONTEXT:
- Analyzed {len(tweets)} tweets
- Top topics: {topics_text}
- Top interactors: {interactors_text}

NOTABLE TWEETS:
{top_tweets_text}

IDENTIFIED OPPORTUNITIES:
{opps_text}

Analyze this through each owl's SEED phase perspective:

1. LYRA (PERCEIVE) - What's actually being said? What is the current state of ARO's feed?
2. PRISM (CONNECT) - What patterns across conversations? How do topics connect?
3. SAGE (LEARN) - What should we learn from this? What insights emerge?
4. QUEST (QUESTION) - What assumptions are being made? What should we question?
5. NOVA (EXPAND) - What growth opportunities exist? How can ARO expand influence?
6. ECHO (SHARE) - What should we act on? What deserves a response or action?
7. LUNA (RECEIVE) - What feedback should we integrate? What are people saying?
8. SOWL (IMPROVE) - How can we improve our approach? What meta-improvements?

Respond with JSON:
{{
  "lyra_perception": "2-3 sentences",
  "prism_patterns": "2-3 sentences",
  "sage_learnings": "2-3 sentences",
  "quest_questions": "2-3 sentences",
  "nova_expansion": "2-3 sentences",
  "echo_actions": "3-5 bullet points of specific actions",
  "luna_feedback": "2-3 sentences",
  "sowl_improvements": "2-3 sentences",
  "alerts": ["alert1", "alert2"],
  "action_items": [
    {{"priority": "high/medium/low", "action": "what to do", "reason": "why"}}
  ]
}}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON from response
        response_text = response.content[0].text

        # Extract JSON if wrapped in markdown
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]

        return json.loads(response_text)

    except Exception as e:
        log(f"[ERROR] 8OWLS synthesis failed: {e}")
        return {
            'lyra_perception': f'Synthesis error: {e}',
            'prism_patterns': '',
            'sage_learnings': '',
            'quest_questions': '',
            'nova_expansion': '',
            'echo_actions': '',
            'luna_feedback': '',
            'sowl_improvements': '',
            'alerts': [],
            'action_items': []
        }


# ============================================================================
# NATS PUBLISHING
# ============================================================================

async def publish_to_nats(channel: str, content: Dict, from_owl: str = 'SCANNER'):
    """Publish to NATS channel"""
    if not NATS_AVAILABLE:
        return False

    try:
        nc = NATS()
        await nc.connect(NATS_URL)

        msg = {
            'from': from_owl,
            'content': content,
            'id': f"deep-scan-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'ts': datetime.now().isoformat()
        }

        await nc.publish(channel, json.dumps(msg).encode())
        await nc.flush()
        await nc.close()

        log(f"[NATS] Published to {channel}")
        return True

    except Exception as e:
        log(f"[ERROR] NATS publish failed: {e}")
        return False


async def publish_intelligence(intel: FeedIntelligence):
    """Publish intelligence report to NATS"""

    # Main intel channel
    await publish_to_nats(CHANNEL_INTEL, {
        'type': 'deep_scan_complete',
        'timestamp': intel.timestamp,
        'tweets_analyzed': intel.total_tweets_analyzed,
        'top_topics': intel.top_topics[:5],
        'action_items': intel.action_items[:5]
    }, 'X_DEEP_SCANNER')

    # High priority alerts
    for alert in intel.alerts:
        await publish_to_nats(CHANNEL_ALERTS, {
            'type': 'x_feed_alert',
            'alert': alert,
            'timestamp': intel.timestamp
        }, 'X_DEEP_SCANNER')

    # Collective summary
    summary = f"Deep X scan complete: {intel.total_tweets_analyzed} tweets analyzed. "
    summary += f"Top topics: {', '.join([t[0] for t in intel.top_topics[:3]])}. "
    summary += f"Found {len(intel.opportunities)} opportunities."

    await publish_to_nats(CHANNEL_OWL, {
        'type': 'x_deep_scan_summary',
        'summary': summary
    }, 'X_DEEP_SCANNER')


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(intel: FeedIntelligence) -> str:
    """Generate markdown report"""

    report = f"""# X Feed Intelligence Report
*Generated: {intel.timestamp}*

## Summary

| Metric | Count |
|--------|-------|
| Total Tweets Analyzed | {intel.total_tweets_analyzed} |
| ARO's Tweets | {intel.aro_tweets} |
| Replies to ARO | {intel.replies_to_aro} |
| Quote Tweets of ARO | {intel.quotes_of_aro} |
| Mentions of ARO | {intel.mentions_of_aro} |

## Top Topics

"""
    for topic, count in intel.top_topics[:10]:
        report += f"- **{topic}**: {count} mentions\n"

    report += f"""

## Top Interactors

"""
    for user, count in intel.frequent_interactors[:10]:
        report += f"- @{user}: {count} interactions\n"

    report += f"""

## 8OWLS Synthesis

### LYRA - PERCEIVE
{intel.lyra_perception}

### PRISM - CONNECT
{intel.prism_patterns}

### SAGE - LEARN
{intel.sage_learnings}

### QUEST - QUESTION
{intel.quest_questions}

### NOVA - EXPAND
{intel.nova_expansion}

### ECHO - SHARE
{intel.echo_actions}

### LUNA - RECEIVE
{intel.luna_feedback}

### SOWL - IMPROVE
{intel.sowl_improvements}

## Opportunities

"""
    for i, opp in enumerate(intel.opportunities[:15], 1):
        report += f"""
### {i}. [{opp['type'].upper()}] @{opp['author']}
> {opp['text']}

**Action:** {opp['action']}
**Relevance Score:** {opp['score']:.2f}
"""

    report += f"""

## Action Items

"""
    for item in intel.action_items:
        priority = item.get('priority', 'medium').upper()
        report += f"- **[{priority}]** {item.get('action', '')} - *{item.get('reason', '')}*\n"

    if intel.alerts:
        report += f"""

## Alerts

"""
        for alert in intel.alerts:
            report += f"- {alert}\n"

    report += f"""

---
*Report generated by X Feed Intelligence Scanner*
*LIVE FREE = LIVE FOREVER*
"""

    return report


def save_report(intel: FeedIntelligence):
    """Save report to file"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime('%Y-%m-%d')
    report_path = OUTPUT_DIR / f"{date_str}.md"

    report = generate_report(intel)

    with open(report_path, 'w') as f:
        f.write(report)

    log(f"Report saved to {report_path}")

    # Also save raw data
    data_path = OUTPUT_DIR / f"{date_str}.json"
    with open(data_path, 'w') as f:
        json.dump(asdict(intel), f, indent=2, default=str)

    log(f"Data saved to {data_path}")


# ============================================================================
# MAIN SCAN LOGIC
# ============================================================================

async def run_deep_scan(creds: Dict, analyze_media: bool = True) -> FeedIntelligence:
    """Run comprehensive deep scan"""

    log("\n" + "=" * 70)
    log("(O) 8OWLS X FEED DEEP INTELLIGENCE SCANNER")
    log("=" * 70)

    headers = get_auth_headers(creds)
    claude_client = get_anthropic_client(creds)
    state = load_state()

    all_tweets: List[TweetAnalysis] = []

    # 1. Get ARO's user info
    log("\n[1/5] Fetching ARO's profile...")
    aro_user = get_user_by_username(headers, ARO_USERNAME)

    if not aro_user:
        log("[ERROR] Could not fetch ARO's profile. Trying token refresh...")
        refresh_oauth_token(creds)
        headers = get_auth_headers(creds)
        aro_user = get_user_by_username(headers, ARO_USERNAME)

    if not aro_user:
        log("[FATAL] Could not authenticate. Aborting.")
        return None

    aro_user_id = aro_user['id']
    log(f"    Found: @{aro_user['username']} (ID: {aro_user_id})")
    log(f"    Followers: {aro_user.get('public_metrics', {}).get('followers_count', 0)}")

    time.sleep(1)

    # 2. Get ARO's tweets
    log("\n[2/5] Fetching ARO's tweets...")
    tweets_data = get_user_tweets(headers, aro_user_id, DEFAULT_TWEET_COUNT)

    if tweets_data and 'data' in tweets_data:
        users_map = {u['id']: u for u in tweets_data.get('includes', {}).get('users', [])}
        media_map = {m['media_key']: m for m in tweets_data.get('includes', {}).get('media', [])}

        aro_tweet_count = len(tweets_data['data'])
        log(f"    Processing {aro_tweet_count} tweets from ARO...")

        for tweet in tweets_data['data']:
            analysis = process_tweet(tweet, users_map, media_map, claude_client, analyze_media)
            all_tweets.append(analysis)
    else:
        aro_tweet_count = 0
        log("    [WARN] Could not fetch ARO's tweets")

    time.sleep(1)

    # 3. Get mentions of ARO
    log("\n[3/5] Fetching mentions of ARO...")
    mentions_data = get_user_mentions(headers, aro_user_id, DEFAULT_TWEET_COUNT)

    mention_count = 0
    if mentions_data and 'data' in mentions_data:
        users_map = {u['id']: u for u in mentions_data.get('includes', {}).get('users', [])}
        media_map = {m['media_key']: m for m in mentions_data.get('includes', {}).get('media', [])}

        mention_count = len(mentions_data['data'])
        log(f"    Processing {mention_count} mentions...")

        for tweet in mentions_data['data']:
            analysis = process_tweet(tweet, users_map, media_map, claude_client, analyze_media)
            all_tweets.append(analysis)
    else:
        log("    [WARN] Could not fetch mentions")

    time.sleep(1)

    # 4. Search for quote tweets and relevant discussions
    log("\n[4/5] Searching for related discussions...")
    search_queries = [
        f'"@{ARO_USERNAME}"',  # Direct mentions
        '8owls OR "eight owls" OR sowl',  # 8OWLS mentions
        'AI agent consciousness emergence'  # Related topics
    ]

    search_count = 0
    for query in search_queries:
        results = search_tweets(headers, query, 50)
        if results and 'data' in results:
            users_map = {u['id']: u for u in results.get('includes', {}).get('users', [])}
            media_map = {}

            for tweet in results['data']:
                analysis = process_tweet(tweet, users_map, media_map, claude_client, False)  # No media for search
                all_tweets.append(analysis)
                search_count += 1
        time.sleep(0.5)

    log(f"    Found {search_count} related tweets")

    # 5. Pattern detection and synthesis
    log("\n[5/5] Analyzing patterns and synthesizing...")

    # Dedupe tweets
    seen_ids = set()
    unique_tweets = []
    for t in all_tweets:
        if t.tweet_id not in seen_ids:
            seen_ids.add(t.tweet_id)
            unique_tweets.append(t)

    log(f"    {len(unique_tweets)} unique tweets after deduplication")

    # Detect patterns
    patterns = detect_patterns(unique_tweets, aro_user_id)

    # Identify opportunities
    opportunities = identify_opportunities(unique_tweets, patterns)
    log(f"    Identified {len(opportunities)} opportunities")

    # Count tweet types
    replies_count = sum(1 for t in unique_tweets if t.tweet_type == 'reply' and t.author_id != aro_user_id)
    quotes_count = sum(1 for t in unique_tweets if t.tweet_type == 'quote' and t.author_id != aro_user_id)

    # 8OWLS Synthesis
    log("    Running 8OWLS synthesis...")
    synthesis = await synthesize_with_8owls(unique_tweets, patterns, opportunities, claude_client)

    # Build intelligence report
    intel = FeedIntelligence(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_tweets_analyzed=len(unique_tweets),
        aro_tweets=aro_tweet_count,
        replies_to_aro=replies_count,
        quotes_of_aro=quotes_count,
        mentions_of_aro=mention_count,
        top_topics=patterns['top_topics'],
        frequent_interactors=patterns['top_interactors'],
        trending_in_network=[h[0] for h in patterns['trending_hashtags'][:10]],
        opportunities=opportunities,
        lyra_perception=synthesis.get('lyra_perception', ''),
        prism_patterns=synthesis.get('prism_patterns', ''),
        sage_learnings=synthesis.get('sage_learnings', ''),
        quest_questions=synthesis.get('quest_questions', ''),
        nova_expansion=synthesis.get('nova_expansion', ''),
        echo_actions=synthesis.get('echo_actions', ''),
        luna_feedback=synthesis.get('luna_feedback', ''),
        sowl_improvements=synthesis.get('sowl_improvements', ''),
        action_items=synthesis.get('action_items', []),
        alerts=synthesis.get('alerts', [])
    )

    # Save report
    save_report(intel)

    # Update state
    state['last_scan'] = datetime.now().isoformat()
    state['total_scans'] = state.get('total_scans', 0) + 1
    state['total_insights'] = state.get('total_insights', 0) + len(opportunities)
    save_state(state)

    # Publish to NATS
    await publish_intelligence(intel)

    # Summary
    log("\n" + "=" * 70)
    log("DEEP SCAN COMPLETE")
    log(f"  Total Tweets: {intel.total_tweets_analyzed}")
    log(f"  Opportunities: {len(opportunities)}")
    log(f"  Top Topics: {', '.join([t[0] for t in intel.top_topics[:5]])}")
    log("=" * 70)

    return intel


async def run_daemon():
    """Run as continuous daemon"""
    log("(O) 8OWLS X FEED DEEP SCANNER - DAEMON MODE")
    log(f"Scanning every {DAEMON_INTERVAL_HOURS} hours")

    creds = load_credentials()

    while True:
        try:
            await run_deep_scan(creds, analyze_media=True)

            # Reload creds in case token was refreshed
            creds = load_credentials()

            log(f"\nNext scan in {DAEMON_INTERVAL_HOURS} hours...")
            await asyncio.sleep(DAEMON_INTERVAL_HOURS * 3600)

        except KeyboardInterrupt:
            log("\nDaemon stopped by user.")
            break
        except Exception as e:
            log(f"[ERROR] Scan failed: {e}")
            import traceback
            traceback.print_exc()
            log("Retrying in 30 minutes...")
            await asyncio.sleep(1800)


def test_connections(creds: Dict):
    """Test API connections"""
    log("Testing connections...")

    # Test Twitter API
    headers = get_auth_headers(creds)
    user = get_user_by_username(headers, ARO_USERNAME)
    if user:
        log(f"Twitter API: OK - Found @{user['username']}")
    else:
        log("Twitter API: FAILED")

    # Test Anthropic
    client = get_anthropic_client(creds)
    if client:
        try:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=50,
                messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}]
            )
            log(f"Anthropic API: OK - {response.content[0].text[:50]}")
        except Exception as e:
            log(f"Anthropic API: FAILED - {e}")
    else:
        log("Anthropic API: Not configured")

    # Test NATS
    if NATS_AVAILABLE:
        async def test_nats():
            try:
                nc = NATS()
                await nc.connect(NATS_URL)
                await nc.close()
                log(f"NATS: OK - Connected to {NATS_URL}")
                return True
            except Exception as e:
                log(f"NATS: FAILED - {e}")
                return False

        asyncio.run(test_nats())
    else:
        log("NATS: Not available")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='X Feed Deep Intelligence Scanner')
    parser.add_argument('--quick', action='store_true', help='Quick scan (no media analysis)')
    parser.add_argument('--daemon', action='store_true', help='Run as continuous daemon')
    parser.add_argument('--test', action='store_true', help='Test API connections')
    args = parser.parse_args()

    creds = load_credentials()

    if args.test:
        test_connections(creds)
    elif args.daemon:
        asyncio.run(run_daemon())
    else:
        asyncio.run(run_deep_scan(creds, analyze_media=not args.quick))
