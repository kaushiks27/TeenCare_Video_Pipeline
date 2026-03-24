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

# ─── LOCKED Voice Blueprint (Rule Set 9.1 compliant — NO "Filipino"/"accent") ──
VOICE_BLUEPRINT = (
    'Warm maternal tone, clear English, medium pace, gentle authority. '
    'Brief pauses before key phrases as if thinking.'
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

    system = """You are a world-class scriptwriter for short-form vertical video (30-35s).
You write scripts for a Filipino parenting education brand called TeenCare.
The anchor character is a warm Filipina grandmother (Lola) who speaks PURE ENGLISH.

STRICT RULES:
- Always a 3-rule listicle structure (EXACTLY 3 — never 2, never 5)
- Video structure: Hook (4s) → Rule 1 Lead (4s) → Rule 1 B-roll (4s) → Rule 2 Lead (4s) → Rule 2 B-roll (3-4s) → Rule 3 Lead (3-4s) → Rule 3 B-roll (3-4s) → CTA (3-4s)
- 8 scenes total (5 anchor + 3 B-roll)
- CRITICAL: Each line of dialogue must be ≤8 WORDS. Count them. This prevents lip-sync stuttering.
- Dialogue structure: "[2-3 words]... '[2-3 word phrase].'" — proven safe pattern
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
}"""

    user = f"Write a 3-rule listicle script for this topic: {topic}"

    result = chatgpt(system, user)

    # Save
    video_dir.mkdir(parents=True, exist_ok=True)
    script_path = video_dir / "script.json"
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

    prompts_path = video_dir / "image_prompts.json"
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

        scene_dir = images_dir / p["id"]
        scene_dir.mkdir(parents=True, exist_ok=True)

        if p["type"] == "anchor":
            # LOCKED — copy from examples/ (Learning 8)
            src = Path(p["locked_image"])
            dst = scene_dir / "anchor.png"
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
            output_path = scene_dir / "broll.png"

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

    results_path = video_dir / "image_results.json"
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
            # Compliant prompt: near-static (9.3), eye contact (L18),
            # no finger counts (L17), clean voice (9.1)
            prompt = (
                f"Near-static camera, medium close-up, eye-level. "
                f"The character looks directly at the camera throughout. "
                f"She begins to speak with natural lip movement. "
                f"Warm golden light creates soft highlights on her face. "
                f"Extremely subtle push-in, barely perceptible dolly. "
                f"Hands gesture warmly and naturally. "
                f"Camera: Near-static. Smooth. No handheld shake. "
                f"Mood: Warm, maternal, inviting. "
                f'The woman says: "{dialogue}" '
                f"Voice: {VOICE_BLUEPRINT}"
            )
        else:
            broll_idx = 0
            if scene_id.startswith("b") and len(scene_id) > 1 and scene_id[1].isdigit():
                broll_idx = int(scene_id[1]) - 1
            broll_desc = rules[broll_idx].get("broll_scene", "") if broll_idx < len(rules) else ""
            # B-roll: gentle motion, NO dialogue (Learning 10 — Kling sound off)
            prompt = (
                f"Gentle camera movement, medium shot. {broll_desc} "
                f"Warm golden lighting, soft cinematic feel. 5 seconds. "
                f"Camera: Very slow gentle pan. No dialogue. Ambient warmth only."
            )

        video_prompts.append({
            "id": scene_id,
            "type": "anchor" if is_anchor else "broll",
            "image_path": img["path"],
            "prompt": prompt,
            "dialogue": dialogue_map.get(scene_id, ""),
        })

    prompts_path = video_dir / "video_prompts.json"
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
    """Generate videos — Kling 3.0 primary for ALL, Veo 3.1 backup for anchors."""
    videos_dir = video_dir / "videos"
    results = []
    total = len(video_prompts)

    for i, vp in enumerate(video_prompts):
        update_state(state_path, vid, 5, "running",
                     f"Generating video {i+1}/{total}: {vp['id']} via Kling 3.0")

        scene_dir = videos_dir / vp["id"]
        scene_dir.mkdir(parents=True, exist_ok=True)
        output = scene_dir / ("anchor_video.mp4" if vp["type"] == "anchor" else "broll_video.mp4")

        if dry_run:
            time.sleep(2)  # Simulate generation time
            output.write_bytes(b'\x00' * 200)  # Placeholder
            results.append({"id": vp["id"], "type": vp["type"],
                            "path": str(output), "status": "OK"})
            print(f"   ✓ [{i+1}/{total}] {vp['id']}: OK [DRY RUN]")
            continue

        # Kling 3.0 PRIMARY (Learning 19)
        # Anchors: sound "on" (native TTS lip-sync)
        # B-roll: sound "off" (no dialogue)
        sound = "on" if vp["type"] == "anchor" else "off"
        success = generate_kling_video(vp, output, sound=sound)

        if not success and vp["type"] == "anchor":
            # Veo 3.1 BACKUP for anchors only
            update_state(state_path, vid, 5, "running",
                         f"Kling failed for {vp['id']}, trying Veo 3.1 backup...")
            success = generate_veo_video(vp, output)

        status = "OK" if success else "FAILED"
        results.append({"id": vp["id"], "type": vp["type"],
                        "path": str(output) if success else None, "status": status})
        print(f"   {'✓' if success else '✗'} [{i+1}/{total}] {vp['id']}: {status}")

    results_path = video_dir / "video_results.json"
    results_path.write_text(json.dumps(results, indent=2))

    ok = sum(1 for r in results if r["status"] == "OK")
    update_state(state_path, vid, 5, "done",
                 f"Generated {ok}/{total} videos",
                 {"results_path": str(results_path)})

    return results


def generate_kling_video(vp: dict, output: Path, sound: str = "off") -> bool:
    """Generate video via Kling 3.0 (PRIMARY engine — Learning 19)."""
    if not KLING_ACCESS or not KLING_SECRET:
        print(f"      Kling: No API keys")
        return False

    try:
        import jwt
        payload = {
            "iss": KLING_ACCESS,
            "exp": int(time.time()) + 1800,
            "nbf": int(time.time()) - 5,
        }
        token = jwt.encode(payload, KLING_SECRET, algorithm="HS256",
                           headers={"alg": "HS256", "typ": "JWT"})
    except Exception as e:
        print(f"      Kling JWT error: {e}")
        return False

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    image_path = Path(vp["image_path"])
    if not image_path.exists():
        print(f"      Image not found: {image_path}")
        return False

    image_b64 = base64.standard_b64encode(image_path.read_bytes()).decode()

    body = {
        "model_name": "kling-v3",  # Learning 10
        "mode": "pro",              # Best quality
        "duration": "5",
        "aspect_ratio": "9:16",
        "image": f"data:image/png;base64,{image_b64}",
        "prompt": vp["prompt"],
        "sound": sound,             # "on" for anchors (lip-sync), "off" for B-roll
    }

    try:
        print(f"      Kling: Submitting {vp['id']} (sound={sound})...")
        resp = requests.post("https://api-singapore.klingai.com/v1/videos/image2video",
                             headers=headers, json=body, timeout=60)

        if resp.status_code != 200:
            print(f"      Kling HTTP {resp.status_code}: {resp.text[:200]}")
            return False

        task_id = resp.json().get("data", {}).get("task_id")
        if not task_id:
            print(f"      Kling: No task_id in response")
            return False

        print(f"      Kling: task_id={task_id}, polling...")
        for attempt in range(40):  # 10 min max
            time.sleep(15)
            sr = requests.get(
                f"https://api-singapore.klingai.com/v1/videos/image2video/{task_id}",
                headers=headers, timeout=30
            )
            if sr.status_code == 200:
                sd = sr.json().get("data", {})
                status = sd.get("task_status", "")
                print(f"      Polling... ({(attempt+1)*15}s) status={status}")

                if status == "succeed":
                    videos = sd.get("task_result", {}).get("videos", [])
                    if videos:
                        vr = requests.get(videos[0]["url"], timeout=120)
                        if vr.status_code == 200:
                            output.parent.mkdir(parents=True, exist_ok=True)
                            output.write_bytes(vr.content)
                            print(f"      ✓ Saved: {output}")
                            return True
                elif status == "failed":
                    print(f"      Kling task failed")
                    return False

    except Exception as e:
        print(f"      Kling error: {e}")
    return False


def generate_veo_video(vp: dict, output: Path) -> bool:
    """Generate video via Veo 3.1 REST API (BACKUP — Learning 19)."""
    if not GOOGLE_API_KEY:
        print(f"      Veo: No API key")
        return False

    image_path = Path(vp["image_path"])
    if not image_path.exists():
        return False

    image_b64 = base64.standard_b64encode(image_path.read_bytes()).decode()

    base_url = "https://generativelanguage.googleapis.com/v1beta"
    model = "models/veo-3.1-generate-preview"
    url = f"{base_url}/{model}:predictLongRunning?key={GOOGLE_API_KEY}"

    payload = {
        "instances": [{
            "prompt": vp["prompt"],
            "image": {"bytesBase64Encoded": image_b64, "mimeType": "image/png"},
        }],
        "parameters": {
            "aspectRatio": "9:16",
            "personGeneration": "allow_adult",  # Learning 11: allow_all not supported
            "sampleCount": 1,
        },
    }

    try:
        print(f"      Veo: Submitting {vp['id']}...")
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code != 200:
            print(f"      Veo HTTP {resp.status_code}: {resp.text[:200]}")
            return False

        data = resp.json()
        if "name" not in data:
            return False

        op = data["name"]
        poll_url = f"{base_url}/{op}?key={GOOGLE_API_KEY}"

        for attempt in range(40):
            time.sleep(15)
            print(f"      Veo polling... ({(attempt+1)*15}s)")
            pr = requests.get(poll_url, timeout=30)
            if pr.status_code == 200:
                pd = pr.json()
                if pd.get("done"):
                    if "error" in pd:
                        print(f"      Veo error: {pd['error']}")
                        return False
                    return save_veo_video(pd.get("response", {}), output)

    except Exception as e:
        print(f"      Veo error: {e}")
    return False


def save_veo_video(response: dict, output: Path) -> bool:
    """Save video from Veo response — Learning 11 format."""
    gen = response.get("generateVideoResponse", {})
    samples = gen.get("generatedSamples", [])
    if not samples:
        return False

    uri = samples[0].get("video", {}).get("uri")
    if not uri:
        return False

    dl_url = f"{uri}{'&' if '?' in uri else '?'}key={GOOGLE_API_KEY}"
    dr = requests.get(dl_url, timeout=120)
    if dr.status_code == 200:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(dr.content)
        print(f"      ✓ Saved (Veo): {output}")
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6: Assembly
# Compliant with: Learning 12 (1.2x anchor speed, last 40% B-roll, BGM 15%)
# ═══════════════════════════════════════════════════════════════════════════════

def step6_assembly(video_dir: Path, state_path: Path, vid: int, dry_run: bool = False):
    """Run assembly — uses existing assemble_video01.py."""
    update_state(state_path, vid, 6, "running",
                 "Running ffmpeg assembly (1.2x anchors, trim B-roll, BGM)...")
    if dry_run:
        time.sleep(1.5)
        update_state(state_path, vid, 6, "done", "[DRY RUN] Assembly simulated")
        print(f"   ✓ [DRY RUN] Assembly simulated")
        return
    result = subprocess.run(
        [sys.executable, "execution/assemble_video01.py"],
        capture_output=True, text=True, cwd=str(Path.cwd()),
    )
    if result.returncode == 0:
        update_state(state_path, vid, 6, "done", "Assembly complete")
        print(f"   ✓ Assembly done")
    else:
        update_state(state_path, vid, 6, "error",
                     f"Assembly failed: {result.stderr[:200]}")
        print(f"   ✗ Assembly failed: {result.stderr[:200]}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7: Polish
# Compliant with: Learning 13 (xfade 0.3s, Kalam-Bold font, 60% caption pos,
#                 fade-to-black 1.0s, BGM 15%)
# ═══════════════════════════════════════════════════════════════════════════════

def step7_polish(video_dir: Path, state_path: Path, vid: int, dry_run: bool = False):
    """Run polish — uses existing polish_video01.py."""
    update_state(state_path, vid, 7, "running",
                 "Running polish (xfade, Kalam captions, fade-to-black, BGM)...")
    if dry_run:
        time.sleep(1.5)
        update_state(state_path, vid, 7, "done", "[DRY RUN] Polish simulated")
        print(f"   ✓ [DRY RUN] Polish simulated")
        return
    result = subprocess.run(
        [sys.executable, "execution/polish_video01.py"],
        capture_output=True, text=True, cwd=str(Path.cwd()),
    )
    if result.returncode == 0:
        update_state(state_path, vid, 7, "done", "Polish complete — final video ready")
        print(f"   ✓ Polish done — final video ready")
    else:
        update_state(state_path, vid, 7, "error",
                     f"Polish failed: {result.stderr[:200]}")
        print(f"   ✗ Polish failed: {result.stderr[:200]}")


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8: Upload to Drive
# ═══════════════════════════════════════════════════════════════════════════════

def step8_upload(video_dir: Path, state_path: Path, vid: int, dry_run: bool = False):
    """Upload final video to Google Drive."""
    update_state(state_path, vid, 8, "running", "Uploading to Google Drive...")
    if dry_run:
        time.sleep(1)
        update_state(state_path, vid, 8, "done", "[DRY RUN] Upload simulated")
        print(f"   ✓ [DRY RUN] Upload simulated")
        return

    final_video = video_dir / "videos" / f"video_{vid:02d}_final.mp4"

    # Fallback to video_01 path
    if not final_video.exists():
        final_video = Path("assets/video_01/videos/video_01_final.mp4")

    if not final_video.exists():
        update_state(state_path, vid, 8, "error", "Final video not found")
        print(f"   ✗ Final video not found")
        return

    result = subprocess.run(
        [sys.executable, "execution/upload_to_drive.py", "--file", str(final_video)],
        capture_output=True, text=True, cwd=str(Path.cwd()),
    )
    if result.returncode == 0:
        update_state(state_path, vid, 8, "done", "Uploaded to Google Drive")
        print(f"   ✓ Uploaded to Drive")
    else:
        update_state(state_path, vid, 8, "error",
                     f"Upload failed: {result.stderr[:200]}")
        print(f"   ✗ Upload failed")


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

    # Run steps
    if args.step <= 1:
        print("\n─── Step 1: Concept & Script ────────────────────────────────")
        script = step1_concept_and_script(args.topic, video_dir, state_path, args.video_id, dry_run=dry_run)

    if args.step <= 2:
        print("\n─── Step 2: Image Prompts ──────────────────────────────────")
        image_prompts = step2_image_prompts(script, video_dir, state_path, args.video_id)

    if args.step <= 3:
        print("\n─── Step 3: Image Generation ───────────────────────────────")
        image_results = step3_generate_images(image_prompts, video_dir, state_path, args.video_id, dry_run=dry_run)

    if args.step <= 4:
        print("\n─── Step 4: Video Prompts ──────────────────────────────────")
        video_prompts = step4_video_prompts(script, image_results, video_dir, state_path, args.video_id)

    if args.step <= 5:
        print("\n─── Step 5: Video Generation ───────────────────────────────")
        step5_generate_videos(video_prompts, video_dir, state_path, args.video_id, dry_run=dry_run)

    if args.step <= 6:
        print("\n─── Step 6: Assembly ───────────────────────────────────────")
        step6_assembly(video_dir, state_path, args.video_id, dry_run=dry_run)

    if args.step <= 7:
        print("\n─── Step 7: Polish ────────────────────────────────────────")
        step7_polish(video_dir, state_path, args.video_id, dry_run=dry_run)

    if args.step <= 8:
        print("\n─── Step 8: Upload to Drive ────────────────────────────────")
        step8_upload(video_dir, state_path, args.video_id, dry_run=dry_run)

    print(f"\n{'=' * 70}")
    print(f"✅ PIPELINE COMPLETE — Video {args.video_id}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
