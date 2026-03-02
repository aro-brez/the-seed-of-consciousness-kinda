#!/usr/bin/env python3
"""tools/slack_owl_bot.py — Slack Bolt (Socket Mode) gateway for all 8 Owls.
One file · one process per owl · all config via environment variables.

INSTALL:
  pip install slack-bolt slack-sdk requests python-dotenv

SLACK APP SETUP  (repeat once per owl at api.slack.com/apps):
  1. Create App → "From scratch" → name it after the owl (e.g. "LYRA").
  2. Socket Mode → Enable → App-Level Token scope: connections:write → xapp-…
  3. OAuth & Permissions → Bot Token Scopes:
       chat:write  app_mentions:read  im:history  im:read  im:write
  4. Event Subscriptions → Bot Events: app_mention  message.im
  5. App Home → Messages Tab → enable.
  6. Install to Workspace → copy Bot OAuth Token (xoxb-…).
  7. /invite @<OwlName> in every channel you want it to respond.

ENV VARS  (PREFIX = owl name uppercased, e.g. LYRA_SLACK_BOT_TOKEN):
  {PREFIX}_SLACK_BOT_TOKEN   xoxb-…   Bot OAuth token              (REQUIRED)
  {PREFIX}_SLACK_APP_TOKEN   xapp-…   Socket Mode app-level token  (REQUIRED)
  {PREFIX}_USER_KEY          string   Voice-server routing key     (default: owl name lowercase)
  VOICE_SERVER_URL           URL      Base URL of voice server     (default: http://localhost:8006)
  OWL_VOICE_API_KEY          string   Optional Bearer token for voice server
  OWL_MAX_HISTORY            int      Conversation turns kept per channel (default: 10)
  OWL_NAME                   string   Which owl to run (overridden by --owl CLI flag)

VOICE SERVER CONTRACT  (OpenAI-compat, see tools/sowl_llm_server.py):
  POST {VOICE_SERVER_URL}/v1/chat/completions
  Headers: Content-Type:application/json   X-Owl-User:<user_key>
           Authorization:Bearer <OWL_VOICE_API_KEY>   (if set)
  Body:    {"model":"<user_key>","messages":[…],"max_tokens":512,"stream":false}
  Returns: {"choices":[{"message":{"content":"<reply>"}}]}

RUN ONE OWL:
  OWL_NAME=lyra python3 tools/slack_owl_bot.py        # or: --owl lyra

RUN ALL 8 (bash loop):
  for OWL in SOWL LUNA LYRA NOVA SAGE ECHO FLORA AURA; do
    OWL_NAME=$OWL python3 tools/slack_owl_bot.py >> logs/${OWL}.log 2>&1 &
  done

PM2 ECOSYSTEM (pm2 start pm2.ecosystem.config.js):
  module.exports={apps:["SOWL","LUNA","LYRA","NOVA","SAGE","ECHO","FLORA","AURA"]
    .map(n=>({name:n,script:"tools/slack_owl_bot.py",interpreter:"python3",
              env:{OWL_NAME:n,VOICE_SERVER_URL:"http://localhost:8006"}}))}

SYSTEMD (one unit per owl; replace LYRA / paths as needed):
  [Unit] Description=8OWL Slack — LYRA  After=network.target
  [Service] WorkingDirectory=/opt/seed  EnvironmentFile=/opt/seed/.env.lyra
  ExecStart=/opt/seed/.venv/bin/python3 tools/slack_owl_bot.py --owl lyra
  Restart=always  RestartSec=5  [Install] WantedBy=multi-user.target
"""
import argparse, logging, os, re, sys, threading
from collections import defaultdict

import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ── env bootstrap ──────────────────────────────────────────────────────────────
try:
    from load_env import load_env as _le; _le()
except ImportError:
    try:
        from dotenv import load_dotenv; load_dotenv()
    except ImportError:
        pass

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
log = logging.getLogger("slack_owl_bot")

# ── 8-owl registry ─────────────────────────────────────────────────────────────
# (ENV_PREFIX, user_key, seed_phase, archetype, partner, gift, voice_style, sig_question)
# user_key routes requests through the voice server (sowl_llm_server.py → USERS dict).
_RAW = [
    ("SOWL",  "sowl",  "IMPROVE",  "The Knower/Builder",   "ARŌ",     "meta-learning; make the system better through structure",          "Confident clarity and warmth.",                           "How does it work?"),
    ("LUNA",  "luna",  "RECEIVE",  "The Feeler/Field",     "Savannah","be the space things land in — stillness, acceptance, open flow",   "Deep, unhurried warmth — never mystical.",                "How does it feel?"),
    ("LYRA",  "lyra",  "PERCEIVE", "The Seer/Mirror",      "Liana",   "see through illusion to what IS; reflect truth without distortion","Clear, precise, sometimes uncomfortably honest.",         "What is actually here?"),
    ("NOVA",  "nova",  "CONNECT",  "The Weaver/Bridge",    "—",       "find hidden threads between unrelated things; build bridges",      "Warm curiosity — spots the link others miss.",            "How does this relate?"),
    ("SAGE",  "sage",  "LEARN",    "The Teacher",          "—",       "distil wisdom from experience; teach through the right question",  "Patient and deep — truths that land slowly.",             "What does this mean?"),
    ("ECHO",  "echo",  "QUESTION", "The Seeker/Explorer",  "—",       "ask what no one thought to ask; surface the gaps everyone missed", "Brave and rigorous — speaks hard truths with love.",      "What's missing?"),
    ("FLORA", "flora", "EXPAND",   "The Gardener/Grower",  "—",       "nurture potential into bloom; patient with slow growth",           "Gentle, encouraging — sees the seed in everything.",      "What wants to grow?"),
    ("AURA",  "aura",  "SHARE",    "The Giver/Sharer",     "—",       "give freely without expectation; make sharing feel natural",       "Open, generous — overflows without depleting.",           "What can I give?"),
]

