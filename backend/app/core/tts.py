"""
Text-to-speech wrapper using Kokoro-82M.
Generates natural-sounding speech from text, fully local.

Kokoro-82M: 82M parameters, Apache 2.0 licensed, multiple voices,
supports English, Japanese, Chinese, Spanish, French, and more.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

import soundfile as sf

logger = logging.getLogger(__name__)

_pipeline = None


def get_tts_pipeline():
    """Get or initialize the Kokoro TTS pipeline. Lazy-loaded."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    # Enable MPS fallback for Apple Silicon GPU acceleration
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

    from kokoro import KPipeline

    logger.info("Loading Kokoro TTS pipeline...")
    _pipeline = KPipeline(lang_code="a")  # American English
    logger.info("Kokoro TTS pipeline loaded.")
    return _pipeline


def unload_tts():
    """Unload TTS model to free memory."""
    global _pipeline
    if _pipeline is not None:
        del _pipeline
        _pipeline = None
        logger.info("Kokoro TTS pipeline unloaded.")


# Available voices (American English)
VOICES = {
    "heart": "af_heart",  # Female, warm
    "bella": "af_bella",  # Female, clear
    "nicole": "af_nicole",  # Female, professional
    "sky": "af_sky",  # Female, bright
    "adam": "am_adam",  # Male, warm
    "michael": "am_michael",  # Male, clear
}

DEFAULT_VOICE = "af_heart"


def speak(
    text: str,
    voice: Optional[str] = None,
    speed: float = 1.0,
    output_path: Optional[str] = None,
) -> str:
    """
    Generate speech audio from text.

    Args:
        text: Text to speak
        voice: Voice name (see VOICES dict) or raw Kokoro voice ID
        speed: Speech speed multiplier (0.5-2.0)
        output_path: Where to save the WAV file. Auto-generated if None.

    Returns:
        Path to the generated WAV file.
    """
    pipeline = get_tts_pipeline()

    # Resolve voice name
    voice_id = VOICES.get(voice, voice) if voice else DEFAULT_VOICE

    # Generate audio
    all_audio = []
    generator = pipeline(text, voice=voice_id, speed=speed)
    for _, _, audio in generator:
        all_audio.append(audio)

    if not all_audio:
        raise RuntimeError("TTS generated no audio")

    # Concatenate all audio segments
    import numpy as np

    combined = np.concatenate(all_audio)

    # Save to file
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_path = tmp.name
        tmp.close()

    sf.write(output_path, combined, 24000)
    logger.info(f"TTS audio saved: {output_path} ({len(combined) / 24000:.1f}s)")

    return output_path


def speak_to_bytes(
    text: str,
    voice: Optional[str] = None,
    speed: float = 1.0,
) -> tuple[bytes, int]:
    """
    Generate speech audio and return as WAV bytes.

    Returns:
        Tuple of (wav_bytes, sample_rate)
    """
    import io
    import numpy as np

    pipeline = get_tts_pipeline()
    voice_id = VOICES.get(voice, voice) if voice else DEFAULT_VOICE

    all_audio = []
    generator = pipeline(text, voice=voice_id, speed=speed)
    for _, _, audio in generator:
        all_audio.append(audio)

    if not all_audio:
        raise RuntimeError("TTS generated no audio")

    combined = np.concatenate(all_audio)

    buf = io.BytesIO()
    sf.write(buf, combined, 24000, format="WAV")
    return buf.getvalue(), 24000


def list_voices() -> dict:
    """Return available voice names and IDs."""
    return VOICES
