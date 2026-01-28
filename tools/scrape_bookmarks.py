#!/usr/bin/env python3
"""
Direct bookmark scraper using Playwright
Logs in to X and extracts all bookmarks
MORE ROBUST VERSION - handles X's varying login flow
"""
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

USERNAME = "AaronJNosbisch"
PASSWORD = "seRTuptl1!"
BOOKMARKS_URL = "https://x.com/i/bookmarks"
OUTPUT_PATH = "/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/twitter_bookmarks.json"

def scrape_bookmarks():
    print("Starting Playwright browser...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Go to Twitter login
        print("Navigating to X login...")
        page.goto("https://x.com/i/flow/login", wait_until="networkidle")
        time.sleep(3)

        # Enter username - try multiple selectors
        print("Looking for username field...")
        try:
            page.wait_for_selector('input[autocomplete="username"]', timeout=10000)
            page.fill('input[autocomplete="username"]', USERNAME)
            print(f"Entered username: {USERNAME}")
        except:
            # Try alternative selector
            page.fill('input[name="text"]', USERNAME)
            print(f"Entered username (alt): {USERNAME}")

        # Click Next
        time.sleep(1)
        page.click('text=Next')
        print("Clicked Next...")
        time.sleep(3)

        # Check if there's an intermediate step (phone/email verification)
        try:
            # Sometimes X asks for phone or email to verify
            verify_input = page.query_selector('input[data-testid="ocfEnterTextTextInput"]')
            if verify_input:
                print("\n" + "="*50)
                print("X is asking for additional verification!")
                print("Please enter your phone or email in the browser window")
                print("Then press Enter here when done...")
                print("="*50)
                input()
                time.sleep(2)
        except:
            pass

        # Enter password - wait longer and try multiple selectors
        print("Looking for password field...")
        try:
            page.wait_for_selector('input[type="password"]', timeout=15000)
            page.fill('input[type="password"]', PASSWORD)
            print("Entered password")
        except:
            print("\n" + "="*50)
            print("Password field not found automatically.")
            print("Please enter your password manually in the browser,")
            print("then press Enter here to continue...")
            print("="*50)
            input()

        # Click Log in
        time.sleep(1)
        try:
            page.click('text=Log in')
            print("Clicked Log in...")
        except:
            page.click('[data-testid="LoginForm_Login_Button"]')

        time.sleep(5)

        # Check if we need to handle 2FA or other challenges
        print("\nIf you see any verification prompts, complete them in the browser.")
        print("Press Enter when you're logged in and ready to scrape bookmarks...")
        input()

        # Navigate to bookmarks
        print("Going to bookmarks...")
        page.goto(BOOKMARKS_URL, wait_until="networkidle")
        time.sleep(3)

        # Scroll and collect tweets
        print("Scrolling to load all bookmarks...")
        bookmarks = []
        seen_texts = set()
        scroll_count = 0
        max_scrolls = 100  # More scrolls to get everything
        no_new_count = 0

        while scroll_count < max_scrolls:
            # Extract visible tweets
            tweets = page.query_selector_all('[data-testid="tweet"]')
            new_found = 0

            for tweet in tweets:
                try:
                    text_elem = tweet.query_selector('[data-testid="tweetText"]')
                    text = text_elem.inner_text() if text_elem else ""

                    if text and text not in seen_texts:
                        seen_texts.add(text)
                        new_found += 1

                        # Try to get author
                        author_elem = tweet.query_selector('[data-testid="User-Name"]')
                        author = author_elem.inner_text() if author_elem else "Unknown"

                        # Try to get link
                        link_elem = tweet.query_selector('a[href*="/status/"]')
                        link = link_elem.get_attribute('href') if link_elem else ""
                        if link and not link.startswith('http'):
                            link = f"https://x.com{link}"

                        bookmarks.append({
                            'text': text,
                            'author': author,
                            'url': link,
                            'scraped_at': datetime.now().isoformat()
                        })
                        print(f"[{len(bookmarks)}] {author.split()[0] if author else 'Unknown'}: {text[:60]}...")
                except Exception as e:
                    continue

            # Scroll down
            page.evaluate("window.scrollBy(0, 1000)")
            time.sleep(1.5)
            scroll_count += 1

            # Check if we've reached the end
            if new_found == 0:
                no_new_count += 1
                if no_new_count >= 5:
                    print("No new tweets found after 5 scrolls - reached end")
                    break
            else:
                no_new_count = 0

            if scroll_count % 10 == 0:
                print(f"Scrolled {scroll_count} times, found {len(bookmarks)} bookmarks so far...")

        browser.close()

        # Save results
        output = {
            'exported_at': datetime.now().isoformat(),
            'total_bookmarks': len(bookmarks),
            'bookmarks': bookmarks
        }

        with open(OUTPUT_PATH, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n{'='*50}")
        print(f"SUCCESS! Exported {len(bookmarks)} bookmarks")
        print(f"Saved to: {OUTPUT_PATH}")
        print(f"{'='*50}\n")

        return bookmarks

if __name__ == "__main__":
    scrape_bookmarks()
