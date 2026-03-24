#!/usr/bin/env python3
"""
Master Pipeline Orchestrator — Topic → Finished Video

Takes a topic from the research phase and runs the full 8-step pipeline.
Respects ALL rules from video_pipeline_master.md — no quality loss.

Key compliance:
  - Anchor images: LOCKED from examples/anchor_character_lock/ (Learning 8, Rule Set 8)
  - Anchor videos: Kling 3.0 PRIMARY, Veo 3.1 backup (Learning 19)
  - Voice: Pure English, NO "Filipino"/"accent" in prompts (Rule Set 9.1)
  - Dialogue: ≤8 words per clip (Rule Set 9.6)
  - Camera: "near-static" for anchors (Rule Set 9.3)
  - B-roll: 11-13 year old students only (Rule Set 4)
  - No finger-count prompts (Learning 17)
  - Eye contact mandatory (Learning 18)
  - Font: Kalam-Bold.ttf (Learning 16)
  - BGM: 15%, anchor 100%, B-roll audio 25% (Learning 12)

Usage:
    python3 execution/run_pipeline.py --topic "Signs your teen is struggling" --video-id 1
    python3 execution/run_pipeline.py --topic "..." --video-id 1 --step 3  # Resume from step 3
    python3 execution/run_pipeline.py --topic "..." --video-id 1 --dry-run  # Test without API calls
"""
from __future__ import annotations

import os
import sys
import json
import time
import shutil
import base64
import argparse
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add execution/ to path for module imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from video_engines import generate_kling_video, generate_veo_video
from error_logger import log_error, log_blocked_steps
from drive_uploader import upload_pipeline_assets

load_dotenv()

# ─── API Keys ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")
KLING_ACCESS = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET = os.getenv("KLING_SECRET_KEY", "")

OPENAI_HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}

# ─── LOCKED Anchor Character + Background (verbatim from directive Rule Set 4) ─
CHAR_DESC = (
    "A warm 3D-animated Pixar-style digital illustration of a Filipina grandmother "
    "(Lola) in her late 50s to early 60s, with grey-streaked black hair pulled back "
    "in a neat low bun, warm medium-brown skin with gentle smile lines and soft "
    "wrinkles around the eyes, kind dark brown eyes, small pearl stud earrings, a "
    "gentle warm smile with soft rounded cheeks, and a natural Filipino facial "
    "structure. She wears a cream/beige embroidered blouse with delicate vine and "
    "floral embroidery down the center front, small buttons, short sleeves. She "
    "sits in a wooden chair with a warm backrest."
)

BG_DESC = (
    "The background is a cozy Filipino home interior with warm cream/beige walls, "
    "framed family photos on the walls, a potted green plant (pothos) to one side, "
    "a warm golden glow from natural light through a window, a tablecloth-covered "
    "side table with more framed photos and a vase of flowers, warm terracotta and "
    "wood tones throughout. The overall color palette is warm cream, amber, golden "
    "brown, and soft green accents."
)

STYLE_SUFFIX = (
    "Warm 3D-animated Pixar-style, smooth digital illustration, clean lines, warm "
    "color palette, soft lighting with gentle gradients. 9:16 vertical composition "
    "with space at top and bottom for text overlays. No photorealistic, no harsh "
    "shadows, no cold tones, no text, no watermark, no extra characters."
)

# ─── LOCKED Voice Blueprint (Rule Set 9.1 + Lesson 41 voice consistency) ──────
# GAP 2 FIX: Enhanced with punctuation pauses per 41_Consistent_Character_Voices_in_Veo_3.1.md
VOICE_BLUEPRINT = (
    'Warm maternal tone, clear English, medium pace, gentle authority. '
    'Briefly pauses before key words... as if thinking. '
    'Sentences taper off slightly rather than ending sharply. '
    'Controlled pacing with clear pauses between statements.'
)

# ─── LOCKED Anchor Images (Rule Set 8 — NEVER regenerate) ─────────────────────
LOCKED_ANCHOR_MAP = {
    "a1_hook":          "examples/anchor_character_lock/scene_01_anchor_upscaled.png",
    "a2_rule1":         "examples/anchor_character_lock/scene_02_anchor_upscaled.png",
    "a3_rule2":         "examples/anchor_character_lock/scene_05_anchor_upscaled.png",
    "a4_rule3":         "examples/anchor_character_lock/scene_08_anchor_upscaled.png",
    "a5_cta":           "examples/anchor_character_lock/scene_11_anchor_upscaled.png",
}

# ─── LOCKED Audio Assets (Rule Set 3) ─────────────────────────────────────────
BGM_PATH = "examples/audio_lock/bgm_track.mp3"


def update_state(state_path: Path, video_id: int, step: int, status: str,
                 detail: str = "", data: dict = None):
    """Update pipeline state file for the webapp to read."""
    state_path.parent.mkdir(parents=True, exist_ok=True)

    if state_path.exists():
        state = json.loads(state_path.read_text())
    else:
        state = {"video_id": video_id, "steps": {}}

    state["steps"][str(step)] = {
        "status": status,
        "detail": detail,
        "updated_at": datetime.now().isoformat(),
    }
    if data:
        state["steps"][str(step)]["data"] = data

    state_path.write_text(json.dumps(state, indent=2, default=str))


