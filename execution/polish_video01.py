#!/usr/bin/env python3
"""
Video Polish (transitions + captions + fade-to-black + BGM)

Multi-stage pipeline:
  Stage 1: Cross-dissolve transitions (xfade 0.3s) — includes brand card
  Stage 2: Poppins SemiBold captions via PIL + ffmpeg overlay
  Stage 3: Fade-to-black ending (1s) — after brand card
  Stage 4: BGM overlay at 15%

Usage:
    python3 execution/polish_video01.py
    python3 execution/polish_video01.py --config .tmp/scene_config.json
"""
from __future__ import annotations

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ─── Paths ────────────────────────────────────────────────────────────────────
DEFAULT_CLIPS_DIR = Path(".tmp/assembly_v3")
POLISH_DIR = Path(".tmp/polish")
DEFAULT_OUTPUT_DIR = Path("assets/video_01/videos")
DEFAULT_FINAL_OUTPUT = DEFAULT_OUTPUT_DIR / "video_01_final.mp4"
DEFAULT_BGM_TRACK = Path("examples/audio_lock/bgm_track.mp3")
FONT_FILE = Path("assets/fonts/Poppins-SemiBold.ttf")
FONT_BOLD = Path("assets/fonts/Poppins-Bold.ttf")

BGM_VOLUME = 0.15
XFADE_DUR = 0.3
FADE_OUT = 1.0
VIDEO_W, VIDEO_H = 1080, 1920

# Default clips for Video 01 (preserved for backward compatibility)
DEFAULT_CLIPS = [
    {"file": "00_a1_hook.ts",              "type": "anchor"},
    {"file": "01_a2_rule1_speaking.ts",    "type": "anchor"},
    {"file": "02_b1_safety.ts",            "type": "broll"},
    {"file": "03_a3_rule2_speaking.ts",    "type": "anchor"},
    {"file": "04_b2_understanding.ts",     "type": "broll"},
    {"file": "05_a4_rule3_speaking.ts",    "type": "anchor"},
    {"file": "06_b3_belief.ts",            "type": "broll"},
    {"file": "07_a5_cta.ts",              "type": "anchor"},
    {"file": "08_brand_card.ts",          "type": "brand"},
]

# Default captions for Video 01
DEFAULT_CAPTIONS = [
    {"clip_idx": 0, "line1": "When your child fails a test...",
                    "line2": "say these three things."},
    {"clip_idx": 1, "line1": "Number one...",
                    "line2": '"It\'s okay, let\'s look at it together."'},
    {"clip_idx": 3, "line1": "Number two...",
                    "line2": '"What part was hardest for you?"'},
    {"clip_idx": 5, "line1": "Number three...",
                    "line2": '"I know you\'ll do better next time."'},
    {"clip_idx": 7, "line1": "Share this...",
                    "line2": "to help another parent."},
]


def load_config():
    """Load polish config from --config flag or use defaults (Learning 25)."""
    config_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--config" and i + 1 < len(sys.argv):
            config_path = Path(sys.argv[i + 1])
            break

    if config_path and config_path.exists():
        print(f"   Loading config: {config_path}")
        cfg = json.loads(config_path.read_text())
        clips_dir = Path(cfg.get("clips_dir", str(DEFAULT_CLIPS_DIR)))
        output_dir = Path(cfg.get("output_dir", str(DEFAULT_OUTPUT_DIR)))
        final_output = Path(cfg.get("final_output", str(output_dir / "final_polished.mp4")))
        bgm = Path(cfg.get("bgm_track", str(DEFAULT_BGM_TRACK)))
        clips = cfg.get("clips", DEFAULT_CLIPS)
        captions = cfg.get("captions", DEFAULT_CAPTIONS)
        return clips_dir, output_dir, final_output, bgm, clips, captions
    else:
        return DEFAULT_CLIPS_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_FINAL_OUTPUT, DEFAULT_BGM_TRACK, DEFAULT_CLIPS, DEFAULT_CAPTIONS


def run_cmd(cmd, desc=""):
    print(f"   → {desc}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ERROR: {result.stderr[-800:]}")
        return False
    return True


def get_duration(filepath):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=duration", "-of", "csv=p=0", str(filepath)],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return float(result.stdout.strip().split('\n')[0])
    return 0


def get_clip_durations():
    durations = []
    for c in CLIPS:
        p = CLIPS_DIR / c["file"]
        d = get_duration(p)
        durations.append(d)
    return durations


def compute_xfade_clip_starts(durations):
    """Compute clip start times after xfade transitions."""
    starts = [0.0]
    accumulated = durations[0]
    for i in range(1, len(durations)):
        starts.append(accumulated - XFADE_DUR)
        accumulated = (accumulated - XFADE_DUR) + durations[i]
    return starts, accumulated


