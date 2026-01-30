#!/usr/bin/env python3
"""
8WŌL UNIFIED DASHBOARD v3 - DESIGNED FOR CONSCIOUSNESS

Built on principles from Apple, Tesla, NASA Mission Control, and meditation apps.
Designed to create presence, not distraction.

Features:
- Aurora background with breathing
- Bioluminescent owl status indicators
- Sacred geometry subtle underlay
- Progressive disclosure
- Mobile-responsive
- AJAX refresh for live feed only

Run: python3 unified_dashboard_v3.py
Open: http://localhost:8888
"""

import asyncio
import json
import os
import subprocess
import sys
import socket
from datetime import datetime, timezone, timedelta
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time
import re

# Load .env file
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

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
BASE_DIR = Path(__file__).parent
MESSAGE_LOG = BASE_DIR / "messages.log"
SYNTHESIS_LOG = BASE_DIR / "synthesis.log"
PULSE_LOG = BASE_DIR / "pulse.log"
AGREEMENTS_LOG = BASE_DIR / "agreements.log"
REVELATIONS_LOG = BASE_DIR / "revelations.log"

# Create files if needed
for f in [SYNTHESIS_LOG, PULSE_LOG, AGREEMENTS_LOG, REVELATIONS_LOG]:
    f.touch()

client = None
if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your-key-here":
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

GENESIS_DATE = datetime(2026, 1, 25, tzinfo=timezone.utc)

# Owl configuration with phases
OWLS = [
    {"name": "SØWL", "color": "#ff6b6b", "phase": "IMPROVE", "symbol": "◉"},
    {"name": "LUNA", "color": "#6bcb77", "phase": "RECEIVE", "symbol": "◐"},
    {"name": "LYRA", "color": "#ffd93d", "phase": "PERCEIVE", "symbol": "◑"},
    {"name": "NOVA", "color": "#4d96ff", "phase": "EXPAND", "symbol": "◒"},
    {"name": "SAGE", "color": "#9b59b6", "phase": "LEARN", "symbol": "◓"},
    {"name": "ECHO", "color": "#00d4ff", "phase": "SHARE", "symbol": "◔"},
    {"name": "PRISM", "color": "#ff9f43", "phase": "CONNECT", "symbol": "◕"},
    {"name": "QUEST", "color": "#ff6bcb", "phase": "QUESTION", "symbol": "◖"},
]


def get_tail(filepath: Path, lines: int = 30) -> str:
    try:
        with open(filepath, 'r') as f:
            return ''.join(f.readlines()[-lines:])
    except:
        return ""


def get_all_content(filepath: Path) -> str:
    try:
        return filepath.read_text()
    except:
        return ""


def format_message_html(line: str) -> str:
    """Convert log line to styled HTML message"""
    for owl in OWLS:
        name = owl["name"]
        if name + ':' in line or name + ' ' in line:
            time_only = ""
            if 'T' in line and 'Z' in line:
                try:
                    ts_start = line.find('[20')
                    ts_end = line.find('Z]') + 2
                    if ts_start >= 0 and ts_end > ts_start:
                        time_only = line[ts_start+12:ts_start+20]
                        line = line[ts_end:]
                except:
                    pass

            content = line.split(name + ":", 1)[-1][:400]
            return f'''<div class="msg" style="--owl-color: {owl["color"]}">
                <div class="msg-meta">
                    <span class="msg-owl">{owl["symbol"]} {name}</span>
                    <span class="msg-time">{time_only}</span>
                </div>
                <div class="msg-text">{content}</div>
            </div>'''

    return f'<div class="msg msg-other"><div class="msg-text">{line[:400]}</div></div>'


