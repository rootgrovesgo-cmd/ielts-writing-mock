#!/usr/bin/env python3
"""Generate Set A listening mp3s from tools/listening_script.py using edge-tts + ffmpeg.

Audio is pre-generated practice TTS, not official Cambridge recordings.
Do not add edge-tts to the web app requirements — this script is build-time only.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT))

from listening_script import SECTIONS, VOICES  # noqa: E402

OUT_DIR = ROOT / "static" / "audio" / "listening_set_a"
PAPER_PATH = ROOT / "prompts" / "listening_set_a.json"
FFMPEG = "ffmpeg"
SAMPLE_RATE = 24000
BITRATE = "72k"
TURN_PAD = 0.15


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def make_silence(path: Path, seconds: float) -> None:
    seconds = max(0.05, float(seconds))
    run(
        [
            FFMPEG,
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r={SAMPLE_RATE}:cl=mono",
            "-t",
            f"{seconds:.3f}",
            "-c:a",
            "libmp3lame",
            "-b:a",
            BITRATE,
            str(path),
        ]
    )


def normalize(src: Path, dest: Path) -> None:
    run(
        [
            FFMPEG,
            "-y",
            "-i",
            str(src),
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-c:a",
            "libmp3lame",
            "-b:a",
            BITRATE,
            str(dest),
        ]
    )


def concat(paths: list[Path], dest: Path, work: Path) -> None:
    list_file = work / "concat.txt"
    lines = []
    for path in paths:
        # ffmpeg concat demuxer requires escaped paths
        escaped = str(path).replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run(
        [
            FFMPEG,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c:a",
            "libmp3lame",
            "-b:a",
            BITRATE,
            "-ar",
            str(SAMPLE_RATE),
            "-ac",
            "1",
            str(dest),
        ]
    )


def probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        text=True,
    )
    return float(out.strip())


async def tts_to_file(text: str, voice: str, dest: Path, attempts: int = 4) -> None:
    import edge_tts

    tmp = dest.with_suffix(".raw.mp3")
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            tmp.unlink(missing_ok=True)
            communicate = edge_tts.Communicate(text, voice, rate="-5%")
            await communicate.save(str(tmp))
            if tmp.stat().st_size < 200:
                raise RuntimeError(f"TTS wrote an empty clip for {dest.name}")
            normalize(tmp, dest)
            tmp.unlink(missing_ok=True)
            return
        except Exception as exc:  # noqa: BLE001 — retry network/TTS flakiness
            last_error = exc
            tmp.unlink(missing_ok=True)
            dest.unlink(missing_ok=True)
            if attempt >= attempts:
                break
            await asyncio.sleep(2 * attempt)
    raise last_error or RuntimeError("TTS failed")


async def build_section(section_id: int, work: Path, force: bool) -> Path:
    cues = SECTIONS[section_id]
    clips: list[Path] = []
    cache = work / f"s{section_id}"
    cache.mkdir(parents=True, exist_ok=True)
    for i, cue in enumerate(cues, start=1):
        dest = cache / f"{i:03d}.mp3"
        kind = cue[0]
        if dest.exists() and not force and dest.stat().st_size > 200:
            clips.append(dest)
            continue
        if kind == "say":
            _, speaker, text = cue
            voice = VOICES[speaker]
            print(f"  S{section_id} {i:03d} {speaker}: {text[:64]}…")
            await tts_to_file(text, voice, dest)
            # tiny pad after each spoken line so turns don't collide
            pad_path = cache / f"{i:03d}p.mp3"
            make_silence(pad_path, TURN_PAD)
            clips.append(dest)
            clips.append(pad_path)
        elif kind in {"pause", "gap"}:
            make_silence(dest, cue[1])
            clips.append(dest)
        else:
            raise ValueError(f"Unknown cue {cue}")
    out = OUT_DIR / f"section{section_id}.mp3"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    concat(clips, out, cache)
    return out


def update_paper_durations(durations: dict[int, int]) -> None:
    paper = json.loads(PAPER_PATH.read_text(encoding="utf-8"))
    for section in paper.get("sections") or []:
        sid = int(section["id"])
        if sid in durations:
            section.setdefault("audio", {})
            section["audio"]["file"] = f"section{sid}.mp3"
            section["audio"]["duration_seconds"] = durations[sid]
    PAPER_PATH.write_text(json.dumps(paper, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def main_async(args: argparse.Namespace) -> int:
    work = Path(args.work or (ROOT / "tools" / ".listening-audio-work"))
    work.mkdir(parents=True, exist_ok=True)
    sections = args.section or [1, 2, 3, 4]
    durations: dict[int, int] = {}
    for sid in sections:
        print(f"Building section {sid}…")
        out = await build_section(sid, work, force=args.force)
        seconds = probe_duration(out)
        durations[sid] = int(round(seconds))
        size_mb = out.stat().st_size / (1024 * 1024)
        print(f"  wrote {out}  {durations[sid]}s  {size_mb:.2f} MB")
    # Preserve durations for sections not rebuilt this run.
    if PAPER_PATH.exists() and set(durations) != {1, 2, 3, 4}:
        paper = json.loads(PAPER_PATH.read_text(encoding="utf-8"))
        for section in paper.get("sections") or []:
            sid = int(section["id"])
            if sid not in durations:
                try:
                    durations[sid] = int((section.get("audio") or {}).get("duration_seconds") or 0)
                except (TypeError, ValueError):
                    durations[sid] = 0
    if durations:
        update_paper_durations(durations)
        print("Updated paper durations:", durations)
        total = sum(p.stat().st_size for p in OUT_DIR.glob("section*.mp3"))
        print(f"Total audio size: {total / (1024 * 1024):.2f} MB")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Listening Set A mp3s")
    parser.add_argument("--section", type=int, action="append", choices=[1, 2, 3, 4])
    parser.add_argument("--force", action="store_true", help="Regenerate clips even if cached")
    parser.add_argument("--work", type=Path, help="Working directory for intermediate clips")
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
