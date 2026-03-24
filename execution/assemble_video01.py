#!/usr/bin/env python3
"""
Video Assembly (ffmpeg filter_complex)

Stitches all video clips in sequence:
  A1 → A2 → B1 → A3 → B2 → A4 → B3 → A5 → Brand Card

Rules (from Learning 12 + 21):
  - Anchor videos (A1-A5): Speed up 1.2x (video + audio)
  - B-roll videos (B1-B3): Normal speed (1.0x), silent audio
  - Brand card: 2s static image with silent audio
  - BGM: bgm_track.mp3 looped at 15% volume beneath dialogue
  - Audio MUST NOT bleed across clip boundaries
  - Output: 9:16 portrait MP4

Fix for audio bleed:
  Each clip is normalized with audio trimmed/padded to EXACT video duration
  using apad + shortest, ensuring zero drift.

Usage:
    python3 execution/assemble_video01.py
    python3 execution/assemble_video01.py --config .tmp/scene_config.json
"""
from __future__ import annotations

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# ─── Default config (Video 01 hardcoded — backward compatible) ────────────────
DEFAULT_BASE = Path("assets/video_01/videos")
DEFAULT_OUTPUT = DEFAULT_BASE / "video_01_final.mp4"
TEMP_DIR = Path(".tmp/assembly_v3")
DEFAULT_BGM_TRACK = Path("examples/audio_lock/bgm_track.mp3")
BGM_VOLUME = 0.15  # 15% volume for BGM
DEFAULT_BRAND_CARD = Path("examples/brand_outro_lock/brand_outro_lock_upscaled.png")
BRAND_CARD_DURATION = 2.0  # seconds

# Default scenes for Video 01 (preserved for backward compatibility)
DEFAULT_SCENES = [
    {"id": "a1_hook",            "file": "a1_hook/anchor_video.mp4",               "type": "anchor"},
    {"id": "a2_rule1_speaking",  "file": "a2_rule1_speaking/anchor_video.mp4",     "type": "anchor"},
    {"id": "b1_safety",          "file": "b1_safety/broll_video.mp4",              "type": "broll"},
    {"id": "a3_rule2_speaking",  "file": "a3_rule2_speaking/anchor_video.mp4",     "type": "anchor"},
    {"id": "b2_understanding",   "file": "b2_understanding/broll_video.mp4",       "type": "broll"},
    {"id": "a4_rule3_speaking",  "file": "a4_rule3_speaking/anchor_video.mp4",     "type": "anchor"},
    {"id": "b3_belief",          "file": "b3_belief/broll_video.mp4",              "type": "broll"},
    {"id": "a5_cta",             "file": "a5_cta/anchor_video.mp4",               "type": "anchor"},
    {"id": "brand_card",         "file": None,                                     "type": "brand"},
]


def load_config():
    """Load scene config from --config flag or use defaults (Learning 25)."""
    config_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--config" and i + 1 < len(sys.argv):
            config_path = Path(sys.argv[i + 1])
            break

    if config_path and config_path.exists():
        print(f"   Loading config: {config_path}")
        cfg = json.loads(config_path.read_text())
        base = Path(cfg.get("base_dir", str(DEFAULT_BASE)))
        output = Path(cfg.get("output", str(base / "final_assembled.mp4")))
        bgm = Path(cfg.get("bgm_track", str(DEFAULT_BGM_TRACK)))
        brand = Path(cfg.get("brand_card", str(DEFAULT_BRAND_CARD)))
        scenes = cfg.get("scenes", DEFAULT_SCENES)
        return base, output, bgm, brand, scenes
    else:
        return DEFAULT_BASE, DEFAULT_OUTPUT, DEFAULT_BGM_TRACK, DEFAULT_BRAND_CARD, DEFAULT_SCENES


def run_cmd(cmd, desc=""):
    """Run a command and check for errors."""
    print(f"   → {desc}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ERROR: {result.stderr[:800]}")
        return False
    return True


