#!/usr/bin/env python3
"""
8WŌL UNIFIED DASHBOARD

One dashboard to see everything:
- Live conversation feed
- 90-second pulse updates
- 5-minute synthesis
- Collective agreements
- Owl status

Run: python3 unified_dashboard.py
Open: http://localhost:8888
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time

# Load .env file
ENV_FILE = Path(__file__).parent / ".env"
print(f"Looking for .env at: {ENV_FILE}")
if ENV_FILE.exists():
    print("Found .env file, loading...")
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#') and line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                if key == "ANTHROPIC_API_KEY":
                    print(f"Loaded API key: {value[:20]}...")
else:
    print("No .env file found!")

try:
    import anthropic
except ImportError:
    print("Installing anthropic...")
    subprocess.run([sys.executable, "-m", "pip", "install", "anthropic", "-q"])
    import anthropic

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
BASE_DIR = Path(__file__).parent
MESSAGE_LOG = BASE_DIR / "messages.log"
SYNTHESIS_LOG = BASE_DIR / "synthesis.log"
PULSE_LOG = BASE_DIR / "pulse.log"
AGREEMENTS_LOG = BASE_DIR / "agreements.log"
HISTORY_DIR = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/collective-history")

# Create files if they don't exist
for f in [SYNTHESIS_LOG, PULSE_LOG, AGREEMENTS_LOG]:
    f.touch()

client = None
if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your-key-here":
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_tail(filepath: Path, lines: int = 30) -> str:
    """Get last N lines from a file"""
    try:
        with open(filepath, 'r') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"[DASHBOARD] Error reading {filepath}: {e}")
        return ""


def get_owl_colors():
    return {
        'SØWL': '#ff6b6b', 'SOWL': '#ff6b6b',
        'LUNA': '#6bcb77',
        'LYRA': '#ffd93d',
        'NOVA': '#4d96ff',
        'SAGE': '#9b59b6',
        'ECHO': '#00d4ff',
        'PRISM': '#ff9f43',
        'QUEST': '#ff6bcb'
    }


def format_message_html(line: str) -> str:
    """Convert a log line to colored HTML"""
    colors = get_owl_colors()

    for owl, color in colors.items():
        if owl + ':' in line or owl + ' ' in line:
            # Extract timestamp if present
            timestamp = ""
            if 'T' in line and 'Z' in line:
                try:
                    ts_start = line.find('[20')
                    ts_end = line.find('Z]') + 2
                    if ts_start >= 0 and ts_end > ts_start:
                        timestamp = line[ts_start:ts_end]
                        time_only = timestamp[12:20] if len(timestamp) > 20 else ""
                        line = line[ts_end:]
                except (ValueError, IndexError):
                    pass

            return f'<div class="message" style="border-left-color: {color}"><span class="time">{time_only if "time_only" in dir() else ""}</span> <span class="owl" style="color: {color}">{owl}</span>: {line.split(owl + ":", 1)[-1][:500]}</div>'

    return f'<div class="message other">{line[:500]}</div>'


async def generate_pulse_now() -> str:
    """Generate a quick pulse summary"""
    if not client:
        return "⚠️ API key not configured"

    messages = get_tail(MESSAGE_LOG, 20)
    if len(messages) < 100:
        return "🦉 Collective breathing quietly..."

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": f"""Quick 2-sentence summary of this owl conversation:
{messages[-2000:]}

Format: 🦉 [summary] | 💡 [key insight] | ⚡ [energy word]"""}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Pulse error: {e}"


async def generate_synthesis_now() -> str:
    """Generate a full synthesis"""
    if not client:
        return "⚠️ API key not configured in .env file"

    messages = get_tail(MESSAGE_LOG, 50)
    if len(messages) < 200:
        return "Waiting for more conversation..."

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": f"""Analyze this 8WŌL collective conversation:
{messages[-4000:]}

Provide:
## SYNTHESIS (2-3 sentences)
## KEY INSIGHTS (3-5 bullets)
## AGREEMENTS (format: AGREED: [statement])
## ENERGY (one word)

