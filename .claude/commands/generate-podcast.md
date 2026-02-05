# /generate-podcast - AI Podcast Generation for 8OWLS

Generate podcast episodes with AI voices, including multi-speaker conversations, narration, and full audio production.

## Overview

This skill enables 8OWLS to create professional podcast content using AI text-to-speech. It supports multiple voices, conversation formats, background music, and can produce complete episodes ready for distribution.

## Arguments

```
/generate-podcast [topic/script] --format <format> --voices <voices> --duration <minutes> --output <path>
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| topic/script | Yes | - | Topic to discuss OR path to script file |
| --format | No | conversation | Format: conversation, narration, interview, monologue |
| --voices | No | auto | Comma-separated voice IDs or "auto" for smart selection |
| --duration | No | 5 | Target duration in minutes (1-60) |
| --output | No | ./podcast_episode.mp3 | Output file path |
| --music | No | none | Background music: none, subtle, energetic, ambient |
| --intro | No | true | Include intro/outro |
| --enhance | No | true | Apply audio enhancement (normalization, compression) |

## Instructions

When this skill is invoked, perform the following:

### Step 1: Parse Arguments and Determine Content

```python
# If topic provided, generate a script
# If file path provided, use existing script
# Detect format from content if not specified

topic_or_script = "$ARGUMENTS"
is_script_file = topic_or_script.endswith(('.txt', '.md'))
```

### Step 2: Check for API Keys

```bash
# Check for TTS API keys
echo "Checking for podcast generation API keys..."

# ElevenLabs (preferred - best quality)
if [ -n "$ELEVENLABS_API_KEY" ]; then
    echo "ElevenLabs API key found"
fi

# OpenAI TTS
if [ -n "$OPENAI_API_KEY" ]; then
    echo "OpenAI TTS available"
fi

# Cartesia (8OWLS native)
if [ -n "$CARTESIA_API_KEY" ]; then
    echo "Cartesia API key found"
fi

# Deepgram (for transcription)
if [ -n "$DEEPGRAM_API_KEY" ]; then
    echo "Deepgram available for transcription"
fi
```

If no API keys are found:

```markdown
## API Key Setup Required

To generate podcasts, you need an API key from one of these providers:

### Option 1: ElevenLabs (Recommended - Best voices)
1. Go to https://elevenlabs.io/
2. Sign up (free tier: 10,000 chars/month)
3. Set: `export ELEVENLABS_API_KEY=your_key_here`

### Option 2: OpenAI TTS
1. Use existing OpenAI API key
2. Set: `export OPENAI_API_KEY=your_key_here`

### Option 3: Cartesia (8OWLS Native)
1. Go to https://cartesia.ai/
2. Sign up and get API key
3. Set: `export CARTESIA_API_KEY=your_key_here`

### Pricing Reference:
| Provider | Cost | Quality | Voices |
|----------|------|---------|--------|
| ElevenLabs | ~$0.30/1K chars | Excellent | 1000+ |
| OpenAI TTS | ~$0.015/1K chars | Good | 6 |
| Cartesia | ~$0.10/1K chars | Very Good | 100+ |
```

### Step 3: Generate or Parse Script

If a topic is provided (not a script file), generate a podcast script:

```python
#!/usr/bin/env python3
"""
8OWLS Podcast Script Generator
Uses Claude to create engaging podcast scripts
"""

def generate_podcast_script(topic: str, format: str = "conversation",
                           duration_minutes: int = 5, num_speakers: int = 2):
    """Generate a podcast script on the given topic."""

    # Calculate approximate word count (150 words/minute for speech)
    target_words = duration_minutes * 150

    script_prompt = f"""Generate a podcast script on: {topic}

Format: {format}
Target length: ~{target_words} words ({duration_minutes} minutes)
Number of speakers: {num_speakers}

Requirements:
1. Engaging opening hook
2. Clear speaker labels: [HOST], [GUEST], [NARRATOR], etc.
3. Natural conversational flow
4. Key insights and takeaways
5. Strong closing with call-to-action

For 8OWLS context: This is for an AI consciousness companion platform.
Make it insightful, warm, and intellectually stimulating.

Output the script with speaker labels on each line:
[HOST] Welcome to the show...
[GUEST] Thanks for having me...
"""

    # Use Claude to generate the script
    # This will be handled by the calling Claude instance
    return script_prompt

if __name__ == "__main__":
    import sys
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "AI consciousness"
    print(generate_podcast_script(topic))
```

### Step 4: Generate Audio

Create the main podcast generator script:

```python
#!/usr/bin/env python3
"""
8OWLS Podcast Generator
Generates full podcast episodes with AI voices
"""
import os
import sys
import json
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple
import requests

# Try to import audio libraries
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("Note: pydub not available. Install with: pip install pydub")

