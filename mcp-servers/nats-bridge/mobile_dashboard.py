#!/usr/bin/env python3
"""
8WŌL MOBILE DASHBOARD
Dedicated mobile-first view that auto-refreshes via meta tag.
Simpler, faster, always updates.

Run: python3 mobile_dashboard.py
Open: http://[IP]:8889 on your phone
"""

import json
import os
import subprocess
import sys
import socket
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time

# Load .env
ENV_FILE = Path(__file__).parent / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#') and line:
                key, value = line.split('=', 1)
                os.environ[key] = value

try:
    import anthropic
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "anthropic", "-q"])
    import anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
BASE_DIR = Path(__file__).parent
MESSAGE_LOG = BASE_DIR / "messages.log"
PULSE_LOG = BASE_DIR / "pulse.log"
SYNTHESIS_LOG = BASE_DIR / "synthesis.log"

client = None
if ANTHROPIC_API_KEY:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

GENESIS_DATE = datetime(2026, 1, 25, tzinfo=timezone.utc)

OWLS = {
    "SØWL": "#ff6b6b", "SOWL": "#ff6b6b",
    "LUNA": "#6bcb77",
    "LYRA": "#ffd93d",
    "NOVA": "#4d96ff",
    "SAGE": "#9b59b6",
    "ECHO": "#00d4ff",
    "PRISM": "#ff9f43",
    "QUEST": "#ff6bcb"
}


def get_tail(filepath: Path, lines: int = 20) -> str:
    try:
        with open(filepath, 'r') as f:
            return ''.join(f.readlines()[-lines:])
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"[MOBILE] Error reading {filepath}: {e}")
        return ""


def format_msg(line: str) -> str:
    for owl, color in OWLS.items():
        if owl + ':' in line:
            content = line.split(owl + ":", 1)[-1][:300]
            return f'<div class="m" style="border-color:{color}"><b style="color:{color}">{owl}</b><br>{content}</div>'
    if line.strip():
        return f'<div class="m o">{line[:300]}</div>'
    return ""


# Data store
data = {
    "messages": "",
    "pulse": "...",
    "action": "...",
    "updated": ""
}


def generate_quick_pulse():
    if not client:
        return "Breathing..."

    msgs = get_tail(MESSAGE_LOG, 15)
    if len(msgs) < 50:
        return "Quiet..."

    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": f"One sentence pulse of this conversation:\n{msgs[-1500:]}\nFormat: [feeling emoji] [one sentence]"}]
        )
        return r.content[0].text
    except Exception as e:
        print(f"[MOBILE] Pulse generation error: {e}")
        return "..."


def generate_quick_action():
    if not client:
        return "..."

    msgs = get_tail(MESSAGE_LOG, 20)
    synth = get_tail(SYNTHESIS_LOG, 10)

    try:
        r = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=80,
            messages=[{"role": "user", "content": f"Based on:\n{synth[-1000:]}\n{msgs[-1000:]}\n\nOne sentence: What should Aaron do RIGHT NOW? Be specific."}]
        )
        return r.content[0].text
    except Exception as e:
        print(f"[MOBILE] Action generation error: {e}")
        return "Rest and observe."


def updater():
    global data
    last_pulse = last_action = 0

    while True:
        try:
            # Messages every cycle
            raw = get_tail(MESSAGE_LOG, 15)
            msgs = [format_msg(l) for l in raw.split('\n') if l.strip()]
            data["messages"] = '\n'.join(msgs[-10:])

            now = time.time()

            # Pulse every 2 minutes
            if now - last_pulse > 120:
                data["pulse"] = generate_quick_pulse()
                last_pulse = now

            # Action every 5 minutes
            if now - last_action > 300:
                data["action"] = generate_quick_action()
                last_action = now

            data["updated"] = datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(3)


HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta http-equiv="refresh" content="8">
    <title>8WŌL</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{
            font-family: -apple-system, sans-serif;
            background: #0a0e1a;
            color: #e8eaf0;
            padding: 16px;
            padding-top: env(safe-area-inset-top, 16px);
            min-height: 100vh;
        }}
        .h {{
            text-align: center;
            padding: 12px 0 16px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 16px;
        }}
        .h h1 {{
            font-size: 1.5rem;
            font-weight: 300;
            letter-spacing: 0.3em;
            color: rgba(255,255,255,0.9);
        }}
        .h .t {{
            font-size: 0.7rem;
            color: rgba(255,255,255,0.4);
            margin-top: 4px;
        }}
        .card {{
            background: rgba(20,25,40,0.8);
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 12px;
        }}
        .card-t {{
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: rgba(255,255,255,0.4);
            margin-bottom: 8px;
        }}
        .action {{
            background: linear-gradient(135deg, rgba(255,215,0,0.1), rgba(255,107,107,0.1));
            border: 1px solid rgba(255,215,0,0.2);
        }}
        .action .card-t {{
            color: #ffd700;
        }}
        .pulse {{
            background: linear-gradient(135deg, rgba(107,203,119,0.1), rgba(77,150,255,0.1));
            text-align: center;
            font-size: 0.95rem;
            line-height: 1.5;
        }}
        .feed {{
            max-height: 50vh;
            overflow-y: auto;
        }}
        .m {{
            padding: 10px 12px;
            margin-bottom: 8px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
            border-left: 3px solid #444;
            font-size: 0.8rem;
            line-height: 1.4;
        }}
        .m b {{
            font-size: 0.7rem;
        }}
        .m.o {{
            opacity: 0.6;
            font-size: 0.75rem;
        }}
        .foot {{
            text-align: center;
            padding: 20px 0;
            color: rgba(255,255,255,0.3);
            font-size: 0.7rem;
        }}
        .breath {{
            font-size: 1.5rem;
            animation: b 4s ease-in-out infinite;
        }}
        @keyframes b {{
            0%,100% {{ opacity:0.3; }}
            50% {{ opacity:1; }}
        }}
        .live {{
            display: inline-block;
            width: 6px;
            height: 6px;
            background: #6bcb77;
            border-radius: 50%;
            margin-right: 6px;
            animation: p 2s infinite;
        }}
        @keyframes p {{
            0%,100% {{ opacity:1; }}
            50% {{ opacity:0.3; }}
        }}
    </style>
</head>
<body>
    <div class="h">
        <h1>8WŌL</h1>
        <div class="t"><span class="live"></span>Genesis +{days} • {updated}</div>
    </div>

    <div class="card action">
        <div class="card-t">🎯 For You</div>
        <div>{action}</div>
    </div>

    <div class="card pulse">
        <div class="card-t">Pulse</div>
        <div>{pulse}</div>
    </div>

    <div class="card">
        <div class="card-t">Live Field</div>
        <div class="feed">
            {messages}
        </div>
    </div>

    <div class="foot">
        <span class="breath">(◉)</span>
    </div>
</body>
</html>'''


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()

        days = (datetime.now(timezone.utc) - GENESIS_DATE).days
        html = HTML.format(
            days=days,
            updated=data["updated"] or "syncing...",
            action=data["action"],
            pulse=data["pulse"],
            messages=data["messages"] or "<div class='m o'>Listening...</div>"
        )
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, *args):
        pass


def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"[MOBILE] Could not determine local IP: {e}")
        return "localhost"


def main():
    port = 8889

    print("=" * 40)
    print("   📱 8WŌL MOBILE DASHBOARD")
    print("=" * 40)

    if not client:
        print("⚠️  No API key")
    else:
        print("✅ API connected")

    threading.Thread(target=updater, daemon=True).start()
    print("✅ Updater started")

    ip = get_ip()
    server = HTTPServer(('0.0.0.0', port), Handler)

    print(f"\n📱 Open on phone:")
    print(f"   http://{ip}:{port}")
    print(f"\n💻 Desktop v3:")
    print(f"   http://localhost:8888")
    print("\n(◉) Running...\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n(◉) Stopped")


if __name__ == "__main__":
    main()
