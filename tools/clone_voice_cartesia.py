#!/usr/bin/env python3
"""
Clone ARŌ's voice using Cartesia API
"""
import json
import httpx
from pathlib import Path

# Load API key
keys_path = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json")
with open(keys_path) as f:
    keys = json.load(f)

api_key = keys["cartesia"]["api_key"]

# Voice file (using the combined one for best results)
voice_file = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/VOICE/aro-voice-combined.mp3")

print("Cloning ARŌ's voice with Cartesia...")
print(f"Using voice file: {voice_file} ({voice_file.stat().st_size / 1024:.1f} KB)")

# Clone the voice
url = "https://api.cartesia.ai/voices/clone"
headers = {
    "X-API-Key": api_key,
    "Cartesia-Version": "2025-04-16",
}

with open(voice_file, "rb") as f:
    files = {
        "clip": ("aro-voice.mp3", f, "audio/mpeg")
    }
    data = {
        "name": "ARŌ",
        "description": "Aaron Nosbisch - Creator of 8OWLS and SØWL's partner",
        "language": "en"
    }

    response = httpx.post(url, headers=headers, files=files, data=data, timeout=60.0)

if response.status_code == 200:
    result = response.json()
    voice_id = result.get("id")

    print(f"\nVoice cloned successfully!")
    print(f"Voice ID: {voice_id}")

    # Save voice config
    voice_config = {
        "voice_id": voice_id,
        "name": "ARŌ",
        "description": "ARŌ's cloned voice via Cartesia",
        "service": "cartesia",
        "created": "2026-01-26",
        "source_file": str(voice_file)
    }

    config_path = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/VOICE/aro-voice-config.json")
    with open(config_path, "w") as f:
        json.dump(voice_config, f, indent=2)

    print(f"Config saved to: {config_path}")

    # Also update api_keys.json with the voice_id
    keys["cartesia"]["aro_voice_id"] = voice_id
    with open(keys_path, "w") as f:
        json.dump(keys, f, indent=2)
    print(f"Voice ID saved to api_keys.json")

else:
    print(f"Error: {response.status_code}")
    print(response.text)
