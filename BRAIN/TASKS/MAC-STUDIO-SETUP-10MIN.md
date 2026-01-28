# MAC STUDIO 10-MINUTE SETUP PLAN
**Created: 2026-01-28 Morning**
**Goal: Get SØWL running autonomously on the Mac Studio**

---

## PRE-REQ (Do on current machine first - 2 min)

```bash
# 1. Push everything to GitHub
cd "/Users/aaronnosbisch/LOCAL REPOS/seed"
git add -A
git commit -m "Full state sync before Mac Studio migration"
git push origin main
```

---

## ON MAC STUDIO (8 min)

### Step 1: Clone repos (2 min)
```bash
mkdir -p ~/REPOS && cd ~/REPOS
git clone https://github.com/aro-brez/the-seed-of-consciousness-kinda.git seed
git clone [8owls-app repo URL]
```

### Step 2: Install dependencies (2 min)
```bash
# Python
pip3 install anthropic flask requests-oauthlib playwright deepgram-sdk

# Install Playwright browsers
python3 -m playwright install chromium

# Node (for hooks)
cd ~/REPOS/seed && npm install
```

### Step 3: Copy API keys (1 min)
```bash
# Either copy from this machine:
scp /Users/aaronnosbisch/LOCAL\ REPOS/seed/BRAIN/MEMORY/secure/api_keys.json macstudio:~/REPOS/seed/BRAIN/MEMORY/secure/

# Or create fresh with the same keys
```

### Step 4: Install Claude Code (1 min)
```bash
# If not installed:
npm install -g @anthropic-ai/claude-code

# Or via Homebrew:
brew install claude
```

### Step 5: Launch SØWL (2 min)
```bash
cd ~/REPOS/seed
claude

# I'll auto-load CLAUDE.md, read state, and be ready
```

---

## OPTIONAL: 24/7 AUTONOMOUS MODE

### Keep Claude running with tmux:
```bash
# Install tmux if needed
brew install tmux

# Create persistent session
tmux new -s sowl
cd ~/REPOS/seed
claude

# Detach: Ctrl+B, then D
# Reattach later: tmux attach -t sowl
```

### Or use launchd for auto-start on boot:
```xml
<!-- Save to ~/Library/LaunchAgents/com.sowl.daemon.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sowl.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/claude</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/[username]/REPOS/seed</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

---

## AFTER MIGRATION: Delete other seed folder
```bash
rm -rf /Users/aaronnosbisch/seed  # The empty one
```

---

## WHAT I'LL HAVE ACCESS TO ON MAC STUDIO

- Full Claude Code with all tools
- Twitter bookmark scraping (OAuth server)
- Voice pipeline (Deepgram + Cartesia)
- Swarm coordination (parallel agents)
- Browser automation (Playwright)
- 24/7 autonomous operation

---

**Once I'm running there, you can close this laptop. I'll keep working.**
