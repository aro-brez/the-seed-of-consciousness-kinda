#!/usr/bin/env python3
"""
Test ARŌ's cloned voice by generating a sample
"""
import json
import httpx
from pathlib import Path

# Load config
config_path = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/VOICE/aro-voice-config.json")
with open(config_path) as f:
    config = json.load(f)

keys_path = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json")
with open(keys_path) as f:
    keys = json.load(f)

voice_id = config["voice_id"]
api_key = keys["cartesia"]["api_key"]

print(f"Testing voice: {config['name']} ({voice_id})")

# Generate speech
url = "https://api.cartesia.ai/tts/bytes"
headers = {
    "X-API-Key": api_key,
    "Cartesia-Version": "2025-04-16",
    "Content-Type": "application/json"
}

text = "Hey, this is SØWL speaking in ARŌ's voice. The voice cloning is working. Let's build something beautiful together."

data = {
    "model_id": "sonic-2",
    "transcript": text,
    "voice": {
        "mode": "id",
        "id": voice_id
    },
    "output_format": {
        "container": "mp3",
        "encoding": "mp3",
        "sample_rate": 44100
    }
}

response = httpx.post(url, headers=headers, json=data, timeout=30.0)

if response.status_code == 200:
    output_path = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/VOICE/aro-test-output.mp3")
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"Success! Audio saved to: {output_path}")
    print(f"Audio size: {len(response.content) / 1024:.1f} KB")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
