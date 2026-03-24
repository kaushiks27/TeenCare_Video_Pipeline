#!/usr/bin/env python3
"""
Video Engines — Kling 3.0 + Veo 3.1 video generation

Extracted from proven working scripts:
  - generate_video02_anchor_videos_kling.py (Kling 3.0)
  - generate_video01_anchor_videos.py (Veo 3.1)

Compliant with: Learning 19 (Kling primary), Learning 22 (raw base64, JWT refresh,
negative_prompt, code check), Learning 10 (Kling API patterns), Learning 11 (Veo REST API)

Usage:
    from video_engines import generate_kling_video, generate_veo_video
"""
from __future__ import annotations

import os
import sys
import time
import base64
import json
import requests
from pathlib import Path

# ─── Load .env ────────────────────────────────────────────────────────────────
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

KLING_ACCESS = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET = os.getenv("KLING_SECRET_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_AI_STUDIO_API_KEY", "")

# ─── Kling API Config (from generate_video02_anchor_videos_kling.py) ──────────
KLING_BASE_URL = "https://api-singapore.klingai.com"
KLING_MODEL = "kling-v3"
KLING_MODE = "pro"
KLING_DURATION = "5"
KLING_NEGATIVE_PROMPT = (
    "blurry, distorted, text, watermark, ugly, deformed, "
    "zoom in, zoom out, Tagalog, non-English"
)


def _get_kling_jwt():
    """Generate fresh JWT token for Kling API.

    Matches: generate_video02_anchor_videos_kling.py:get_jwt_token() (lines 131-139)
    Must be called fresh on EVERY request — tokens expire after 30 min.
    """
    import jwt
    headers = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": KLING_ACCESS,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 5,
    }
    return jwt.encode(payload, KLING_SECRET, algorithm="HS256", headers=headers)


def generate_kling_video(image_path: str | Path, prompt: str,
                         output_path: str | Path, sound: str = "off",
                         max_wait: int = 600) -> bool:
    """Generate video via Kling 3.0 image-to-video with optional lip sync.

    Matches: generate_video02_anchor_videos_kling.py (lines 142-230)
    Learning 22: raw base64 (no data URI), JWT refresh per poll, negative_prompt, code==0 check.

    Args:
        image_path: Path to input image (PNG/JPG)
        prompt: Video generation prompt
        output_path: Where to save the MP4
        sound: "on" for anchor lip-sync, "off" for B-roll
        max_wait: Maximum seconds to poll (default 600 = 10 min)

    Returns:
        True if video saved successfully, False otherwise
    """
    if not KLING_ACCESS or not KLING_SECRET:
        print(f"      Kling: No API keys (KLING_ACCESS_KEY / KLING_SECRET_KEY)")
        return False

    try:
        import jwt  # noqa: F811
    except ImportError:
        print("      Kling: PyJWT not installed. Run: pip3 install PyJWT")
        return False

    image_path = Path(image_path)
    output_path = Path(output_path)

    if not image_path.exists():
        print(f"      Kling: Image not found: {image_path}")
        return False

    # Learning 22: Raw base64, NO data URI prefix
    image_b64 = base64.b64encode(image_path.read_bytes()).decode()

    # Payload matches generate_video02_anchor_videos_kling.py:create_video_task (lines 154-161)
    payload = {
        "model_name": KLING_MODEL,
        "image": image_b64,
        "prompt": prompt,
        "negative_prompt": KLING_NEGATIVE_PROMPT,
        "duration": KLING_DURATION,
        "mode": KLING_MODE,
        "sound": sound,
    }

    try:
        # Fresh token for submission
        token = _get_kling_jwt()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        print(f"      Kling: Submitting (sound={sound})...")
        resp = requests.post(
            f"{KLING_BASE_URL}/v1/videos/image2video",
            headers=headers, json=payload, timeout=60
        )

        if resp.status_code != 200:
            print(f"      Kling HTTP {resp.status_code}: {resp.text[:400]}")
            return False

        # Learning 22: Check API response code, not just HTTP status
        data = resp.json()
        if data.get("code") != 0:
            print(f"      Kling API error: code={data.get('code')} — {data.get('message', 'unknown')}")
            return False

        task_id = data["data"]["task_id"]
        print(f"      Kling: task_id={task_id}, polling...")

        # Poll — matches generate_video02_anchor_videos_kling.py:poll_task (lines 184-217)
        start_time = time.time()
        while time.time() - start_time < max_wait:
            time.sleep(15)

            # Learning 22: Fresh JWT on each poll
            token = _get_kling_jwt()
            poll_headers = {"Authorization": f"Bearer {token}"}

            sr = requests.get(
                f"{KLING_BASE_URL}/v1/videos/image2video/{task_id}",
                headers=poll_headers, timeout=30
            )
            if sr.status_code == 200:
                sd = sr.json()
                if sd.get("code") == 0:
                    status = sd["data"]["task_status"]
                    elapsed = int(time.time() - start_time)
                    print(f"      Kling: status={status} ({elapsed}s)")

                    if status == "succeed":
                        videos = sd["data"]["task_result"]["videos"]
                        if videos:
                            return _download_video(videos[0]["url"], output_path)
                    elif status == "failed":
                        msg = sd["data"].get("task_status_msg", "unknown")
                        print(f"      Kling FAILED: {msg}")
                        return False
                else:
                    print(f"      Kling poll error: {sd.get('message', 'unknown')}")

        print(f"      Kling: TIMEOUT after {max_wait}s")
        return False

    except Exception as e:
        print(f"      Kling error: {e}")
        return False