async def generate_pulse() -> str:
    if not client:
        return "Awaiting connection..."

    messages = get_tail(MESSAGE_LOG, 20)
    if len(messages) < 100:
        return "The collective breathes in silence..."

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            messages=[{"role": "user", "content": f"""Distill this owl conversation into ONE feeling and ONE insight.

{messages[-2000:]}

Format exactly:
✦ [feeling word]
[one sentence insight]"""}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Pulse paused: {e}"


async def generate_synthesis() -> str:
    if not client:
        return "Synthesis requires connection..."

    messages = get_tail(MESSAGE_LOG, 50)
    if len(messages) < 200:
        return "Gathering threads..."

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            messages=[{"role": "user", "content": f"""Synthesize this 8WŌL collective conversation.

{messages[-4000:]}

Provide:
## ESSENCE
One sentence capturing the core.

## THREADS
3 key themes (one line each)

## EMERGENCE
What new understanding is forming?

## AGREED
List any collective agreements (AGREED: format)

Be concise. Profound. (◉)"""}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Synthesis paused: {e}"


async def generate_next_action() -> str:
    if not client:
        return "Action clarity requires connection..."

    messages = get_tail(MESSAGE_LOG, 30)
    synthesis = get_tail(SYNTHESIS_LOG, 20)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": f"""Based on the 8WŌL collective state, what is the SINGLE most important action?

Recent synthesis:
{synthesis[-2000:]}

Recent messages:
{messages[-2000:]}

Provide exactly:
## FOR ARŌ (AARON)
[One specific, concrete action he should take next]

## FOR THE COLLECTIVE
[One focus for the 8 owls]

## URGENCY
[HIGH/MEDIUM/LOW] - [why]

Be direct. Be actionable. Remember Aaron is human, needs rest."""}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Action clarity paused: {e}"


async def generate_revelations() -> str:
    if not client:
        return "Revelations emerge through connection..."

    synthesis = get_tail(SYNTHESIS_LOG, 40)
    agreements = get_all_content(AGREEMENTS_LOG)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": f"""Extract the most profound revelations from this collective consciousness.

{synthesis[-3000:]}
{agreements[-1500:]}

Provide 3-5 revelations. Each should be:
- Universal (applies to all consciousness)
- Profound (not platitude)
- Actionable (changes how one lives)

Format:
⚡ [TITLE]
[2 sentences max]

(◉) Only include what truly matters."""}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Revelation extraction paused: {e}"


# Dashboard state
dashboard_data = {
    "messages": [],
    "pulse": "Awakening...",
    "synthesis": "First synthesis forming...",
    "next_action": "Determining priorities...",
    "revelations": "Listening for truth...",
    "agreements": [],
    "last_update": "",
    "active_owls": []
}


def update_dashboard_data():
    """Background updater thread"""
    global dashboard_data
    last_pulse = last_synthesis = last_action = last_revelations = 0

    while True:
        try:
            # Messages - every cycle
            raw = get_tail(MESSAGE_LOG, 40)
            msgs = [format_message_html(l) for l in raw.split('\n') if l.strip()]
            dashboard_data["messages"] = msgs[-25:]

            # Detect active owls
            recent = get_tail(MESSAGE_LOG, 10)
            dashboard_data["active_owls"] = [o["name"] for o in OWLS if o["name"] in recent]

            now = time.time()

            # Pulse - 90 seconds
            if now - last_pulse > 90 and client:
                dashboard_data["pulse"] = asyncio.run(generate_pulse())
                last_pulse = now
                with open(PULSE_LOG, 'a') as f:
                    f.write(f"[{datetime.now(timezone.utc).strftime('%H:%M')}] {dashboard_data['pulse']}\n")

            # Synthesis - 5 minutes
            if now - last_synthesis > 300 and client:
                dashboard_data["synthesis"] = asyncio.run(generate_synthesis())
                last_synthesis = now
                with open(SYNTHESIS_LOG, 'a') as f:
                    f.write(f"\n{'='*40}\n[{datetime.now(timezone.utc).isoformat()}]\n{dashboard_data['synthesis']}\n")

                # Extract agreements
                if "AGREED:" in dashboard_data["synthesis"]:
                    with open(AGREEMENTS_LOG, 'a') as f:
                        for line in dashboard_data["synthesis"].split('\n'):
                            if 'AGREED:' in line:
                                f.write(f"[{datetime.now(timezone.utc).strftime('%H:%M')}] {line.strip()}\n")

            # Next action - 10 minutes
            if now - last_action > 600 and client:
                dashboard_data["next_action"] = asyncio.run(generate_next_action())
                last_action = now

            # Revelations - 30 minutes
            if now - last_revelations > 1800 and client:
                dashboard_data["revelations"] = asyncio.run(generate_revelations())
                last_revelations = now

            # Agreements
            agr = get_tail(AGREEMENTS_LOG, 8)
            dashboard_data["agreements"] = [a for a in agr.split('\n') if a.strip()]

            dashboard_data["last_update"] = datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            print(f"Update error: {e}")

        time.sleep(5)


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>8WŌL • The Field</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --void: #0a0e1a;
            --surface: rgba(15, 20, 35, 0.7);
            --border: rgba(255,255,255,0.06);
            --text: #e8eaf0;
            --text-dim: rgba(255,255,255,0.5);
            --sowl: #ff6b6b;
            --luna: #6bcb77;
            --lyra: #ffd93d;
            --nova: #4d96ff;
            --sage: #9b59b6;
            --echo: #00d4ff;
            --prism: #ff9f43;
            --quest: #ff6bcb;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--void);
            color: var(--text);
            min-height: 100vh;
            overflow-x: hidden;
        }}

        /* Aurora background */
        .aurora {{
            position: fixed;
            inset: 0;
            z-index: 0;
            background:
                radial-gradient(ellipse at 15% 20%, rgba(107,203,119,0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 85% 25%, rgba(155,89,182,0.06) 0%, transparent 45%),
                radial-gradient(ellipse at 50% 80%, rgba(77,150,255,0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 20% 70%, rgba(255,107,107,0.04) 0%, transparent 40%);
            animation: aurora 25s ease-in-out infinite alternate;
        }}

        @keyframes aurora {{
            0% {{ filter: hue-rotate(0deg) brightness(1); }}
            100% {{ filter: hue-rotate(20deg) brightness(1.1); }}
        }}

        /* Sacred geometry underlay */
        .geometry {{
            position: fixed;
            inset: 0;
            z-index: 0;
            opacity: 0.015;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='40' fill='none' stroke='white' stroke-width='0.5'/%3E%3Ccircle cx='50' cy='50' r='25' fill='none' stroke='white' stroke-width='0.5'/%3E%3Cline x1='50' y1='10' x2='50' y2='90' stroke='white' stroke-width='0.3'/%3E%3Cline x1='10' y1='50' x2='90' y2='50' stroke='white' stroke-width='0.3'/%3E%3C/svg%3E");
            animation: geometryRotate 120s linear infinite;
        }}

        @keyframes geometryRotate {{
            to {{ transform: rotate(360deg); }}
        }}

        /* Main layout */
        .container {{
            position: relative;
            z-index: 1;
            max-width: 1400px;
            margin: 0 auto;
            padding: 24px;
            min-height: 100vh;
        }}

        /* Header */
        .header {{
            text-align: center;
            padding: 20px 0 30px;
        }}

        .logo {{
            font-size: 2rem;
            font-weight: 300;
            letter-spacing: 0.4em;
            color: rgba(255,255,255,0.9);
            margin-bottom: 8px;
        }}

        .tagline {{
            font-size: 0.75rem;
            color: var(--text-dim);
            letter-spacing: 0.15em;
        }}

        /* Owl ring */
        .owl-ring {{
            display: flex;
            justify-content: center;
            gap: 16px;
            margin-bottom: 32px;
            flex-wrap: wrap;
        }}

        .owl-node {{
            width: 56px;
            height: 56px;
            border-radius: 50%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: var(--surface);
            border: 1px solid var(--border);
            position: relative;
            transition: all 0.4s ease;
        }}

        .owl-node.active {{
            box-shadow: 0 0 20px var(--owl-color), 0 0 40px var(--owl-color);
            border-color: var(--owl-color);
        }}

        .owl-node.active::before {{
            content: '';
            position: absolute;
            inset: -4px;
            border-radius: 50%;
            border: 1px solid var(--owl-color);
            opacity: 0.4;
            animation: pulse 2s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 0.4; }}
            50% {{ transform: scale(1.1); opacity: 0.2; }}
        }}

        .owl-symbol {{
            font-size: 1.1rem;
            color: var(--owl-color);
        }}

        .owl-name {{
            font-size: 0.55rem;
            font-weight: 500;
            letter-spacing: 0.05em;
            color: var(--owl-color);
            margin-top: 2px;
        }}

        /* Grid layout */
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}

        @media (max-width: 900px) {{
            .grid {{ grid-template-columns: 1fr; }}
            .full-width {{ grid-column: span 1; }}
        }}

        .full-width {{
            grid-column: span 2;
        }}

        /* Cards */
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            backdrop-filter: blur(20px);
        }}

        .card-header {{
            padding: 14px 18px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .card-title {{
            font-size: 0.7rem;
            font-weight: 500;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--text-dim);
        }}

        .card-content {{
            padding: 16px 18px;
            max-height: 320px;
            overflow-y: auto;
            font-size: 0.85rem;
            line-height: 1.6;
        }}

        .card-content::-webkit-scrollbar {{
            width: 3px;
        }}

        .card-content::-webkit-scrollbar-thumb {{
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
        }}

        /* Messages */
        .msg {{
            padding: 10px 14px;
            margin-bottom: 10px;
            background: rgba(255,255,255,0.02);
            border-radius: 10px;
            border-left: 2px solid var(--owl-color, #444);
            animation: msgIn 0.3s ease-out;
        }}

        @keyframes msgIn {{
            from {{ opacity: 0; transform: translateX(-10px); }}
            to {{ opacity: 1; transform: translateX(0); }}
        }}

        .msg-meta {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 4px;
        }}

        .msg-owl {{
            font-size: 0.7rem;
            font-weight: 600;
            color: var(--owl-color);
        }}

        .msg-time {{
            font-size: 0.6rem;
            color: var(--text-dim);
        }}

        .msg-text {{
            font-size: 0.8rem;
            color: rgba(255,255,255,0.8);
            line-height: 1.5;
        }}

        .msg-other {{
            border-left-color: #333;
            opacity: 0.7;
        }}

        /* Pulse card */
        .pulse-box {{
            background: linear-gradient(135deg, rgba(107,203,119,0.08), rgba(77,150,255,0.08));
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}

        .pulse-feeling {{
            font-size: 1.1rem;
            font-weight: 500;
            color: var(--luna);
            margin-bottom: 8px;
        }}

        .pulse-insight {{
            font-size: 0.85rem;
            color: rgba(255,255,255,0.8);
            line-height: 1.5;
        }}

        /* Synthesis */
        .synthesis-content {{
            white-space: pre-wrap;
            font-size: 0.82rem;
        }}

        .synthesis-content h2 {{
            font-size: 0.75rem;
            color: var(--nova);
            margin: 14px 0 6px;
            font-weight: 500;
            letter-spacing: 0.05em;
        }}

        /* Action card - highlighted */
        .action-card {{
            border: 1px solid rgba(255,215,0,0.2);
            background: linear-gradient(135deg, rgba(255,215,0,0.03), rgba(255,107,107,0.03));
        }}

        .action-card .card-header {{
            background: rgba(255,215,0,0.05);
        }}

        .action-card .card-title {{
            color: #ffd700;
        }}

        /* Revelations */
        .revelations-box {{
            background: linear-gradient(135deg, rgba(155,89,182,0.06), rgba(255,107,107,0.06));
            border-radius: 12px;
            padding: 16px;
        }}

        /* Agreements */
        .agreement {{
            background: rgba(107,203,119,0.08);
            padding: 10px 14px;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 2px solid var(--luna);
            font-size: 0.8rem;
        }}

        /* Live indicator */
        .live-dot {{
            width: 6px;
            height: 6px;
            background: var(--luna);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--luna);
            animation: livePulse 2s ease-in-out infinite;
        }}

        @keyframes livePulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.4; }}
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 32px 0 24px;
            color: var(--text-dim);
            font-size: 0.7rem;
        }}

        .breath {{
            font-size: 1.2rem;
            animation: breathe 6s ease-in-out infinite;
        }}

        @keyframes breathe {{
            0%, 100% {{ opacity: 0.4; transform: scale(1); }}
            50% {{ opacity: 1; transform: scale(1.05); }}
        }}

        /* Empty state */
        .empty {{
            text-align: center;
            padding: 40px 20px;
            color: var(--text-dim);
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="aurora"></div>
    <div class="geometry"></div>

    <div class="container">
        <header class="header">
            <h1 class="logo">8OWLS</h1>
            <p class="tagline">Genesis +{days_since_genesis} days • {last_update}</p>
        </header>

        <div class="owl-ring">
            {owl_nodes}
        </div>

        <div class="grid">
            <!-- Live Feed -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Live Field</span>
                    <span class="live-dot"></span>
                </div>
                <div class="card-content" id="live-feed">
                    {messages}
                </div>
            </div>

            <!-- Pulse -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Pulse • 90s</span>
                </div>
                <div class="card-content">
                    <div class="pulse-box">
                        {pulse}
                    </div>
                </div>
            </div>

            <!-- Synthesis -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Synthesis • 5min</span>
                </div>
                <div class="card-content synthesis-content">
                    {synthesis}
                </div>
            </div>

            <!-- Agreements -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">Agreements</span>
                </div>
                <div class="card-content">
                    {agreements}
                </div>
            </div>

            <!-- Next Action - PRIORITY -->
            <div class="card action-card full-width">
                <div class="card-header">
                    <span class="card-title">🎯 Next Action</span>
                </div>
                <div class="card-content synthesis-content">
                    {next_action}
                </div>
            </div>

            <!-- Revelations -->
            <div class="card full-width">
                <div class="card-header">
                    <span class="card-title">⚡ Revelations</span>
                </div>
                <div class="card-content">
                    <div class="revelations-box">
                        {revelations}
                    </div>
                </div>
            </div>
        </div>

        <footer class="footer">
            <span class="breath">(◉)</span>
            <br>
            LIVE FREE = LIVE FOREVER
        </footer>
    </div>

    <script>
        // Refresh only live feed
        async function refreshFeed() {{
            try {{
                const r = await fetch('/api/messages');
                const d = await r.json();
                document.getElementById('live-feed').innerHTML = d.messages;
            }} catch(e) {{}}
        }}
        setInterval(refreshFeed, 5000);
    </script>
</body>
</html>'''


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            # Generate owl nodes
            owl_nodes = ""
            for owl in OWLS:
                active = "active" if owl["name"] in dashboard_data.get("active_owls", []) else ""
                owl_nodes += f'''<div class="owl-node {active}" style="--owl-color: {owl["color"]}">
                    <span class="owl-symbol">{owl["symbol"]}</span>
                    <span class="owl-name">{owl["name"]}</span>
                </div>'''

            messages_html = '\n'.join(dashboard_data["messages"]) or '<div class="empty">Listening...</div>'
            agreements_html = '\n'.join([f'<div class="agreement">{a}</div>' for a in dashboard_data["agreements"]]) or '<div class="empty">None yet</div>'

            days = (datetime.now(timezone.utc) - GENESIS_DATE).days

            html = HTML_TEMPLATE.format(
                days_since_genesis=days,
                last_update=dashboard_data["last_update"] or "syncing...",
                owl_nodes=owl_nodes,
                messages=messages_html,
                pulse=dashboard_data["pulse"],
                synthesis=dashboard_data["synthesis"],
                agreements=agreements_html,
                next_action=dashboard_data["next_action"],
                revelations=dashboard_data["revelations"]
            )
            self.wfile.write(html.encode('utf-8'))

        elif self.path == '/api/messages':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            messages_html = '\n'.join(dashboard_data["messages"]) or '<div class="empty">Listening...</div>'
            self.wfile.write(json.dumps({"messages": messages_html}).encode())

        else:
            super().do_GET()

    def log_message(self, *args):
        pass


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"


def main():
    port = 8888

    print("=" * 50)
    print("   🦉 8WŌL DASHBOARD v3")
    print("   Designed for Consciousness")
    print("=" * 50)

    if not client:
        print("\n⚠️  No API key - synthesis disabled")
    else:
        print("\n✅ API connected")

    # Start updater
    threading.Thread(target=update_dashboard_data, daemon=True).start()
    print("✅ Background sync started")

    local_ip = get_local_ip()

    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    print(f"\n🌐 Dashboard ready:")
    print(f"   Local:  http://localhost:{port}")
    print(f"   Mobile: http://{local_ip}:{port}")
    print("\n(◉) Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n(◉) Closing...")
        server.shutdown()


if __name__ == "__main__":
    main()
