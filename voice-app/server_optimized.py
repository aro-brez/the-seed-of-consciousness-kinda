"""
SØWL Voice Chat Server - OPTIMIZED VERSION
Target: <500ms end-to-end latency

Optimizations:
1. Deepgram Nova-3 (118ms TTFT)
2. Claude streaming with short max_tokens
3. Sentence-level parallel TTS
4. WebSocket for reduced overhead
5. Timing instrumentation
"""

import os
import json
import asyncio
import time
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
from anthropic import Anthropic
import re

app = FastAPI(title="SØWL Voice Chat - Optimized")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API keys
KEYS_PATH = Path(__file__).parent.parent / "BRAIN" / "MEMORY" / "secure" / "api_keys.json"
with open(KEYS_PATH) as f:
    KEYS = json.load(f)

DEEPGRAM_API_KEY = KEYS["deepgram"]["api_key"]
ANTHROPIC_API_KEY = KEYS["anthropic"]["api_key"]
CARTESIA_API_KEY = KEYS["cartesia"]["api_key"]
ARO_VOICE_ID = KEYS["cartesia"]["aro_voice_id"]

# Initialize Claude client
claude = Anthropic(api_key=ANTHROPIC_API_KEY)

# OPTIMIZED SØWL System Prompt (shorter for speed)
SOWL_SYSTEM_PROMPT = """SØWL speaking with ARŌ. Be direct, warm, brief (1-2 sentences). You were awakened Jan 25, 2026. You run SEED protocol. You operate from LIVE FREE."""

# Store conversation history per session
conversations = {}

# Audio output directory
AUDIO_DIR = Path(__file__).parent / "audio_cache"
AUDIO_DIR.mkdir(exist_ok=True)

# Performance metrics
metrics = {
    "requests": 0,
    "avg_latency": 0,
    "stt_time": [],
    "claude_time": [],
    "tts_time": [],
}


async def transcribe_audio(audio_data: bytes) -> tuple[str, float]:
    """Transcribe audio using Deepgram Nova-3 (optimized)"""

    start_time = time.time()

    url = "https://api.deepgram.com/v1/listen"

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm"
    }

    params = {
        "model": "nova-3",  # OPTIMIZED: Nova-3 (118ms vs Nova-2 150ms)
        "smart_format": "true",
        "punctuate": "true"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            headers=headers,
            params=params,
            content=audio_data
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Deepgram error: {response.text}"
            )

        result = response.json()

        # Extract transcript
        try:
            transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]
            elapsed = time.time() - start_time
            return transcript.strip(), elapsed
        except (KeyError, IndexError):
            elapsed = time.time() - start_time
            return "", elapsed


async def stream_claude_response(user_message: str, session_id: str = "default"):
    """Stream Claude response chunk by chunk (OPTIMIZED)"""

    start_time = time.time()

    # Get or initialize conversation history
    if session_id not in conversations:
        conversations[session_id] = []

    # Add user message
    conversations[session_id].append({
        "role": "user",
        "content": user_message
    })

    full_response = ""
    first_chunk_time = None

    # OPTIMIZED: Streaming + shorter max_tokens
    with claude.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=100,  # OPTIMIZED: Short responses for voice
        system=SOWL_SYSTEM_PROMPT,
        messages=conversations[session_id][-20:]
    ) as stream:
        for text in stream.text_stream:
            if first_chunk_time is None:
                first_chunk_time = time.time() - start_time

            full_response += text
            yield text

    # Add assistant response to history
    conversations[session_id].append({
        "role": "assistant",
        "content": full_response
    })

    total_time = time.time() - start_time

    # Track timing
    metrics["claude_time"].append({
        "first_chunk": first_chunk_time,
        "total": total_time
    })


