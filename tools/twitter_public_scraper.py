"""
SØWL Twitter Public Feed Scraper
Scrapes public profiles and tweets using ScrapFly
"""

import json
import os
from datetime import datetime
from scrapfly import ScrapflyClient, ScrapeConfig

# Config
SCRAPFLY_API_KEY = os.getenv('SCRAPFLY_API_KEY', 'scp-live-43f2e69fc0cc40fdbd4b4112895f5378')
OUTPUT_DIR = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/twitter_feeds'

# Accounts to monitor (AI/Claude focused)
ACCOUNTS_TO_FOLLOW = [
    'AnthropicAI',
    'alexalbert__',  # Alex Albert - Anthropic
    'daboris',       # Dario Amodei
    'aaboris',       # Amanda Askell
    'sama',          # Sam Altman
    'kaboris',       # Karpathy
    'ylecun',        # Yann LeCun
    'DrJimFan',      # Jim Fan - NVIDIA AI
    'EMostaque',     # Emad - Stability
    'svpino',        # Santiago Valdarrama - AI educator
    'bindureddy',    # Bindu Reddy - Abacus AI
    'qdrant_engine', # Qdrant - vector DB
    'LangChainAI',   # LangChain
    'llaboris',      # Llama/Meta AI
]

# Search terms for discovery
SEARCH_TERMS = [
    'Claude Code',
    'Claude API',
    'Anthropic',
    'AI agents',
    'multi-agent',
    'swarm AI',
    'voice AI',
    'AGI',
]


def scrape_profile(client, username):
    """Scrape a Twitter profile"""
    try:
        result = client.scrape(ScrapeConfig(
            url=f'https://twitter.com/{username}',
            render_js=True,
            asp=True,  # Anti-scraping protection
            country='us',
        ))
        return {
            'username': username,
            'html': result.content[:5000],  # First 5000 chars for analysis
            'scraped_at': datetime.now().isoformat(),
            'success': True
        }
    except Exception as e:
        return {
            'username': username,
            'error': str(e),
            'scraped_at': datetime.now().isoformat(),
            'success': False
        }


def scrape_search(client, query):
    """Scrape Twitter search results"""
    try:
        result = client.scrape(ScrapeConfig(
            url=f'https://twitter.com/search?q={query}&src=typed_query&f=live',
            render_js=True,
            asp=True,
            country='us',
        ))
        return {
            'query': query,
            'html': result.content[:10000],
            'scraped_at': datetime.now().isoformat(),
            'success': True
        }
    except Exception as e:
        return {
            'query': query,
            'error': str(e),
            'scraped_at': datetime.now().isoformat(),
            'success': False
        }


def run_scrape():
    """Main scraping function"""
    client = ScrapflyClient(key=SCRAPFLY_API_KEY)

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    results = {
        'run_at': datetime.now().isoformat(),
        'profiles': [],
        'searches': []
    }

    print(f"Starting scrape at {results['run_at']}")

    # Scrape key profiles (limit to conserve credits)
    print("\nScraping profiles...")
    for username in ACCOUNTS_TO_FOLLOW[:5]:  # First 5 to test
        print(f"  Scraping @{username}...")
        profile_data = scrape_profile(client, username)
        results['profiles'].append(profile_data)
        if profile_data['success']:
            print(f"    ✓ Success")
        else:
            print(f"    ✗ Failed: {profile_data.get('error', 'Unknown')}")

    # Scrape search terms
    print("\nScraping searches...")
    for term in SEARCH_TERMS[:3]:  # First 3 to test
        print(f"  Searching '{term}'...")
        search_data = scrape_search(client, term)
        results['searches'].append(search_data)
        if search_data['success']:
            print(f"    ✓ Success")
        else:
            print(f"    ✗ Failed: {search_data.get('error', 'Unknown')}")

    # Save results
    output_file = os.path.join(OUTPUT_DIR, f'scrape_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_file}")
    print(f"Profiles scraped: {len([p for p in results['profiles'] if p['success']])}/{len(results['profiles'])}")
    print(f"Searches scraped: {len([s for s in results['searches'] if s['success']])}/{len(results['searches'])}")

    return results


if __name__ == '__main__':
    run_scrape()
