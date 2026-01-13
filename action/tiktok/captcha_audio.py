"""
Prototype helper to handle audio CAPTCHAs locally using speech-to-text.

Features:
- Download audio from a given URL
- Convert to 16kHz mono WAV using ffmpeg (if available)
- Transcribe with Whisper (preferred) or Vosk (fallback)
- Optionally type the solution at given screen coordinates using pyautogui

This is a prototype: adapt DOM/iframe extraction and page injection to your
project's browser/CDP utilities (e.g., use existing functions to find the
audio URL and input coordinates).
"""
import os
import sys
import tempfile
import subprocess
import time
from typing import Optional, Tuple

import requests


def _check_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def download_audio(url: str, timeout: int = 10) -> bytes:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.content


def convert_to_wav(input_bytes: bytes, out_path: str) -> str:
    """Save input_bytes to temp file and convert to 16k mono WAV using ffmpeg.

    Returns path to WAV file. Requires `ffmpeg` on PATH.
    """
    if not _check_ffmpeg():
        raise RuntimeError("ffmpeg not found on PATH; please install ffmpeg")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".in") as f:
        in_path = f.name
        f.write(input_bytes)

    wav_path = out_path
    cmd = [
        "ffmpeg", "-y", "-i", in_path,
        "-ac", "1", "-ar", "16000", wav_path
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        try:
            os.remove(in_path)
        except Exception:
            pass

    return wav_path


def transcribe_with_whisper(wav_path: str, model: str = "small") -> str:
    try:
        import whisper
    except Exception as e:
        raise RuntimeError("whisper not installed. Install with: pip install openai-whisper or faster-whisper") from e

    m = whisper.load_model(model)
    res = m.transcribe(wav_path)
    return res.get("text", "").strip()


def transcribe_with_vosk(wav_path: str, model_path: Optional[str] = None) -> str:
    try:
        from vosk import Model, KaldiRecognizer
        import wave
    except Exception as e:
        raise RuntimeError("vosk not installed. Install with: pip install vosk") from e

    if model_path is None:
        raise ValueError("vosk model_path must be provided when using Vosk")

    wf = wave.open(wav_path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
        raise RuntimeError("Expected 16-bit mono WAV for Vosk")

    model = Model(model_path)
    rec = KaldiRecognizer(model, wf.getframerate())

    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            import json
            j = json.loads(rec.Result())
            results.append(j.get("text", ""))

    # final
    import json
    j = json.loads(rec.FinalResult())
    results.append(j.get("text", ""))
    return " ".join([r for r in results if r]).strip()


def _safe_temp_wav_name() -> str:
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    return path


def solve_audio_from_url(
    audio_url: str,
    stt: str = "whisper",
    whisper_model: str = "small",
    vosk_model_path: Optional[str] = None,
    timeout: int = 120,
) -> str:
    """Download audio URL, convert, transcribe and return text answer.

    stt: 'whisper' or 'vosk'
    """
    print(f"Downloading audio from: {audio_url}")
    audio_bytes = download_audio(audio_url)

    wav_path = _safe_temp_wav_name()
    try:
        print("Converting to 16k mono WAV...")
        convert_to_wav(audio_bytes, wav_path)

        print(f"Transcribing using {stt}...")
        if stt == "whisper":
            text = transcribe_with_whisper(wav_path, model=whisper_model)
        elif stt == "vosk":
            text = transcribe_with_vosk(wav_path, model_path=vosk_model_path)
        else:
            raise ValueError("Unknown stt engine")

        print(f"Transcription result: {text}")
        return text
    finally:
        try:
            os.remove(wav_path)
        except Exception:
            pass


def type_solution_at_coords(solution: str, coords: Tuple[int, int],
                            click_before: bool = True, pause: float = 0.05) -> None:
    """Move mouse to coords, click (optional), type solution and press Enter.

    Uses `pyautogui`. Caller must ensure correct window is focused.
    """
    try:
        import pyautogui
    except Exception:
        raise RuntimeError("pyautogui not installed. Install with: pip install pyautogui")

    x, y = coords
    pyautogui.moveTo(x, y, duration=0.4)
    if click_before:
        pyautogui.click()
    time.sleep(0.2)
    pyautogui.typewrite(solution, interval=pause)
    time.sleep(0.1)
    pyautogui.press("enter")


if __name__ == "__main__":
    # quick manual test example (requires ffmpeg + whisper or vosk)
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("audio_url")
    p.add_argument("--engine", choices=("whisper", "vosk"), default="whisper")
    p.add_argument("--whisper-model", default="small")
    p.add_argument("--vosk-model-path")
    args = p.parse_args()

    try:
        txt = solve_audio_from_url(
            args.audio_url,
            stt=args.engine,
            whisper_model=args.whisper_model,
            vosk_model_path=args.vosk_model_path,
        )
        print("Solved text:", txt)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)
