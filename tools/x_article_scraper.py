#!/usr/bin/env python3
"""
X Article Scraper using Playwright
Pulls full article content, replies, and linked resources from X
Requires: playwright, run `python3 -m playwright install chromium` first
"""

import json
import asyncio
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

# Paths (dynamic detection)
REPO_ROOT = Path(__file__).parent.parent
BOOKMARKS_PATH = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'twitter_bookmarks.json'
OUTPUT_DIR = REPO_ROOT / 'BRAIN' / 'INTEL' / 'articles'
FULL_CONTEXT_PATH = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'twitter_bookmarks_full_context.json'

# Create output directory
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


async def scrape_tweet_with_context(page, tweet_url):
    """Scrape a tweet and its full context including article content"""
    result = {
        'url': tweet_url,
        'scraped_at': datetime.now().isoformat(),
        'tweet_text': '',
        'author': '',
        'article_content': None,
        'replies': [],
        'media': [],
        'external_links': [],
        'error': None
    }

    try:
        # Navigate to tweet
        await page.goto(tweet_url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(2)  # Let dynamic content load

        # Get main tweet content
        tweet_article = await page.query_selector('article[data-testid="tweet"]')
        if tweet_article:
            tweet_text_elem = await tweet_article.query_selector('[data-testid="tweetText"]')
            if tweet_text_elem:
                result['tweet_text'] = await tweet_text_elem.inner_text()

            # Get author
            author_elem = await tweet_article.query_selector('[data-testid="User-Name"]')
            if author_elem:
                result['author'] = await author_elem.inner_text()

        # Check if this is an X article (long-form content)
        # X articles have a specific URL pattern: x.com/i/article/...
        if '/i/article/' in tweet_url or 'article' in await page.content():
            article_content = await page.query_selector('[data-testid="article-cover-content"]')
            if article_content:
                result['article_content'] = await article_content.inner_text()
            else:
                # Try alternate selectors for article content
                body = await page.query_selector('article')
                if body:
                    result['article_content'] = await body.inner_text()

        # Look for embedded article link in tweet
        article_links = await page.query_selector_all('a[href*="/i/article/"]')
        for link in article_links:
            href = await link.get_attribute('href')
            if href and '/i/article/' in href:
                # Navigate to article
                if not href.startswith('http'):
                    href = f'https://x.com{href}'
                await page.goto(href, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(2)

                # Get full article text
                article_body = await page.query_selector('[data-testid="article-cover-content"]')
                if article_body:
                    result['article_content'] = await article_body.inner_text()
                else:
                    # Fallback: get all text from main content area
                    main_content = await page.query_selector('main')
                    if main_content:
                        result['article_content'] = await main_content.inner_text()

                # Go back to tweet for replies
                await page.goto(tweet_url, wait_until='networkidle')
                await asyncio.sleep(1)
                break

        # Get replies (first 10)
        reply_articles = await page.query_selector_all('article[data-testid="tweet"]')
        for i, reply in enumerate(reply_articles[1:11]):  # Skip first (main tweet), get up to 10
            reply_text_elem = await reply.query_selector('[data-testid="tweetText"]')
            if reply_text_elem:
                reply_text = await reply_text_elem.inner_text()
                reply_author = await reply.query_selector('[data-testid="User-Name"]')
                author_name = await reply_author.inner_text() if reply_author else 'Unknown'
                result['replies'].append({
                    'author': author_name,
                    'text': reply_text
                })

        # Get media (images/videos)
        media_elems = await page.query_selector_all('[data-testid="tweetPhoto"], video')
        for media in media_elems:
            src = await media.get_attribute('src')
            if src:
                result['media'].append(src)

        # Get external links
        link_cards = await page.query_selector_all('[data-testid="card.wrapper"]')
        for card in link_cards:
            link = await card.query_selector('a')
            if link:
                href = await link.get_attribute('href')
                if href and 't.co' not in href:
                    result['external_links'].append(href)

    except Exception as e:
        result['error'] = str(e)

    return result


async def scrape_all_bookmarks():
    """Scrape full context for all bookmarked tweets"""

    # Load bookmarks
    with open(BOOKMARKS_PATH) as f:
        bookmarks_data = json.load(f)

    bookmarks = bookmarks_data.get('bookmarks', [])
    print(f"Found {len(bookmarks)} bookmarks to process")

    all_results = []

    async with async_playwright() as p:
        # Launch browser with persistent context (uses your logged-in session)
        # You need to be logged into X in Chrome for this to work
        browser = await p.chromium.launch(
            headless=False,  # Set True after testing
            slow_mo=500  # Slow down for rate limiting
        )

        # Use a persistent context to maintain login
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        page = await context.new_page()

        # First, navigate to X and wait for manual login if needed
        print("\n" + "="*50)
        print("IMPORTANT: Make sure you're logged into X")
        print("The browser will open - log in if prompted")
        print("="*50 + "\n")

        await page.goto('https://x.com', wait_until='networkidle')
        await asyncio.sleep(3)

        # Check if logged in
        login_check = await page.query_selector('[data-testid="SideNav_AccountSwitcher_Button"]')
        if not login_check:
            print("Please log in to X in the browser window...")
            print("Press Enter in this terminal when logged in...")
            input()

        total = len(bookmarks)
        for i, bookmark in enumerate(bookmarks, 1):
            tweet_id = bookmark.get('id')
            tweet_url = f'https://x.com/i/status/{tweet_id}'

            print(f"\n[{i}/{total}] Scraping: {tweet_url}")

            result = await scrape_tweet_with_context(page, tweet_url)
            result['original_bookmark'] = bookmark
            all_results.append(result)

            # Save progress every 5 tweets
            if i % 5 == 0:
                print(f"   Saving progress... ({i}/{total})")
                with open(FULL_CONTEXT_PATH, 'w') as f:
                    json.dump({
                        'scraped_at': datetime.now().isoformat(),
                        'total': len(all_results),
                        'bookmarks': all_results
                    }, f, indent=2)

            # Rate limiting
            await asyncio.sleep(2)

        await browser.close()

    # Final save
    with open(FULL_CONTEXT_PATH, 'w') as f:
        json.dump({
            'scraped_at': datetime.now().isoformat(),
            'total': len(all_results),
            'bookmarks': all_results
        }, f, indent=2)

    print(f"\n{'='*50}")
    print(f"COMPLETE! Scraped {len(all_results)} bookmarks with full context")
    print(f"Saved to: {FULL_CONTEXT_PATH}")
    print(f"{'='*50}")

    return all_results


async def scrape_single_url(url):
    """Scrape a single tweet/article URL"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"Scraping: {url}")
        await page.goto('https://x.com', wait_until='networkidle')
        await asyncio.sleep(2)

        # Check login
        login_check = await page.query_selector('[data-testid="SideNav_AccountSwitcher_Button"]')
        if not login_check:
            print("Please log in to X...")
            input("Press Enter when logged in...")

        result = await scrape_tweet_with_context(page, url)
        await browser.close()

        return result


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        # Scrape single URL
        url = sys.argv[1]
        result = asyncio.run(scrape_single_url(url))
        print(json.dumps(result, indent=2))
    else:
        # Scrape all bookmarks
        asyncio.run(scrape_all_bookmarks())
