# SØWL Voice Chat - Quick Start

## One Command

```bash
cd /Users/aaronnosbisch/REPOS/seed/voice-app && ./START.sh
```

Then open: **http://localhost:8003**

## How to Use

1. **Click and hold** the microphone button
2. **Speak** your message
3. **Release** the button to send
4. **Wait** - SØWL transcribes, thinks, and responds
5. **Listen** - Audio plays automatically in ARŌ's voice
6. **Repeat** - Conversation continues with full context

## What Happens Behind the Scenes

```
Your voice → Web Audio API → Server
    ↓
Deepgram transcribes to text
    ↓
Claude Sonnet 4.5 generates response
    ↓
Cartesia synthesizes in ARŌ's cloned voice
    ↓
MP3 plays in browser
```

**Latency:** 2-4 seconds total (most time is synthesis)

## Features

- **Voice cloning**: Sounds like ARŌ
- **Full context**: Remembers conversation
- **Clean UI**: Beautiful, simple interface
- **Works everywhere**: Chrome, Safari, Firefox
- **Mobile ready**: Touch events supported

## Stopping the Server

Press `Ctrl+C` in the terminal

## Troubleshooting

**Microphone not working?**
- Allow mic access in browser
- Check System Preferences → Security → Microphone
- Reload the page

**Server won't start?**
```bash
# Kill any process on port 8003
lsof -i :8003 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Try again
./START.sh
```

**No audio playback?**
- Check browser console for errors
- Verify audio files appear in `audio_cache/`
- Try a different browser

## Files Generated

- `audio_cache/response_*.mp3` - Audio responses (can delete anytime)
- `venv/` - Python virtual environment (auto-created)

---

**That's it. Just run and talk.**

Built for ARŌ in <30 minutes.

*SØWL - January 29, 2026*
