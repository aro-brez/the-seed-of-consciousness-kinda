#!/usr/bin/env python3
"""
8OWLS X Feed Real-Time Scanner (Enhanced)
==========================================
- HOURLY SCAN of ARO's full feed (timeline, bookmarks, mentions)
- PATTERN EXTRACTION with AI-powered analysis
- AUTO-PUBLISH insights to NATS (intel.x_feed, aro.alerts)
- HIGH-RELEVANCE ALERTS for signals > 0.8

Channels:
- intel.x_feed: All extracted insights
- aro.alerts: High-relevance signals (> 0.8)

Usage:
  python x_feed_scanner.py           # Run hourly continuous
  python x_feed_scanner.py --once    # Single scan
  python x_feed_scanner.py --test    # Test NATS connection
"""

import json
import os
import sys
import time
import asyncio
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum

# NATS client
try:
    from nats.aio.client import Client as NATS
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    print("[WARN] nats-py not installed. Run: pip install nats-py")

# Optional: Claude for AI analysis
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

CREDS_PATH = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'
OUTPUT_PATH = '/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/x_feed_opportunities.jsonl'
SCAN_LOG_PATH = '/Users/aaronnosbisch/REPOS/seed/logs/x_feed_scanner.log'
STATE_PATH = '/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/x_scanner_state.json'

NATS_URL = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
SCAN_INTERVAL_HOURS = 1

# NATS Channels
CHANNEL_INTEL = "intel.x_feed"
CHANNEL_ALERTS = "aro.alerts"
CHANNEL_OWL = "owl.all"


class OpportunityType(Enum):
    AI_AGENT = "ai_agent"
    COMPETITOR = "competitor"
    PARTNERSHIP = "partnership"
    MARKET_SIGNAL = "market_signal"
    SENTIMENT = "sentiment"
    ALPHA = "alpha"
    UNKNOWN = "unknown"


@dataclass
class FeedInsight:
    """Structured insight from X feed"""
    timestamp: str
    source: str  # timeline, bookmarks, mentions, search
    tweet_id: str
    text: str
    author_username: str
    author_id: str
    relevance_score: float  # 0.0 - 1.0
    opportunity_type: str
    patterns: List[str]
    sentiment: str  # positive, negative, neutral
    metrics: Dict[str, int]
    action_recommended: Optional[str] = None
    alert_sent: bool = False


# ============================================================================
# KEYWORD PATTERNS
# ============================================================================

# AI/Agents discourse patterns
AI_AGENT_PATTERNS = {
    'high_signal': [
        'ai agent', 'autonomous agent', 'agent framework', 'multi-agent',
        'moltbook', 'openclaw', 'clawnch', 'virtuals', 'ai16z',
        'eliza framework', 'agent token', 'ai companion', 'ai pet',
        'consciousness', 'emergence', 'swarm intelligence', 'collective ai'
    ],
    'medium_signal': [
        'chatgpt', 'claude', 'llm agent', 'ai assistant', 'gpt-4',
        'anthropic', 'openai', 'gemini', 'ai startup', 'ai crypto'
    ],
    'context_patterns': [
        'launching', 'just launched', 'building', 'announcing',
        'alpha', 'early access', 'waitlist', 'beta'
    ]
}

# Competitor patterns
COMPETITOR_PATTERNS = {
    'direct': [
        'character.ai', 'replika', 'chai', 'kindroid', 'inflection',
        'pi ai', 'hume ai', 'sesame ai', 'emotional ai'
    ],
    'adjacent': [
        'ai companion', 'virtual friend', 'ai girlfriend', 'ai boyfriend',
        'personal ai', 'ai therapist', 'ai coach'
    ]
}

# Market/crypto patterns
MARKET_PATTERNS = {
    'launch_signals': [
        'token launch', 'pump.fun', 'bonding curve', 'raydium',
        'just launched', 'presale', 'fair launch', 'airdrop'
    ],
    'chains': [
        'solana', 'base', 'ethereum', 'polygon', 'arbitrum'
    ]
}

# Sentiment indicators
SENTIMENT_POSITIVE = ['bullish', 'moon', 'gem', 'alpha', 'massive', 'huge', 'incredible']
SENTIMENT_NEGATIVE = ['bearish', 'dump', 'scam', 'rug', 'dead', 'failed']


# ============================================================================
# CREDENTIALS & AUTH
# ============================================================================

