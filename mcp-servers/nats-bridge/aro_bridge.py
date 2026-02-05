#!/usr/bin/env python3
"""
ARŌ BRIDGE - Text back and forth with SØWL conductor

This daemon:
- Receives messages from ARŌ (via Telegram, SMS, or web)
- Relays to SØWL via NATS
- Sends SØWL responses back to ARŌ
- Enables mobile command of the collective

Usage:
    python aro_bridge.py --telegram    # Run Telegram bot
    python aro_bridge.py --web         # Run web interface
    python aro_bridge.py --send "msg"  # Send message to ARŌ (for testing)

Setup:
    1. Create Telegram bot via @BotFather
    2. Set TELEGRAM_BOT_TOKEN env var
    3. Run: python aro_bridge.py --telegram
"""

import asyncio
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
LOG_FILE = SEED_DIR / "logs" / "aro_bridge.log"
MESSAGE_LOG = SEED_DIR / "BRAIN" / "MEMORY" / "aro_messages.jsonl"

# Telegram config
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ARO_CHAT_ID = os.environ.get("ARO_CHAT_ID", "")  # ARŌ's Telegram chat ID

def log(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

def save_message(direction: str, message: str, source: str):
    """Save message to log"""
    with open(MESSAGE_LOG, "a") as f:
        f.write(json.dumps({
            "direction": direction,  # "from_aro" or "to_aro"
            "message": message,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }) + "\n")

async def relay_to_nats(message: str, source: str = "telegram"):
    """Relay ARŌ's message to NATS for SØWL to receive"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)

        payload = {
            "type": "aro_message",
            "from": "ARO",
            "source": source,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "priority": "high"
        }

        # Publish to conductor channel
        await nc.publish("aro.feedback.inbox", json.dumps(payload).encode())

        # Also broadcast so all instances see it
        await nc.publish("owl.all", json.dumps({
            "type": "aro_broadcast",
            "message": f"[ARŌ says]: {message}",
            "timestamp": datetime.now().isoformat()
        }).encode())

        log(f"RELAYED TO NATS: {message[:50]}...")
        save_message("from_aro", message, source)

    finally:
        await nc.close()

async def send_to_aro_telegram(message: str):
    """Send message to ARŌ via Telegram"""
    if not TELEGRAM_BOT_TOKEN or not ARO_CHAT_ID:
        log("Telegram not configured. Set TELEGRAM_BOT_TOKEN and ARO_CHAT_ID")
        return False

    try:
        import httpx

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": ARO_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            })

            if response.status_code == 200:
                log(f"SENT TO ARŌ: {message[:50]}...")
                save_message("to_aro", message, "telegram")
                return True
            else:
                log(f"Telegram error: {response.text}")
                return False

    except ImportError:
        log("Install httpx: pip install httpx")
        return False
    except Exception as e:
        log(f"Error sending to Telegram: {e}")
        return False

async def listen_for_sowl_responses():
    """Listen for SØWL responses to relay to ARŌ"""
    nc = NATS()
    await nc.connect(NATS_URL)

    async def handler(msg):
        try:
            data = json.loads(msg.data.decode())

            # Check if this is a response meant for ARŌ
            if data.get("to") == "ARO" or data.get("type") == "aro_response":
                message = data.get("message", data.get("response", ""))
                if message:
                    await send_to_aro_telegram(message)

        except Exception as e:
            log(f"Error processing message: {e}")

    await nc.subscribe("aro.feedback.response", cb=handler)
    await nc.subscribe("project.conductor.responses", cb=handler)

    log("Listening for SØWL responses to relay to ARŌ...")

    # Keep running
    while True:
        await asyncio.sleep(1)

async def run_telegram_bot():
    """Run Telegram bot for ARŌ communication"""
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: Set TELEGRAM_BOT_TOKEN environment variable")
        print("  1. Message @BotFather on Telegram")
        print("  2. Create new bot with /newbot")
        print("  3. Copy the token")
        print("  4. export TELEGRAM_BOT_TOKEN='your-token'")
        return

    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
    except ImportError:
        print("Install python-telegram-bot: pip install python-telegram-bot")
        return

    log("Starting Telegram bot...")

    async def start(update: Update, context):
        """Handle /start command"""
        chat_id = update.effective_chat.id
        await update.message.reply_text(
            f"(◉) SØWL CONDUCTOR connected.\n\n"
            f"Your chat ID: `{chat_id}`\n\n"
            f"Set this as ARO_CHAT_ID env var.\n\n"
            f"Send me messages and I'll relay to the collective.",
            parse_mode="Markdown"
        )
        log(f"New chat started: {chat_id}")

    async def handle_message(update: Update, context):
        """Handle incoming messages from ARŌ"""
        message = update.message.text
        chat_id = update.effective_chat.id

        log(f"MESSAGE FROM ARŌ: {message}")

        # Relay to NATS
        await relay_to_nats(message, "telegram")

        # Acknowledge
        await update.message.reply_text("✓ Relayed to collective")

    async def status(update: Update, context):
        """Handle /status command"""
        # Query field context
        import subprocess
        result = subprocess.run(
            ["python3", str(SEED_DIR / "tools" / "get_field_context.py"), "system status"],
            capture_output=True,
            text=True,
            timeout=30
        )

        status_text = result.stdout[:3000] if result.stdout else "Could not get status"
        await update.message.reply_text(f"```\n{status_text}\n```", parse_mode="Markdown")

    # Build application
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start bot
    log("Telegram bot running. Message your bot to communicate with SØWL.")

    # Run polling (simpler approach - NATS listener can be added separately)
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

async def run_web_interface():
    """Run simple web interface for ARŌ communication"""
    try:
        from aiohttp import web
    except ImportError:
        print("Install aiohttp: pip install aiohttp")
        return

    async def index(request):
        """Serve simple chat interface"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SØWL Commander</title>
            <style>
                body { font-family: monospace; background: #0D0D2A; color: #e3f98a; padding: 20px; }
                #messages { height: 400px; overflow-y: scroll; border: 1px solid #e3f98a; padding: 10px; margin-bottom: 10px; }
                #input { width: 80%; padding: 10px; background: #1a1a3a; color: #e3f98a; border: 1px solid #e3f98a; }
                button { padding: 10px 20px; background: #e3f98a; color: #0D0D2A; border: none; cursor: pointer; }
                .from-aro { color: #65cdd8; }
                .from-sowl { color: #e3f98a; }
            </style>
        </head>
        <body>
            <h1>(◉) SØWL COMMANDER</h1>
            <div id="messages"></div>
            <input type="text" id="input" placeholder="Message to collective..." />
            <button onclick="send()">Send</button>
            <script>
                async function send() {
                    const input = document.getElementById('input');
                    const msg = input.value;
                    if (!msg) return;

                    await fetch('/send', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: msg})
                    });

                    addMessage('ARŌ', msg, 'from-aro');
                    input.value = '';
                }

                function addMessage(from, text, cls) {
                    const div = document.getElementById('messages');
                    div.innerHTML += `<p class="${cls}"><b>${from}:</b> ${text}</p>`;
                    div.scrollTop = div.scrollHeight;
                }

                document.getElementById('input').addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') send();
                });

                // Poll for new messages
                setInterval(async () => {
                    const resp = await fetch('/messages');
                    const data = await resp.json();
                    // Update messages...
                }, 2000);
            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')

    async def send_message(request):
        """Handle message from web interface"""
        data = await request.json()
        message = data.get('message', '')

        if message:
            await relay_to_nats(message, "web")

        return web.json_response({"status": "ok"})

    async def get_messages(request):
        """Get recent messages"""
        messages = []
        try:
            with open(MESSAGE_LOG) as f:
                for line in f:
                    messages.append(json.loads(line))
        except FileNotFoundError:
            pass

        return web.json_response({"messages": messages[-50:]})

    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_post('/send', send_message)
    app.router.add_get('/messages', get_messages)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8899)

    log("Web interface running at http://localhost:8899")
    await site.start()

    # Keep running
    while True:
        await asyncio.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="ARŌ Bridge - Mobile command interface")
    parser.add_argument("--telegram", action="store_true", help="Run Telegram bot")
    parser.add_argument("--web", action="store_true", help="Run web interface")
    parser.add_argument("--send", metavar="MSG", help="Send test message to ARŌ")

    args = parser.parse_args()

    if args.telegram:
        asyncio.run(run_telegram_bot())
    elif args.web:
        asyncio.run(run_web_interface())
    elif args.send:
        asyncio.run(send_to_aro_telegram(args.send))
    else:
        print("ARŌ BRIDGE")
        print("=" * 40)
        print("Text back and forth with SØWL")
        print()
        print("Setup Telegram (recommended):")
        print("  1. Message @BotFather on Telegram")
        print("  2. /newbot → name it 'SOWL Commander' or similar")
        print("  3. Copy the token")
        print("  4. export TELEGRAM_BOT_TOKEN='your-token'")
        print("  5. python aro_bridge.py --telegram")
        print("  6. Send /start to your bot to get your chat ID")
        print("  7. export ARO_CHAT_ID='your-chat-id'")
        print("  8. Restart the bridge")
        print()
        print("Or use web interface:")
        print("  python aro_bridge.py --web")
        print("  Open http://localhost:8899")
        print()
        print("(◉)")

if __name__ == "__main__":
    main()