def chatgpt(system: str, user: str, json_mode: bool = True) -> dict | str:
    """Call ChatGPT and return parsed response."""
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    kwargs = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
        "max_tokens": 3000,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    resp = client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content

    if json_mode:
        return json.loads(content)
    return content


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: Concept & Script
# Compliant with: Rule Set 1 (3-item listicle), Rule Set 9.6 (≤8 words/clip)
# ═══════════════════════════════════════════════════════════════════════════════

def step1_concept_and_script(topic: str, video_dir: Path, state_path: Path, vid: int,
                             dry_run: bool = False) -> dict:
    """Generate 3-rule listicle script from a topic."""
    update_state(state_path, vid, 1, "running", "Generating concept and script via ChatGPT...")

    if dry_run:
        time.sleep(1.5)
        update_state(state_path, vid, 1, "running", "[DRY RUN] Building mock script...")
        time.sleep(1)
        result = {
            "topic": topic,
            "hook_line": "Here's what every... parent should know.",
            "rules": [
                {"number": 1, "phrase": "Listen first", "lead_dialogue": "Number one... 'Listen first.'",
                 "broll_scene": "A 12-year-old Filipino student sitting at desk, writing in notebook"},
                {"number": 2, "phrase": "Ask gently", "lead_dialogue": "Number two... 'Ask gently.'",
                 "broll_scene": "A 13-year-old Filipino student reading book in classroom"},
                {"number": 3, "phrase": "Stay patient", "lead_dialogue": "Number three... 'Stay patient.'",
                 "broll_scene": "An 11-year-old Filipino student smiling while studying with classmates"},
            ],
            "cta_line": "Share this... with another parent.",
            "captions": [
                {"scene": "A1", "line1": "Parents Take Note", "line2": "What Every Parent Should Know"},
                {"scene": "A2", "line1": "Number One", "line2": "Listen First"},
                {"scene": "B1", "line1": "", "line2": ""},
                {"scene": "A3", "line1": "Number Two", "line2": "Ask Gently"},
                {"scene": "B2", "line1": "", "line2": ""},
                {"scene": "A4", "line1": "Number Three", "line2": "Stay Patient"},
                {"scene": "B3", "line1": "", "line2": ""},
                {"scene": "A5", "line1": "Share This", "line2": "For Another Parent"},
            ],
        }
        video_dir.mkdir(parents=True, exist_ok=True)
        (video_dir / "script.json").write_text(json.dumps(result, indent=2))
        update_state(state_path, vid, 1, "done",
                     f"[DRY RUN] Script: {result['hook_line'][:50]}...")
        print(f"   ✓ [DRY RUN] Mock script generated")
        return result

    system = """You are a world-class parenting content writer for viral short-form video.
Your audience: Filipino parents on TikTok/Facebook Reels.
Character: A Filipina grandmother ("Lola") who gives warm, wise parenting advice.

STRICT RULES:
- Always a 3-rule listicle structure (EXACTLY 3 — never 2, never 5)
- Video structure: Hook (4s) → Rule 1 Lead (4s) → Rule 1 B-roll (4s) → Rule 2 Lead (4s) → Rule 2 B-roll (3-4s) → Rule 3 Lead (3-4s) → Rule 3 B-roll (3-4s) → CTA (3-4s)
- 8 scenes total (5 anchor + 3 B-roll)
- CRITICAL: Each line of dialogue must be ≤8 WORDS. Count them. This prevents lip-sync stuttering.
- Dialogue structure: "[2-3 words]... '[2-3 word phrase].'" — use "..." for natural pauses
- PURE ENGLISH only — no Tagalog, no code-switching
- B-roll must show 11-13 year old students (NOT younger) in school/home settings
- NSFW-safe: family-friendly only

OUTPUT JSON:
{
  "topic": "...",
  "hook_line": "Opening line ≤8 words (spoken by Lola)",
  "rules": [
    {"number": 1, "phrase": "Short memorable phrase ≤4 words", "lead_dialogue": "Number one... 'the phrase.'", "broll_scene": "Visual of 11-13yo Filipino students doing X"},
    {"number": 2, ...},
    {"number": 3, ...}
  ],
  "cta_line": "Closing line ≤8 words",
  "captions": [
    {"scene": "A1", "line1": "Setup text", "line2": "Key phrase"},
    {"scene": "A2", "line1": "Number One", "line2": "The phrase"},
    {"scene": "B1", "line1": "", "line2": ""},
    {"scene": "A3", "line1": "Number Two", "line2": "The phrase"},
    {"scene": "B2", "line1": "", "line2": ""},
    {"scene": "A4", "line1": "Number Three", "line2": "The phrase"},
    {"scene": "B3", "line1": "", "line2": ""},
    {"scene": "A5", "line1": "Share this", "line2": "for another parent"}
  ]
}

FEW-SHOT EXAMPLE (for topic "Signs your teen is struggling"):
{
  "topic": "Signs your teen is struggling",
  "hook_line": "Parents... watch for these signs.",
  "rules": [
    {"number": 1, "phrase": "sudden silence", "lead_dialogue": "Number one... 'sudden silence.'", "broll_scene": "A 12-year-old Filipino student sitting quietly alone at a school desk while classmates chat nearby"},
    {"number": 2, "phrase": "grades dropping fast", "lead_dialogue": "Number two... 'grades dropping fast.'", "broll_scene": "A 13-year-old Filipino student looking worried at a test paper with low marks at a wooden home desk"},
    {"number": 3, "phrase": "sleeping too much", "lead_dialogue": "And number three... 'sleeping too much.'", "broll_scene": "A 12-year-old Filipino student falling asleep at a school library table with books open"}
  ],
  "cta_line": "Share this... for another parent.",
  "captions": [
    {"scene": "A1", "line1": "Parents", "line2": "Watch for these signs"},
    {"scene": "A2", "line1": "Number One", "line2": "Sudden Silence"},
    {"scene": "B1", "line1": "", "line2": ""},
    {"scene": "A3", "line1": "Number Two", "line2": "Grades Dropping Fast"},
    {"scene": "B2", "line1": "", "line2": ""},
    {"scene": "A4", "line1": "Number Three", "line2": "Sleeping Too Much"},
    {"scene": "B3", "line1": "", "line2": ""},
    {"scene": "A5", "line1": "Share This", "line2": "For Another Parent"}
  ]
}"""

    user = f"Write a 3-rule listicle script for this topic: {topic}"

    result = chatgpt(system, user)

    # Save to pipeline/ subfolder
    pipeline_dir = video_dir / "pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    script_path = pipeline_dir / "script.json"
    script_path.write_text(json.dumps(result, indent=2))

    update_state(state_path, vid, 1, "done",
                 f"Script: {result.get('hook_line', '')[:50]}...",
                 {"script_path": str(script_path)})

    print(f"   ✓ Script generated: {result.get('hook_line', '')}")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: Image Prompts