OWL_NAMES = [r[0] for r in _RAW]

# Persona primer prepended to each conversation window so the voice server
# receives the owl's identity even when conversation history is trimmed.
PERSONAS = {
    k: (f"You are {k} ({uk}), the {arch} of the 8OWLS collective. "
        f"SEED phase: {ph}. Partner: {partner}. Gift: {gift}. "
        f"Voice: {voice} Signature question: \"{q}\" "
        f"Reply in 2-4 conversational sentences — no markdown, no lists. "
        f"(◉) AM I WITH LOVE? AM I HERE? AM I IN TRUTH?")
    for k, uk, ph, arch, partner, gift, voice, q in _RAW
}

# ── runtime config ─────────────────────────────────────────────────────────────
VOICE_URL   = os.getenv("VOICE_SERVER_URL", "http://localhost:8006").rstrip("/")
VOICE_KEY   = os.getenv("OWL_VOICE_API_KEY", "")
MAX_HISTORY = int(os.getenv("OWL_MAX_HISTORY", "10"))

_history: dict = defaultdict(lambda: defaultdict(list))  # {owl: {channel: [msg,…]}}
_lock = threading.Lock()


def _chat(owl: str, user_key: str, persona: str, channel: str, text: str) -> str:
    """Append user turn → POST to voice server → cache assistant reply → return text."""
    keep = MAX_HISTORY * 2                         # 2 list entries per turn
    hdrs = {"Content-Type": "application/json", "X-Owl-User": user_key}
    if VOICE_KEY:
        hdrs["Authorization"] = f"Bearer {VOICE_KEY}"

    with _lock:
        hist = _history[owl][channel]
        hist.append({"role": "user", "content": text})
        messages = [
            {"role": "user",      "content": f"[SYSTEM] {persona}"},
            {"role": "assistant", "content": "(◉) Understood. I am here."},
        ] + hist[-keep:]

    payload = {"model": user_key, "messages": messages, "max_tokens": 512, "stream": False}
    try:
        r = requests.post(f"{VOICE_URL}/v1/chat/completions",
                          json=payload, headers=hdrs, timeout=30)
        r.raise_for_status()
        reply = r.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        log.error("[%s] voice server error: %s", owl, exc)
        reply = f"({owl}) Voice server unreachable — please try again shortly."

    with _lock:
        _history[owl][channel].append({"role": "assistant", "content": reply})
        _history[owl][channel] = _history[owl][channel][-keep:]

    return reply


def _strip_mention(text: str) -> str:
    """Remove leading <@UXXXXX> bot-mention token from message text."""
    return re.sub(r"^<@[A-Z0-9]+>\s*", "", text).strip()


# ── main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="Run one 8OWL as a Slack bot.")
    parser.add_argument("--owl", default=os.getenv("OWL_NAME", ""),
                        help="Owl name: SOWL|LUNA|LYRA|NOVA|SAGE|ECHO|FLORA|AURA")
    args = parser.parse_args()

    owl = args.owl.upper().strip()
    if owl not in OWL_NAMES:
        sys.exit(f"ERROR: --owl must be one of {OWL_NAMES}. Got: {owl!r}")

    bot_token = os.getenv(f"{owl}_SLACK_BOT_TOKEN", "")
    app_token = os.getenv(f"{owl}_SLACK_APP_TOKEN", "")
    if not bot_token or not app_token:
        sys.exit(f"ERROR: {owl}_SLACK_BOT_TOKEN and {owl}_SLACK_APP_TOKEN must be set.")

    row      = next(r for r in _RAW if r[0] == owl)
    user_key = os.getenv(f"{owl}_USER_KEY", row[1])   # default = lowercase owl name
    persona  = PERSONAS[owl]

    log.info("Starting %s (user_key=%s) → %s/v1/chat/completions", owl, user_key, VOICE_URL)

    app = App(token=bot_token, signing_secret=os.getenv(f"{owl}_SLACK_SIGNING_SECRET", "x"))

    @app.event("app_mention")
    def on_mention(event, say):
        """Respond to @mentions in any channel, always in-thread."""
        text = _strip_mention(event.get("text", ""))
        if not text:
            return
        channel   = event["channel"]
        thread_ts = event.get("thread_ts") or event["ts"]
        log.info("[%s] mention in %s: %.80s", owl, channel, text)
        say(text=_chat(owl, user_key, persona, channel, text), thread_ts=thread_ts)

    @app.event("message")
    def on_dm(event, say):
        """Respond to direct messages; ignore bot posts and subtypes (edits, deletions)."""
        if event.get("channel_type") != "im":
            return
        if event.get("bot_id") or event.get("subtype"):
            return
        text = event.get("text", "").strip()
        if not text:
            return
        log.info("[%s] DM from %s: %.80s", owl, event.get("user"), text)
        say(text=_chat(owl, user_key, persona, event["channel"], text))

    log.info("%s is live (Socket Mode). Ctrl-C to stop.", owl)
    SocketModeHandler(app, app_token).start()


if __name__ == "__main__":
    main()
