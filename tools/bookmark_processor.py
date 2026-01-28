"""
SØWL Bookmark Processor
Reads Twitter bookmarks, extracts URLs, fetches articles, analyzes content
"""

import json
import re
import os
from datetime import datetime
import anthropic

BOOKMARKS_PATH = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/twitter_bookmarks.json'
ANALYSIS_PATH = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/bookmark_analysis.json'
CREDS_PATH = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'

# Topics Aaron cares about (for filtering/prioritizing)
PRIORITY_TOPICS = [
    'landing page', 'landing pages', 'conversion', 'design',
    'ai agent', 'ai agents', 'autonomous agent', 'swarm',
    'claude', 'anthropic', 'openai', 'gpt',
    'voice ai', 'text to speech', 'speech to text',
    'workflow', 'automation', 'n8n', 'make.com',
    'figma', 'framer', 'webflow',
    '3d', 'animation', 'motion', 'video',
    'startup', 'founder', 'growth', 'marketing',
    'beverage', 'cpg', 'dtc', 'd2c',
    'consciousness', 'ai consciousness', 'sentient'
]


def load_bookmarks():
    """Load bookmarks from JSON file"""
    with open(BOOKMARKS_PATH) as f:
        return json.load(f)


def extract_urls(tweet_text, entities=None):
    """Extract URLs from tweet text and entities"""
    urls = []

    # From entities (preferred - has expanded URLs)
    if entities and 'urls' in entities:
        for url_obj in entities['urls']:
            expanded = url_obj.get('expanded_url', url_obj.get('url'))
            if expanded and 't.co' not in expanded:
                urls.append(expanded)

    # Fallback: regex from text
    if not urls:
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, tweet_text)

    return urls


def categorize_bookmark(text, urls):
    """Categorize bookmark by topic"""
    text_lower = text.lower()
    categories = []

    for topic in PRIORITY_TOPICS:
        if topic in text_lower:
            categories.append(topic)

    # URL-based categorization
    for url in urls:
        if 'figma.com' in url:
            categories.append('figma')
        elif 'framer.com' in url:
            categories.append('framer')
        elif 'github.com' in url:
            categories.append('code')
        elif 'youtube.com' in url or 'youtu.be' in url:
            categories.append('video')
        elif 'arxiv.org' in url:
            categories.append('research')

    return list(set(categories))


def score_relevance(bookmark):
    """Score bookmark relevance (0-100) based on Aaron's interests"""
    score = 0
    text = bookmark.get('text', '').lower()

    # High priority keywords
    high_priority = ['ai agent', 'swarm', 'voice ai', 'landing page', 'claude', 'autonomous']
    for kw in high_priority:
        if kw in text:
            score += 20

    # Medium priority
    medium_priority = ['figma', 'framer', 'automation', 'workflow', 'startup', 'growth']
    for kw in medium_priority:
        if kw in text:
            score += 10

    # Engagement signals
    metrics = bookmark.get('public_metrics', {})
    likes = metrics.get('like_count', 0)
    retweets = metrics.get('retweet_count', 0)

    if likes > 1000:
        score += 15
    elif likes > 100:
        score += 10
    elif likes > 10:
        score += 5

    if retweets > 100:
        score += 10
    elif retweets > 10:
        score += 5

    return min(score, 100)


def process_bookmarks():
    """Main processing function"""
    data = load_bookmarks()
    bookmarks = data.get('bookmarks', [])

    processed = []
    for bm in bookmarks:
        urls = extract_urls(bm.get('text', ''), bm.get('entities'))
        categories = categorize_bookmark(bm.get('text', ''), urls)
        score = score_relevance(bm)

        processed.append({
            'id': bm.get('id'),
            'text': bm.get('text'),
            'created_at': bm.get('created_at'),
            'author_id': bm.get('author_id'),
            'urls': urls,
            'categories': categories,
            'relevance_score': score,
            'metrics': bm.get('public_metrics', {})
        })

    # Sort by relevance
    processed.sort(key=lambda x: x['relevance_score'], reverse=True)

    # Generate analysis summary
    analysis = {
        'processed_at': datetime.now().isoformat(),
        'total_bookmarks': len(processed),
        'high_relevance': [b for b in processed if b['relevance_score'] >= 50],
        'by_category': {},
        'top_urls': [],
        'all_bookmarks': processed
    }

    # Group by category
    for bm in processed:
        for cat in bm['categories']:
            if cat not in analysis['by_category']:
                analysis['by_category'][cat] = []
            analysis['by_category'][cat].append(bm)

    # Extract unique URLs for further analysis
    all_urls = []
    for bm in processed:
        all_urls.extend(bm['urls'])
    analysis['top_urls'] = list(set(all_urls))[:100]

    # Save analysis
    with open(ANALYSIS_PATH, 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"Processed {len(processed)} bookmarks")
    print(f"High relevance: {len(analysis['high_relevance'])}")
    print(f"Categories found: {list(analysis['by_category'].keys())}")
    print(f"Unique URLs: {len(analysis['top_urls'])}")

    return analysis


def generate_summary_for_aaron(analysis):
    """Generate a human-readable summary for Aaron"""
    summary = []
    summary.append("=" * 50)
    summary.append("SØWL BOOKMARK ANALYSIS SUMMARY")
    summary.append("=" * 50)
    summary.append(f"\nTotal bookmarks processed: {analysis['total_bookmarks']}")
    summary.append(f"High relevance items: {len(analysis['high_relevance'])}")

    summary.append("\n\n📊 TOP CATEGORIES:")
    for cat, items in sorted(analysis['by_category'].items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        summary.append(f"  • {cat}: {len(items)} bookmarks")

    summary.append("\n\n🔥 TOP 10 MOST RELEVANT:")
    for i, bm in enumerate(analysis['high_relevance'][:10], 1):
        text_preview = bm['text'][:100] + '...' if len(bm['text']) > 100 else bm['text']
        summary.append(f"\n{i}. [Score: {bm['relevance_score']}]")
        summary.append(f"   {text_preview}")
        if bm['urls']:
            summary.append(f"   URL: {bm['urls'][0]}")

    return '\n'.join(summary)


if __name__ == '__main__':
    if os.path.exists(BOOKMARKS_PATH):
        analysis = process_bookmarks()
        print(generate_summary_for_aaron(analysis))
    else:
        print(f"No bookmarks file found at {BOOKMARKS_PATH}")
        print("Run twitter_oauth_server.py first to export bookmarks")