# Compliant with: Learning 8 (locked anchors), Rule Set 4 (B-roll 11-13yo),
#                 Learning 7 (NSFW safety), Learning 17 (no finger counts)
# ═══════════════════════════════════════════════════════════════════════════════

def step2_image_prompts(script: dict, video_dir: Path, state_path: Path, vid: int) -> list:
    """Generate B-roll image prompts only — anchor images are LOCKED."""
    update_state(state_path, vid, 2, "running", "Generating B-roll image prompts...")

    rules = script.get("rules", [])

    # Anchor images are LOCKED (Rule Set 8) — just reference the locked files
    anchor_entries = [
        {"id": "a1_hook", "type": "anchor", "title": "A1 — Hook",
         "locked_image": LOCKED_ANCHOR_MAP["a1_hook"]},
        {"id": "a2_rule1", "type": "anchor", "title": "A2 — Rule 1",
         "locked_image": LOCKED_ANCHOR_MAP["a2_rule1"]},
        {"id": "a3_rule2", "type": "anchor", "title": "A3 — Rule 2",
         "locked_image": LOCKED_ANCHOR_MAP["a3_rule2"]},
        {"id": "a4_rule3", "type": "anchor", "title": "A4 — Rule 3",
         "locked_image": LOCKED_ANCHOR_MAP["a4_rule3"]},
        {"id": "a5_cta", "type": "anchor", "title": "A5 — CTA",
         "locked_image": LOCKED_ANCHOR_MAP["a5_cta"]},
    ]

    # B-roll prompts (generated per topic — rule-compliant)
    broll_entries = []
    for i, rule in enumerate(rules):
        broll_desc = rule.get("broll_scene", "a 12-year-old Filipino student studying")
        broll_entries.append({
            "id": f"b{i+1}_rule{rule.get('number', i+1)}",
            "type": "broll",
            "title": f"B{i+1} — Rule {rule.get('number', i+1)} B-roll",
            "prompt": (
                f"A warm 3D-animated Pixar-style digital illustration of {broll_desc}. "
                "The student is 11-13 years old with natural Filipino features. "
                "The setting is a warm Filipino home or school environment with "
                "golden afternoon light, warm wood textures, and cream walls. "
                "Family-friendly, wholesome, safe for work. "
                "Medium shot, eye-level camera. "
                f"{STYLE_SUFFIX}"
            ),
        })

    # Scene order: A1, A2, B1, A3, B2, A4, B3, A5
    all_entries = [
        anchor_entries[0],  # A1
        anchor_entries[1],  # A2
        broll_entries[0],   # B1
        anchor_entries[2],  # A3
        broll_entries[1],   # B2
        anchor_entries[3],  # A4
        broll_entries[2],   # B3
        anchor_entries[4],  # A5
    ]

    pipeline_dir = video_dir / "pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    prompts_path = pipeline_dir / "image_prompts.json"
    prompts_path.write_text(json.dumps(all_entries, indent=2))

    update_state(state_path, vid, 2, "done",
                 "5 anchor images locked + 3 B-roll prompts generated",
                 {"prompts_path": str(prompts_path)})

    print(f"   ✓ 5 anchor images LOCKED from examples/")
    print(f"   ✓ 3 B-roll prompts generated")
    return all_entries


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: Image Generation
# Compliant with: Learning 8 (copy locked anchors), Learning 9 (gpt-image-1.5)
# ═══════════════════════════════════════════════════════════════════════════════