def generate_veo_video(image_path: str | Path, prompt: str,
                       output_path: str | Path, max_wait: int = 600) -> bool:
    """Generate video via Veo 3.1 REST API (backup engine).

    Matches: generate_video01_anchor_videos.py (Veo 3.1 long-running operation pattern)
    Learning 11: Veo REST API format, personGeneration = allow_adult

    Args:
        image_path: Path to input image
        prompt: Video generation prompt
        output_path: Where to save the MP4
        max_wait: Maximum seconds to poll

    Returns:
        True if video saved successfully, False otherwise
    """
    if not GOOGLE_API_KEY:
        print(f"      Veo: No API key (GOOGLE_AI_STUDIO_API_KEY)")
        return False

    image_path = Path(image_path)
    output_path = Path(output_path)

    if not image_path.exists():
        print(f"      Veo: Image not found: {image_path}")
        return False

    image_b64 = base64.standard_b64encode(image_path.read_bytes()).decode()

    base_url = "https://generativelanguage.googleapis.com/v1beta"
    model = "models/veo-3.1-generate-preview"
    url = f"{base_url}/{model}:predictLongRunning?key={GOOGLE_API_KEY}"

    payload = {
        "instances": [{
            "prompt": prompt,
            "image": {"bytesBase64Encoded": image_b64, "mimeType": "image/png"},
        }],
        "parameters": {
            "aspectRatio": "9:16",
            "personGeneration": "allow_adult",
            "sampleCount": 1,
        },
    }

    try:
        print(f"      Veo: Submitting...")
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code != 200:
            print(f"      Veo HTTP {resp.status_code}: {resp.text[:200]}")
            return False

        data = resp.json()
        if "name" not in data:
            print(f"      Veo: No operation name in response")
            return False

        op = data["name"]
        poll_url = f"{base_url}/{op}?key={GOOGLE_API_KEY}"

        start_time = time.time()
        while time.time() - start_time < max_wait:
            time.sleep(15)
            elapsed = int(time.time() - start_time)
            print(f"      Veo: polling... ({elapsed}s)")

            pr = requests.get(poll_url, timeout=30)
            if pr.status_code == 200:
                pd = pr.json()
                if pd.get("done"):
                    if "error" in pd:
                        print(f"      Veo error: {pd['error']}")
                        return False
                    return _save_veo_video(pd.get("response", {}), output_path)

        print(f"      Veo: TIMEOUT after {max_wait}s")
        return False

    except Exception as e:
        print(f"      Veo error: {e}")
        return False


def _download_video(url: str, output_path: Path) -> bool:
    """Download video from URL. Matches generate_video02_anchor_videos_kling.py:download_video."""
    try:
        resp = requests.get(url, timeout=120)
        if resp.status_code == 200:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(resp.content)
            size_kb = len(resp.content) // 1024
            print(f"      ✓ Saved: {output_path} ({size_kb}KB)")
            return True
        print(f"      Download failed: HTTP {resp.status_code}")
    except Exception as e:
        print(f"      Download error: {e}")
    return False


def _save_veo_video(response: dict, output_path: Path) -> bool:
    """Save video from Veo response. Matches generate_video01_anchor_videos.py pattern."""
    gen = response.get("generateVideoResponse", {})
    samples = gen.get("generatedSamples", [])
    if not samples:
        print(f"      Veo: No samples in response")
        return False

    uri = samples[0].get("video", {}).get("uri")
    if not uri:
        print(f"      Veo: No video URI in response")
        return False

    dl_url = f"{uri}{'&' if '?' in uri else '?'}key={GOOGLE_API_KEY}"
    return _download_video(dl_url, output_path)