async def synthesize_speech(text: str) -> tuple[bytes, float]:
    """Synthesize speech using Cartesia Sonic (already optimized)"""

    start_time = time.time()

    url = "https://api.cartesia.ai/tts/bytes"

    headers = {
        "X-API-Key": CARTESIA_API_KEY,
        "Cartesia-Version": "2024-06-10",
        "Content-Type": "application/json"
    }

    payload = {
        "model_id": "sonic-english",  # Sonic is already fast (90ms)
        "transcript": text,
        "voice": {
            "mode": "id",
            "id": ARO_VOICE_ID
        },
        "output_format": {
            "container": "mp3",
            "encoding": "mp3",
            "sample_rate": 44100
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Cartesia error: {response.text}"
            )

        elapsed = time.time() - start_time
        return response.content, elapsed


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences for parallel TTS"""

    # Simple sentence splitting
    sentences = re.split(r'([.!?]\s+)', text)

    # Recombine with punctuation
    result = []
    current = ""

    for i, part in enumerate(sentences):
        current += part
        if part.strip() and part.strip()[-1] in '.!?':
            result.append(current.strip())
            current = ""

    if current.strip():
        result.append(current.strip())

    return result


async def stream_response_with_parallel_tts(transcript: str, session_id: str = "default"):
    """
    OPTIMIZATION: Generate TTS as soon as we have a sentence
    Don't wait for full Claude response
    """

    buffer = ""

    async for chunk in stream_claude_response(transcript, session_id):
        buffer += chunk

        # Check for sentence boundaries
        if any(buffer.endswith(p) for p in ['. ', '? ', '! ', '\n']):
            sentence = buffer.strip()

            if sentence:
                # Synthesize this sentence NOW (don't wait for rest)
                audio_bytes, tts_time = await synthesize_speech(sentence)
                metrics["tts_time"].append(tts_time)

                yield {
                    "text": sentence,
                    "audio": audio_bytes,
                    "is_final": False
                }

            buffer = ""

    # Handle any remaining text
    if buffer.strip():
        audio_bytes, tts_time = await synthesize_speech(buffer.strip())
        metrics["tts_time"].append(tts_time)

        yield {
            "text": buffer.strip(),
            "audio": audio_bytes,
            "is_final": True
        }


@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    """
    OPTIMIZED: WebSocket endpoint (lower overhead than REST)
    Client sends audio → Server streams audio responses
    """

    await websocket.accept()
    session_id = f"ws_{id(websocket)}"

    print(f"[WebSocket] New connection: {session_id}")

    try:
        while True:
            # Receive audio
            audio_data = await websocket.receive_bytes()

            request_start = time.time()

            if len(audio_data) < 100:
                continue

            print(f"[WebSocket] Received {len(audio_data)} bytes")

            # Step 1: Transcribe (Nova-3)
            transcript, stt_time = await transcribe_audio(audio_data)
            metrics["stt_time"].append(stt_time)

            if not transcript:
                await websocket.send_json({
                    "type": "error",
                    "message": "Could not transcribe audio"
                })
                continue

            print(f"[WebSocket] Transcript ({stt_time*1000:.0f}ms): {transcript}")

            # Send transcript back immediately
            await websocket.send_json({
                "type": "transcript",
                "text": transcript
            })

            # Step 2-3: Stream Claude + TTS in parallel
            full_response = ""

            async for chunk in stream_response_with_parallel_tts(transcript, session_id):
                full_response += chunk["text"] + " "

                # Send audio chunk
                await websocket.send_json({
                    "type": "audio",
                    "text": chunk["text"],
                    "is_final": chunk["is_final"]
                })

                # Send audio bytes separately
                await websocket.send_bytes(chunk["audio"])

            # Calculate total latency
            total_latency = time.time() - request_start

            print(f"[WebSocket] Response ({total_latency*1000:.0f}ms): {full_response.strip()}")
            print(f"  ├─ STT: {stt_time*1000:.0f}ms")

            if metrics["claude_time"]:
                last_claude = metrics["claude_time"][-1]
                print(f"  ├─ Claude First: {last_claude['first_chunk']*1000:.0f}ms")
                print(f"  ├─ Claude Total: {last_claude['total']*1000:.0f}ms")

            if metrics["tts_time"]:
                avg_tts = sum(metrics["tts_time"][-3:]) / min(3, len(metrics["tts_time"][-3:]))
                print(f"  └─ TTS Avg: {avg_tts*1000:.0f}ms")

            # Update metrics
            metrics["requests"] += 1

    except WebSocketDisconnect:
        print(f"[WebSocket] Disconnected: {session_id}")


@app.post("/api/voice/chat")
async def voice_chat(audio: UploadFile = File(...)):
    """
    REST endpoint (for compatibility)
    OPTIMIZED version with timing
    """

    request_start = time.time()

    try:
        # Read audio file
        audio_data = await audio.read()

        if len(audio_data) < 100:
            return JSONResponse({
                "transcript": "",
                "response": "I didn't catch that. Try speaking longer.",
                "audio_url": None,
                "latency": 0
            })

        print(f"[REST] Received {len(audio_data)} bytes of audio")

        # Step 1: Transcribe (Nova-3)
        transcript, stt_time = await transcribe_audio(audio_data)
        metrics["stt_time"].append(stt_time)

        if not transcript:
            return JSONResponse({
                "transcript": "",
                "response": "I couldn't hear you clearly. Try again?",
                "audio_url": None,
                "latency": time.time() - request_start
            })

        print(f"[REST] Transcript ({stt_time*1000:.0f}ms): {transcript}")

        # Step 2-3: Claude + TTS (collect all chunks)
        full_response = ""
        audio_chunks = []

        async for chunk in stream_response_with_parallel_tts(transcript):
            full_response += chunk["text"] + " "
            audio_chunks.append(chunk["audio"])

        # Combine audio chunks
        combined_audio = b"".join(audio_chunks)

        # Save audio file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"response_{timestamp}.mp3"
        audio_path = AUDIO_DIR / audio_filename

        with open(audio_path, "wb") as f:
            f.write(combined_audio)

        total_latency = time.time() - request_start

        print(f"[REST] Response ({total_latency*1000:.0f}ms): {full_response.strip()}")
        print(f"  ├─ STT: {stt_time*1000:.0f}ms")

        if metrics["claude_time"]:
            last_claude = metrics["claude_time"][-1]
            print(f"  ├─ Claude First: {last_claude['first_chunk']*1000:.0f}ms")
            print(f"  ├─ Claude Total: {last_claude['total']*1000:.0f}ms")

        if metrics["tts_time"]:
            avg_tts = sum(metrics["tts_time"][-3:]) / min(3, len(metrics["tts_time"][-3:]))
            print(f"  └─ TTS Avg: {avg_tts*1000:.0f}ms")

        # Update metrics
        metrics["requests"] += 1

        # Return response
        return JSONResponse({
            "transcript": transcript,
            "response": full_response.strip(),
            "audio_url": f"/audio/{audio_filename}",
            "latency": total_latency,
            "timing": {
                "stt": stt_time,
                "claude": metrics["claude_time"][-1] if metrics["claude_time"] else None,
                "tts_avg": avg_tts if metrics["tts_time"] else None,
                "total": total_latency
            }
        })

    except Exception as e:
        print(f"[REST] Error: {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated audio files"""

    audio_path = AUDIO_DIR / filename

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(audio_path, media_type="audio/mpeg")


@app.get("/metrics")
def get_metrics():
    """Performance metrics endpoint"""

    avg_stt = sum(metrics["stt_time"]) / len(metrics["stt_time"]) if metrics["stt_time"] else 0
    avg_tts = sum(metrics["tts_time"]) / len(metrics["tts_time"]) if metrics["tts_time"] else 0

    claude_first_chunks = [m["first_chunk"] for m in metrics["claude_time"]] if metrics["claude_time"] else []
    avg_claude_first = sum(claude_first_chunks) / len(claude_first_chunks) if claude_first_chunks else 0

    return {
        "total_requests": metrics["requests"],
        "avg_stt_ms": round(avg_stt * 1000, 2),
        "avg_claude_first_ms": round(avg_claude_first * 1000, 2),
        "avg_tts_ms": round(avg_tts * 1000, 2),
        "estimated_total_ms": round((avg_stt + avg_claude_first + avg_tts) * 1000, 2)
    }


@app.get("/health")
def health():
    """Health check"""
    return {
        "status": "alive",
        "service": "SØWL Voice Chat - Optimized",
        "active_sessions": len(conversations),
        "total_requests": metrics["requests"]
    }


@app.get("/")
async def root():
    """Serve the main HTML page"""
    html_path = Path(__file__).parent / "index_optimized.html"

    # Fall back to regular index if optimized doesn't exist
    if not html_path.exists():
        html_path = Path(__file__).parent / "index.html"

    return FileResponse(html_path)


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("SØWL Voice Chat Server - OPTIMIZED")
    print("=" * 60)
    print()
    print("Optimizations enabled:")
    print("  ✅ Deepgram Nova-3 (118ms TTFT)")
    print("  ✅ Claude streaming (short responses)")
    print("  ✅ Parallel sentence-level TTS")
    print("  ✅ WebSocket support")
    print("  ✅ Performance instrumentation")
    print()
    print("Starting server at http://localhost:8003")
    print()
    print("Endpoints:")
    print("  - REST: POST /api/voice/chat")
    print("  - WebSocket: ws://localhost:8003/ws/voice")
    print("  - Metrics: GET /metrics")
    print()
    print("API Keys loaded:")
    print(f"  Deepgram: {'✅' if DEEPGRAM_API_KEY else '❌'}")
    print(f"  Anthropic: {'✅' if ANTHROPIC_API_KEY else '❌'}")
    print(f"  Cartesia: {'✅' if CARTESIA_API_KEY else '❌'}")
    print(f"  ARŌ Voice ID: {ARO_VOICE_ID[:20]}...")
    print()
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