def get_duration(filepath):
    """Get exact video stream duration."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=duration",
         "-of", "csv=p=0", str(filepath)],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return float(result.stdout.strip().split('\n')[0])
    return 0


def main():
    BASE, OUTPUT, BGM_TRACK, BRAND_CARD, SCENES = load_config()

    print("=" * 70)
    print("VIDEO ASSEMBLY (filter_complex)")
    print(f"   Scenes: {len(SCENES)} clips")
    print(f"   Anchor speed: 1.2x")
    print(f"   B-roll speed: 1.0x (normal)")
    print(f"   BGM: {BGM_TRACK} at {BGM_VOLUME} volume")
    print(f"   Output: {OUTPUT}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Verify all source files exist
    missing = []
    for s in SCENES:
        if s["type"] == "brand":
            continue  # Brand card is generated from PNG, not a video file
        p = BASE / s["file"]
        if not p.exists():
            missing.append(str(p))
    if not BGM_TRACK.exists():
        missing.append(str(BGM_TRACK))
    if not BRAND_CARD.exists():
        missing.append(str(BRAND_CARD))
    if missing:
        print(f"\nERROR: Missing files:")
        for m in missing:
            print(f"   - {m}")
        sys.exit(1)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # ─── Step 1: Normalize each clip ─────────────────────────────────────
    # Key fix: each clip gets audio EXACTLY matching video duration
    # using -t to hard-cut both streams to exact same length
    normalized = []
    for i, scene in enumerate(SCENES):
        dst = TEMP_DIR / f"{i:02d}_{scene['id']}.ts"  # Use .ts for lossless concat

        print(f"\n[{i+1}/{len(SCENES)}] {scene['id']} ({scene['type']})")

        if scene["type"] == "brand":
            # Brand card: generate 2s video from static PNG with silent audio
            print(f"   Brand card: {BRAND_CARD} → {BRAND_CARD_DURATION}s clip")
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(BRAND_CARD),
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", f"{BRAND_CARD_DURATION:.6f}",
                "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,"
                       "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                str(dst),
            ]
            if not run_cmd(cmd, f"Brand card → {dst.name}"):
                print(f"   FAILED: {scene['id']}")
                sys.exit(1)
        elif scene["type"] == "anchor":
            src = BASE / scene["file"]
            # Get source video duration, then compute sped-up duration
            src_dur = get_duration(src)
            target_dur = src_dur / 1.2
            print(f"   Source: {src_dur:.3f}s → Target (1.2x): {target_dur:.3f}s")

            # Speed up 1.2x, normalize, hard-cut audio to exact video duration
            cmd = [
                "ffmpeg", "-y", "-i", str(src),
                "-filter_complex",
                "[0:v]setpts=PTS/1.2,scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30[v];"
                "[0:a]atempo=1.2,apad[a]",
                "-map", "[v]", "-map", "[a]",
                "-t", f"{target_dur:.6f}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
                str(dst),
            ]
            if not run_cmd(cmd, f"1.2x + normalize + trim to {target_dur:.3f}s"):
                # Fallback: no audio
                cmd_fallback = [
                    "ffmpeg", "-y", "-i", str(src),
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-filter_complex",
                    "[0:v]setpts=PTS/1.2,scale=1080:1920:force_original_aspect_ratio=decrease,"
                    "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30[v]",
                    "-map", "[v]", "-map", "1:a",
                    "-t", f"{target_dur:.6f}",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                    "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
                    str(dst),
                ]
                if not run_cmd(cmd_fallback, "fallback (silent audio)"):
                    print(f"   FAILED: {scene['id']}")
                    sys.exit(1)
        elif scene["type"] == "broll":
            # B-roll: normal speed, silent audio, TRIM TO LAST 40%
            # (keep second half — skip first 60% of the clip)
            src = BASE / scene["file"]
            src_dur = get_duration(src)
            trim_dur = src_dur * 0.40  # keep last 40%
            skip_to = src_dur * 0.60   # start from 60% mark
            print(f"   Source: {src_dur:.3f}s → Trim to last 40%: {trim_dur:.3f}s (skip {skip_to:.3f}s)")

            cmd = [
                "ffmpeg", "-y",
                "-ss", f"{skip_to:.6f}",  # Seek to 60% mark
                "-i", str(src),
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-filter_complex",
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30[v]",
                "-map", "[v]", "-map", "1:a",
                "-t", f"{trim_dur:.6f}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
                str(dst),
            ]
            if not run_cmd(cmd, f"trim last 40% + silent audio → {dst.name}"):
                print(f"   FAILED: {scene['id']}")
                sys.exit(1)

        normalized.append(dst)
        size_kb = dst.stat().st_size // 1024
        # Verify exact alignment
        v_dur = get_duration(dst)
        a_result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=duration", "-of", "csv=p=0", str(dst)],
            capture_output=True, text=True,
        )
        a_dur = float(a_result.stdout.strip().split('\n')[0]) if a_result.returncode == 0 and a_result.stdout.strip() else 0
        drift = abs(v_dur - a_dur) * 1000  # ms
        status = "✓" if drift < 50 else "⚠️ DRIFT"
        print(f"   {status} {dst.name} ({size_kb}KB) | v={v_dur:.3f}s a={a_dur:.3f}s drift={drift:.1f}ms")

    # ─── Step 2: Concat using concat demuxer with .ts files ──────────────
    concat_file = TEMP_DIR / "concat.txt"
    with open(concat_file, "w") as f:
        for n in normalized:
            f.write(f"file '{n.resolve()}'\n")

    print(f"\n{'_' * 70}")
    print("Concatenating all clips...")

    concat_output = TEMP_DIR / "concat_no_bgm.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
        "-movflags", "+faststart",
        str(concat_output),
    ]
    if not run_cmd(cmd, f"Concat → {concat_output.name}"):
        print("FAILED to concatenate")
        sys.exit(1)

    # Verify concat audio/video alignment
    concat_v = get_duration(concat_output)
    a_res = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=duration", "-of", "csv=p=0", str(concat_output)],
        capture_output=True, text=True,
    )
    concat_a = float(a_res.stdout.strip().split('\n')[0]) if a_res.returncode == 0 and a_res.stdout.strip() else 0
    print(f"   Concat: video={concat_v:.3f}s audio={concat_a:.3f}s drift={abs(concat_v-concat_a)*1000:.1f}ms")

    # ─── Step 3: Add BGM track ───────────────────────────────────────────
    print(f"\n{'_' * 70}")
    print(f"Adding BGM track ({BGM_TRACK})...")
    print(f"   BGM volume: {BGM_VOLUME} (anchor dialogue: 1.0)")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(concat_output),
        "-stream_loop", "-1", "-i", str(BGM_TRACK),
        "-filter_complex",
        f"[0:a]volume=1.0[dialogue];"
        f"[1:a]volume={BGM_VOLUME}[bgm];"
        f"[dialogue][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        str(OUTPUT),
    ]
    if not run_cmd(cmd, f"BGM overlay → {OUTPUT}"):
        print("FAILED to add BGM")
        sys.exit(1)

    # ─── Summary ─────────────────────────────────────────────────────────
    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print(f"\n{'=' * 70}")
    print(f"✅ FINAL VIDEO ASSEMBLED: {OUTPUT}")
    print(f"   Size: {size_mb:.1f}MB")
    print(f"   Resolution: 1080x1920 (9:16)")
    print(f"   Anchor speed: 1.2x | B-roll speed: 1.0x | Brand card: {BRAND_CARD_DURATION}s")
    print(f"   BGM: {BGM_TRACK} at {BGM_VOLUME} volume")

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(OUTPUT)],
        capture_output=True, text=True,
    )
    if probe.returncode == 0:
        duration = float(probe.stdout.strip())
        print(f"   Duration: {duration:.1f}s")

    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
