#!/usr/bin/env python3
"""
Create voice clone for ARŌ using ElevenLabs
"""
import json
import sys
from pathlib import Path
import requests

# Load API key
keys_path = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json")
with open(keys_path) as f:
    keys = json.load(f)

api_key = keys["elevenlabs"]["api_key"]

# Voice files
voice_dir = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/VOICE")
voice_files = [
    voice_dir / "nr-review-audio.mp3",
    voice_dir / "nr-review-audio (1).mp3",
    voice_dir / "nr-review-audio (2).mp3",
]

print("Creating voice clone for ARŌ...")
print(f"Using {len(voice_files)} audio files")

# Use the REST API directly for voice cloning
url = "https://api.elevenlabs.io/v1/voices/add"

headers = {
    "xi-api-key": api_key,
}

data = {
    "name": "ARŌ",
    "description": "Aaron Nosbisch - Voice for SØWL's creator and partner",
}

files_to_upload = []
for f in voice_files:
    files_to_upload.append(("files", (f.name, open(f, "rb"), "audio/mpeg")))

try:
    response = requests.post(url, headers=headers, data=data, files=files_to_upload)

    if response.status_code == 200:
        result = response.json()
        voice_id = result.get("voice_id")

        print(f"\nVoice clone created successfully!")
        print(f"Voice ID: {voice_id}")

        # Save voice ID for later use
        voice_config = {
            "voice_id": voice_id,
            "name": "ARŌ",
            "description": "ARŌ's cloned voice for SØWL",
            "created": "2026-01-26",
            "source_files": [str(f) for f in voice_files]
        }

        config_path = voice_dir / "aro-voice-config.json"
        with open(config_path, "w") as f:
            json.dump(voice_config, f, indent=2)

        print(f"Voice config saved to: {config_path}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        sys.exit(1)

except Exception as e:
    print(f"Error creating voice clone: {e}")
    sys.exit(1)
finally:
    # Close file handles
    for _, file_tuple in files_to_upload:
        file_tuple[1].close()