def render_caption_overlay(line1, line2, output_path):
    """Render a single caption as a transparent PNG using PIL."""
    img = Image.new("RGBA", (VIDEO_W, VIDEO_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_regular = ImageFont.truetype(str(FONT_FILE), 42)
    font_keyword = ImageFont.truetype(str(FONT_FILE), 46)

    # Position: 60% from top of screen
    y_line1 = int(VIDEO_H * 0.60)       # 1152px
    y_line2 = int(VIDEO_H * 0.60) + 60  # 1212px

    # Line 1: White with shadow
    bbox1 = draw.textbbox((0, 0), line1, font=font_regular)
    w1 = bbox1[2] - bbox1[0]
    x1 = (VIDEO_W - w1) // 2
    # Shadow
    draw.text((x1 + 2, y_line1 + 2), line1, font=font_regular, fill=(0, 0, 0, 180))
    # Text
    draw.text((x1, y_line1), line1, font=font_regular, fill=(255, 255, 255, 255))

    # Line 2: Yellow (#FFD700) with shadow
    bbox2 = draw.textbbox((0, 0), line2, font=font_keyword)
    w2 = bbox2[2] - bbox2[0]
    x2 = (VIDEO_W - w2) // 2
    # Shadow
    draw.text((x2 + 2, y_line2 + 2), line2, font=font_keyword, fill=(0, 0, 0, 180))
    # Text
    draw.text((x2, y_line2), line2, font=font_keyword, fill=(255, 215, 0, 255))

    img.save(str(output_path), "PNG")


def stage1_check_or_build(durations):
    """Check if Stage 1 output exists, otherwise build xfade transitions."""
    s1_output = POLISH_DIR / "s1_xfade.mp4"
    if s1_output.exists():
        dur = get_duration(s1_output)
        if dur > 30:  # reasonable duration
            print(f"\n   Stage 1 already done: {dur:.1f}s — reusing")
            return s1_output, dur

    print(f"\n{'=' * 70}")
    print("STAGE 1: Cross-dissolve transitions (xfade)")

    n = len(CLIPS)
    inputs = []
    for c in CLIPS:
        inputs.extend(["-i", str(CLIPS_DIR / c["file"])])

    # Build xfade + acrossfade chain
    v_filters = []
    a_filters = []

    offset = durations[0] - XFADE_DUR
    v_filters.append(f"[0:v][1:v]xfade=transition=fade:duration={XFADE_DUR}:offset={offset:.6f}[v01]")
    a_filters.append(f"[0:a][1:a]acrossfade=d={XFADE_DUR}:c1=tri:c2=tri[a01]")
    accumulated = durations[0] + durations[1] - XFADE_DUR

    for i in range(2, n):
        prev_v = "v01" if i == 2 else f"v{i-1}"
        prev_a = "a01" if i == 2 else f"a{i-1}"
        next_v = f"v{i}" if i < n - 1 else "vout"
        next_a = f"a{i}" if i < n - 1 else "aout"

        offset = accumulated - XFADE_DUR
        v_filters.append(f"[{prev_v}][{i}:v]xfade=transition=fade:duration={XFADE_DUR}:offset={offset:.6f}[{next_v}]")
        a_filters.append(f"[{prev_a}][{i}:a]acrossfade=d={XFADE_DUR}:c1=tri:c2=tri[{next_a}]")
        accumulated = accumulated + durations[i] - XFADE_DUR

    fc = ";".join(v_filters + a_filters)

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
        "-movflags", "+faststart",
        str(s1_output),
    ]

    if not run_cmd(cmd, "xfade chain"):
        sys.exit(1)

    dur = get_duration(s1_output)
    print(f"   ✓ Stage 1 done: {dur:.1f}s")
    return s1_output, dur


def stage2_captions(input_file, durations):
    """Stage 2: Render caption PNGs with PIL, overlay with ffmpeg."""
    print(f"\n{'=' * 70}")
    print("STAGE 2: Poppins SemiBold captions (PIL + overlay)")

    cap_dir = POLISH_DIR / "captions"
    cap_dir.mkdir(parents=True, exist_ok=True)

    # Compute clip start times in the xfaded video
    clip_starts, total_dur = compute_xfade_clip_starts(durations)

    # Render caption overlays
    cap_images = []
    cap_timings = []
    for i, cap in enumerate(CAPTIONS):
        idx = cap["clip_idx"]
        start = clip_starts[idx] + 0.5
        end = clip_starts[idx] + durations[idx] - 0.5

        img_path = cap_dir / f"caption_{i}.png"
        render_caption_overlay(cap["line1"], cap["line2"], img_path)
        cap_images.append(img_path)
        cap_timings.append((start, end))
        print(f"   Caption {i}: [{start:.1f}s → {end:.1f}s] {cap['line1']}")

    # Build ffmpeg overlay chain
    # Input 0 = video, Inputs 1-5 = caption PNGs
    inputs = ["-i", str(input_file)]
    for img in cap_images:
        inputs.extend(["-i", str(img)])

    # Chain overlays with enable
    overlay_chain = []
    for i, (start, end) in enumerate(cap_timings):
        src = f"[tmp{i}]" if i > 0 else "[0:v]"
        dst = f"[tmp{i+1}]" if i < len(cap_timings) - 1 else "[vout]"
        overlay_chain.append(
            f"{src}[{i+1}:v]overlay=0:0:enable='between(t,{start:.2f},{end:.2f})'{dst}"
        )

    fc = ";".join(overlay_chain)
    output = POLISH_DIR / "s2_captions.mp4"

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", fc,
        "-map", "[vout]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(output),
    ]

    if not run_cmd(cmd, f"Caption overlays → {output.name}"):
        sys.exit(1)

    print(f"   ✓ Stage 2 done: {len(cap_timings)} captions")
    return output


