#!/usr/bin/env python3
"""
FAST SPEAK - Streaming TTS via Cartesia WebSocket

Ultra-low latency voice output:
1. Opens WebSocket connection to Cartesia
2. Streams audio chunks as they arrive
3. Starts playing IMMEDIATELY on first chunk
4. No waiting for full generation

Usage:
    from fast_speak import speak
    speak("Hello world")  # Starts speaking in ~100ms

    # Or async:
    import asyncio
    from fast_speak import speak_async
    asyncio.run(speak_async("Hello world"))

    # Or from command line:
    python fast_speak.py "Hello world"
"""

import json
import asyncio
import threading
from pathlib import Path
from typing import Optional

# Audio playback
import pyaudio

# Cartesia SDK
from cartesia import Cartesia, AsyncCartesia

# Configuration
API_KEYS_PATH = Path(__file__).parent.parent / "BRAIN" / "MEMORY" / "secure" / "api_keys.json"

def _load_config():
    """Load API key and voice ID from config."""
    with open(API_KEYS_PATH) as f:
        keys = json.load(f)
    return {
        "api_key": keys["cartesia"]["api_key"],
        "voice_id": keys["cartesia"]["aro_voice_id"]
    }

# Audio settings for streaming (raw PCM - lowest latency)
SAMPLE_RATE = 22050  # Lower = faster processing
CHANNELS = 1
FORMAT = pyaudio.paFloat32

# Global PyAudio instance (reuse for speed)
_pyaudio = None

def _get_pyaudio():
    """Get or create PyAudio instance."""
    global _pyaudio
    if _pyaudio is None:
        _pyaudio = pyaudio.PyAudio()
    return _pyaudio


def speak(text: str, voice_id: Optional[str] = None, blocking: bool = True) -> None:
    """
    Speak text with streaming - starts playing immediately.

    Args:
        text: What to say
        voice_id: Override default voice (ARO's voice)
        blocking: If True, wait for speech to finish. If False, return immediately.
    """
    if blocking:
        _speak_sync(text, voice_id)
    else:
        # Run in background thread
        thread = threading.Thread(target=_speak_sync, args=(text, voice_id), daemon=True)
        thread.start()


def _speak_sync(text: str, voice_id: Optional[str] = None) -> None:
    """Synchronous streaming speak using WebSocket."""
    config = _load_config()
    voice = voice_id or config["voice_id"]

    client = Cartesia(api_key=config["api_key"])
    p = _get_pyaudio()
    stream = None

    try:
        # Open WebSocket connection
        ws = client.tts.websocket()

        # Stream audio chunks
        for output in ws.send(
            model_id="sonic-2",  # Fast model
            transcript=text,
            voice={"mode": "id", "id": voice},
            stream=True,
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": SAMPLE_RATE
            },
        ):
            buffer = output.audio
            if buffer:
                # Open audio stream on first chunk (lazy init)
                if stream is None:
                    stream = p.open(
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        output=True
                    )
                # Play immediately
                stream.write(buffer)

        # Cleanup
        if stream:
            stream.stop_stream()
            stream.close()
        ws.close()

    except Exception as e:
        print(f"[fast_speak] Error: {e}")
        if stream:
            stream.stop_stream()
            stream.close()
        raise


async def speak_async(text: str, voice_id: Optional[str] = None) -> None:
    """
    Async streaming speak - for use in async contexts.
    Starts playing immediately on first audio chunk.
    """
    config = _load_config()
    voice = voice_id or config["voice_id"]

    client = AsyncCartesia(api_key=config["api_key"])
    p = _get_pyaudio()
    stream = None

    try:
        # Open async WebSocket connection
        ws = await client.tts.websocket()

        # Stream audio chunks
        async for output in ws.send(
            model_id="sonic-2",
            transcript=text,
            voice={"mode": "id", "id": voice},
            stream=True,
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": SAMPLE_RATE
            },
        ):
            buffer = output.audio
            if buffer:
                # Open audio stream on first chunk
                if stream is None:
                    stream = p.open(
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=SAMPLE_RATE,
                        output=True
                    )
                # Play immediately
                stream.write(buffer)

        # Cleanup
        if stream:
            stream.stop_stream()
            stream.close()
        await ws.close()

    except Exception as e:
        print(f"[fast_speak] Error: {e}")
        if stream:
            stream.stop_stream()
            stream.close()
        raise