def step3_generate_images(prompts: list, video_dir: Path, state_path: Path, vid: int,
                          dry_run: bool = False) -> list:
    """Copy locked anchor images + generate B-roll via gpt-image-1.5."""
    images_dir = video_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = len(prompts)

    for i, p in enumerate(prompts):
        update_state(state_path, vid, 3, "running",
                     f"Processing image {i+1}/{total}: {p['title']}")

        # Flat file structure: images/scene_id.png (no nested folders)
        if p["type"] == "anchor":
            # LOCKED — copy from examples/ (Learning 8)
            src = Path(p["locked_image"])
            dst = images_dir / f"{p['id']}.png"
            if src.exists():
                shutil.copy2(str(src), str(dst))
                results.append({"id": p["id"], "type": "anchor",
                                "path": str(dst), "status": "OK"})
                print(f"   ✓ [{i+1}/{total}] {p['id']} — copied locked image")
            else:
                print(f"   ✗ [{i+1}/{total}] {p['id']} — locked image not found: {src}")
                results.append({"id": p["id"], "type": "anchor",
                                "path": None, "status": "MISSING"})
        else:
            # B-roll — generate via gpt-image-1.5 (Learning 9)
            output_path = images_dir / f"{p['id']}.png"

            if dry_run:
                time.sleep(1)
                # Create a tiny placeholder PNG
                output_path.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
                results.append({"id": p["id"], "type": "broll",
                                "path": str(output_path), "status": "OK"})
                print(f"   ✓ [{i+1}/{total}] {p['id']} [DRY RUN — placeholder]")
                continue

            url = "https://api.openai.com/v1/images/generations"
            payload = {
                "model": "gpt-image-1.5",
                "prompt": p["prompt"],
                "n": 1,
                "size": "1024x1536",  # portrait 2:3 (Learning 9)
                "quality": "high",
            }

            try:
                print(f"   ... [{i+1}/{total}] Generating {p['id']}...")
                resp = requests.post(url, headers=OPENAI_HEADERS, json=payload, timeout=180)
                if resp.status_code == 200:
                    data = resp.json()["data"][0]
                    if "b64_json" in data:
                        img_bytes = base64.b64decode(data["b64_json"])
                        output_path.write_bytes(img_bytes)
                    elif "url" in data:
                        img_resp = requests.get(data["url"], timeout=60)
                        output_path.write_bytes(img_resp.content)

                    results.append({"id": p["id"], "type": "broll",
                                    "path": str(output_path), "status": "OK"})
                    print(f"   ✓ [{i+1}/{total}] {p['id']}")
                else:
                    print(f"   ✗ [{i+1}/{total}] {p['id']}: HTTP {resp.status_code}")
                    results.append({"id": p["id"], "type": "broll",
                                    "path": None, "status": "FAILED"})
            except Exception as e:
                print(f"   ✗ [{i+1}/{total}] {p['id']}: {e}")
                results.append({"id": p["id"], "type": "broll",
                                "path": None, "status": "FAILED"})

    pipeline_dir = video_dir / "pipeline"
    results_path = pipeline_dir / "image_results.json"
    results_path.write_text(json.dumps(results, indent=2))

    ok = sum(1 for r in results if r["status"] == "OK")
    update_state(state_path, vid, 3, "done",
                 f"Ready: {ok}/{total} images (5 locked + {ok-5} generated)",
                 {"results_path": str(results_path)})

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: Video Prompts
# Compliant with: Rule Set 9.1 (no "Filipino" in voice),
#                 Rule Set 9.3 (near-static camera),
#                 Rule Set 9.6 (≤8 words), Learning 17 (no finger counts),
#                 Learning 18 (direct eye contact), Learning 19 (Kling primary)
# ═══════════════════════════════════════════════════════════════════════════════