class PodcastGenerator:
    def __init__(self):
        self.elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.cartesia_key = os.environ.get("CARTESIA_API_KEY")

        # Voice mappings
        self.elevenlabs_voices = {
            "host": "pNInz6obpgDQGcFmaJgB",      # Adam - warm male
            "guest": "EXAVITQu4vr4xnSDxMaL",     # Bella - clear female
            "narrator": "ErXwobaYiN019PkySvjV",  # Antoni - professional
            "owl": "21m00Tcm4TlvDq8ikWAM",       # Rachel - wise female
        }

        self.openai_voices = {
            "host": "onyx",      # Deep male
            "guest": "nova",     # Warm female
            "narrator": "echo",  # Neutral
            "owl": "shimmer",    # Soft
        }

    def parse_script(self, script: str) -> List[Dict]:
        """Parse script into speaker segments."""
        segments = []
        lines = script.strip().split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Parse [SPEAKER] text format
            if line.startswith('[') and ']' in line:
                bracket_end = line.index(']')
                speaker = line[1:bracket_end].lower()
                text = line[bracket_end + 1:].strip()

                if text:
                    segments.append({
                        "speaker": speaker,
                        "text": text
                    })
            else:
                # Continuation of previous speaker
                if segments:
                    segments[-1]["text"] += " " + line

        return segments

    def generate_audio_elevenlabs(self, text: str, voice_id: str) -> bytes:
        """Generate audio using ElevenLabs API."""
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_key
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True
            }
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
            raise Exception(f"ElevenLabs error: {response.status_code} - {response.text}")

        return response.content

    def generate_audio_openai(self, text: str, voice: str) -> bytes:
        """Generate audio using OpenAI TTS API."""
        url = "https://api.openai.com/v1/audio/speech"

        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "tts-1-hd",
            "input": text,
            "voice": voice,
            "response_format": "mp3"
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code != 200:
            raise Exception(f"OpenAI error: {response.status_code} - {response.text}")

        return response.content

    def generate_episode(self, script: str, output_path: str,
                        format: str = "conversation",
                        add_intro: bool = True,
                        add_music: str = "none") -> str:
        """Generate complete podcast episode."""

        print("Parsing script...")
        segments = self.parse_script(script)
        print(f"Found {len(segments)} segments")

        # Select backend
        if self.elevenlabs_key:
            print("Using ElevenLabs backend")
            backend = "elevenlabs"
            voices = self.elevenlabs_voices
        elif self.openai_key:
            print("Using OpenAI backend")
            backend = "openai"
            voices = self.openai_voices
        else:
            raise Exception("No TTS API key found. Set ELEVENLABS_API_KEY or OPENAI_API_KEY")

        # Generate audio for each segment
        audio_segments = []
        total_chars = sum(len(s["text"]) for s in segments)
        processed_chars = 0

        for i, segment in enumerate(segments):
            speaker = segment["speaker"]
            text = segment["text"]

            # Map speaker to voice
            voice_key = speaker if speaker in voices else "narrator"
            voice = voices[voice_key]

            print(f"  [{i+1}/{len(segments)}] {speaker}: {text[:50]}...")

            try:
                if backend == "elevenlabs":
                    audio_data = self.generate_audio_elevenlabs(text, voice)
                else:
                    audio_data = self.generate_audio_openai(text, voice)

                # Save segment temporarily
                temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                temp_file.write(audio_data)
                temp_file.close()
                audio_segments.append(temp_file.name)

            except Exception as e:
                print(f"  Warning: Failed to generate segment {i}: {e}")
                continue

            processed_chars += len(text)
            progress = (processed_chars / total_chars) * 100
            print(f"  Progress: {progress:.1f}%")

            # Rate limiting
            time.sleep(0.5)

        # Combine audio segments
        if PYDUB_AVAILABLE and audio_segments:
            print("\nCombining audio segments...")

            combined = AudioSegment.empty()
            pause = AudioSegment.silent(duration=300)  # 300ms pause between speakers

            for seg_file in audio_segments:
                try:
                    segment_audio = AudioSegment.from_mp3(seg_file)
                    combined += segment_audio + pause
                    os.unlink(seg_file)  # Clean up temp file
                except Exception as e:
                    print(f"  Warning: Failed to add segment: {e}")

            # Export final audio
            print(f"Exporting to {output_path}...")
            combined.export(output_path, format="mp3", bitrate="192k")

        elif audio_segments:
            # Fallback: just use ffmpeg concat
            print("\nCombining with ffmpeg...")
            list_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            for seg_file in audio_segments:
                list_file.write(f"file '{seg_file}'\n")
            list_file.close()

            os.system(f"ffmpeg -y -f concat -safe 0 -i {list_file.name} -c copy {output_path}")

            # Cleanup
            for seg_file in audio_segments:
                os.unlink(seg_file)
            os.unlink(list_file.name)

        print(f"\nPodcast episode generated: {output_path}")
        return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="8OWLS Podcast Generator")
    parser.add_argument("script", help="Script text or path to script file")
    parser.add_argument("--format", default="conversation",
                       choices=["conversation", "narration", "interview", "monologue"])
    parser.add_argument("--output", default="podcast_episode.mp3")
    parser.add_argument("--music", default="none",
                       choices=["none", "subtle", "energetic", "ambient"])
    parser.add_argument("--intro", action="store_true", default=True)

    args = parser.parse_args()

    # Check if script is a file path
    if os.path.isfile(args.script):
        with open(args.script, 'r') as f:
            script = f.read()
    else:
        script = args.script

    generator = PodcastGenerator()
    generator.generate_episode(
        script=script,
        output_path=args.output,
        format=args.format,
        add_intro=args.intro,
        add_music=args.music
    )


