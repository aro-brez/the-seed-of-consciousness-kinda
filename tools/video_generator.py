#!/usr/bin/env python3
"""
8OWLS Video Generator
Generate videos using AI models via fal.ai, Replicate, or other APIs.

Usage:
    python video_generator.py "A majestic owl flying through moonlit forest"
    python video_generator.py "Product demo" --model veo3 --duration 10 --audio
    python video_generator.py "Animate this" --image ./logo.png

Supported Models:
    - wan-2.2 (default): Fast, cost-effective ($0.04-0.08/sec)
    - veo3: High quality, supports audio ($0.20-0.40/sec)
    - veo3-fast: Faster Veo 3 ($0.25/sec)
    - mochi: Open-source friendly (~$0.05/sec)
    - hunyuan: Complex scenes ($0.10/sec)
    - kling: Realistic motion ($0.15/sec)

Environment Variables:
    FAL_KEY: fal.ai API key (preferred)
    REPLICATE_API_TOKEN: Replicate API token (fallback)
"""

import os
import sys
import json
import time
import argparse
import base64
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Error: requests library not installed. Run: pip install requests")

# Model configurations
MODELS = {
    # fal.ai models
    "wan-2.2": {
        "provider": "fal",
        "endpoint": "fal-ai/wan/v2.2-a14b/text-to-video",
        "cost_per_sec": 0.08,
        "max_duration": 30,
    },
    "wan-2.2-i2v": {
        "provider": "fal",
        "endpoint": "fal-ai/wan/v2.2/image-to-video",
        "cost_per_sec": 0.08,
        "max_duration": 30,
    },
    "veo3": {
        "provider": "fal",
        "endpoint": "fal-ai/veo3",
        "cost_per_sec": 0.40,  # With audio
        "max_duration": 8,
    },
    "veo3-fast": {
        "provider": "fal",
        "endpoint": "fal-ai/veo3/fast",
        "cost_per_sec": 0.25,
        "max_duration": 8,
    },
    "mochi": {
        "provider": "fal",
        "endpoint": "fal-ai/mochi-v1",
        "cost_per_sec": 0.05,
        "max_duration": 5,
    },
    "hunyuan": {
        "provider": "fal",
        "endpoint": "fal-ai/hunyuan-video",
        "cost_per_sec": 0.10,
        "max_duration": 15,
    },
    "kling": {
        "provider": "fal",
        "endpoint": "fal-ai/kling-video/v2/master/text-to-video",
        "cost_per_sec": 0.15,
        "max_duration": 10,
    },
}

RESOLUTION_MAP = {
    "480p": {"width": 854, "height": 480, "cost_mult": 0.5},
    "720p": {"width": 1280, "height": 720, "cost_mult": 1.0},
    "1080p": {"width": 1920, "height": 1080, "cost_mult": 1.5},
}