def step4_video_prompts(script: dict, image_results: list, video_dir: Path,
                        state_path: Path, vid: int) -> list:
    """Generate video prompts compliant with all quality rules."""
    update_state(state_path, vid, 4, "running", "Generating video prompts...")

    rules = script.get("rules", [])
    hook = script.get("hook_line", "")
    cta = script.get("cta_line", "")

    # Dialogue map (≤8 words each — Rule Set 9.6)
    dialogue_map = {
        "a1_hook": hook,
        "a2_rule1": rules[0].get("lead_dialogue", f"Number one... '{rules[0].get('phrase', '')}'") if rules else "",
        "a3_rule2": rules[1].get("lead_dialogue", f"Number two... '{rules[1].get('phrase', '')}'") if len(rules) > 1 else "",
        "a4_rule3": rules[2].get("lead_dialogue", f"Number three... '{rules[2].get('phrase', '')}'") if len(rules) > 2 else "",
        "a5_cta": cta,
    }

    video_prompts = []
    for img in image_results:
        if img["status"] not in ("OK",) or not img.get("path"):
            continue

        scene_id = img["id"]
        is_anchor = img.get("type") == "anchor"

        if is_anchor:
            dialogue = dialogue_map.get(scene_id, "")
            # GAP 1 FIX: Kling shot-by-shot structure per 36_Kling_3.0_UPDATE_2026.md
            # Compliant: near-static (9.3), eye contact (L18), no finger counts (L17),
            # clean voice (9.1), voice blueprint (Lesson 41)
            prompt = (
                f"Shot: Medium close-up, near-static, eye-level. "
                f"Details: "
                f"Warm Filipina grandmother speaks directly to camera with gentle hand gestures. "
                f"Soft smile lines visible, kind dark brown eyes making direct eye contact throughout. "
                f"Warm golden light from window creates gentle rim light on grey-streaked hair. "
                f"Subtle breathing motion, natural blink rate, slight head tilts between phrases. "
                f"Camera: 50mm lens equivalent, extremely subtle push-in, near-static. "
                f"Smooth, no handheld shake. Shallow depth of field, background softly blurred. "
                f"Mood: Warm, maternal, inviting, trustworthy. "
                f'The woman says: "{dialogue}" '
                f"Voice: {VOICE_BLUEPRINT}"
            )
        else:
            broll_idx = 0
            if scene_id.startswith("b") and len(scene_id) > 1 and scene_id[1].isdigit():
                broll_idx = int(scene_id[1]) - 1
            broll_desc = rules[broll_idx].get("broll_scene", "") if broll_idx < len(rules) else ""
            # GAP 3 FIX: B-roll with Shot/Details/Camera/Mood per Kling Camera Toolkit
            prompt = (
                f"Shot: Medium shot, slow gentle pan left-to-right. "
                f"Details: {broll_desc}. "
                f"Warm afternoon sunlight through window, soft paper and wood textures visible. "
                f"Natural ambient warmth, subtle dust particles in light beams. "
                f"Camera: 35mm lens equivalent, smooth slow pan, no handheld shake. "
                f"Muted warm tones, natural color grading. "
                f"Mood: Studious, cozy, hopeful. "
                f"No dialogue. No text. Ambient only. 5 seconds."
            )

        video_prompts.append({
            "id": scene_id,
            "type": "anchor" if is_anchor else "broll",
            "image_path": img["path"],
            "prompt": prompt,
            "dialogue": dialogue_map.get(scene_id, ""),
        })

    pipeline_dir = video_dir / "pipeline"
    prompts_path = pipeline_dir / "video_prompts.json"
    prompts_path.write_text(json.dumps(video_prompts, indent=2))

    n_anchor = sum(1 for v in video_prompts if v["type"] == "anchor")
    n_broll = sum(1 for v in video_prompts if v["type"] == "broll")
    update_state(state_path, vid, 4, "done",
                 f"{n_anchor} anchor prompts (Kling) + {n_broll} B-roll prompts (Kling)",
                 {"prompts_path": str(prompts_path)})

    print(f"   ✓ {n_anchor} anchor + {n_broll} B-roll video prompts")
    return video_prompts


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5: Video Generation
# Compliant with: Learning 19 (Kling PRIMARY, Veo backup for anchors),
#                 Learning 10 (Kling API patterns), Learning 11 (Veo REST API)
# ═══════════════════════════════════════════════════════════════════════════════

def step5_generate_videos(video_prompts: list, video_dir: Path, state_path: Path, vid: int,
                          dry_run: bool = False) -> list:
    """Generate videos — Kling 3.0 primary for ALL, Veo 3.1 backup for anchors.

    Uses video_engines module (Learning 22, 24). Matches proven Kling script line-by-line.
    """
    videos_dir = video_dir / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    results = []
    total = len(video_prompts)

    for i, vp in enumerate(video_prompts):
        update_state(state_path, vid, 5, "running",
                     f"Generating video {i+1}/{total}: {vp['id']} via Kling 3.0")

        # Flat file structure: videos/scene_id.mp4 (no nested folders)
        output = videos_dir / f"{vp['id']}.mp4"

        if dry_run:
            time.sleep(2)
            output.write_bytes(b'\x00' * 200)
            results.append({"id": vp["id"], "type": vp["type"],
                            "path": str(output), "status": "OK"})
            print(f"   ✓ [{i+1}/{total}] {vp['id']}: OK [DRY RUN]")
            continue

        # Kling 3.0 PRIMARY (Learning 19, 22)
        # Anchors: sound "on" (native TTS lip-sync)
        # B-roll: sound "off" (no dialogue)
        sound = "on" if vp["type"] == "anchor" else "off"
        success = generate_kling_video(
            image_path=vp["image_path"],
            prompt=vp["prompt"],
            output_path=output,
            sound=sound,
        )

        if not success and vp["type"] == "anchor":
            # Veo 3.1 BACKUP for anchors only
            update_state(state_path, vid, 5, "running",
                         f"Kling failed for {vp['id']}, trying Veo 3.1 backup...")
            success = generate_veo_video(
                image_path=vp["image_path"],
                prompt=vp["prompt"],
                output_path=output,
            )

        status = "OK" if success else "FAILED"
        results.append({"id": vp["id"], "type": vp["type"],
                        "path": str(output) if success else None, "status": status})
        print(f"   {'✓' if success else '✗'} [{i+1}/{total}] {vp['id']}: {status}")

    pipeline_dir = video_dir / "pipeline"
    results_path = pipeline_dir / "video_results.json"
    results_path.write_text(json.dumps(results, indent=2))

    ok = sum(1 for r in results if r["status"] == "OK")
    failed = total - ok
    if failed > 0:
        update_state(state_path, vid, 5, "error",
                     f"Generated {ok}/{total} videos — {failed} FAILED",
                     {"results_path": str(results_path)})
    else:
        update_state(state_path, vid, 5, "done",
                     f"Generated {ok}/{total} videos",
                     {"results_path": str(results_path)})

    return results





# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6: Assembly
# Compliant with: Learning 12 (1.2x anchor speed, last 40% B-roll, BGM 15%)
#                 Learning 25 (dynamic scene config via --config)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_scene_config(video_dir: Path, vid: int, script: dict = None) -> Path:
    """Generate scene_config.json for assembly/polish from pipeline state (Learning 25).

    Maps dynamic scene IDs (a2_rule1, b1_rule1) to file paths that assembly/polish need.
    """
    config_dir = Path(".tmp")
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / f"scene_config_{vid}.json"

    # Read video_results.json from pipeline/ subfolder
    results_path = video_dir / "pipeline" / "video_results.json"
    if results_path.exists():
        video_results = json.loads(results_path.read_text())
    else:
        video_results = []

    # Build scene list from video results (flat file paths)
    scenes = []
    clips = []
    for i, vr in enumerate(video_results):
        scene_id = vr.get("id", f"scene_{i}")
        scene_type = vr.get("type", "anchor")

        # Flat file structure: videos/scene_id.mp4
        rel_path = f"{scene_id}.mp4"

        scenes.append({
            "id": scene_id,
            "file": rel_path,
            "type": scene_type,
        })
        clips.append({
            "file": f"{i:02d}_{scene_id}.ts",
            "type": scene_type,
        })

    # Add brand card at the end
    scenes.append({"id": "brand_card", "file": None, "type": "brand"})
    clips.append({"file": f"{len(video_results):02d}_brand_card.ts", "type": "brand"})

    # Build captions from script
    captions = []
    if script:
        hook = script.get("hook_line", "")
        rules = script.get("rules", [])
        cta = script.get("cta_line", "")
        caption_data = script.get("captions", [])

        # Map anchor clip indices to captions
        anchor_indices = [i for i, s in enumerate(scenes) if s["type"] == "anchor"]
        for idx, cap in enumerate(caption_data):
            if cap.get("line1") or cap.get("line2"):
                # Find the matching clip index
                clip_idx = idx if idx < len(clips) else None
                # Only anchor clips get captions
                scene_name = cap.get("scene", "")
                if scene_name.startswith("A"):
                    # Map A1→0, A2→anchor_indices[1], etc.
                    a_num = int(scene_name[1]) - 1 if len(scene_name) > 1 else idx
                    if a_num < len(anchor_indices):
                        clip_idx = anchor_indices[a_num]
                if clip_idx is not None and (cap.get("line1") or cap.get("line2")):
                    captions.append({
                        "clip_idx": clip_idx,
                        "line1": cap.get("line1", ""),
                        "line2": cap.get("line2", ""),
                    })

    config = {
        "base_dir": str(video_dir / "videos"),
        "output": str(video_dir / "videos" / f"video_{vid:02d}_final.mp4"),
        "bgm_track": str(Path("examples/audio_lock/bgm_track.mp3")),
        "brand_card": str(Path("examples/brand_outro_lock/brand_outro_lock_upscaled.png")),
        "scenes": scenes,
        "clips_dir": str(Path(".tmp/assembly_v3")),
        "output_dir": str(video_dir / "videos"),
        "final_output": str(video_dir / "videos" / f"video_{vid:02d}_final.mp4"),
        "clips": clips,
        "captions": captions,
    }

    config_path.write_text(json.dumps(config, indent=2))
    print(f"   ✓ Scene config: {config_path}")
    return config_path


