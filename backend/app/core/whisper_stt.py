"""
Speech-to-text wrapper using faster-whisper.
Provides transcription from audio files and raw audio data.
Uses Whisper small model with int8 quantization for 8GB RAM efficiency.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from app.config import get_config

logger = logging.getLogger(__name__)

_model = None
_loaded_size: Optional[str] = None


def get_whisper_model():
    """Get or initialize the Whisper model singleton. Lazy-loaded."""
    global _model, _loaded_size
    config = get_config()

    if _model is not None and _loaded_size == config.whisper.model_size:
        return _model

    from faster_whisper import WhisperModel

    logger.info(
        f"Loading Whisper model (size={config.whisper.model_size}, "
        f"device={config.whisper.device}, compute={config.whisper.compute_type})..."
    )

    _model = WhisperModel(
        config.whisper.model_size,
        device=config.whisper.device,
        compute_type=config.whisper.compute_type,
    )
    _loaded_size = config.whisper.model_size
    logger.info("Whisper model loaded successfully.")
    return _model


def unload_whisper():
    """Unload whisper model to free memory."""
    global _model, _loaded_size
    if _model is not None:
        del _model
        _model = None
        _loaded_size = None
        logger.info("Whisper model unloaded.")


def transcribe_file(
    audio_path: str,
    language: Optional[str] = None,
) -> dict:
    """
    Transcribe an audio file.

    Returns:
        dict with keys:
            - text: full transcription text
            - segments: list of {start, end, text} dicts
            - language: detected language
            - language_probability: confidence
    """
    config = get_config()
    model = get_whisper_model()

    segments_iter, info = model.transcribe(
        audio_path,
        beam_size=config.whisper.beam_size,
        language=language or config.whisper.language,
        vad_filter=config.whisper.vad_filter,
    )

    segments = []
    full_text_parts = []
    for segment in segments_iter:
        seg_data = {
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
        }
        segments.append(seg_data)
        full_text_parts.append(segment.text.strip())

    return {
        "text": " ".join(full_text_parts),
        "segments": segments,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
    }


def transcribe_audio_data(
    audio_data: bytes,
    sample_rate: int = 16000,
    language: Optional[str] = None,
) -> dict:
    """Transcribe raw audio bytes (WAV format expected)."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    try:
        return transcribe_file(tmp_path, language=language)
    finally:
        Path(tmp_path).unlink(missing_ok=True)
