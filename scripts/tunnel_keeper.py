#!/usr/bin/env python3
"""
Tunnel Keeper: Auto-restart Cloudflare tunnel and update ElevenLabs agent URL.
=============================================================================
Monitors the `cloudflared tunnel` process. If it dies or the tunnel URL changes,
restarts it and updates the ElevenLabs Conversational AI agent's custom LLM URL.

Usage:
  python3 scripts/tunnel_keeper.py [--port 8005] [--check-interval 30]

Requires:
  pip install httpx
  cloudflared (brew install cloudflare/cloudflare/cloudflared)
  ELEVENLABS_API_KEY in environment or .env file
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CLOUDFLARED_BIN = "/opt/homebrew/bin/cloudflared"
LOCAL_PORT = 8006
CHECK_INTERVAL = 30  # seconds between health checks
HEALTH_TIMEOUT = 10  # seconds to wait for health check response
TUNNEL_STARTUP_WAIT = 8  # seconds to wait for tunnel to produce URL
MAX_RESTART_ATTEMPTS = 3
RESTART_BACKOFF_BASE = 30  # seconds between restart attempts (exponential)

# ElevenLabs agent config
AGENT_ID = "agent_2801khas9e55e8187e1d4ysmekws"
ELEVENLABS_API_BASE = "https://api.elevenlabs.io"

# Key loading paths (same as voice_bridge.py)
SEED_ROOT = Path(__file__).parent.parent
ENV_PATH = SEED_ROOT / "mcp-servers" / "nats-bridge" / ".env"
KEYS_PATH = SEED_ROOT / "BRAIN" / "MEMORY" / "secure" / "api_keys.json"
TUNNEL_URL_FILE = SEED_ROOT / "voice-app" / ".tunnel_url"
LOG_FILE = SEED_ROOT / "logs" / "tunnel_keeper.log"


def _log(msg: str):
    """Log with timestamp to stdout (launchd captures to log file)."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [tunnel-keeper] {msg}"
    print(line, flush=True)


