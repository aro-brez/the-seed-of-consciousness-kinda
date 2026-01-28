#!/usr/bin/env python3
"""
SØWL LAUNCH SEQUENCE
Master script to start all systems
"""

import subprocess
import sys
import os
from pathlib import Path

BASE_DIR = '/Users/aaronnosbisch/LOCAL REPOS/seed'
TOOLS_DIR = f'{BASE_DIR}/tools'

def check_dependencies():
    """Check all required dependencies are installed"""
    print("Checking dependencies...")

    deps = ['anthropic', 'flask', 'requests_oauthlib', 'playwright']
    missing = []

    for dep in deps:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            missing.append(dep)

    if missing:
        print(f"Missing: {', '.join(missing)}")
        print(f"Installing: pip3 install {' '.join(missing)}")
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing)

    # Check Playwright browsers
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch(headless=True).close()
    except Exception as e:
        print("Installing Playwright browsers...")
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'])

    print("All dependencies ready!")


def launch_scraper():
    """Launch the X article scraper in background"""
    print("\nLaunching X Article Scraper...")
    subprocess.Popen(
        [sys.executable, f'{TOOLS_DIR}/x_article_scraper.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print("Scraper running in background")


def launch_trading_loop():
    """Launch the 15-minute trading loop"""
    print("\nLaunching Trading Loop...")
    subprocess.run([sys.executable, f'{TOOLS_DIR}/trading_loop_15min.py'])


def launch_oauth_server():
    """Launch OAuth server for fresh bookmark export"""
    print("\nLaunching OAuth Server on http://localhost:5050...")
    subprocess.Popen(
        [sys.executable, f'{TOOLS_DIR}/twitter_oauth_server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print("OAuth server running - visit http://localhost:5050 to authorize")


def show_status():
    """Show current system status"""
    print("\n" + "="*60)
    print("SØWL SYSTEM STATUS")
    print("="*60)

    # Check files
    files = [
        ('Bookmarks', f'{BASE_DIR}/BRAIN/MEMORY/twitter_bookmarks.json'),
        ('Full Context', f'{BASE_DIR}/BRAIN/MEMORY/twitter_bookmarks_full_context.json'),
        ('Trade History', f'{BASE_DIR}/BRAIN/INTEL/signal_history.json'),
        ('API Keys', f'{BASE_DIR}/BRAIN/MEMORY/secure/api_keys.json'),
    ]

    for name, path in files:
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        status = f"OK ({size//1024}KB)" if exists else "MISSING"
        print(f"  {name}: {status}")

    print("="*60)


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║              SØWL LAUNCH SEQUENCE v2.0                        ║
║                                                               ║
║  1. status  - Show system status                              ║
║  2. deps    - Check/install dependencies                      ║
║  3. oauth   - Start Twitter OAuth server                      ║
║  4. scrape  - Start X article scraper                         ║
║  5. trade   - Start 15-min trading loop                       ║
║  6. all     - Launch everything                               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    if len(sys.argv) < 2:
        cmd = input("Enter command: ").strip().lower()
    else:
        cmd = sys.argv[1].lower()

    if cmd == 'status':
        show_status()
    elif cmd == 'deps':
        check_dependencies()
    elif cmd == 'oauth':
        launch_oauth_server()
    elif cmd == 'scrape':
        launch_scraper()
    elif cmd == 'trade':
        launch_trading_loop()
    elif cmd == 'all':
        check_dependencies()
        show_status()
        launch_oauth_server()
        print("\nWaiting 5s for OAuth server...")
        import time
        time.sleep(5)
        launch_scraper()
        print("\nScraper launched. Starting trading loop in 10s...")
        time.sleep(10)
        launch_trading_loop()
    else:
        print(f"Unknown command: {cmd}")


if __name__ == '__main__':
    main()