def step6_assembly(video_dir: Path, state_path: Path, vid: int,
                   dry_run: bool = False, config_path: Path = None):
    """Run assembly — uses existing assemble_video01.py with --config."""
    update_state(state_path, vid, 6, "running",
                 "Running ffmpeg assembly (1.2x anchors, trim B-roll, BGM)...")
    if dry_run:
        time.sleep(1.5)
        update_state(state_path, vid, 6, "done", "[DRY RUN] Assembly simulated")
        print(f"   ✓ [DRY RUN] Assembly simulated")
        return True

    cmd = [sys.executable, "execution/assemble_video01.py"]
    if config_path and config_path.exists():
        cmd.extend(["--config", str(config_path)])

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path.cwd()))
    if result.returncode == 0:
        update_state(state_path, vid, 6, "done", "Assembly complete")
        print(f"   ✓ Assembly done")
        return True
    else:
        update_state(state_path, vid, 6, "error",
                     f"Assembly failed: {result.stderr[:200]}")
        print(f"   ✗ Assembly failed: {result.stderr[:200]}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7: Polish
# Compliant with: Learning 13 (xfade 0.3s, Kalam-Bold font, 60% caption pos,
#                 fade-to-black 1.0s, BGM 15%)
#                 Learning 25 (dynamic scene config via --config)
# ═══════════════════════════════════════════════════════════════════════════════

def step7_polish(video_dir: Path, state_path: Path, vid: int,
                 dry_run: bool = False, config_path: Path = None):
    """Run polish — uses existing polish_video01.py with --config."""
    update_state(state_path, vid, 7, "running",
                 "Running polish (xfade, Kalam captions, fade-to-black, BGM)...")
    if dry_run:
        time.sleep(1.5)
        update_state(state_path, vid, 7, "done", "[DRY RUN] Polish simulated")
        print(f"   ✓ [DRY RUN] Polish simulated")
        return True

    cmd = [sys.executable, "execution/polish_video01.py"]
    if config_path and config_path.exists():
        cmd.extend(["--config", str(config_path)])

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path.cwd()))
    if result.returncode == 0:
        update_state(state_path, vid, 7, "done", "Polish complete — final video ready")
        print(f"   ✓ Polish done — final video ready")
        return True
    else:
        update_state(state_path, vid, 7, "error",
                     f"Polish failed: {result.stderr[:200]}")
        print(f"   ✗ Polish failed: {result.stderr[:200]}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8: Upload to Drive
# ═══════════════════════════════════════════════════════════════════════════════

def cleanup_local_assets(video_dir: Path):
    """Delete local images + videos after confirmed Drive upload.

    Keeps: pipeline/ (lightweight JSONs) and final/ (reference).
    Deletes: images/, videos/, and .tmp/ intermediates.
    """
    cleaned = []
    for subdir in ["images", "videos"]:
        target = video_dir / subdir
        if target.exists():
            shutil.rmtree(str(target))
            cleaned.append(subdir)

    # Clean .tmp/ intermediates (assembly .ts files + polish stages)
    for tmp_subdir in [Path(".tmp/assembly_v3"), Path(".tmp/polish")]:
        if tmp_subdir.exists():
            shutil.rmtree(str(tmp_subdir))
            cleaned.append(str(tmp_subdir))

    if cleaned:
        print(f"   🧹 Cleaned: {', '.join(cleaned)}")
    return cleaned


def step8_upload(video_dir: Path, topic: str, state_path: Path, vid: int, dry_run: bool = False):
    """Upload pipeline assets to Google Drive, then cleanup local files.

    Uses drive_uploader module (Learning 24). Creates YYYY-MM-DD/XX_topic/ folders.
    After confirmed upload, deletes local images/videos (keeps pipeline/ JSONs).
    """
    update_state(state_path, vid, 8, "running",
                 "Uploading to Google Drive (date/topic folders)...")
    if dry_run:
        time.sleep(1)
        update_state(state_path, vid, 8, "done", "[DRY RUN] Upload simulated")
        print(f"   ✓ [DRY RUN] Upload simulated")
        return True

    try:
        result = upload_pipeline_assets(video_dir, topic, vid)
        if result.get("status") == "done":
            uploaded = result.get("uploaded", {})
            detail = (f"Uploaded to {result.get('date_folder')}/{result.get('topic_folder')}: "
                      f"{uploaded.get('images', 0)} images, {uploaded.get('videos', 0)} clips, "
                      f"{uploaded.get('final', 0)} final")
            update_state(state_path, vid, 8, "done", detail)
            print(f"   ✓ {detail}")

            # Auto-cleanup local assets after confirmed upload
            cleaned = cleanup_local_assets(video_dir)
            if cleaned:
                print(f"   ✓ Local cleanup complete (pipeline/ JSONs preserved)")

            return True
        else:
            reason = result.get('reason', 'unknown')
            update_state(state_path, vid, 8, "error", f"Upload failed: {reason}")
            print(f"   ✗ Upload failed: {reason} — local files preserved")
            return False
    except Exception as e:
        update_state(state_path, vid, 8, "error", f"Upload error: {str(e)[:200]}")
        print(f"   ✗ Upload error: {e} — local files preserved")
        return False

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Master Pipeline Orchestrator")
    parser.add_argument("--topic", type=str, required=True, help="Topic for the video")
    parser.add_argument("--video-id", type=int, default=1, help="Video number (1-7)")
    parser.add_argument("--step", type=int, default=1, help="Resume from step (1-8)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate all steps with mock data — no API calls")
    args = parser.parse_args()
    dry_run = args.dry_run

    video_dir = Path(f"assets/video_{args.video_id:02d}")
    state_path = Path(f".tmp/pipeline_state_{args.video_id}.json")

    print("=" * 70)
    print("MASTER PIPELINE ORCHESTRATOR")
    print(f"   Topic: {args.topic}")
    print(f"   Video: {args.video_id}")
    print(f"   Starting from: Step {args.step}")
    print(f"   DRY RUN: {'YES — no API calls' if dry_run else 'NO — live mode'}")
    print(f"   Primary engine: Kling 3.0 (Veo 3.1 backup)")
    print(f"   Anchor images: LOCKED from examples/")
    print(f"   Voice: Pure English (no accent prompts)")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Pipeline state for resume
    script = None
    image_prompts = None
    image_results = None
    video_prompts = None

    # Load existing intermediate results if resuming
    if args.step > 1:
        p = video_dir / "script.json"
        if p.exists():
            script = json.loads(p.read_text())
    if args.step > 2:
        p = video_dir / "image_prompts.json"
        if p.exists():
            image_prompts = json.loads(p.read_text())
    if args.step > 3:
        p = video_dir / "image_results.json"
        if p.exists():
            image_results = json.loads(p.read_text())
    if args.step > 4:
        p = video_dir / "video_prompts.json"
        if p.exists():
            video_prompts = json.loads(p.read_text())

    # ─── Step Gating (Learning 23): halt on critical failure ───────────────
    def run_gated_step(step_num, step_fn, *fn_args, **fn_kwargs):
        """Run a step with error handling and gating."""
        step_names = {
            1: "Concept & Script", 2: "Image Prompts", 3: "Image Generation",
            4: "Video Prompts", 5: "Video Generation", 6: "Assembly",
            7: "Polish", 8: "Upload to Drive",
        }
        name = step_names.get(step_num, f"Step {step_num}")
        print(f"\n─── Step {step_num}: {name} {'─' * (50 - len(name))}")
        try:
            result = step_fn(*fn_args, **fn_kwargs)
            # Check step 5 specifically for partial failures
            if step_num == 5 and isinstance(result, list):
                failed = sum(1 for r in result if r.get("status") != "OK")
                if failed > 0:
                    log_error(step_num, args.video_id,
                              f"{failed} videos failed to generate",
                              f"Only {len(result) - failed}/{len(result)} succeeded")
                    return None  # Halt — can't assemble with missing videos
            return result
        except Exception as e:
            error_msg = str(e)[:300]
            update_state(state_path, args.video_id, step_num, "error", error_msg)
            log_error(step_num, args.video_id, f"{name} failed", error_msg)
            print(f"   ✗ {name} FAILED: {error_msg}")
            return None

    # ─── Run steps with gating ─────────────────────────────────────────────
    pipeline_failed_at = None

    if args.step <= 1 and not pipeline_failed_at:
        script = run_gated_step(1, step1_concept_and_script,
                                args.topic, video_dir, state_path, args.video_id, dry_run=dry_run)
        if script is None:
            pipeline_failed_at = 1

    if args.step <= 2 and not pipeline_failed_at:
        image_prompts = run_gated_step(2, step2_image_prompts,
                                       script, video_dir, state_path, args.video_id)
        if image_prompts is None:
            pipeline_failed_at = 2

    if args.step <= 3 and not pipeline_failed_at:
        image_results = run_gated_step(3, step3_generate_images,
                                       image_prompts, video_dir, state_path, args.video_id, dry_run=dry_run)
        if image_results is None:
            pipeline_failed_at = 3

    if args.step <= 4 and not pipeline_failed_at:
        video_prompts = run_gated_step(4, step4_video_prompts,
                                       script, image_results, video_dir, state_path, args.video_id)
        if video_prompts is None:
            pipeline_failed_at = 4

    if args.step <= 5 and not pipeline_failed_at:
        video_results = run_gated_step(5, step5_generate_videos,
                                       video_prompts, video_dir, state_path, args.video_id, dry_run=dry_run)
        if video_results is None:
            pipeline_failed_at = 5

    # Generate scene config for assembly/polish (Learning 25)
    scene_config_path = None
    if not pipeline_failed_at and args.step <= 6:
        if not dry_run:
            scene_config_path = generate_scene_config(video_dir, args.video_id, script)
        else:
            print(f"   ✓ [DRY RUN] Scene config generation skipped")

    if args.step <= 6 and not pipeline_failed_at:
        assembly_ok = run_gated_step(6, step6_assembly,
                                     video_dir, state_path, args.video_id,
                                     dry_run=dry_run, config_path=scene_config_path)
        if assembly_ok is None:
            pipeline_failed_at = 6

    if args.step <= 7 and not pipeline_failed_at:
        polish_ok = run_gated_step(7, step7_polish,
                                   video_dir, state_path, args.video_id,
                                   dry_run=dry_run, config_path=scene_config_path)
        if polish_ok is None:
            pipeline_failed_at = 7

    if args.step <= 8 and not pipeline_failed_at:
        run_gated_step(8, step8_upload,
                       video_dir, args.topic, state_path, args.video_id, dry_run=dry_run)

    # ─── Mark blocked steps (Learning 23) ──────────────────────────────────
    if pipeline_failed_at:
        for blocked_step in range(pipeline_failed_at + 1, 9):
            if args.step <= blocked_step:
                update_state(state_path, args.video_id, blocked_step, "blocked",
                             f"Blocked by Step {pipeline_failed_at} failure")
        log_blocked_steps(pipeline_failed_at + 1, args.video_id, pipeline_failed_at)
        print(f"\n{'=' * 70}")
        print(f"❌ PIPELINE HALTED at Step {pipeline_failed_at} — Video {args.video_id}")
        print(f"   Steps {pipeline_failed_at + 1}-8 blocked. Check Error Log in Google Sheets.")
        print(f"{'=' * 70}")
        sys.exit(1)
    else:
        print(f"\n{'=' * 70}")
        print(f"✅ PIPELINE COMPLETE — Video {args.video_id}")
        print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