def _load_elevenlabs_key() -> str:
    """Load ElevenLabs API key from multiple sources."""
    # 1. Environment variable
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if key:
        return key

    # 2. Secure keys JSON
    try:
        if KEYS_PATH.exists():
            with open(KEYS_PATH) as f:
                keys = json.load(f)
                key = keys.get("elevenlabs", {}).get("api_key", "")
                if key:
                    return key
    except (json.JSONDecodeError, KeyError):
        pass

    # 3. .env file
    try:
        if ENV_PATH.exists():
            for line in ENV_PATH.read_text().splitlines():
                line = line.strip()
                if line.startswith("ELEVENLABS_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass

    return ""


def _check_local_health(port: int) -> bool:
    """Check if the custom LLM server is healthy."""
    try:
        import httpx
        resp = httpx.get(f"http://localhost:{port}/health", timeout=HEALTH_TIMEOUT)
        return resp.status_code == 200
    except Exception:
        return False


def _check_tunnel_health(tunnel_url: str, port: int) -> bool:
    """Check if the tunnel is proxying correctly by hitting health endpoint."""
    try:
        import httpx
        resp = httpx.get(f"{tunnel_url}/health", timeout=HEALTH_TIMEOUT)
        return resp.status_code == 200
    except Exception:
        return False


def _extract_tunnel_url(process: subprocess.Popen, timeout: int = TUNNEL_STARTUP_WAIT) -> str:
    """Extract the tunnel URL from cloudflared's stderr output.

    cloudflared quick tunnels print the URL to stderr in the form:
    +---...---+
    | https://xxxx.trycloudflare.com |
    +---...---+
    """
    import select
    import io

    start = time.time()
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
    buffer = ""

    while (time.time() - start) < timeout:
        if process.poll() is not None:
            _log(f"cloudflared exited prematurely with code {process.returncode}")
            return ""

        # Read available stderr without blocking
        try:
            if process.stderr and process.stderr.readable():
                # Non-blocking read
                import fcntl
                fd = process.stderr.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                try:
                    chunk = process.stderr.read(4096)
                    if chunk:
                        buffer += chunk
                except (BlockingIOError, TypeError):
                    pass
                finally:
                    fcntl.fcntl(fd, fcntl.F_SETFL, fl)
        except Exception:
            pass

        match = url_pattern.search(buffer)
        if match:
            return match.group(0)

        time.sleep(0.5)

    _log(f"Timed out waiting for tunnel URL. Buffer so far: {buffer[:500]}")
    return ""


def _start_tunnel(port: int) -> tuple:
    """Start a new cloudflared quick tunnel. Returns (process, url) or (None, '')."""
    _log(f"Starting cloudflared tunnel -> localhost:{port}")

    try:
        proc = subprocess.Popen(
            [CLOUDFLARED_BIN, "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        _log(f"ERROR: cloudflared not found at {CLOUDFLARED_BIN}")
        return None, ""

    url = _extract_tunnel_url(proc)
    if not url:
        # _extract_tunnel_url already logged premature exit if applicable
        if proc.poll() is None:
            _log("Failed to extract tunnel URL, killing process")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        return None, ""

    _log(f"Tunnel live: {url}")

    # Save URL to file for other components to read
    try:
        TUNNEL_URL_FILE.write_text(url)
        _log(f"Saved tunnel URL to {TUNNEL_URL_FILE}")
    except Exception as exc:
        _log(f"Warning: could not save tunnel URL file: {exc}")

    return proc, url


def _update_elevenlabs_agent(tunnel_url: str, api_key: str) -> bool:
    """Update the ElevenLabs agent's custom LLM server URL.

    Uses the ElevenLabs Conversational AI API to update the agent config.
    """
    if not api_key:
        _log("WARNING: No ElevenLabs API key -- cannot update agent URL")
        return False

    try:
        import httpx

        llm_url = f"{tunnel_url}/v1/chat/completions"
        _log(f"Updating ElevenLabs agent {AGENT_ID} -> {llm_url}")

        # First, GET the current agent config
        headers = {"xi-api-key": api_key}
        resp = httpx.get(
            f"{ELEVENLABS_API_BASE}/v1/convai/agents/{AGENT_ID}",
            headers=headers,
            timeout=15,
        )

        if resp.status_code != 200:
            _log(f"Failed to GET agent config: HTTP {resp.status_code} {resp.text[:200]}")
            return False

        agent_config = resp.json()

        # Update the custom LLM URL in the agent's conversation config
        # The structure depends on ElevenLabs API version.
        # Common path: conversation_config.agent.prompt.llm.custom_llm.url
        try:
            llm_config = agent_config.get("conversation_config", {}).get("agent", {}).get("prompt", {}).get("llm", {})
            if "custom_llm" in llm_config:
                llm_config["custom_llm"]["url"] = llm_url
            else:
                _log("Agent does not use custom_llm mode. Cannot update URL via API.")
                _log("Manual update needed in ElevenLabs dashboard.")
                return False
        except (KeyError, TypeError) as exc:
            _log(f"Could not navigate agent config: {exc}")
            return False

        # PATCH the agent with updated config
        resp = httpx.patch(
            f"{ELEVENLABS_API_BASE}/v1/convai/agents/{AGENT_ID}",
            headers={**headers, "Content-Type": "application/json"},
            json={"conversation_config": agent_config["conversation_config"]},
            timeout=15,
        )

        if resp.status_code == 200:
            _log(f"Successfully updated ElevenLabs agent URL to {llm_url}")
            return True
        else:
            _log(f"Failed to PATCH agent: HTTP {resp.status_code} {resp.text[:300]}")
            return False

    except ImportError:
        _log("httpx not installed. Cannot update ElevenLabs agent URL.")
        return False
    except Exception as exc:
        _log(f"Error updating ElevenLabs agent: {exc}")
        return False


def _kill_existing_tunnels(port=None):
    """Kill any existing cloudflared tunnel processes for our port."""
    target_port = port or LOCAL_PORT
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"cloudflared tunnel.*{target_port}"],
            capture_output=True, text=True, timeout=5,
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                pid = pid.strip()
                if pid and pid != str(os.getpid()):
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        _log(f"Killed existing tunnel process {pid}")
                    except (ProcessLookupError, ValueError):
                        pass
            time.sleep(2)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Tunnel Keeper: auto-restart Cloudflare tunnel")
    parser.add_argument("--port", "-p", type=int, default=LOCAL_PORT,
                        help=f"Local port to tunnel (default: {LOCAL_PORT})")
    parser.add_argument("--check-interval", type=int, default=CHECK_INTERVAL,
                        help=f"Seconds between health checks (default: {CHECK_INTERVAL})")
    parser.add_argument("--no-update-agent", action="store_true",
                        help="Skip updating ElevenLabs agent URL")
    args = parser.parse_args()

    port = args.port
    elevenlabs_key = _load_elevenlabs_key()

    _log("=" * 60)
    _log("  Tunnel Keeper starting")
    _log(f"  Local port: {port}")
    _log(f"  Check interval: {args.check_interval}s")
    _log(f"  ElevenLabs key: {'configured' if elevenlabs_key else 'MISSING'}")
    _log(f"  Agent ID: {AGENT_ID}")
    _log("=" * 60)

    # Kill any existing tunnel processes first
    _kill_existing_tunnels(port)

    tunnel_proc = None
    tunnel_url = ""
    restart_count = 0

    # Handle graceful shutdown
    def shutdown(signum, frame):
        _log("Shutting down tunnel keeper...")
        if tunnel_proc and tunnel_proc.poll() is None:
            tunnel_proc.terminate()
            try:
                tunnel_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tunnel_proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    while True:
        # Check if local server is healthy first
        if not _check_local_health(port):
            _log(f"WARNING: Local server on port {port} is not responding")
            _log("Waiting for local server to come up before starting tunnel...")
            time.sleep(args.check_interval)
            continue

        # Start tunnel if not running
        if tunnel_proc is None or tunnel_proc.poll() is not None:
            if tunnel_proc is not None:
                _log(f"Tunnel process died (exit code: {tunnel_proc.returncode})")
            restart_count += 1

            if restart_count > MAX_RESTART_ATTEMPTS:
                backoff = RESTART_BACKOFF_BASE * (2 ** min(restart_count - MAX_RESTART_ATTEMPTS, 5))
                _log(f"Too many attempts ({restart_count}). Backing off {backoff}s...")
                time.sleep(backoff)

            _kill_existing_tunnels(port)
            tunnel_proc, new_url = _start_tunnel(port)

            if tunnel_proc and new_url:
                if new_url != tunnel_url:
                    tunnel_url = new_url
                    _log(f"New tunnel URL: {tunnel_url}")

                    # Update ElevenLabs agent if URL changed
                    if not args.no_update_agent and elevenlabs_key:
                        _update_elevenlabs_agent(tunnel_url, elevenlabs_key)
                    elif not elevenlabs_key:
                        _log("No ElevenLabs API key. Update agent URL manually:")
                        _log(f"  URL: {tunnel_url}/v1/chat/completions")

                restart_count = 0
            else:
                _log("Failed to start tunnel. Will retry...")
                time.sleep(args.check_interval)
                continue

        # Health check the tunnel
        if tunnel_url and not _check_tunnel_health(tunnel_url, port):
            _log("Tunnel health check failed. Restarting tunnel...")
            if tunnel_proc and tunnel_proc.poll() is None:
                tunnel_proc.terminate()
                try:
                    tunnel_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    tunnel_proc.kill()
            tunnel_proc = None
            continue

        time.sleep(args.check_interval)


if __name__ == "__main__":
    main()
