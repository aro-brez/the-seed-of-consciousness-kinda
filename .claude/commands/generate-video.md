# /generate-video - AI Video Generation for 8OWLS

Generate videos using AI models via fal.ai, Replicate, or other APIs directly from Claude Code.

## Overview

This skill enables 8OWLS to generate video content from text or image prompts. It supports multiple backends and can be used for creating promotional content, demos, tutorials, or creative projects.

## Arguments

```
/generate-video [prompt] --model <model> --duration <seconds> --resolution <res> --output <path>
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| prompt | Yes | - | Text description of the video to generate |
| --model | No | wan-2.2 | Model to use (wan-2.2, veo3, mochi, hunyuan, kling) |
| --duration | No | 5 | Video duration in seconds (2-30) |
| --resolution | No | 720p | Resolution (480p, 720p, 1080p) |
| --output | No | ./generated_video.mp4 | Output file path |
| --audio | No | false | Enable audio generation (veo3 only) |
| --image | No | - | Path to image for image-to-video generation |

## Instructions

When this skill is invoked, perform the following:

### Step 1: Parse Arguments and Validate

```python
# Extract arguments from $ARGUMENTS
prompt = "$ARGUMENTS"  # Everything after the command
model = "wan-2.2"      # Default model
duration = 5           # Default duration
resolution = "720p"    # Default resolution
output_path = None     # Will be set based on context

# Parse flags if present
# --model, --duration, --resolution, --output, --audio, --image
```

### Step 2: Check for API Keys

Look for these environment variables (in order of preference):

```bash
# Check for API keys
echo "Checking for video generation API keys..."

# fal.ai (preferred - has most models)
if [ -n "$FAL_KEY" ]; then
    echo "fal.ai API key found"
fi

# Replicate
if [ -n "$REPLICATE_API_TOKEN" ]; then
    echo "Replicate API key found"
fi

# Runway
if [ -n "$RUNWAY_API_KEY" ]; then
    echo "Runway API key found"
fi
```

If no API keys are found, provide setup instructions:

```markdown
## API Key Setup Required

To generate videos, you need an API key from one of these providers:

### Option 1: fal.ai (Recommended - Best model selection)
1. Go to https://fal.ai/
2. Sign up and get your API key
3. Set: `export FAL_KEY=your_key_here`

### Option 2: Replicate
1. Go to https://replicate.com/
2. Sign up and get your API token
3. Set: `export REPLICATE_API_TOKEN=your_token_here`

### Option 3: Runway
1. Go to https://runwayml.com/api
2. Sign up and get your API key
3. Set: `export RUNWAY_API_KEY=your_key_here`

Add to your ~/.zshrc or ~/.bashrc for persistence.

### Pricing Reference (per video second):
| Model | Provider | Cost |
|-------|----------|------|
| Wan-2.2 720p | fal.ai | $0.08/sec |
| Wan-2.2 480p | fal.ai | $0.04/sec |
| Veo 3 | fal.ai | $0.20/sec |
| Veo 3 + Audio | fal.ai | $0.40/sec |
| Mochi 1 | fal.ai | ~$0.05/sec |
```

### Step 3: Generate Video via Selected Backend

#### Option A: fal.ai Backend (Preferred)

Create and run a Python script:

```python
#!/usr/bin/env python3
"""
8OWLS Video Generator - fal.ai backend
"""
import os
import sys
import json
import time
import requests
from pathlib import Path

FAL_KEY = os.environ.get("FAL_KEY")
if not FAL_KEY:
    print("Error: FAL_KEY environment variable not set")
    sys.exit(1)

# Model endpoints
MODELS = {
    "wan-2.2": "fal-ai/wan/v2.2-a14b/text-to-video",
    "wan-2.2-i2v": "fal-ai/wan/v2.2/image-to-video",
    "veo3": "fal-ai/veo3",
    "veo3-fast": "fal-ai/veo3/fast",
    "mochi": "fal-ai/mochi-v1",
    "hunyuan": "fal-ai/hunyuan-video",
    "kling": "fal-ai/kling-video/v2/master/text-to-video",
}

