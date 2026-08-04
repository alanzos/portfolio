#!/usr/bin/env python3
"""Generate Kokoro MP3 narration for portfolio articles (GitHub Pages listen feature)."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTICLES_DIR = REPO_ROOT / "articles"
DEFAULT_VOICE = "af_heart"
DEFAULT_SPEED = 1.0


def resolve_kokoro_python() -> str:
    override = os.environ.get("IDUNOX_KOKORO_PYTHON", "").strip()
    candidates = [
        override,
        str(Path("/Users/ALC/Git/idunox_investor_portal/.venv-kokoro/bin/python")),
        "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12",
        "/usr/local/bin/python3.12",
        shutil.which("python3.12") or "",
    ]
    for candidate in candidates:
        if not candidate or not Path(candidate).exists():
            continue
        probe = subprocess.run(
            [
                candidate,
                "-c",
                "import sys; from kokoro import KPipeline; raise SystemExit(0 if sys.version_info < (3, 13) else 1)",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if probe.returncode == 0:
            return candidate
    raise RuntimeError(
        "No Kokoro-compatible Python found. Install Kokoro on Python 3.12 "
        "or set IDUNOX_KOKORO_PYTHON."
    )


def strip_front_matter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    return parts[2]


def extract_title(text: str) -> str:
    match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', text, flags=re.M)
    if not match:
        return ""
    return match.group(1).strip().strip('"').strip("'")


def qmd_to_speech_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    title = extract_title(raw)
    body = strip_front_matter(raw)

    # Drop fenced code blocks.
    body = re.sub(r"```[\s\S]*?```", "\n", body)
    # Drop inline images but keep alt text when present.
    body = re.sub(
        r"!\[([^\]]*)\]\([^)]+\)(?:\{[^}]*\})?",
        lambda m: f" Image: {m.group(1)}. " if m.group(1).strip() else " ",
        body,
    )
    # Links: keep label.
    body = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
    # Callout / div fences.
    body = re.sub(r"^:::+.*$", "", body, flags=re.M)
    # Headings markers.
    body = re.sub(r"^#{1,6}\s+", "", body, flags=re.M)
    # Bold / italic / code.
    body = re.sub(r"[`*_]+", "", body)
    # HTML tags.
    body = re.sub(r"<[^>]+>", " ", body)
    # Reference-style leftovers like [1] or [1-3].
    body = re.sub(r"\[(\d+(?:\s*[-–,]\s*\d+)*)\]", r" (\1) ", body)
    # Collapse whitespace.
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = body.strip()

    # Light pronunciation helpers for common portfolio tokens.
    replacements = {
        r"\bML\b": "machine learning",
        r"\bAI\b": "A I",
        r"\bNHS\b": "N H S",
        r"\bCSF\b": "C S F",
        r"\bPET\b": "P E T",
        r"\bMRI\b": "M R I",
        r"\bNfL\b": "N F L",
        r"\bGFAP\b": "G F A P",
        r"\bp-tau217\b": "p tau 217",
        r"\bMCC\b": "M C C",
        r"\bCHF\b": "Swiss francs",
        r"\bIdunox\b": "Eedunox",
        r"\bCSEM\b": "C S E M",
    }
    for pattern, repl in replacements.items():
        body = re.sub(pattern, repl, body)

    parts = []
    if title:
        parts.append(title if title.endswith((".", "!", "?")) else f"{title}.")
    if body:
        parts.append(body)
    return "\n\n".join(parts).strip()


def generate_kokoro_mp3(text: str, output_mp3: Path, *, voice: str, speed: float, python_bin: str) -> None:
    output_mp3.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="portfolio-kokoro-") as tmp:
        wav_path = Path(tmp) / "speech.wav"
        text_path = Path(tmp) / "speech.txt"
        text_path.write_text(text, encoding="utf-8")

        kokoro_code = f"""
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro import KPipeline

text = Path(r"{text_path}").read_text(encoding="utf-8")
voice = "{voice}"
speed = {speed}
output_wav = Path(r"{wav_path}")

pipeline = KPipeline(lang_code="en-US", device="cpu", repo_id="hexgrad/Kokoro-82M")
results = list(pipeline(text, voice=voice, speed=speed))
if not results:
    raise RuntimeError("No audio generated")

chunks = []
for result in results:
    audio = getattr(result, "audio", None)
    if audio is None and isinstance(result, (tuple, list)) and len(result) >= 3:
        audio = result[2]
    if audio is None:
        continue
    if hasattr(audio, "numpy"):
        audio = audio.numpy()
    chunks.append(audio)

if not chunks:
    raise RuntimeError("No audio chunks found")

full = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
sf.write(str(output_wav), full, 24000)
"""
        result = subprocess.run(
            [python_bin, "-c", kokoro_code],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=900,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Kokoro failed")

        ffmpeg = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(wav_path),
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "64k",
                str(output_mp3),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if ffmpeg.returncode != 0:
            raise RuntimeError(ffmpeg.stderr.strip() or "ffmpeg failed")


def iter_articles(only: str | None = None) -> list[Path]:
    articles = sorted(p for p in ARTICLES_DIR.glob("*/index.qmd") if p.parent.name[:4].isdigit())
    if only:
        articles = [p for p in articles if p.parent.name == only]
        if not articles:
            raise RuntimeError(f"No article matching --only {only}")
    return articles


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Generate for one article folder name")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED)
    parser.add_argument("--force", action="store_true", help="Regenerate even if audio.mp3 exists")
    args = parser.parse_args()

    python_bin = resolve_kokoro_python()
    articles = iter_articles(args.only)
    print(f"Using Kokoro Python: {python_bin}")
    print(f"Articles: {len(articles)}")

    for qmd in articles:
        out = REPO_ROOT / "gh-audio" / qmd.parent.name / "narration.mp3"
        if out.exists() and not args.force:
            print(f"skip  {qmd.parent.name} (exists)")
            continue
        text = qmd_to_speech_text(qmd)
        if not text:
            print(f"skip  {qmd.parent.name} (empty text)")
            continue
        words = len(re.findall(r"\w+", text))
        print(f"gen   {qmd.parent.name} ({words} words) -> {out.name}")
        generate_kokoro_mp3(text, out, voice=args.voice, speed=args.speed, python_bin=python_bin)
        size_kb = out.stat().st_size / 1024
        print(f"done  {qmd.parent.name} ({size_kb:.0f} KB)")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