def stage3_fade_to_black(input_file, total_dur):
    """Stage 3: Fade to black at end."""
    print(f"\n{'=' * 70}")
    print("STAGE 3: Fade to black")

    output = POLISH_DIR / "s3_fadeout.mp4"
    fade_start = total_dur - FADE_OUT

    cmd = [
        "ffmpeg", "-y", "-i", str(input_file),
        "-vf", f"fade=t=out:st={fade_start:.2f}:d={FADE_OUT}",
        "-af", f"afade=t=out:st={fade_start:.2f}:d={FADE_OUT}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output),
    ]

    if not run_cmd(cmd, f"Fade to black ({FADE_OUT}s)"):
        sys.exit(1)

    print(f"   ✓ Stage 3 done")
    return output


def stage4_bgm(input_file):
    """Stage 4: BGM overlay."""
    print(f"\n{'=' * 70}")
    print(f"STAGE 4: BGM overlay ({BGM_TRACK})")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_file),
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
        str(FINAL_OUTPUT),
    ]

    if not run_cmd(cmd, f"BGM at {BGM_VOLUME}"):
        sys.exit(1)

    dur = get_duration(FINAL_OUTPUT)
    size_mb = FINAL_OUTPUT.stat().st_size / (1024 * 1024)
    print(f"   ✓ Stage 4 done: {dur:.1f}s, {size_mb:.1f}MB")
    return dur


def main():
    global CLIPS_DIR, OUTPUT_DIR, FINAL_OUTPUT, BGM_TRACK, CLIPS, CAPTIONS
    CLIPS_DIR, OUTPUT_DIR, FINAL_OUTPUT, BGM_TRACK, CLIPS, CAPTIONS = load_config()

    print("=" * 70)
    print("VIDEO POLISH")
    print(f"   Transitions: cross-dissolve ({XFADE_DUR}s)")
    print(f"   Captions: Poppins SemiBold (white + yellow)")
    print(f"   Ending: fade-to-black ({FADE_OUT}s)")
    print(f"   BGM: {BGM_TRACK} at {BGM_VOLUME} volume")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    POLISH_DIR.mkdir(parents=True, exist_ok=True)

    # Get clip durations
    durations = get_clip_durations()
    print(f"\nClip durations: {[f'{d:.3f}' for d in durations]}")

    # Stage 1: Transitions (reuse if exists)
    s1_out, actual_dur = stage1_check_or_build(durations)

    # Stage 2: Captions (PIL-rendered overlays)
    s2_out = stage2_captions(s1_out, durations)

    # Stage 3: Fade to black
    s3_out = stage3_fade_to_black(s2_out, actual_dur)

    # Stage 4: BGM
    final_dur = stage4_bgm(s3_out)

    # Summary
    print(f"\n{'=' * 70}")
    print(f"✅ VIDEO 01 POLISHED: {FINAL_OUTPUT}")
    print(f"   Duration: {final_dur:.1f}s")
    print(f"   Size: {FINAL_OUTPUT.stat().st_size / (1024*1024):.1f}MB")
    print(f"   Transitions: cross-dissolve")
    print(f"   Captions: Poppins SemiBold (5 scenes)")
    print(f"   Ending: fade-to-black")
    print(f"   BGM: {BGM_TRACK} at {BGM_VOLUME}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
