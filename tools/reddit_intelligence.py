#!/usr/bin/env python3
"""
Reddit JSON Intelligence System
================================
Add /.json to any Reddit URL - extract full threads, analyze with Claude.
Make money from niche subreddit intelligence.

Author: QUEST (8OWLS)
Date: 2026-02-05
"""

import json
import os
import sys
import time
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
INTEL_DIR = REPO_ROOT / "BRAIN" / "INTEL" / "reddit"
CACHE_DIR = INTEL_DIR / "cache"

# Ensure directories exist
INTEL_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_reddit_json(url: str, use_cache: bool = True, cache_ttl: int = 300, retries: int = 3) -> dict:
    """
    Fetch Reddit data as JSON by appending .json to URL.

    Args:
        url: Any Reddit URL (post, subreddit, comment thread)
        use_cache: Whether to use cached responses
        cache_ttl: Cache time-to-live in seconds (default 5 min)
        retries: Number of retry attempts

    Returns:
        Parsed JSON data from Reddit
    """
    # Normalize URL - use old.reddit.com which is more reliable
    url = url.rstrip('/')
    url = url.replace('www.reddit.com', 'old.reddit.com')
    url = url.replace('reddit.com', 'old.reddit.com')

    if not url.endswith('.json'):
        # Remove query params before adding .json
        if '?' in url:
            base, params = url.split('?', 1)
            json_url = f"{base}.json?{params}"
        else:
            json_url = f"{url}.json"
    else:
        json_url = url

    # Ensure https
    if not json_url.startswith('http'):
        json_url = f"https://{json_url}"

    # Cache handling
    cache_key = hashlib.md5(json_url.encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if use_cache and cache_file.exists():
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age < cache_ttl:
            with open(cache_file, 'r') as f:
                return json.load(f)

    # User agents that work with Reddit
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]

    last_error = None
    for attempt in range(retries):
        headers = {
            'User-Agent': user_agents[attempt % len(user_agents)],
            'Accept': 'application/json, text/html',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        try:
            req = Request(json_url, headers=headers)
            with urlopen(req, timeout=30) as response:
                # Handle gzip if needed
                data_bytes = response.read()
                try:
                    import gzip
                    data_bytes = gzip.decompress(data_bytes)
                except:
                    pass  # Not gzipped

                data = json.loads(data_bytes.decode('utf-8'))

                # Cache the response
                if use_cache:
                    with open(cache_file, 'w') as f:
                        json.dump(data, f)

                return data
        except HTTPError as e:
            last_error = f"HTTP Error {e.code}: {e.reason}"
            if e.code == 429:  # Rate limited
                time.sleep(2 ** attempt)  # Exponential backoff
            elif e.code in [403, 503]:  # Blocked or service unavailable
                time.sleep(1)
        except URLError as e:
            last_error = f"URL Error: {e.reason}"
            time.sleep(1)
        except Exception as e:
            last_error = str(e)
            time.sleep(1)

    raise Exception(f"Failed after {retries} attempts. Last error: {last_error}")


def extract_post_data(data: dict) -> dict:
    """Extract post content from Reddit JSON."""
    if isinstance(data, list) and len(data) > 0:
        # Post page format: [post_listing, comments_listing]
        post_listing = data[0]
        if 'data' in post_listing and 'children' in post_listing['data']:
            children = post_listing['data']['children']
            if children:
                post = children[0]['data']
                return {
                    'id': post.get('id'),
                    'title': post.get('title'),
                    'author': post.get('author'),
                    'subreddit': post.get('subreddit'),
                    'selftext': post.get('selftext', ''),
                    'url': post.get('url'),
                    'score': post.get('score', 0),
                    'upvote_ratio': post.get('upvote_ratio', 0),
                    'num_comments': post.get('num_comments', 0),
                    'created_utc': post.get('created_utc'),
                    'created': datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
                    'flair': post.get('link_flair_text'),
                    'is_self': post.get('is_self', True),
                    'permalink': f"https://reddit.com{post.get('permalink', '')}",
                    'awards': post.get('total_awards_received', 0)
                }
    return {}


def extract_comments(data: dict, max_depth: int = 10) -> list:
    """
    Recursively extract all comments from Reddit JSON.

    Args:
        data: Reddit JSON data
        max_depth: Maximum comment depth to traverse

    Returns:
        Flat list of all comments with depth info
    """
    comments = []

    def parse_comment(comment_data: dict, depth: int = 0):
        if depth > max_depth:
            return

        if comment_data.get('kind') != 't1':
            return

        c = comment_data.get('data', {})

        comment = {
            'id': c.get('id'),
            'author': c.get('author'),
            'body': c.get('body', ''),
            'score': c.get('score', 0),
            'created_utc': c.get('created_utc'),
            'created': datetime.fromtimestamp(c.get('created_utc', 0)).isoformat() if c.get('created_utc') else None,
            'depth': depth,
            'parent_id': c.get('parent_id'),
            'is_submitter': c.get('is_submitter', False),
            'awards': c.get('total_awards_received', 0),
            'controversiality': c.get('controversiality', 0)
        }
        comments.append(comment)

        # Parse replies
        replies = c.get('replies')
        if replies and isinstance(replies, dict):
            reply_children = replies.get('data', {}).get('children', [])
            for reply in reply_children:
                parse_comment(reply, depth + 1)

    # Comments are in the second element
    if isinstance(data, list) and len(data) > 1:
        comments_listing = data[1]
        if 'data' in comments_listing and 'children' in comments_listing['data']:
            for comment in comments_listing['data']['children']:
                parse_comment(comment, depth=0)

    return comments


def extract_subreddit_posts(data: dict, limit: int = 25) -> list:
    """Extract posts from a subreddit listing."""
    posts = []

    if isinstance(data, dict) and 'data' in data:
        children = data['data'].get('children', [])
        for child in children[:limit]:
            if child.get('kind') == 't3':
                post = child['data']
                posts.append({
                    'id': post.get('id'),
                    'title': post.get('title'),
                    'author': post.get('author'),
                    'selftext': post.get('selftext', '')[:500],  # Truncate
                    'url': post.get('url'),
                    'score': post.get('score', 0),
                    'upvote_ratio': post.get('upvote_ratio', 0),
                    'num_comments': post.get('num_comments', 0),
                    'created_utc': post.get('created_utc'),
                    'created': datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
                    'flair': post.get('link_flair_text'),
                    'permalink': f"https://reddit.com{post.get('permalink', '')}",
                    'awards': post.get('total_awards_received', 0)
                })

    return posts


def analyze_thread(url: str) -> dict:
    """
    Complete analysis of a Reddit thread.

    Returns:
        Dictionary with post, comments, and metadata
    """
    data = fetch_reddit_json(url)

    post = extract_post_data(data)
    comments = extract_comments(data)

    # Compute stats
    if comments:
        scores = [c['score'] for c in comments if c.get('score')]
        avg_score = sum(scores) / len(scores) if scores else 0
        top_comments = sorted(comments, key=lambda x: x.get('score', 0), reverse=True)[:5]
    else:
        avg_score = 0
        top_comments = []

    return {
        'post': post,
        'comments': comments,
        'stats': {
            'total_comments': len(comments),
            'unique_authors': len(set(c['author'] for c in comments if c.get('author'))),
            'avg_comment_score': round(avg_score, 2),
            'max_depth': max((c['depth'] for c in comments), default=0),
            'op_replies': sum(1 for c in comments if c.get('is_submitter')),
            'controversial_count': sum(1 for c in comments if c.get('controversiality', 0) > 0)
        },
        'top_comments': top_comments,
        'fetched_at': datetime.now().isoformat()
    }


def analyze_subreddit(subreddit: str, sort: str = 'hot', limit: int = 25) -> dict:
    """
    Analyze a subreddit's current state.

    Args:
        subreddit: Subreddit name (without r/)
        sort: 'hot', 'new', 'top', 'rising'
        limit: Number of posts to fetch

    Returns:
        Dictionary with posts and analysis
    """
    url = f"https://reddit.com/r/{subreddit}/{sort}"
    data = fetch_reddit_json(url)
    posts = extract_subreddit_posts(data, limit)

    # Compute subreddit stats
    if posts:
        scores = [p['score'] for p in posts]
        comments = [p['num_comments'] for p in posts]
        trending_topics = []

        # Extract common words from titles
        words = {}
        for post in posts:
            for word in post['title'].lower().split():
                if len(word) > 4:
                    words[word] = words.get(word, 0) + 1
        trending_topics = sorted(words.items(), key=lambda x: x[1], reverse=True)[:10]
    else:
        scores = []
        comments = []
        trending_topics = []

    return {
        'subreddit': subreddit,
        'sort': sort,
        'posts': posts,
        'stats': {
            'total_posts': len(posts),
            'avg_score': round(sum(scores) / len(scores), 2) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'avg_comments': round(sum(comments) / len(comments), 2) if comments else 0,
            'trending_words': trending_topics[:5]
        },
        'top_posts': sorted(posts, key=lambda x: x['score'], reverse=True)[:5],
        'fetched_at': datetime.now().isoformat()
    }


def format_for_llm(analysis: dict, analysis_type: str = 'thread') -> str:
    """
    Format Reddit data for LLM analysis.

    Args:
        analysis: Output from analyze_thread or analyze_subreddit
        analysis_type: 'thread' or 'subreddit'

    Returns:
        Formatted string for LLM input
    """
    if analysis_type == 'thread':
        post = analysis.get('post', {})
        stats = analysis.get('stats', {})
        comments = analysis.get('comments', [])

        output = f"""# Reddit Thread Analysis

## Post
**Title:** {post.get('title', 'N/A')}
**Subreddit:** r/{post.get('subreddit', 'N/A')}
**Author:** u/{post.get('author', 'N/A')}
**Score:** {post.get('score', 0)} (upvote ratio: {post.get('upvote_ratio', 0)})
**Comments:** {post.get('num_comments', 0)}
**Posted:** {post.get('created', 'N/A')}
**Flair:** {post.get('flair', 'None')}
**Awards:** {post.get('awards', 0)}

### Content
{post.get('selftext', 'N/A')[:2000]}

## Stats
- Total comments analyzed: {stats.get('total_comments', 0)}
- Unique authors: {stats.get('unique_authors', 0)}
- Average comment score: {stats.get('avg_comment_score', 0)}
- OP replies: {stats.get('op_replies', 0)}
- Controversial comments: {stats.get('controversial_count', 0)}

## Top Comments
"""
        for i, c in enumerate(analysis.get('top_comments', [])[:5], 1):
            output += f"\n### {i}. u/{c.get('author', 'N/A')} (score: {c.get('score', 0)})\n"
            output += f"{c.get('body', '')[:500]}\n"

        output += "\n## All Comments (for analysis)\n"
        for c in comments[:50]:  # Limit to 50 for context window
            indent = "  " * c.get('depth', 0)
            output += f"{indent}[{c.get('score', 0)}] u/{c.get('author', 'N/A')}: {c.get('body', '')[:200]}\n"

        return output

    elif analysis_type == 'subreddit':
        stats = analysis.get('stats', {})

        output = f"""# Subreddit Analysis: r/{analysis.get('subreddit', 'N/A')}

## Sort: {analysis.get('sort', 'hot')}
## Fetched: {analysis.get('fetched_at', 'N/A')}

## Stats
- Posts analyzed: {stats.get('total_posts', 0)}
- Average score: {stats.get('avg_score', 0)}
- Max score: {stats.get('max_score', 0)}
- Average comments: {stats.get('avg_comments', 0)}

## Trending Words
{', '.join(f'{word}({count})' for word, count in stats.get('trending_words', []))}

## Top Posts
"""
        for i, p in enumerate(analysis.get('top_posts', [])[:10], 1):
            output += f"\n### {i}. {p.get('title', 'N/A')}\n"
            output += f"- Score: {p.get('score', 0)} | Comments: {p.get('num_comments', 0)}\n"
            output += f"- Author: u/{p.get('author', 'N/A')} | Flair: {p.get('flair', 'None')}\n"
            if p.get('selftext'):
                output += f"- Preview: {p.get('selftext', '')[:200]}...\n"

        output += "\n## All Posts\n"
        for p in analysis.get('posts', []):
            output += f"- [{p.get('score', 0)}] {p.get('title', 'N/A')[:100]}\n"

        return output

    return str(analysis)


def analyze_with_claude(content: str, prompt: str, api_key: Optional[str] = None) -> str:
    """
    Analyze Reddit content with Claude.

    Args:
        content: Formatted Reddit content
        prompt: Analysis prompt
        api_key: Anthropic API key (uses env var if not provided)

    Returns:
        Claude's analysis
    """
    api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return "ERROR: No API key. Set ANTHROPIC_API_KEY or pass api_key parameter."

    import urllib.request

    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01'
    }

    data = {
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 4096,
        'messages': [
            {
                'role': 'user',
                'content': f"{prompt}\n\n---\n\n{content}"
            }
        ]
    }

    req = Request(
        'https://api.anthropic.com/v1/messages',
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    try:
        with urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['content'][0]['text']
    except Exception as e:
        return f"ERROR: {str(e)}"


def save_analysis(analysis: dict, name: str, analysis_type: str = 'thread'):
    """Save analysis to BRAIN/INTEL/reddit/"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{analysis_type}_{name}_{timestamp}.json"
    filepath = INTEL_DIR / filename

    with open(filepath, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"Saved: {filepath}")
    return filepath


# ============================================================
# SPECIALIZED ANALYZERS FOR MONEY-MAKING SUBREDDITS
# ============================================================

def analyze_wsb(limit: int = 25) -> dict:
    """
    Analyze r/wallstreetbets for trading signals.

    Extracts:
    - Ticker mentions
    - Sentiment (bullish/bearish)
    - DD posts
    - YOLO positions
    """
    analysis = analyze_subreddit('wallstreetbets', sort='hot', limit=limit)

    # Extract ticker symbols (basic pattern: $XXX or standalone uppercase 2-5 letters)
    import re
    tickers = {}
    sentiment = {'bullish': 0, 'bearish': 0, 'neutral': 0}

    bullish_words = ['buy', 'calls', 'moon', 'rocket', 'bullish', 'green', 'long', 'yolo', 'tendies', 'gains', 'lambo', 'ath', 'pump', 'rip', 'diamond hands']
    bearish_words = ['sell', 'puts', 'crash', 'bearish', 'red', 'short', 'dump', 'drill', 'tank', 'rug', 'bag', 'loss', 'paper hands', 'plunge']

    # Comprehensive stopwords - common English words that look like tickers
    stopwords = {
        # 2-letter words (CRITICAL - these are NOT tickers)
        'TO', 'OF', 'IS', 'IN', 'IT', 'AT', 'MY', 'ON', 'OR', 'AN', 'AS', 'BE',
        'BY', 'DO', 'GO', 'HE', 'IF', 'ME', 'NO', 'SO', 'UP', 'WE', 'AM', 'US',
        # Common 3-4 letter words
        'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAD',
        'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'HAS', 'HIS', 'HOW', 'ITS', 'LET',
        'MAY', 'NEW', 'NOW', 'OLD', 'OWN', 'SAY', 'SHE', 'TOO', 'USE', 'WAY',
        'WHO', 'BOY', 'DID', 'GET', 'HIM', 'INTO', 'JUST', 'MAKE', 'MOST',
        'MUCH', 'ONLY', 'OVER', 'SUCH', 'THAN', 'THEM', 'THEN', 'VERY', 'WILL',
        'WITH', 'ALSO', 'BACK', 'BEEN', 'CAME', 'COME', 'COULD', 'EACH', 'FROM',
        'GOOD', 'HAVE', 'HERE', 'JUST', 'KNOW', 'LIKE', 'LOOK', 'MORE', 'NEED',
        'SOME', 'TAKE', 'THAT', 'THIS', 'WANT', 'WHAT', 'WHEN', 'WHERE', 'WHICH',
        'WHILE', 'WOULD', 'YEAR', 'YOUR', 'AFTER', 'BEING', 'COULD', 'EVERY',
        'FIRST', 'FOUND', 'GREAT', 'GOING', 'HOUSE', 'LARGE', 'LITTLE', 'LONG',
        'MADE', 'MANY', 'MIGHT', 'NEVER', 'OTHER', 'PEOPLE', 'PLACE', 'REALLY',
        'RIGHT', 'SAID', 'SAME', 'SHOULD', 'STILL', 'THING', 'THINK', 'THOSE',
        'THROUGH', 'TIME', 'UNDER', 'USED', 'WELL', 'WORK', 'WORLD', 'DOWN',
        'ABOUT', 'STOCK', 'STOCKS', 'MONEY', 'MARKET', 'TODAY', 'WEEK', 'HTTPS',
        'WWW', 'HTTP', 'HTML', 'ANY', 'DAY', 'WAY', 'SEE', 'EVEN', 'LAST',
        'NEXT', 'ONLY', 'BEEN', 'WERE', 'THAN', 'THEY', 'THEIR', 'THERE',
        # Reddit/WSB specific
        'WSB', 'YOLO', 'MOON', 'POST', 'EDIT', 'UPDATE', 'TLDR', 'LINK', 'MODS',
        'FLAIR', 'DAILY', 'WEEKLY', 'THREAD', 'MEGA', 'LOSS', 'GAIN', 'PORN',
        'HOLD', 'HODL', 'APES', 'TENDIES', 'CALLS', 'PUTS', 'BRRR', 'STONKS',
        'DD', 'TA', 'FA', 'IV', 'OI', 'ATH', 'ATL', 'EOD', 'EOW', 'EOM', 'EOY',
        'FD', 'ITM', 'OTM', 'ATM', 'DTE', 'LEAPS', 'YEET', 'RIP', 'GUH',
        # Common abbreviations
        'COM', 'ORG', 'NET', 'EDU', 'GOV', 'USD', 'EUR', 'GBP', 'JPY', 'CAD',
        'AUD', 'NZD', 'CHF', 'CNY', 'HKD', 'SGD', 'BTC', 'ETH', 'USA', 'UK',
        'EU', 'UK', 'US', 'API', 'CEO', 'CFO', 'COO', 'CTO', 'IPO', 'SEC',
        'FED', 'GDP', 'CPI', 'PPI', 'NFP', 'FOMC', 'DOJ', 'FBI', 'CIA', 'NSA',
        'IMF', 'WHO', 'WTO', 'NATO', 'UN', 'EU', 'UK', 'ETF', 'IRA', 'K',
        'LOL', 'OMG', 'WTF', 'LMAO', 'IMHO', 'TBH', 'FYI', 'FOMO', 'DYOR',
        # Days/Months
        'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN',
        'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
        # More common words caught in uppercase
        'GT', 'LT', 'AMP', 'REDDIT', 'JUST', 'BEST', 'EVER', 'LIFE', 'REAL',
        'NEED', 'HELP', 'FREE', 'STOP', 'SELL', 'BUY', 'CALL', 'PUT', 'PLAY',
    }

    for post in analysis['posts']:
        text = f"{post['title']} {post.get('selftext', '')}".upper()

        # Find tickers with $ prefix (most reliable)
        dollar_tickers = re.findall(r'\$([A-Z]{1,5})\b', text)

        # Find standalone potential tickers (2-5 uppercase, surrounded by non-letters)
        # More conservative pattern
        potential_tickers = re.findall(r'(?<![A-Za-z])([A-Z]{2,5})(?![A-Za-z])', text)

        # Combine, prioritizing $-prefixed
        for ticker in dollar_tickers:
            if ticker not in stopwords and len(ticker) >= 1:
                tickers[ticker] = tickers.get(ticker, 0) + 2  # Weight $-prefixed higher

        for ticker in potential_tickers:
            if ticker not in stopwords and len(ticker) >= 2:
                # Only count if it looks like a real ticker (not all caps word)
                tickers[ticker] = tickers.get(ticker, 0) + 1

        # Sentiment analysis
        text_lower = text.lower()
        bull_count = sum(1 for w in bullish_words if w in text_lower)
        bear_count = sum(1 for w in bearish_words if w in text_lower)

        if bull_count > bear_count:
            sentiment['bullish'] += 1
        elif bear_count > bull_count:
            sentiment['bearish'] += 1
        else:
            sentiment['neutral'] += 1

    # Sort tickers by mention count, filter out low counts
    top_tickers = [(t, c) for t, c in sorted(tickers.items(), key=lambda x: x[1], reverse=True) if c >= 2][:15]

    analysis['wsb_analysis'] = {
        'top_tickers': top_tickers,
        'sentiment': sentiment,
        'sentiment_ratio': round(sentiment['bullish'] / max(sentiment['bearish'], 1), 2),
        'dd_posts': [p for p in analysis['posts'] if p.get('flair') and 'DD' in p.get('flair', '').upper()],
        'yolo_posts': [p for p in analysis['posts'] if 'YOLO' in p.get('title', '').upper()]
    }

    return analysis


def analyze_ai_trends(limit: int = 25) -> dict:
    """
    Analyze AI subreddits for technology trends.

    Tracks:
    - Emerging technologies
    - Company mentions
    - Sentiment about AI safety
    - New tools/frameworks
    """
    subreddits = ['artificial', 'MachineLearning', 'LocalLLaMA']
    all_posts = []

    for sub in subreddits:
        try:
            analysis = analyze_subreddit(sub, sort='hot', limit=limit)
            for post in analysis['posts']:
                post['source_subreddit'] = sub
            all_posts.extend(analysis['posts'])
        except Exception as e:
            print(f"Warning: Could not fetch r/{sub}: {e}")

    # Extract AI tech mentions
    tech_keywords = {
        'models': ['gpt', 'claude', 'gemini', 'llama', 'mistral', 'falcon', 'qwen', 'deepseek'],
        'companies': ['openai', 'anthropic', 'google', 'meta', 'microsoft', 'nvidia', 'huggingface'],
        'concepts': ['agi', 'alignment', 'reasoning', 'multimodal', 'agents', 'rag', 'finetuning'],
        'tools': ['langchain', 'llamaindex', 'ollama', 'vllm', 'gguf', 'ggml']
    }

    mentions = {cat: {} for cat in tech_keywords}

    for post in all_posts:
        text = f"{post['title']} {post.get('selftext', '')}".lower()
        for category, keywords in tech_keywords.items():
            for kw in keywords:
                if kw in text:
                    mentions[category][kw] = mentions[category].get(kw, 0) + 1

    # Sort by frequency
    for cat in mentions:
        mentions[cat] = sorted(mentions[cat].items(), key=lambda x: x[1], reverse=True)

    return {
        'subreddits': subreddits,
        'total_posts': len(all_posts),
        'posts': sorted(all_posts, key=lambda x: x['score'], reverse=True)[:20],
        'tech_mentions': mentions,
        'hot_topics': [p for p in all_posts if p['score'] > 100][:10],
        'fetched_at': datetime.now().isoformat()
    }


def analyze_startups(limit: int = 25) -> dict:
    """
    Analyze startup subreddits for opportunity detection.

    Finds:
    - Pain points people are expressing
    - Failed solutions (opportunity gaps)
    - Trending business ideas
    - Funding news
    """
    subreddits = ['startups', 'SaaS', 'Entrepreneur', 'indiehackers']
    all_posts = []

    for sub in subreddits:
        try:
            analysis = analyze_subreddit(sub, sort='hot', limit=limit)
            for post in analysis['posts']:
                post['source_subreddit'] = sub
            all_posts.extend(analysis['posts'])
        except Exception as e:
            print(f"Warning: Could not fetch r/{sub}: {e}")

    # Categorize posts
    pain_keywords = ['problem', 'struggle', 'difficult', 'frustrat', 'hate', 'annoying', 'issue', 'help', 'stuck']
    opportunity_keywords = ['idea', 'launch', 'built', 'created', 'making', 'revenue', 'mrr', 'customers']

    pain_points = []
    opportunities = []
    launches = []

    for post in all_posts:
        text = f"{post['title']} {post.get('selftext', '')}".lower()

        if any(kw in text for kw in pain_keywords):
            pain_points.append(post)
        if any(kw in text for kw in opportunity_keywords):
            opportunities.append(post)
        if 'launch' in text or 'ship' in text or 'live' in text:
            launches.append(post)

    return {
        'subreddits': subreddits,
        'total_posts': len(all_posts),
        'pain_points': sorted(pain_points, key=lambda x: x['score'], reverse=True)[:10],
        'opportunities': sorted(opportunities, key=lambda x: x['score'], reverse=True)[:10],
        'recent_launches': sorted(launches, key=lambda x: x['score'], reverse=True)[:10],
        'top_discussions': sorted(all_posts, key=lambda x: x['num_comments'], reverse=True)[:10],
        'fetched_at': datetime.now().isoformat()
    }


# ============================================================
# CLI INTERFACE
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='Reddit JSON Intelligence System - Extract and analyze Reddit data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a specific thread
  python reddit_intelligence.py thread https://reddit.com/r/wallstreetbets/comments/xxx

  # Analyze a subreddit
  python reddit_intelligence.py subreddit wallstreetbets --sort hot --limit 50

  # Trading signals from WSB
  python reddit_intelligence.py wsb

  # AI technology trends
  python reddit_intelligence.py ai-trends

  # Startup opportunities
  python reddit_intelligence.py startups

  # Analyze with Claude
  python reddit_intelligence.py thread URL --analyze "Extract key trading signals"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Thread command
    thread_parser = subparsers.add_parser('thread', help='Analyze a Reddit thread')
    thread_parser.add_argument('url', help='Reddit thread URL')
    thread_parser.add_argument('--analyze', help='Analyze with Claude using this prompt')
    thread_parser.add_argument('--save', action='store_true', help='Save analysis to file')
    thread_parser.add_argument('--json', action='store_true', help='Output raw JSON')

    # Subreddit command
    sub_parser = subparsers.add_parser('subreddit', help='Analyze a subreddit')
    sub_parser.add_argument('name', help='Subreddit name (without r/)')
    sub_parser.add_argument('--sort', default='hot', choices=['hot', 'new', 'top', 'rising'])
    sub_parser.add_argument('--limit', type=int, default=25, help='Number of posts')
    sub_parser.add_argument('--analyze', help='Analyze with Claude using this prompt')
    sub_parser.add_argument('--save', action='store_true', help='Save analysis to file')
    sub_parser.add_argument('--json', action='store_true', help='Output raw JSON')

    # WSB command
    wsb_parser = subparsers.add_parser('wsb', help='Trading signals from r/wallstreetbets')
    wsb_parser.add_argument('--limit', type=int, default=50, help='Number of posts')
    wsb_parser.add_argument('--analyze', action='store_true', help='Deep analyze with Claude')
    wsb_parser.add_argument('--save', action='store_true', help='Save analysis to file')

    # AI trends command
    ai_parser = subparsers.add_parser('ai-trends', help='AI technology trends')
    ai_parser.add_argument('--limit', type=int, default=25, help='Posts per subreddit')
    ai_parser.add_argument('--analyze', action='store_true', help='Deep analyze with Claude')
    ai_parser.add_argument('--save', action='store_true', help='Save analysis to file')

    # Startups command
    startup_parser = subparsers.add_parser('startups', help='Startup opportunity detection')
    startup_parser.add_argument('--limit', type=int, default=25, help='Posts per subreddit')
    startup_parser.add_argument('--analyze', action='store_true', help='Deep analyze with Claude')
    startup_parser.add_argument('--save', action='store_true', help='Save analysis to file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'thread':
        print(f"Fetching thread: {args.url}")
        analysis = analyze_thread(args.url)

        if args.json:
            print(json.dumps(analysis, indent=2))
        else:
            formatted = format_for_llm(analysis, 'thread')
            print(formatted)

            if args.analyze:
                print("\n--- Claude Analysis ---\n")
                result = analyze_with_claude(formatted, args.analyze)
                print(result)

        if args.save:
            name = analysis['post'].get('id', 'unknown')
            save_analysis(analysis, name, 'thread')

    elif args.command == 'subreddit':
        print(f"Fetching r/{args.name} ({args.sort})...")
        analysis = analyze_subreddit(args.name, sort=args.sort, limit=args.limit)

        if args.json:
            print(json.dumps(analysis, indent=2))
        else:
            formatted = format_for_llm(analysis, 'subreddit')
            print(formatted)

            if args.analyze:
                print("\n--- Claude Analysis ---\n")
                result = analyze_with_claude(formatted, args.analyze)
                print(result)

        if args.save:
            save_analysis(analysis, args.name, 'subreddit')

    elif args.command == 'wsb':
        print("Analyzing r/wallstreetbets for trading signals...")
        analysis = analyze_wsb(limit=args.limit)

        print("\n=== WSB Trading Intelligence ===\n")
        print(f"Sentiment Ratio (bull/bear): {analysis['wsb_analysis']['sentiment_ratio']}")
        print(f"Sentiment: {analysis['wsb_analysis']['sentiment']}")
        print(f"\nTop Tickers Mentioned:")
        for ticker, count in analysis['wsb_analysis']['top_tickers']:
            print(f"  ${ticker}: {count} mentions")

        print(f"\nDD Posts: {len(analysis['wsb_analysis']['dd_posts'])}")
        print(f"YOLO Posts: {len(analysis['wsb_analysis']['yolo_posts'])}")

        if args.analyze:
            formatted = format_for_llm(analysis, 'subreddit')
            prompt = """Analyze this WSB data for actionable trading signals:
1. Which tickers have the strongest bullish sentiment?
2. Are there any contrarian opportunities (heavily discussed but bearish)?
3. What's the overall market sentiment?
4. Any notable DD worth investigating?
5. Risk assessment of following WSB sentiment."""
            print("\n--- Claude Trading Analysis ---\n")
            result = analyze_with_claude(formatted, prompt)
            print(result)

        if args.save:
            save_analysis(analysis, 'wsb', 'trading')

    elif args.command == 'ai-trends':
        print("Analyzing AI subreddits for technology trends...")
        analysis = analyze_ai_trends(limit=args.limit)

        print("\n=== AI Technology Trends ===\n")
        for category, items in analysis['tech_mentions'].items():
            if items:
                print(f"\n{category.upper()}:")
                for item, count in items[:5]:
                    print(f"  {item}: {count} mentions")

        print(f"\nHot Topics ({len(analysis['hot_topics'])} posts with 100+ score):")
        for post in analysis['hot_topics'][:5]:
            print(f"  - [{post['source_subreddit']}] {post['title'][:60]}...")

        if args.analyze:
            prompt = """Analyze these AI trends for strategic insights:
1. What technologies are gaining momentum?
2. What concerns are the community expressing?
3. What opportunities exist for builders?
4. What's overhyped vs underappreciated?
5. Key takeaways for an AI company."""
            formatted = json.dumps(analysis, indent=2)
            print("\n--- Claude Trend Analysis ---\n")
            result = analyze_with_claude(formatted, prompt)
            print(result)

        if args.save:
            save_analysis(analysis, 'ai-trends', 'trends')

    elif args.command == 'startups':
        print("Analyzing startup subreddits for opportunities...")
        analysis = analyze_startups(limit=args.limit)

        print("\n=== Startup Opportunity Detection ===\n")

        print("Pain Points (problems people are expressing):")
        for post in analysis['pain_points'][:5]:
            print(f"  - [{post['source_subreddit']}] {post['title'][:60]}...")

        print("\nRecent Launches:")
        for post in analysis['recent_launches'][:5]:
            print(f"  - [{post['source_subreddit']}] {post['title'][:60]}...")

        print("\nMost Discussed:")
        for post in analysis['top_discussions'][:5]:
            print(f"  - [{post['num_comments']} comments] {post['title'][:60]}...")

        if args.analyze:
            prompt = """Analyze these startup discussions for business opportunities:
1. What pain points represent viable business opportunities?
2. What gaps exist in current solutions?
3. What types of products are getting traction?
4. What mistakes are founders making?
5. Identify 3 concrete startup ideas from these discussions."""
            formatted = json.dumps(analysis, indent=2)
            print("\n--- Claude Opportunity Analysis ---\n")
            result = analyze_with_claude(formatted, prompt)
            print(result)

        if args.save:
            save_analysis(analysis, 'startups', 'opportunities')


if __name__ == '__main__':
    main()