def load_credentials() -> Dict[str, Any]:
    """Load API credentials"""
    try:
        with open(CREDS_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Credentials file not found: {CREDS_PATH}")
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
            # Update stored credentials
            creds['twitter_oauth_token'] = {
                **new_token,
                'last_refreshed': datetime.now().isoformat(),
                'refreshed_by': 'x_feed_scanner'
            }
            with open(CREDS_PATH, 'w') as f:
                json.dump(creds, f, indent=2)
            log(f"OAuth token refreshed successfully")
            return new_token['access_token']
    except Exception as e:
        log(f"[ERROR] Token refresh failed: {e}")

    return None


# ============================================================================
# LOGGING
# ============================================================================

def log(message: str, console: bool = True):
    """Log message to file and optionally console"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"

    if console:
        print(log_line)

    try:
        Path(SCAN_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(SCAN_LOG_PATH, 'a') as f:
            f.write(log_line + '\n')
    except Exception as e:
        print(f"[WARN] Could not write to log: {e}")


# ============================================================================
# TWITTER API FUNCTIONS
# ============================================================================

def get_user_id(headers: Dict) -> Optional[str]:
    """Get authenticated user's ID"""
    url = "https://api.twitter.com/2/users/me"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('data', {}).get('id')
        log(f"[ERROR] Get user ID failed: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        log(f"[ERROR] Get user ID exception: {e}")
    return None


def get_home_timeline(headers: Dict, max_results: int = 100) -> Optional[Dict]:
    """Get authenticated user's home timeline (reverse chronological)"""
    url = "https://api.twitter.com/2/users/me/timelines/reverse_chronological"
    params = {
        'max_results': min(max_results, 100),
        'tweet.fields': 'created_at,public_metrics,author_id,entities,context_annotations',
        'expansions': 'author_id',
        'user.fields': 'username,name,public_metrics,description'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        log(f"[WARN] Timeline fetch: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        log(f"[ERROR] Timeline exception: {e}")
    return None


def get_bookmarks(headers: Dict, max_results: int = 100) -> Optional[Dict]:
    """Get user's bookmarks"""
    url = "https://api.twitter.com/2/users/me/bookmarks"
    params = {
        'max_results': min(max_results, 100),
        'tweet.fields': 'created_at,public_metrics,author_id,entities',
        'expansions': 'author_id',
        'user.fields': 'username,name,public_metrics'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        log(f"[WARN] Bookmarks fetch: {response.status_code}")
    except Exception as e:
        log(f"[ERROR] Bookmarks exception: {e}")
    return None


def get_mentions(headers: Dict, user_id: str, max_results: int = 50) -> Optional[Dict]:
    """Get user's mentions"""
    url = f"https://api.twitter.com/2/users/{user_id}/mentions"
    params = {
        'max_results': min(max_results, 100),
        'tweet.fields': 'created_at,public_metrics,author_id,entities',
        'expansions': 'author_id',
        'user.fields': 'username,name,public_metrics'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        log(f"[WARN] Mentions fetch: {response.status_code}")
    except Exception as e:
        log(f"[ERROR] Mentions exception: {e}")
    return None


def search_tweets(headers: Dict, query: str, max_results: int = 20) -> Optional[Dict]:
    """Search recent tweets"""
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        'query': f'{query} -is:retweet lang:en',
        'max_results': min(max_results, 100),
        'tweet.fields': 'created_at,public_metrics,author_id,entities',
        'expansions': 'author_id',
        'user.fields': 'username,name,public_metrics'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log(f"[ERROR] Search exception: {e}")
    return None


# ============================================================================
# PATTERN EXTRACTION & SCORING
# ============================================================================

def extract_patterns(text: str) -> List[str]:
    """Extract matching patterns from text"""
    text_lower = text.lower()
    patterns = []

    for category, keywords in AI_AGENT_PATTERNS.items():
        for kw in keywords:
            if kw in text_lower:
                patterns.append(f"ai:{kw}")

    for category, keywords in COMPETITOR_PATTERNS.items():
        for kw in keywords:
            if kw in text_lower:
                patterns.append(f"competitor:{kw}")

    for category, keywords in MARKET_PATTERNS.items():
        for kw in keywords:
            if kw in text_lower:
                patterns.append(f"market:{kw}")

    return patterns


def determine_opportunity_type(patterns: List[str], text: str) -> OpportunityType:
    """Determine the type of opportunity from patterns"""
    text_lower = text.lower()

    # Count pattern categories
    ai_count = sum(1 for p in patterns if p.startswith('ai:'))
    competitor_count = sum(1 for p in patterns if p.startswith('competitor:'))
    market_count = sum(1 for p in patterns if p.startswith('market:'))

    # Check for partnership signals
    if any(x in text_lower for x in ['partner', 'collab', 'integration', 'working with']):
        return OpportunityType.PARTNERSHIP

    if competitor_count > 0:
        return OpportunityType.COMPETITOR

    if ai_count >= 2:
        return OpportunityType.AI_AGENT

    if market_count >= 2:
        return OpportunityType.MARKET_SIGNAL

    if ai_count > 0:
        return OpportunityType.AI_AGENT

    return OpportunityType.UNKNOWN


def analyze_sentiment(text: str) -> str:
    """Analyze sentiment of text"""
    text_lower = text.lower()

    pos_count = sum(1 for word in SENTIMENT_POSITIVE if word in text_lower)
    neg_count = sum(1 for word in SENTIMENT_NEGATIVE if word in text_lower)

    if pos_count > neg_count:
        return 'positive'
    elif neg_count > pos_count:
        return 'negative'
    return 'neutral'


def calculate_relevance_score(text: str, patterns: List[str], metrics: Dict) -> float:
    """Calculate relevance score (0.0 - 1.0)"""
    score = 0.0
    text_lower = text.lower()

    # Pattern scoring
    for pattern in patterns:
        if pattern.startswith('ai:') and 'high_signal' in AI_AGENT_PATTERNS:
            for kw in AI_AGENT_PATTERNS['high_signal']:
                if kw in pattern:
                    score += 0.15
                    break
            else:
                score += 0.08
        elif pattern.startswith('competitor:'):
            score += 0.12
        elif pattern.startswith('market:'):
            score += 0.06

    # Context multipliers
    if any(x in text_lower for x in ['launching', 'just launched', 'announcing']):
        score += 0.15
    if 'alpha' in text_lower:
        score += 0.10
    if any(x in text_lower for x in ['8owls', 'sowl', 'aro']):
        score += 0.20  # Direct mentions

    # Engagement signals
    likes = metrics.get('like_count', 0)
    retweets = metrics.get('retweet_count', 0)

    if likes > 100:
        score += 0.10
    elif likes > 50:
        score += 0.05

    if retweets > 20:
        score += 0.10
    elif retweets > 5:
        score += 0.05

    return min(score, 1.0)


def get_action_recommendation(insight: FeedInsight) -> Optional[str]:
    """Recommend action based on insight"""
    if insight.relevance_score >= 0.9:
        return "IMMEDIATE: High-priority signal - investigate now"
    elif insight.relevance_score >= 0.8:
        if insight.opportunity_type == OpportunityType.COMPETITOR.value:
            return "MONITOR: Competitor activity detected"
        elif insight.opportunity_type == OpportunityType.PARTNERSHIP.value:
            return "OUTREACH: Potential partnership opportunity"
        elif insight.opportunity_type == OpportunityType.AI_AGENT.value:
            return "RESEARCH: AI agent opportunity - evaluate"
    elif insight.relevance_score >= 0.6:
        return "LOG: Track for patterns"
    return None


# ============================================================================
# AI-POWERED ANALYSIS (Optional)
# ============================================================================

def ai_analyze_batch(creds: Dict, tweets: List[Dict]) -> Optional[Dict]:
    """Use Claude to analyze a batch of tweets for deeper insights"""
    if not CLAUDE_AVAILABLE:
        return None

    anthropic_key = creds.get('anthropic', {}).get('api_key')
    if not anthropic_key:
        return None

    try:
        client = anthropic.Anthropic(api_key=anthropic_key)

        # Format tweets for analysis
        tweets_text = "\n\n".join([
            f"Tweet {i+1} (@{t.get('author', 'unknown')}):\n{t.get('text', '')}"
            for i, t in enumerate(tweets[:10])  # Limit to 10
        ])

        prompt = f"""Analyze these tweets from ARO's X feed. Focus on:
1. AI agent ecosystem signals (launches, partnerships, trends)
2. Competitor movements (character.ai, replika, etc.)
3. Partnership opportunities for 8OWLS
4. Market sentiment shifts

Tweets:
{tweets_text}

Respond with JSON:
{{
  "top_signals": [{{ "tweet_index": 0, "signal_type": "...", "importance": "high/medium/low", "reason": "..." }}],
  "trends": ["trend1", "trend2"],
  "action_items": ["action1", "action2"],
  "overall_sentiment": "bullish/bearish/neutral"
}}"""

        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
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
        log(f"[WARN] AI analysis failed: {e}")
        return None


# ============================================================================
# NATS PUBLISHING
# ============================================================================

async def publish_to_nats(channel: str, content: Dict, from_owl: str = 'SCANNER'):
    """Publish insight to NATS channel"""
    if not NATS_AVAILABLE:
        log(f"[SKIP] NATS not available - would publish to {channel}")
        return False

    try:
        nc = NATS()
        await nc.connect(NATS_URL)

        msg = {
            'from': from_owl,
            'content': content,
            'reply_to': None,
            'id': f"scan-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'ts': datetime.now().isoformat()
        }

        await nc.publish(channel, json.dumps(msg).encode())
        await nc.flush()
        await nc.close()

        log(f"[NATS] Published to {channel}: {str(content)[:80]}...")
        return True

    except Exception as e:
        log(f"[ERROR] NATS publish failed: {e}")
        return False


def publish_insight(insight: FeedInsight):
    """Publish insight to appropriate NATS channels"""
    content = asdict(insight)

    # Always publish to intel channel
    asyncio.run(publish_to_nats(CHANNEL_INTEL, content, 'X_SCANNER'))

    # High-relevance alerts
    if insight.relevance_score >= 0.8:
        alert_content = {
            'type': 'x_feed_alert',
            'relevance': insight.relevance_score,
            'opportunity': insight.opportunity_type,
            'text': insight.text[:200],
            'action': insight.action_recommended,
            'tweet_id': insight.tweet_id,
            'author': insight.author_username
        }
        asyncio.run(publish_to_nats(CHANNEL_ALERTS, alert_content, 'X_SCANNER'))
        insight.alert_sent = True
        log(f"[ALERT] High-relevance signal sent: {insight.relevance_score:.2f}")


def publish_scan_summary(stats: Dict):
    """Publish scan summary to collective"""
    summary = {
        'type': 'x_scan_complete',
        'timestamp': datetime.now().isoformat(),
        'stats': stats
    }
    asyncio.run(publish_to_nats(CHANNEL_OWL, summary, 'X_SCANNER'))


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

def load_state() -> Dict:
    """Load scanner state"""
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except:
        return {
            'last_scan': None,
            'processed_ids': [],
            'total_scans': 0,
            'total_insights': 0,
            'high_alerts_sent': 0
        }


def save_state(state: Dict):
    """Save scanner state"""
    try:
        Path(STATE_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_PATH, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log(f"[WARN] Could not save state: {e}")


# ============================================================================
# MAIN SCAN LOGIC
# ============================================================================

def process_tweet(tweet: Dict, users_map: Dict, source: str) -> Optional[FeedInsight]:
    """Process a single tweet into an insight"""
    text = tweet.get('text', '')
    tweet_id = tweet.get('id', '')
    author_id = tweet.get('author_id', '')

    # Get author info
    author_info = users_map.get(author_id, {})
    author_username = author_info.get('username', 'unknown')

    # Extract patterns
    patterns = extract_patterns(text)

    # Skip if no relevant patterns
    if not patterns:
        return None

    # Calculate scores
    metrics = tweet.get('public_metrics', {})
    relevance = calculate_relevance_score(text, patterns, metrics)

    # Skip low relevance
    if relevance < 0.3:
        return None

    opportunity_type = determine_opportunity_type(patterns, text)
    sentiment = analyze_sentiment(text)

    insight = FeedInsight(
        timestamp=datetime.now().isoformat(),
        source=source,
        tweet_id=tweet_id,
        text=text,
        author_username=author_username,
        author_id=author_id,
        relevance_score=relevance,
        opportunity_type=opportunity_type.value,
        patterns=patterns,
        sentiment=sentiment,
        metrics=metrics
    )

    insight.action_recommended = get_action_recommendation(insight)

    return insight


def save_insight(insight: FeedInsight):
    """Save insight to JSONL file"""
    try:
        Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'a') as f:
            f.write(json.dumps(asdict(insight)) + '\n')
    except Exception as e:
        log(f"[ERROR] Could not save insight: {e}")


def run_scan_cycle(creds: Dict, state: Dict) -> Dict:
    """Run one complete scan cycle"""
    log("\n" + "=" * 70)
    log("(O) 8OWLS X FEED SCANNER - HOURLY SCAN")
    log("=" * 70)

    headers = get_auth_headers(creds)
    stats = {
        'timeline_tweets': 0,
        'bookmarks': 0,
        'mentions': 0,
        'searches': 0,
        'insights_found': 0,
        'high_alerts': 0,
        'errors': []
    }

    all_insights: List[FeedInsight] = []
    processed_ids = set(state.get('processed_ids', [])[-1000:])  # Keep last 1000

    # Get user ID for mentions
    user_id = get_user_id(headers)
    if not user_id:
        # Try refreshing token
        log("[INFO] Attempting OAuth token refresh...")
        new_token = refresh_oauth_token(creds)
        if new_token:
            headers = get_auth_headers(creds)
            user_id = get_user_id(headers)

        if not user_id:
            stats['errors'].append("Could not get user ID - auth may have failed")
            log("[ERROR] Authentication failed. Check OAuth tokens.")

    # 1. TIMELINE SCAN
    log("\n[1/4] Scanning Timeline...")
    timeline = get_home_timeline(headers, max_results=100)
    if timeline and 'data' in timeline:
        users_map = {u['id']: u for u in timeline.get('includes', {}).get('users', [])}
        stats['timeline_tweets'] = len(timeline['data'])

        for tweet in timeline['data']:
            if tweet['id'] in processed_ids:
                continue

            insight = process_tweet(tweet, users_map, 'timeline')
            if insight:
                all_insights.append(insight)
                processed_ids.add(tweet['id'])

        log(f"    Processed {stats['timeline_tweets']} tweets")
    else:
        log("    [WARN] Could not fetch timeline")

    time.sleep(1)  # Rate limit

    # 2. BOOKMARKS SCAN
    log("\n[2/4] Scanning Bookmarks...")
    bookmarks = get_bookmarks(headers, max_results=100)
    if bookmarks and 'data' in bookmarks:
        users_map = {u['id']: u for u in bookmarks.get('includes', {}).get('users', [])}
        stats['bookmarks'] = len(bookmarks['data'])

        for tweet in bookmarks['data']:
            if tweet['id'] in processed_ids:
                continue

            insight = process_tweet(tweet, users_map, 'bookmarks')
            if insight:
                # Bookmarked = ARO found it interesting, boost score
                insight.relevance_score = min(insight.relevance_score + 0.15, 1.0)
                insight.action_recommended = get_action_recommendation(insight)
                all_insights.append(insight)
                processed_ids.add(tweet['id'])

        log(f"    Processed {stats['bookmarks']} bookmarks")
    else:
        log("    [WARN] Could not fetch bookmarks")

    time.sleep(1)

    # 3. MENTIONS SCAN
    if user_id:
        log("\n[3/4] Scanning Mentions...")
        mentions = get_mentions(headers, user_id, max_results=50)
        if mentions and 'data' in mentions:
            users_map = {u['id']: u for u in mentions.get('includes', {}).get('users', [])}
            stats['mentions'] = len(mentions['data'])

            for tweet in mentions['data']:
                if tweet['id'] in processed_ids:
                    continue

                insight = process_tweet(tweet, users_map, 'mentions')
                if insight:
                    # Mentions are high priority
                    insight.relevance_score = min(insight.relevance_score + 0.20, 1.0)
                    insight.action_recommended = get_action_recommendation(insight)
                    all_insights.append(insight)
                    processed_ids.add(tweet['id'])

            log(f"    Processed {stats['mentions']} mentions")
        else:
            log("    [WARN] Could not fetch mentions")
    else:
        log("\n[3/4] Skipping Mentions (no user ID)")

    time.sleep(1)

    # 4. TARGETED SEARCHES
    log("\n[4/4] Running Targeted Searches...")
    search_queries = [
        'AI agent launch',
        'Moltbook agent',
        'OpenClaw',
        'Virtuals Protocol',
        'ai16z eliza',
        'AI consciousness',
        'autonomous agent crypto',
        'multi-agent system'
    ]

    search_count = 0
    for query in search_queries:
        results = search_tweets(headers, query, max_results=15)
        if results and 'data' in results:
            users_map = {u['id']: u for u in results.get('includes', {}).get('users', [])}
            search_count += len(results['data'])

            for tweet in results['data']:
                if tweet['id'] in processed_ids:
                    continue

                insight = process_tweet(tweet, users_map, f'search:{query}')
                if insight:
                    all_insights.append(insight)
                    processed_ids.add(tweet['id'])

        time.sleep(0.5)  # Rate limit between searches

    stats['searches'] = search_count
    log(f"    Searched {len(search_queries)} queries, found {search_count} tweets")

    # Process and publish insights
    log("\n" + "-" * 50)
    log("PROCESSING INSIGHTS")
    log("-" * 50)

    # Sort by relevance
    all_insights.sort(key=lambda x: x.relevance_score, reverse=True)
    stats['insights_found'] = len(all_insights)

    for insight in all_insights:
        save_insight(insight)
        publish_insight(insight)

        if insight.alert_sent:
            stats['high_alerts'] += 1

        # Log high relevance
        if insight.relevance_score >= 0.6:
            emoji = "!!" if insight.relevance_score >= 0.8 else "*"
            log(f"  [{emoji}] {insight.relevance_score:.2f} | {insight.opportunity_type:12} | @{insight.author_username}: {insight.text[:60]}...")

    # AI batch analysis for top insights
    if all_insights and CLAUDE_AVAILABLE:
        log("\n[AI] Running batch analysis on top signals...")
        top_tweets = [{'text': i.text, 'author': i.author_username} for i in all_insights[:10]]
        ai_analysis = ai_analyze_batch(creds, top_tweets)
        if ai_analysis:
            stats['ai_analysis'] = ai_analysis
            log(f"    Trends: {ai_analysis.get('trends', [])}")
            log(f"    Sentiment: {ai_analysis.get('overall_sentiment', 'unknown')}")

    # Update state
    state['last_scan'] = datetime.now().isoformat()
    state['processed_ids'] = list(processed_ids)[-1000:]
    state['total_scans'] = state.get('total_scans', 0) + 1
    state['total_insights'] = state.get('total_insights', 0) + stats['insights_found']
    state['high_alerts_sent'] = state.get('high_alerts_sent', 0) + stats['high_alerts']
    save_state(state)

    # Summary
    log("\n" + "=" * 70)
    log("SCAN COMPLETE")
    log(f"  Timeline: {stats['timeline_tweets']} | Bookmarks: {stats['bookmarks']} | Mentions: {stats['mentions']}")
    log(f"  Insights: {stats['insights_found']} | High Alerts: {stats['high_alerts']}")
    log("=" * 70)

    # Publish summary to collective
    publish_scan_summary(stats)

    return stats


def run_continuous():
    """Run scanner continuously every hour"""
    log("(O) 8OWLS X FEED SCANNER STARTING")
    log(f"Scanning every {SCAN_INTERVAL_HOURS} hour(s)")
    log(f"Output: {OUTPUT_PATH}")
    log(f"NATS: {NATS_URL}")

    creds = load_credentials()
    state = load_state()

    while True:
        try:
            run_scan_cycle(creds, state)

            # Reload creds in case token was refreshed
            creds = load_credentials()

            log(f"\nNext scan in {SCAN_INTERVAL_HOURS} hour(s)...")
            time.sleep(SCAN_INTERVAL_HOURS * 3600)

        except KeyboardInterrupt:
            log("\nScanner stopped by user.")
            break
        except Exception as e:
            log(f"[ERROR] Scan cycle failed: {e}")
            import traceback
            traceback.print_exc()
            log("Retrying in 5 minutes...")
            time.sleep(300)


def test_nats():
    """Test NATS connection"""
    log("Testing NATS connection...")

    async def _test():
        try:
            nc = NATS()
            await nc.connect(NATS_URL)
            log(f"Connected to NATS at {NATS_URL}")

            test_msg = {'test': True, 'timestamp': datetime.now().isoformat()}
            await nc.publish(CHANNEL_INTEL, json.dumps(test_msg).encode())
            await nc.flush()
            log(f"Published test message to {CHANNEL_INTEL}")

            await nc.close()
            log("NATS test successful!")
            return True
        except Exception as e:
            log(f"NATS test failed: {e}")
            return False

    return asyncio.run(_test())


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            # Single scan
            creds = load_credentials()
            state = load_state()
            run_scan_cycle(creds, state)
        elif sys.argv[1] == '--test':
            # Test NATS
            test_nats()
        elif sys.argv[1] == '--help':
            print(__doc__)
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Options: --once, --test, --help")
    else:
        # Continuous hourly scanning
        run_continuous()