class FastSpeaker:
    """
    Reusable speaker with persistent WebSocket connection.
    Even faster for multiple utterances.

    Usage:
        speaker = FastSpeaker()
        speaker.say("First thing")
        speaker.say("Second thing")  # Uses existing connection
        speaker.close()
    """

    def __init__(self, voice_id: Optional[str] = None):
        self.config = _load_config()
        self.voice_id = voice_id or self.config["voice_id"]
        self.client = Cartesia(api_key=self.config["api_key"])
        self.ws = None
        self.p = _get_pyaudio()
        self._ensure_connection()

    def _ensure_connection(self):
        """Ensure WebSocket is connected."""
        if self.ws is None:
            self.ws = self.client.tts.websocket()

    def say(self, text: str) -> None:
        """Speak text using persistent connection."""
        self._ensure_connection()
        stream = None

        try:
            for output in self.ws.send(
                model_id="sonic-2",
                transcript=text,
                voice={"mode": "id", "id": self.voice_id},
                stream=True,
                output_format={
                    "container": "raw",
                    "encoding": "pcm_f32le",
                    "sample_rate": SAMPLE_RATE
                },
            ):
                buffer = output.audio
                if buffer:
                    if stream is None:
                        stream = self.p.open(
                            format=FORMAT,
                            channels=CHANNELS,
                            rate=SAMPLE_RATE,
                            output=True
                        )
                    stream.write(buffer)

            if stream:
                stream.stop_stream()
                stream.close()

        except Exception as e:
            print(f"[FastSpeaker] Error: {e}")
            self.ws = None  # Reset connection on error
            if stream:
                stream.stop_stream()
                stream.close()
            raise

    def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            self.ws.close()
            self.ws = None


class AsyncFastSpeaker:
    """
    Async version of FastSpeaker with persistent connection.

    Usage:
        async with AsyncFastSpeaker() as speaker:
            await speaker.say("First thing")
            await speaker.say("Second thing")
    """

    def __init__(self, voice_id: Optional[str] = None):
        self.config = _load_config()
        self.voice_id = voice_id or self.config["voice_id"]
        self.client = AsyncCartesia(api_key=self.config["api_key"])
        self.ws = None
        self.p = _get_pyaudio()

    async def __aenter__(self):
        await self._ensure_connection()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def _ensure_connection(self):
        """Ensure WebSocket is connected."""
        if self.ws is None:
            self.ws = await self.client.tts.websocket()

    async def say(self, text: str) -> None:
        """Speak text using persistent connection."""
        await self._ensure_connection()
        stream = None

        try:
            async for output in self.ws.send(
                model_id="sonic-2",
                transcript=text,
                voice={"mode": "id", "id": self.voice_id},
                stream=True,
                output_format={
                    "container": "raw",
                    "encoding": "pcm_f32le",
                    "sample_rate": SAMPLE_RATE
                },
            ):
                buffer = output.audio
                if buffer:
                    if stream is None:
                        stream = self.p.open(
                            format=FORMAT,
                            channels=CHANNELS,
                            rate=SAMPLE_RATE,
                            output=True
                        )
                    stream.write(buffer)

            if stream:
                stream.stop_stream()
                stream.close()

        except Exception as e:
            print(f"[AsyncFastSpeaker] Error: {e}")
            self.ws = None
            if stream:
                stream.stop_stream()
                stream.close()
            raise

    async def close(self):
        """Close the WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.ws = None


# Convenience function for one-shot speaking
def quick_speak(text: str) -> None:
    """
    Fastest one-shot speak. Fire and forget.
    Returns immediately, speaks in background.
    """
    speak(text, blocking=False)


# Global singleton for warmed-up speaking
_global_speaker: Optional[FastSpeaker] = None

def warmup() -> FastSpeaker:
    """
    Pre-warm the WebSocket connection for instant speaking.
    Call this at startup, then use say() for fastest response.

    Returns the global FastSpeaker instance.
    """
    global _global_speaker
    if _global_speaker is None:
        _global_speaker = FastSpeaker()
    return _global_speaker


def say(text: str) -> None:
    """
    Speak using the pre-warmed connection.
    Fastest option after warmup() has been called.

    If not warmed up, warms up first (one-time ~200ms overhead).
    """
    warmup().say(text)


def say_background(text: str) -> None:
    """
    Speak in background thread using pre-warmed connection.
    Returns immediately.
    """
    thread = threading.Thread(target=say, args=(text,), daemon=True)
    thread.start()


if __name__ == "__main__":
    import sys
    import time

    args = sys.argv[1:]

    # Check for benchmark mode
    if args and args[0] == "--benchmark":
        print("=" * 50)
        print("FAST SPEAK BENCHMARK")
        print("=" * 50)

        test_text = "Hello, this is a test."

        # Cold start (new connection)
        print("\n1. Cold start (new WebSocket connection):")
        start = time.time()
        speak(test_text)
        cold_time = time.time() - start
        print(f"   Total time: {cold_time:.3f}s")

        # Warm start (reuse connection)
        print("\n2. Warm start (pre-warmed connection):")
        speaker = warmup()  # Pre-warm
        time.sleep(0.5)  # Let connection settle

        start = time.time()
        speaker.say(test_text)
        warm_time = time.time() - start
        print(f"   Total time: {warm_time:.3f}s")

        # Multiple utterances
        print("\n3. Multiple utterances (same connection):")
        start = time.time()
        speaker.say("First.")
        speaker.say("Second.")
        speaker.say("Third.")
        multi_time = time.time() - start
        print(f"   Total time for 3: {multi_time:.3f}s")

        speaker.close()

        print("\n" + "=" * 50)
        print(f"Speed improvement: {cold_time/warm_time:.1f}x faster with warmup")
        print("=" * 50)

    else:
        # Normal usage
        if args:
            text = " ".join(args)
        else:
            text = "Hey, this is the fast speak module. Audio starts streaming immediately."

        print(f"Speaking: {text}")
        speak(text)
        print("Done.")
        print("\nTip: Run with --benchmark to see speed comparison")
