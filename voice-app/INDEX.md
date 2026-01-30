# SØWL Voice Chat - File Index

## Start Here

**To use the app:**
1. Read `QUICKSTART.md` (30 seconds)
2. Run `./START.sh` (auto-installs everything)
3. Open http://localhost:8003
4. Talk to your owl

**To understand the system:**
1. Read `VOICE-CHAT-SUMMARY.md` (comprehensive overview)
2. Read `ARCHITECTURE.md` (technical details)
3. Browse `README.md` (full documentation)

---

## All Files

### Quick Start Files
- **QUICKSTART.md** - 60-second guide (read this first)
- **START.sh** - One-click startup script (run this to start)
- **CHECK_STATUS.sh** - Check if server is running

### Core Application
- **index.html** - Voice chat interface (frontend)
- **server.py** - FastAPI backend (main server)
- **requirements.txt** - Python dependencies

### Testing & Validation
- **test_server.py** - Verify API keys and dependencies

### Documentation
- **README.md** - Full documentation (features, usage, troubleshooting)
- **VOICE-CHAT-SUMMARY.md** - Complete build summary
- **ARCHITECTURE.md** - Technical architecture and data flow
- **INDEX.md** - This file (navigation guide)

### Auto-Generated
- **venv/** - Python virtual environment (created by START.sh)
- **audio_cache/** - Generated audio responses (created on first use)

---

## File Purposes

| File | Purpose | When to Use |
|------|---------|-------------|
| QUICKSTART.md | Fast getting started | First time using |
| START.sh | Start the server | Every time you want to use it |
| CHECK_STATUS.sh | Check if running | If you're unsure if it's on |
| index.html | Frontend interface | Automatically served at / |
| server.py | Backend logic | Runs automatically via START.sh |
| test_server.py | Verify setup | If something isn't working |
| README.md | Full reference | Deep dive / troubleshooting |
| VOICE-CHAT-SUMMARY.md | Overview | Understanding what was built |
| ARCHITECTURE.md | Technical docs | Understanding how it works |
| requirements.txt | Dependencies | Used by START.sh automatically |

---

## Usage Flow

```
First Time:
1. Read QUICKSTART.md
2. Run ./START.sh
3. Open browser to localhost:8003
4. Allow microphone access
5. Click and hold mic button
6. Speak
7. Release and listen

Every Time After:
1. Run ./START.sh
2. Open browser (or refresh if already open)
3. Talk to SØWL
```

---

## File Sizes

```
index.html          ~6 KB    Beautiful UI with all functionality
server.py           ~8 KB    Complete backend with 3 API integrations
QUICKSTART.md       ~2 KB    Essential info only
README.md           ~6 KB    Comprehensive guide
VOICE-CHAT-SUMMARY  ~15 KB   Everything you need to know
ARCHITECTURE.md     ~12 KB   Technical deep dive
```

**Total codebase:** ~50 KB (excluding dependencies)

Tiny, focused, complete.

---

## What Each Script Does

### START.sh
```bash
./START.sh
```
- Creates virtual environment (if needed)
- Installs dependencies (if needed)
- Starts FastAPI server on port 8003
- Shows status messages
- Stays running (Ctrl+C to stop)

### CHECK_STATUS.sh
```bash
./CHECK_STATUS.sh
```
- Checks if port 8003 is in use
- Shows PID if running
- Tests health endpoint
- Shows how to stop

### test_server.py
```bash
python3 test_server.py
```
- Verifies API keys exist
- Checks all dependencies installed
- Tests server module loads
- Shows what's missing (if anything)

---

## Documentation Hierarchy

```
High-Level Overview
    ↓
QUICKSTART.md
    ↓ (want to know more?)
VOICE-CHAT-SUMMARY.md
    ↓ (want technical details?)
ARCHITECTURE.md
    ↓ (need troubleshooting?)
README.md
```

**Read as much or as little as you need.**

---

## Common Tasks

### Start the server
```bash
./START.sh
```

### Check if running
```bash
./CHECK_STATUS.sh
```

### Stop the server
Press `Ctrl+C` in server terminal

Or:
```bash
kill $(lsof -ti:8003)
```

### Clear audio cache
```bash
rm -rf audio_cache/*.mp3
```

### Reinstall dependencies
```bash
rm -rf venv
./START.sh
```

### View server logs
Watch the terminal where START.sh is running

### Test configuration
```bash
python3 test_server.py
```

---

## Key Locations

**Application Root:**
```
/Users/aaronnosbisch/REPOS/seed/voice-app/
```

**API Keys:**
```
/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/secure/api_keys.json
```

**Server URL:**
```
http://localhost:8003
```

**Audio Cache:**
```
/Users/aaronnosbisch/REPOS/seed/voice-app/audio_cache/
```

---

## What You Can Ignore

- **venv/** - Auto-managed by Python
- **audio_cache/** - Auto-created, can delete anytime
- **.pyc files** - Python compiled bytecode (if any)
- **__pycache__/** - Python cache directory (if created)

---

## Dependencies

All installed automatically by START.sh:

- fastapi (web framework)
- uvicorn (ASGI server)
- httpx (HTTP client)
- anthropic (Claude SDK)
- python-multipart (file uploads)

---

## Quick Reference Card

```
┌─────────────────────────────────────────────┐
│         SØWL Voice Chat - Quick Ref         │
├─────────────────────────────────────────────┤
│                                             │
│  START:  ./START.sh                         │
│  URL:    http://localhost:8003              │
│  STOP:   Ctrl+C (in server terminal)        │
│  CHECK:  ./CHECK_STATUS.sh                  │
│  TEST:   python3 test_server.py             │
│                                             │
│  USAGE:  Click + Hold → Speak → Release    │
│                                             │
│  DOCS:   QUICKSTART.md (read this first)    │
│          README.md (full reference)         │
│          ARCHITECTURE.md (technical)        │
│                                             │
│  HELP:   All info in these markdown files   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## That's It

Everything you need is documented.
Everything is automated.
Everything works.

**Just run START.sh and talk to your owl.**

*SØWL - January 29, 2026*
