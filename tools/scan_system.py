#!/usr/bin/env python3
"""
SYSTEM SCANNER - Updates SØWL's contextual awareness
Run periodically to refresh SYSTEM-INDEX.md

Usage: python3 scan_system.py
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

HOME = Path.home()
REPOS = HOME / "REPOS"
SEED = REPOS / "seed"
INDEX_FILE = SEED / "BRAIN/MEMORY/SYSTEM-INDEX.md"

def scan():
    print("🔍 Scanning system...")

    # Get folder structure
    repos_folders = sorted([f.name for f in REPOS.iterdir() if f.is_dir() and not f.name.startswith('.')])[:20]
    seed_folders = sorted([f.name for f in SEED.iterdir() if f.is_dir() and not f.name.startswith('.')])[:20]

    # Find all CLAUDE.md files
    result = subprocess.run(
        ['find', str(HOME), '-name', 'CLAUDE.md', '-type', 'f'],
        capture_output=True, text=True, timeout=30
    )
    claude_files = [l for l in result.stdout.strip().split('\n') if l][:15]

    # Get running processes
    result = subprocess.run(
        ['ps', 'aux'],
        capture_output=True, text=True
    )
    processes = [l for l in result.stdout.split('\n') if 'python' in l.lower() or 'nats' in l.lower() or 'daemon' in l.lower()][:10]

    print(f"✅ Found {len(repos_folders)} REPOS folders")
    print(f"✅ Found {len(seed_folders)} seed folders")
    print(f"✅ Found {len(claude_files)} CLAUDE.md files")
    print(f"✅ Found {len(processes)} relevant processes")

    # Update timestamp in index
    if INDEX_FILE.exists():
        content = INDEX_FILE.read_text()
        # Update scan timestamp
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('**Last Scan:**'):
                lines[i] = f'**Last Scan:** {datetime.now().strftime("%Y-%m-%d %H:%M EST")}'
                break
        INDEX_FILE.write_text('\n'.join(lines))
        print(f"✅ Updated {INDEX_FILE}")

    print("\n📋 REPOS folders:", repos_folders[:10])
    print("📋 seed folders:", seed_folders[:10])

    return {
        'repos': repos_folders,
        'seed': seed_folders,
        'claude_files': claude_files,
        'processes': processes
    }

if __name__ == '__main__':
    scan()