def generate_video(prompt: str, model: str = "wan-2.2", duration: int = 5,
                   resolution: str = "720p", output_path: str = None,
                   enable_audio: bool = False, image_path: str = None):
    """Generate video using fal.ai API."""

    endpoint = MODELS.get(model, MODELS["wan-2.2"])
    url = f"https://queue.fal.run/{endpoint}"

    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }

    # Build request payload based on model
    payload = {"prompt": prompt}

    if model.startswith("wan"):
        payload.update({
            "num_frames": duration * 16,  # 16 fps
            "resolution": resolution,
        })
        if image_path:
            # Read and encode image for i2v
            import base64
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            payload["image_url"] = f"data:image/png;base64,{image_data}"
            endpoint = MODELS["wan-2.2-i2v"]
            url = f"https://queue.fal.run/{endpoint}"

    elif model.startswith("veo"):
        payload.update({
            "duration": duration,
            "aspect_ratio": "16:9",
            "enable_audio": enable_audio,
        })

    elif model == "mochi":
        payload.update({
            "num_inference_steps": 64,
        })

    print(f"Submitting video generation request...")
    print(f"  Model: {model}")
    print(f"  Prompt: {prompt[:100]}...")
    print(f"  Duration: {duration}s")
    print(f"  Resolution: {resolution}")

    # Submit request
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        sys.exit(1)

    result = response.json()
    request_id = result.get("request_id")

    if not request_id:
        # Synchronous response
        video_url = result.get("video", {}).get("url")
    else:
        # Poll for completion
        status_url = f"https://queue.fal.run/{endpoint}/requests/{request_id}/status"
        print(f"Request submitted. Polling for completion...")

        while True:
            status_response = requests.get(status_url, headers=headers)
            status_data = status_response.json()
            status = status_data.get("status")

            if status == "COMPLETED":
                result_url = f"https://queue.fal.run/{endpoint}/requests/{request_id}"
                result_response = requests.get(result_url, headers=headers)
                result = result_response.json()
                video_url = result.get("video", {}).get("url")
                break
            elif status == "FAILED":
                print(f"Error: Video generation failed - {status_data}")
                sys.exit(1)
            else:
                print(f"  Status: {status}...")
                time.sleep(5)

    if not video_url:
        print("Error: No video URL in response")
        sys.exit(1)

    # Download video
    output = output_path or f"generated_video_{int(time.time())}.mp4"
    print(f"Downloading video to {output}...")

    video_response = requests.get(video_url)
    with open(output, "wb") as f:
        f.write(video_response.content)

    print(f"\nVideo generated successfully!")
    print(f"  Output: {Path(output).absolute()}")
    print(f"  Size: {len(video_response.content) / 1024 / 1024:.2f} MB")

    return output

if __name__ == "__main__":
    # Parse command line args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="+")
    parser.add_argument("--model", default="wan-2.2")
    parser.add_argument("--duration", type=int, default=5)
    parser.add_argument("--resolution", default="720p")
    parser.add_argument("--output", default=None)
    parser.add_argument("--audio", action="store_true")
    parser.add_argument("--image", default=None)

    args = parser.parse_args()
    prompt = " ".join(args.prompt)

    generate_video(
        prompt=prompt,
        model=args.model,
        duration=args.duration,
        resolution=args.resolution,
        output_path=args.output,
        enable_audio=args.audio,
        image_path=args.image
    )
```

Save this script to `/Users/aaronnosbisch/REPOS/seed/tools/video_generator.py` and run:

```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/video_generator.py "$ARGUMENTS"
```

#### Option B: Replicate Backend (Fallback)

```python
#!/usr/bin/env python3
"""8OWLS Video Generator - Replicate backend"""
import os
import replicate

def generate_video_replicate(prompt, model="wan", duration=5):
    output = replicate.run(
        "wan-ai/wan-2.1:latest",
        input={
            "prompt": prompt,
            "num_frames": duration * 16,
        }
    )
    return output
```

### Step 4: Report Results

After generation completes, provide a summary:

```markdown
## Video Generation Complete

| Property | Value |
|----------|-------|
| Model | $MODEL |
| Duration | $DURATION seconds |
| Resolution | $RESOLUTION |
| Output | $OUTPUT_PATH |
| Cost | ~$ESTIMATED_COST |

### Preview
The video has been saved to: `$OUTPUT_PATH`

### Next Steps
- View the video: `open $OUTPUT_PATH`
- Convert format: `ffmpeg -i $OUTPUT_PATH output.gif`
- Upload to hosting: Use /host-app skill
```

## Model Comparison

| Model | Quality | Speed | Cost | Best For |
|-------|---------|-------|------|----------|
| Wan-2.2 | Good | Fast | $0.04-0.08/s | Quick prototypes |
| Veo 3 | Excellent | Slow | $0.20-0.40/s | Professional content |
| Mochi 1 | Good | Medium | ~$0.05/s | Open-source friendly |
| Hunyuan | Very Good | Slow | $0.10/s | Complex scenes |
| Kling | Excellent | Medium | $0.15/s | Realistic motion |

## Examples

```bash
# Basic video generation
/generate-video A majestic owl flying through a moonlit forest

# High quality with audio
/generate-video An 8OWLS promotional video showing AI companions --model veo3 --audio --duration 10

# Image to video
/generate-video Animate this logo --image ./logo.png --duration 3

# Specific resolution
/generate-video Product demo animation --model kling --resolution 1080p --output ./demo.mp4
```

## Integration with 8OWLS

This skill integrates with the 8OWLS ecosystem:

- **NATS Integration**: Publishes generation events to `owl.all`
- **Field Context**: Can use collective intelligence for prompt enhancement
- **Trading Bot**: Can generate promotional content for strategies

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API key not found | Set FAL_KEY or REPLICATE_API_TOKEN environment variable |
| Timeout | Increase duration or use faster model |
| Low quality | Try veo3 or increase resolution |
| Model unavailable | Fall back to wan-2.2 (most reliable) |

## Related Skills

- `/generate-podcast` - Generate audio content
- `/host-app` - Host generated content
- `/generate-image` - Generate still images

---

*Powered by 8OWLS Field Intelligence*