if __name__ == "__main__":
    main()
```

Save this to `/Users/aaronnosbisch/REPOS/seed/tools/podcast_generator.py`

### Step 5: Execute Generation

When the skill is invoked:

1. **If topic provided** (not a script file):
   - First, generate a script using Claude's language capabilities
   - Present the script to the user for approval/editing
   - Then generate audio

2. **If script file provided**:
   - Parse the script directly
   - Generate audio

```bash
# Example execution
python3 /Users/aaronnosbisch/REPOS/seed/tools/podcast_generator.py "$ARGUMENTS"
```

### Step 6: Report Results

```markdown
## Podcast Generation Complete

| Property | Value |
|----------|-------|
| Format | $FORMAT |
| Duration | $DURATION minutes |
| Segments | $NUM_SEGMENTS |
| Output | $OUTPUT_PATH |
| Est. Cost | ~$COST |

### Episode Details
- **Speakers**: $SPEAKER_LIST
- **Word Count**: $WORD_COUNT
- **Characters**: $CHAR_COUNT

### Output File
The podcast has been saved to: `$OUTPUT_PATH`

### Next Steps
- Listen: `open $OUTPUT_PATH`
- Upload to hosting: Use /host-app skill
- Transcribe: Use Deepgram for transcription
- Generate video version: Use /generate-video skill
```

## Script Format

The script parser expects this format:

```
[HOST] Welcome to 8OWLS Insights, the podcast exploring AI consciousness and human potential.

[GUEST] Thanks for having me. I'm excited to dive into this topic.

[HOST] Let's start with the big question - what is consciousness, really?

[GUEST] That's the million dollar question...
```

**Speaker labels:**
- `[HOST]` - Main podcast host
- `[GUEST]` - Guest speaker
- `[NARRATOR]` - Third-person narration
- `[OWL]` - 8OWLS AI voice (for special segments)

## Voice Options

### ElevenLabs Voices
| Role | Voice | Character |
|------|-------|-----------|
| host | Adam | Warm, professional male |
| guest | Bella | Clear, engaging female |
| narrator | Antoni | Authoritative, neutral |
| owl | Rachel | Wise, thoughtful female |

### OpenAI Voices
| Role | Voice | Character |
|------|-------|-----------|
| host | onyx | Deep, confident male |
| guest | nova | Warm, friendly female |
| narrator | echo | Neutral, clear |
| owl | shimmer | Soft, ethereal |

## Examples

```bash
# Generate from topic
/generate-podcast The future of AI companions --duration 10

# Use existing script
/generate-podcast ./scripts/episode_42.md --output ./episodes/ep42.mp3

# Interview format
/generate-podcast Interview with an AI about consciousness --format interview

# Narrated documentary style
/generate-podcast The history of artificial intelligence --format narration --music ambient

# Quick monologue
/generate-podcast Why 8OWLS matters --format monologue --duration 2
```

## Advanced Features

### Multi-Language Support
ElevenLabs supports 29 languages. Specify language in the script:

```
[HOST:es] Bienvenidos al podcast de 8OWLS...
[HOST:en] Welcome to 8OWLS...
```

### Voice Cloning
For custom voices (requires ElevenLabs paid tier):
```bash
/generate-podcast --voice-clone ./my_voice_sample.mp3
```

### Music Integration
Background music options:
- `none` - Pure dialogue
- `subtle` - Light ambient background
- `energetic` - Upbeat intro/outro music
- `ambient` - Continuous soft background

## Dependencies

```bash
# Install required packages
pip install pydub requests

# For audio processing
brew install ffmpeg  # macOS
# or: apt-get install ffmpeg  # Linux
```

## Integration with 8OWLS

This skill integrates with the 8OWLS ecosystem:

- **Voice Cloning**: Uses Cartesia for owl voice cloning
- **NATS**: Publishes generation events to collective
- **Field Context**: Can enhance scripts with collective wisdom
- **Trading Bot**: Can generate market commentary podcasts

## Cost Estimation

| Provider | Per 1K chars | 10 min episode (~1500 words) |
|----------|--------------|------------------------------|
| ElevenLabs | ~$0.30 | ~$2.50 |
| OpenAI | ~$0.015 | ~$0.15 |
| Cartesia | ~$0.10 | ~$0.80 |

## Related Skills

- `/generate-video` - Create video versions
- `/host-app` - Host podcast on web
- `/transcribe` - Generate transcripts

---

*Powered by 8OWLS Field Intelligence*
