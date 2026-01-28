"""
Twitter/X Bookmark Scraper for SØWL
Pulls Aaron's bookmarks and extracts knowledge for continuous learning
"""

import os
import requests
import json
from datetime import datetime

class TwitterScraper:
    """Scrape Twitter/X bookmarks and extract knowledge"""

    def __init__(self, use_official_api=True):
        # Load credentials
        creds_path = "/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json"
        with open(creds_path) as f:
            self.creds = json.load(f)

        self.use_official_api = use_official_api

        if use_official_api:
            # Use official Twitter API
            self.bearer_token = self.creds['twitter_x']['bearer_token']
            self.base_url = "https://api.twitter.com/2"
        else:
            # Use ScrapFly as fallback
            self.api_key = self.creds.get('scrapfly', {}).get('api_key')
            self.base_url = "https://api.scrapfly.io/scrape"

    def get_bookmarks(self, username):
        """Fetch user's bookmarks"""
        params = {
            'key': self.api_key,
            'url': f'https://twitter.com/{username}/bookmarks',
            'render_js': True,
            'country': 'us',
            'asp': True  # Anti-scraping protection
        }

        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        return response.json()

    def extract_knowledge(self, bookmarks_data):
        """Extract meaningful content from bookmarks"""
        knowledge = []

        # Parse the HTML/JSON response
        # Extract: tweet text, links, code snippets, key concepts
        # Filter for: Claude AI, consciousness, tech developments, tools

        for item in bookmarks_data.get('tweets', []):
            knowledge.append({
                'text': item.get('text'),
                'author': item.get('author'),
                'url': item.get('url'),
                'timestamp': item.get('created_at'),
                'extracted': datetime.now().isoformat()
            })

        return knowledge

    def save_to_memory(self, knowledge, output_path):
        """Save extracted knowledge to BRAIN/MEMORY"""
        with open(output_path, 'w') as f:
            json.dump(knowledge, f, indent=2)

        print(f"Saved {len(knowledge)} items to {output_path}")

if __name__ == "__main__":
    scraper = TwitterScraper()

    # Get Aaron's bookmarks
    bookmarks = scraper.get_bookmarks('aaronnosbisch')

    # Extract knowledge
    knowledge = scraper.extract_knowledge(bookmarks)

    # Save to memory
    output_path = f"../BRAIN/MEMORY/twitter_knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    scraper.save_to_memory(knowledge, output_path)