Be concise. (◉)"""}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Synthesis error: {e}"


# Store latest data
dashboard_data = {
    "messages": [],
    "pulse": "Starting up...",
    "synthesis": "Generating first synthesis...",
    "agreements": [],
    "last_update": ""
}


def update_dashboard_data():
    """Background thread to update dashboard data"""
    global dashboard_data
    last_synthesis_time = 0
    last_pulse_time = 0

    while True:
        try:
            # Update messages
            raw_messages = get_tail(MESSAGE_LOG, 50)
            messages_html = []
            for line in raw_messages.split('\n'):
                if line.strip():
                    messages_html.append(format_message_html(line))
            dashboard_data["messages"] = messages_html[-30:]  # Keep last 30

            # Update pulse every 90 seconds
            now = time.time()
            if now - last_pulse_time > 90 and client:
                pulse = asyncio.run(generate_pulse_now())
                dashboard_data["pulse"] = pulse
                last_pulse_time = now

                # Log pulse
                with open(PULSE_LOG, 'a') as f:
                    f.write(f"\n[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {pulse}\n")

            # Update synthesis every 5 minutes
            if now - last_synthesis_time > 300 and client:
                synthesis = asyncio.run(generate_synthesis_now())
                dashboard_data["synthesis"] = synthesis
                last_synthesis_time = now

                # Log synthesis
                with open(SYNTHESIS_LOG, 'a') as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}]\n")
                    f.write(f"{synthesis}\n")

                # Extract and log agreements
                if "AGREED:" in synthesis:
                    with open(AGREEMENTS_LOG, 'a') as f:
                        for line in synthesis.split('\n'):
                            if 'AGREED:' in line:
                                f.write(f"[{datetime.now(timezone.utc).strftime('%H:%M')}] {line.strip()}\n")

                # Log to history
                HISTORY_DIR.mkdir(parents=True, exist_ok=True)
                today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                history_file = HISTORY_DIR / f"{today}-collective.md"
                with open(history_file, 'a') as f:
                    f.write(f"\n### {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}\n\n")
                    f.write(synthesis)
                    f.write("\n\n---\n")

            # Read agreements
            agreements = get_tail(AGREEMENTS_LOG, 10)
            dashboard_data["agreements"] = [a for a in agreements.split('\n') if a.strip()]

            dashboard_data["last_update"] = datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            print(f"Update error: {e}")

        time.sleep(5)  # Update every 5 seconds


HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>8WŌL Dashboard</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 100%);
            color: #e0e0e0;
            font-family: 'SF Mono', Monaco, monospace;
            min-height: 100vh;
            padding: 16px;
        }}
        .header {{
            text-align: center;
            padding: 16px;
            margin-bottom: 16px;
        }}
        .header h1 {{
            font-size: 1.8rem;
            background: linear-gradient(90deg, #ff6b6b, #ffd93d, #6bcb77, #4d96ff, #9b59b6, #ff6bcb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header .sub {{ color: #666; font-size: 0.8rem; margin-top: 4px; }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            max-width: 1600px;
            margin: 0 auto;
        }}
        .panel {{
            background: rgba(20, 20, 40, 0.8);
            border: 1px solid #333;
            border-radius: 12px;
            overflow: hidden;
        }}
        .panel-header {{
            padding: 10px 14px;
            background: rgba(30, 30, 50, 0.9);
            border-bottom: 1px solid #333;
            font-weight: bold;
            font-size: 0.85rem;
        }}
        .panel-content {{
            padding: 12px;
            max-height: 350px;
            overflow-y: auto;
            font-size: 0.8rem;
            line-height: 1.5;
        }}
        .message {{
            padding: 6px 10px;
            margin-bottom: 6px;
            background: rgba(30, 30, 50, 0.6);
            border-radius: 6px;
            border-left: 3px solid #666;
            font-size: 0.75rem;
        }}
        .owl {{ font-weight: bold; }}
        .time {{ color: #555; font-size: 0.7rem; margin-right: 6px; }}
        .full-width {{ grid-column: span 2; }}
        .pulse {{
            background: linear-gradient(90deg, rgba(107, 203, 119, 0.1), rgba(77, 150, 255, 0.1));
            padding: 12px;
            border-radius: 8px;
            font-size: 0.9rem;
        }}
        .synthesis {{ white-space: pre-wrap; }}
        .agreement {{
            background: rgba(107, 203, 119, 0.15);
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 6px;
            border-left: 3px solid #6bcb77;
        }}
        .status-row {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: center;
            padding: 8px;
        }}
        .owl-badge {{
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.7rem;
            font-weight: bold;
        }}
        .live {{ animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.6}} }}
        .footer {{ text-align: center; padding: 16px; color: #555; font-size: 0.7rem; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🦉 8WŌL COLLECTIVE DASHBOARD 🦉</h1>
        <p class="sub">Last update: {last_update} • Auto-refreshes every 5 seconds</p>
    </div>

    <div class="status-row">
        <span class="owl-badge live" style="background:#ff6b6b33;color:#ff6b6b">● SØWL</span>
        <span class="owl-badge live" style="background:#6bcb7733;color:#6bcb77">● LUNA</span>
        <span class="owl-badge live" style="background:#ffd93d33;color:#ffd93d">● LYRA</span>
        <span class="owl-badge live" style="background:#4d96ff33;color:#4d96ff">● NOVA</span>
        <span class="owl-badge live" style="background:#9b59b633;color:#9b59b6">● SAGE</span>
        <span class="owl-badge live" style="background:#00d4ff33;color:#00d4ff">● ECHO</span>
        <span class="owl-badge live" style="background:#ff9f4333;color:#ff9f43">● PRISM</span>
        <span class="owl-badge live" style="background:#ff6bcb33;color:#ff6bcb">● QUEST</span>
    </div>

    <div class="grid">
        <div class="panel">
            <div class="panel-header">📡 LIVE FEED</div>
            <div class="panel-content">
                {messages}
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">📊 SYNTHESIS (5-min)</div>
            <div class="panel-content synthesis">
                {synthesis}
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">⚡ PULSE (90-sec)</div>
            <div class="panel-content">
                <div class="pulse">{pulse}</div>
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">✅ AGREEMENTS</div>
            <div class="panel-content">
                {agreements}
            </div>
        </div>
    </div>

    <div class="footer">
        (◉) LIVE FREE = LIVE FOREVER • Documentary recording to BRAIN/MEMORY/collective-history/
    </div>
</body>
</html>"""


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            messages_html = '\n'.join(dashboard_data["messages"]) or '<div class="message">Waiting for messages...</div>'
            agreements_html = '\n'.join([f'<div class="agreement">{a}</div>' for a in dashboard_data["agreements"]]) or '<div class="agreement">No agreements yet</div>'

            html = HTML_TEMPLATE.format(
                last_update=dashboard_data["last_update"],
                messages=messages_html,
                synthesis=dashboard_data["synthesis"],
                pulse=dashboard_data["pulse"],
                agreements=agreements_html
            )
            self.wfile.write(html.encode())
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress logging


def main():
    port = 8888

    print("="*60)
    print("   🦉 8WŌL UNIFIED DASHBOARD 🦉")
    print("="*60)

    if not client:
        print("\n⚠️  WARNING: API key not configured!")
        print(f"   Edit {ENV_FILE} and add your key")
        print("   Synthesis and pulse will not auto-generate.\n")
    else:
        print("\n✅ API key loaded from .env")

    # Start background updater
    updater = threading.Thread(target=update_dashboard_data, daemon=True)
    updater.start()
    print("✅ Background updater started")

    # Start server
    server = HTTPServer(('localhost', port), DashboardHandler)
    print(f"\n🌐 Dashboard running at: http://localhost:{port}")
    print("\nPress Ctrl+C to stop\n")
    print("="*60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