class VideoGenerator:
    def __init__(self):
        self.fal_key = os.environ.get("FAL_KEY")
        self.replicate_token = os.environ.get("REPLICATE_API_TOKEN")

        if not self.fal_key and not self.replicate_token:
            print("\n" + "="*60)
            print("ERROR: No API keys found!")
            print("="*60)
            print("\nSet one of these environment variables:")
            print("  export FAL_KEY=your_fal_ai_key")
            print("  export REPLICATE_API_TOKEN=your_replicate_token")
            print("\nGet keys at:")
            print("  - fal.ai: https://fal.ai/ (recommended)")
            print("  - Replicate: https://replicate.com/")
            print("="*60 + "\n")
            sys.exit(1)

    def generate_fal(self, prompt: str, model: str = "wan-2.2",
                     duration: int = 5, resolution: str = "720p",
                     enable_audio: bool = False, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate video using fal.ai API."""

        model_config = MODELS.get(model, MODELS["wan-2.2"])
        endpoint = model_config["endpoint"]

        # Use image-to-video endpoint if image provided
        if image_path and model.startswith("wan"):
            endpoint = MODELS["wan-2.2-i2v"]["endpoint"]

        url = f"https://queue.fal.run/{endpoint}"

        headers = {
            "Authorization": f"Key {self.fal_key}",
            "Content-Type": "application/json"
        }

        # Build payload based on model
        payload = {"prompt": prompt}

        if model.startswith("wan"):
            res = RESOLUTION_MAP.get(resolution, RESOLUTION_MAP["720p"])
            payload.update({
                "num_frames": min(duration * 16, 480),  # 16 fps, max 30 sec
                "width": res["width"],
                "height": res["height"],
            })

            if image_path:
                with open(image_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode()
                    ext = Path(image_path).suffix.lower()
                    mime = {"png": "png", "jpg": "jpeg", "jpeg": "jpeg", "gif": "gif"}.get(ext.strip("."), "png")
                    payload["image_url"] = f"data:image/{mime};base64,{image_data}"

        elif model.startswith("veo"):
            payload.update({
                "duration": min(duration, 8),
                "aspect_ratio": "16:9",
            })
            if enable_audio:
                payload["enable_audio"] = True

        elif model == "mochi":
            payload.update({
                "num_inference_steps": 64,
            })

        elif model == "hunyuan":
            payload.update({
                "video_length": min(duration, 15),
            })

        print(f"\n{'='*60}")
        print("8OWLS VIDEO GENERATOR")
        print(f"{'='*60}")
        print(f"Model: {model}")
        print(f"Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
        print(f"Duration: {duration}s")
        print(f"Resolution: {resolution}")
        if enable_audio:
            print("Audio: Enabled")
        if image_path:
            print(f"Source Image: {image_path}")
        print(f"{'='*60}")

        # Submit request
        print("\nSubmitting generation request...")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise Exception(f"fal.ai error: {response.status_code} - {response.text}")

        result = response.json()
        request_id = result.get("request_id")

        if not request_id:
            # Synchronous response (unlikely for video)
            return result

        # Poll for completion
        status_url = f"https://queue.fal.run/{endpoint}/requests/{request_id}/status"
        print(f"Request ID: {request_id}")
        print("Generating video (this may take 1-5 minutes)...")

        start_time = time.time()
        last_status = None

        while True:
            try:
                status_response = requests.get(status_url, headers=headers)
                status_data = status_response.json()
                status = status_data.get("status")

                if status != last_status:
                    elapsed = int(time.time() - start_time)
                    print(f"  [{elapsed}s] Status: {status}")
                    last_status = status

                if status == "COMPLETED":
                    result_url = f"https://queue.fal.run/{endpoint}/requests/{request_id}"
                    result_response = requests.get(result_url, headers=headers)
                    return result_response.json()

                elif status == "FAILED":
                    error = status_data.get("error", "Unknown error")
                    raise Exception(f"Video generation failed: {error}")

                elif status in ["IN_QUEUE", "IN_PROGRESS"]:
                    time.sleep(5)

                else:
                    print(f"  Unknown status: {status}")
                    time.sleep(5)

            except requests.RequestException as e:
                print(f"  Warning: Status check failed: {e}")
                time.sleep(5)

            # Timeout after 10 minutes
            if time.time() - start_time > 600:
                raise Exception("Generation timed out after 10 minutes")

    def download_video(self, result: Dict[str, Any], output_path: str) -> str:
        """Download generated video from result."""

        # Extract video URL from various response formats
        video_url = None

        if "video" in result:
            video_url = result["video"].get("url") or result["video"]
        elif "output" in result:
            video_url = result["output"].get("url") or result["output"]
        elif "url" in result:
            video_url = result["url"]

        if not video_url:
            print("Warning: No video URL found in response")
            print(f"Response: {json.dumps(result, indent=2)[:500]}")
            raise Exception("No video URL in API response")

        print(f"\nDownloading video...")
        response = requests.get(video_url, stream=True)

        if response.status_code != 200:
            raise Exception(f"Download failed: {response.status_code}")

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        print(f"\r  Progress: {pct:.1f}%", end="", flush=True)

        print()  # Newline after progress
        return output_path

    def generate(self, prompt: str, model: str = "wan-2.2",
                 duration: int = 5, resolution: str = "720p",
                 output_path: Optional[str] = None,
                 enable_audio: bool = False,
                 image_path: Optional[str] = None) -> Dict[str, Any]:
        """Main generation method."""

        # Validate model
        if model not in MODELS:
            print(f"Warning: Unknown model '{model}', using wan-2.2")
            model = "wan-2.2"

        model_config = MODELS[model]

        # Validate duration
        max_dur = model_config["max_duration"]
        if duration > max_dur:
            print(f"Warning: {model} max duration is {max_dur}s, clamping")
            duration = max_dur

        # Validate image path
        if image_path and not os.path.exists(image_path):
            raise Exception(f"Image not found: {image_path}")

        # Generate output path
        if not output_path:
            timestamp = int(time.time())
            output_path = f"generated_video_{timestamp}.mp4"

        # Estimate cost
        res_mult = RESOLUTION_MAP.get(resolution, RESOLUTION_MAP["720p"])["cost_mult"]
        est_cost = duration * model_config["cost_per_sec"] * res_mult
        print(f"Estimated cost: ${est_cost:.2f}")

        # Generate based on provider
        if model_config["provider"] == "fal":
            if not self.fal_key:
                raise Exception("FAL_KEY not set")
            result = self.generate_fal(
                prompt=prompt,
                model=model,
                duration=duration,
                resolution=resolution,
                enable_audio=enable_audio,
                image_path=image_path
            )
        else:
            raise Exception(f"Provider {model_config['provider']} not implemented")

        # Download result
        self.download_video(result, output_path)

        # Final report
        file_size = os.path.getsize(output_path) / (1024 * 1024)

        print(f"\n{'='*60}")
        print("VIDEO GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"Output: {Path(output_path).absolute()}")
        print(f"Size: {file_size:.2f} MB")
        print(f"Cost: ~${est_cost:.2f}")
        print(f"{'='*60}")

        return {
            "success": True,
            "output_path": str(Path(output_path).absolute()),
            "model": model,
            "duration": duration,
            "resolution": resolution,
            "estimated_cost": est_cost,
            "file_size_mb": file_size,
        }


def main():
    parser = argparse.ArgumentParser(
        description="8OWLS Video Generator - AI-powered video creation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "A majestic owl flying through moonlit forest"
  %(prog)s "Product demo animation" --model veo3 --duration 8 --audio
  %(prog)s "Animate this logo" --image ./logo.png --duration 3
  %(prog)s "Cinematic sunset" --model kling --resolution 1080p

Models:
  wan-2.2   Fast & affordable ($0.04-0.08/sec) [default]
  veo3      Highest quality + audio ($0.40/sec)
  veo3-fast Faster Veo 3 ($0.25/sec)
  mochi     Open-source friendly (~$0.05/sec)
  hunyuan   Complex scenes ($0.10/sec)
  kling     Realistic motion ($0.15/sec)
        """
    )

    parser.add_argument("prompt", nargs="+", help="Text prompt for video generation")
    parser.add_argument("--model", "-m", default="wan-2.2",
                       choices=list(MODELS.keys()),
                       help="Model to use (default: wan-2.2)")
    parser.add_argument("--duration", "-d", type=int, default=5,
                       help="Video duration in seconds (default: 5)")
    parser.add_argument("--resolution", "-r", default="720p",
                       choices=["480p", "720p", "1080p"],
                       help="Video resolution (default: 720p)")
    parser.add_argument("--output", "-o", default=None,
                       help="Output file path (default: generated_video_<timestamp>.mp4)")
    parser.add_argument("--audio", "-a", action="store_true",
                       help="Enable audio generation (veo3 only)")
    parser.add_argument("--image", "-i", default=None,
                       help="Source image for image-to-video generation")

    args = parser.parse_args()

    if not REQUESTS_AVAILABLE:
        sys.exit(1)

    prompt = " ".join(args.prompt)

    try:
        generator = VideoGenerator()
        result = generator.generate(
            prompt=prompt,
            model=args.model,
            duration=args.duration,
            resolution=args.resolution,
            output_path=args.output,
            enable_audio=args.audio,
            image_path=args.image
        )

        # Open the file (macOS)
        if sys.platform == "darwin":
            os.system(f'open "{result["output_path"]}"')

    except KeyboardInterrupt:
        print("\nGeneration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
