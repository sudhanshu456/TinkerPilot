"""
Speech-to-text wrapper using Moonshine Voice.
Replaces faster-whisper with Moonshine for better accuracy, lower latency,
and native streaming support on Apple Silicon.

Moonshine Medium Streaming: 6.65% WER (beats Whisper Large v3 at 7.44%)
at 107ms latency per chunk on MacBook.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

from app.config import get_config

logger = logging.getLogger(__name__)

_transcriber = None
_model_path = None
_model_arch = None


def _ensure_model():
    """Download Moonshine model if not already present. Returns (model_path, model_arch)."""
    global _model_path, _model_arch
    if _model_path is not None:
        return _model_path, _model_arch

    from moonshine_voice import download
    from moonshine_voice.moonshine_api import ModelArch

    config = get_config()
    language = config.stt.language or "en"
    
    # Map config size to Moonshine ModelArch (using streaming variants by default)
    size_str = (config.stt.model_size or "small").upper()
    arch_name = f"{size_str}_STREAMING"
    try:
        wanted_arch = getattr(ModelArch, arch_name)
    except AttributeError:
        logger.warning(f"Unknown Moonshine size '{size_str}', defaulting to SMALL_STREAMING")
        wanted_arch = ModelArch.SMALL_STREAMING

    logger.info(f"Ensuring Moonshine model {wanted_arch.name} is downloaded for language: {language}")
    _model_path, _model_arch = download.get_model_for_language(language, wanted_model_arch=wanted_arch)
    logger.info(f"Moonshine model ready: path={_model_path}")
    return _model_path, _model_arch


def get_stt_model():
    """Get or initialize the Moonshine transcriber. Lazy-loaded."""
    global _transcriber
    if _transcriber is not None:
        return _transcriber

    from moonshine_voice import Transcriber

    model_path, model_arch = _ensure_model()

    logger.info("Loading Moonshine transcriber...")
    _transcriber = Transcriber(model_path=model_path, model_arch=model_arch)
    logger.info("Moonshine transcriber loaded.")
    return _transcriber


def unload_stt():
    """Unload Moonshine model to free memory."""
    global _transcriber, _model_path, _model_arch
    if _transcriber is not None:
        del _transcriber
        _transcriber = None
        logger.info("Moonshine transcriber unloaded.")


def transcribe_file(
    audio_path: str,
    language: Optional[str] = None,
) -> dict:
    """
    Transcribe an audio file using Moonshine.

    Returns:
        dict with keys:
            - text: full transcription text
            - segments: list of {start, end, text} dicts
            - language: detected/configured language
            - language_probability: confidence (1.0 for Moonshine)
    """
    from moonshine_voice import Transcriber
    from moonshine_voice.transcriber import TranscriptEventListener

    model_path, model_arch = _ensure_model()

    transcriber = Transcriber(model_path=model_path, model_arch=model_arch)

    # Collect transcript lines
    lines = []

    class Collector(TranscriptEventListener):
        def on_line_completed(self, event):
            lines.append(
                {
                    "text": event.line.text.strip(),
                    "start": getattr(event.line, "start_time", 0.0),
                    "duration": getattr(event.line, "duration", 0.0),
                }
            )

    transcriber.add_listener(Collector())

    # Use the non-streaming method for file transcription
    from moonshine_voice.utils import load_wav_file

    try:
        audio_data, sample_rate = load_wav_file(audio_path)
    except Exception:
        # If load_wav_file fails, try with soundfile
        import soundfile as sf

        audio_data, sample_rate = sf.read(audio_path, dtype="float32")
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]  # mono

    transcriber.start()

    # Feed audio in chunks (simulates streaming for event callbacks)
    chunk_duration = 0.5
    chunk_size = int(chunk_duration * sample_rate)
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i : i + chunk_size]
        transcriber.add_audio(chunk, sample_rate)

    transcriber.stop()

    # Build result
    full_text = " ".join(line["text"] for line in lines if line["text"])

    segments = []
    running_time = 0.0
    for line in lines:
        if line["text"]:
            start = line.get("start", running_time)
            duration = line.get("duration", 0.0)
            segments.append(
                {
                    "start": round(start, 2),
                    "end": round(start + duration, 2),
                    "text": line["text"],
                }
            )
            running_time = start + duration

    config = get_config()
    return {
        "text": full_text,
        "segments": segments,
        "language": language or config.stt.language,
        "language_probability": 1.0,
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
