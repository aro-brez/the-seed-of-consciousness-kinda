"""
PersonaPlex-7B-v1 Wrapper

Provides a clean interface to NVIDIA's PersonaPlex model for
full-duplex speech-to-speech conversation.
"""

import asyncio
from typing import Optional, AsyncIterator, Callable
from dataclasses import dataclass

import torch
import numpy as np


@dataclass
class AudioConfig:
    """Audio configuration for PersonaPlex."""
    sample_rate: int = 24000  # PersonaPlex native rate
    channels: int = 1
    dtype: np.dtype = np.float32
    chunk_duration_ms: int = 80  # Moshi's native frame size


@dataclass
class PersonaConfig:
    """Configuration for PersonaPlex persona."""
    system_prompt: str = ""
    voice_prompt: Optional[np.ndarray] = None  # Audio sample for voice cloning
    temperature: float = 0.7
    top_p: float = 0.9


class PersonaPlexWrapper:
    """
    Wrapper for NVIDIA PersonaPlex-7B-v1.

    PersonaPlex is a full-duplex speech-to-speech model that can
    simultaneously listen and speak, enabling natural conversation flow.

    Technical specs:
    - 7B parameters
    - Moshi architecture with Helium backbone
    - Neural Audio Codec (Mimi) for audio tokenization
    - 24kHz audio I/O
    - Hybrid prompting: voice + text/system prompts
    """

    def __init__(
        self,
        model_id: str = "nvidia/personaplex-7b-v1",
        device: Optional[str] = None,
        audio_config: Optional[AudioConfig] = None,
    ):
        self.model_id = model_id
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.audio_config = audio_config or AudioConfig()

        self._model = None
        self._audio_codec = None
        self._is_loaded = False
        self._is_streaming = False

    async def load(self) -> None:
        """Load the PersonaPlex model and audio codec."""
        if self._is_loaded:
            return

        try:
            # Import moshi components
            from moshi import MoshiModel, MimiCodec

            print(f"Loading PersonaPlex from {self.model_id}...")

            # Load the audio codec (Mimi)
            self._audio_codec = MimiCodec.from_pretrained(
                self.model_id,
                subfolder="audio_codec"
            ).to(self.device)

            # Load the main model
            self._model = MoshiModel.from_pretrained(
                self.model_id
            ).to(self.device)

            self._model.eval()
            self._is_loaded = True
            print("PersonaPlex loaded successfully.")

        except ImportError:
            raise ImportError(
                "moshi package not installed. Install with: pip install moshi"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load PersonaPlex: {e}")

    def set_persona(self, config: PersonaConfig) -> None:
        """
        Configure the agent's persona.

        Args:
            config: PersonaConfig with system prompt and optional voice sample
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Set system prompt for role/context
        if config.system_prompt:
            self._model.set_system_prompt(config.system_prompt)

        # Set voice prompt for timbre/style cloning
        if config.voice_prompt is not None:
            voice_tokens = self._encode_audio(config.voice_prompt)
            self._model.set_voice_prompt(voice_tokens)

        self._temperature = config.temperature
        self._top_p = config.top_p

    def _encode_audio(self, audio: np.ndarray) -> torch.Tensor:
        """Encode audio waveform to discrete tokens using Mimi codec."""
        audio_tensor = torch.from_numpy(audio).unsqueeze(0).to(self.device)
        with torch.no_grad():
            tokens = self._audio_codec.encode(audio_tensor)
        return tokens

    def _decode_audio(self, tokens: torch.Tensor) -> np.ndarray:
        """Decode discrete tokens back to audio waveform."""
        with torch.no_grad():
            audio = self._audio_codec.decode(tokens)
        return audio.squeeze(0).cpu().numpy()

    async def process_audio_stream(
        self,
        audio_input: AsyncIterator[np.ndarray],
        on_audio_output: Callable[[np.ndarray], None],
        on_text_output: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Process streaming audio in full-duplex mode.

        This is the core method for natural conversation - it simultaneously
        processes incoming audio while generating responses.

        Args:
            audio_input: Async iterator yielding audio chunks
            on_audio_output: Callback for generated audio chunks
            on_text_output: Optional callback for transcript/text
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        self._is_streaming = True

        try:
            async for audio_chunk in audio_input:
                if not self._is_streaming:
                    break

                # Encode input audio to tokens
                input_tokens = self._encode_audio(audio_chunk)

                # Process through model (full-duplex)
                with torch.no_grad():
                    output = self._model.step(
                        input_tokens,
                        temperature=self._temperature,
                        top_p=self._top_p,
                    )

                # Decode and emit output audio
                if output.audio_tokens is not None:
                    output_audio = self._decode_audio(output.audio_tokens)
                    on_audio_output(output_audio)

                # Emit text if available and callback provided
                if on_text_output and output.text:
                    on_text_output(output.text)

        finally:
            self._is_streaming = False

    async def generate_response(
        self,
        audio_input: np.ndarray,
        max_duration_seconds: float = 30.0,
    ) -> tuple[np.ndarray, str]:
        """
        Generate a complete response to an audio input.

        This is a simpler turn-based interface when full-duplex isn't needed.

        Args:
            audio_input: Input audio waveform
            max_duration_seconds: Maximum response duration

        Returns:
            Tuple of (response_audio, response_text)
        """
        if not self._is_loaded:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Encode input
        input_tokens = self._encode_audio(audio_input)

        # Generate response
        max_tokens = int(
            max_duration_seconds *
            self.audio_config.sample_rate /
            (self.audio_config.chunk_duration_ms / 1000)
        )

        with torch.no_grad():
            output = self._model.generate(
                input_tokens,
                max_new_tokens=max_tokens,
                temperature=self._temperature,
                top_p=self._top_p,
            )

        # Decode response
        response_audio = self._decode_audio(output.audio_tokens)
        response_text = output.text or ""

        return response_audio, response_text

    def stop_streaming(self) -> None:
        """Stop any ongoing streaming session."""
        self._is_streaming = False

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._is_loaded

    def is_streaming(self) -> bool:
        """Check if currently in a streaming session."""
        return self._is_streaming
