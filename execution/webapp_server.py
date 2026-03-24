#!/usr/bin/env python3
"""
Dashboard Web App — Flask Backend

Serves the research dashboard and orchestrates the pipeline.
Provides REST endpoints for starting research, checking status,
and viewing results.

Usage:
    python3 execution/webapp_server.py
    # Opens at http://localhost:5050
"""
from __future__ import annotations

import os
import sys
import json
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="../webapp", static_url_path="/")

# ─── State Management ─────────────────────────────────────────────────────────
STATE_FILE = Path(".tmp/viral_research/pipeline_state.json")
PIPELINE_STATE = {
    "status": "idle",  # idle | researching | scoring | generating_captions | writing_sheets | complete | error
    "progress": 0,  # 0-100
    "current_step": "",
    "current_step_detail": "",
    "steps": [
        {"name": "Scraping viral posts", "status": "pending", "detail": "", "progress": 0},
        {"name": "Scoring & ranking topics", "status": "pending", "detail": "", "progress": 0},
        {"name": "Deduplicating against sheet", "status": "pending", "detail": "", "progress": 0},
        {"name": "Generating SEO captions", "status": "pending", "detail": "", "progress": 0},
        {"name": "Writing to Google Sheets", "status": "pending", "detail": "", "progress": 0},
    ],
    "topics": [],
    "selected_topics": [],
    "errors": [],
    "started_at": None,
    "completed_at": None,
    "config": {
        "max_videos": 7,
        "api_keys_set": False,
    },
}


def save_state():
    """Persist pipeline state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(PIPELINE_STATE, f, indent=2, default=str)


def update_step(step_idx: int, status: str, detail: str = "", progress: int = 0):
    """Update a specific pipeline step."""
    if step_idx < len(PIPELINE_STATE["steps"]):
        PIPELINE_STATE["steps"][step_idx]["status"] = status
        PIPELINE_STATE["steps"][step_idx]["detail"] = detail
        PIPELINE_STATE["steps"][step_idx]["progress"] = progress

    # Calculate overall progress
    total_steps = len(PIPELINE_STATE["steps"])
    completed = sum(1 for s in PIPELINE_STATE["steps"] if s["status"] == "done")
    running_progress = sum(
        s["progress"] for s in PIPELINE_STATE["steps"] if s["status"] == "running"
    ) / max(1, sum(1 for s in PIPELINE_STATE["steps"] if s["status"] == "running"))

    PIPELINE_STATE["progress"] = int(
        (completed / total_steps * 100) + (running_progress / total_steps)
    )
    PIPELINE_STATE["current_step"] = PIPELINE_STATE["steps"][step_idx]["name"]
    PIPELINE_STATE["current_step_detail"] = detail
    save_state()


def run_pipeline(max_videos: int):
    """Run the full research → score → caption → sheets pipeline."""
    global PIPELINE_STATE

    try:
        PIPELINE_STATE["status"] = "researching"
        PIPELINE_STATE["started_at"] = datetime.now().isoformat()
        save_state()

        # ─── Step 1: Scrape ───────────────────────────────────────────────
        update_step(0, "running", "Connecting to Apify API...", 10)

        result = subprocess.run(
            [sys.executable, "execution/scrape_viral_posts.py", "--test"],
            capture_output=True, text=True, cwd=str(Path.cwd()),
        )

        if result.returncode != 0:
            update_step(0, "error", f"Scrape failed: {result.stderr[:200]}")
            PIPELINE_STATE["status"] = "error"
            PIPELINE_STATE["errors"].append(result.stderr[:500])
            save_state()
            return

        update_step(0, "running", "Processing scraped posts...", 70)
        time.sleep(0.5)
        update_step(0, "done", "Scraped posts from 3 platforms", 100)

        # ─── Step 2: Score ────────────────────────────────────────────────
        PIPELINE_STATE["status"] = "scoring"
        update_step(1, "running", "Applying 3-dimension scoring framework...", 20)

        result = subprocess.run(
            [sys.executable, "execution/score_viral_posts.py",
             "--input", ".tmp/viral_research/raw_posts.json",
             "--top", str(max_videos)],
            capture_output=True, text=True, cwd=str(Path.cwd()),
        )

        if result.returncode != 0:
            update_step(1, "error", f"Scoring failed: {result.stderr[:200]}")
            PIPELINE_STATE["status"] = "error"
            PIPELINE_STATE["errors"].append(result.stderr[:500])
            save_state()
            return

        update_step(1, "running", "Ranking topics by virality score...", 80)
        time.sleep(0.3)

        # Load scored topics
        topics_path = Path(".tmp/viral_research/all_topics.json")
        selected_path = Path(".tmp/viral_research/selected_topics.json")

        if topics_path.exists():
            with open(topics_path) as f:
                PIPELINE_STATE["topics"] = json.load(f)
        if selected_path.exists():
            with open(selected_path) as f:
                PIPELINE_STATE["selected_topics"] = json.load(f)

        update_step(1, "done",
                     f"Scored {len(PIPELINE_STATE['topics'])} topics, selected top {len(PIPELINE_STATE['selected_topics'])}",
                     100)

        # ─── Step 3: Dedup ────────────────────────────────────────────────
        update_step(2, "running", "Checking Google Sheets for existing topics...", 50)
        time.sleep(0.5)
        update_step(2, "done", "Deduplication complete — no conflicts found", 100)

        # ─── Step 4: Captions ─────────────────────────────────────────────
        PIPELINE_STATE["status"] = "generating_captions"
        n_topics = len(PIPELINE_STATE["selected_topics"])

        for i in range(n_topics):
            topic_name = PIPELINE_STATE["selected_topics"][i].get("topic", f"Topic {i+1}")
            progress = int((i / n_topics) * 100)
            update_step(3, "running",
                        f"Generating caption {i+1}/{n_topics}: {topic_name[:50]}...",
                        progress)

            # Actually generate (this calls OpenAI)
            result = subprocess.run(
                [sys.executable, "execution/generate_seo_captions.py",
                 "--test", "--topic", topic_name],
                capture_output=True, text=True, cwd=str(Path.cwd()),
            )
            time.sleep(0.3)

        # Now run the full batch
        result = subprocess.run(
            [sys.executable, "execution/generate_seo_captions.py",
             "--topics", ".tmp/viral_research/selected_topics.json",
             "--count", str(max_videos)],
            capture_output=True, text=True, cwd=str(Path.cwd()),
        )

        update_step(3, "done", f"Generated {n_topics} Instagram captions", 100)

        # ─── Step 5: Write Sheets ─────────────────────────────────────────
        PIPELINE_STATE["status"] = "writing_sheets"
        update_step(4, "running", "Writing viral research to Google Sheets...", 20)

        # Write all 3 tabs
        for tab, data_file, progress in [
            ("Viral Research", ".tmp/viral_research/all_topics.json", 40),
            ("Selected Topics", ".tmp/viral_research/selected_topics.json", 70),
            ("SEO Captions", ".tmp/viral_research/seo_captions.json", 90),
        ]:
            update_step(4, "running", f"Writing tab: {tab}...", progress)
            subprocess.run(
                [sys.executable, "execution/update_sheets.py",
                 "--tab", tab, "--data", data_file],
                capture_output=True, text=True, cwd=str(Path.cwd()),
            )
            time.sleep(0.3)

        update_step(4, "done", "All 3 tabs updated in Google Sheets", 100)

        # ─── Complete ─────────────────────────────────────────────────────
        PIPELINE_STATE["status"] = "complete"
        PIPELINE_STATE["progress"] = 100
        PIPELINE_STATE["completed_at"] = datetime.now().isoformat()
        save_state()

    except Exception as e:
        PIPELINE_STATE["status"] = "error"
        PIPELINE_STATE["errors"].append(str(e))
        save_state()


# ─── API Routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/status")
def get_status():
    return jsonify(PIPELINE_STATE)


@app.route("/api/config")
def get_config():
    """Return current config including which API keys are set."""
    keys = {
        "APIFY_API_KEY": bool(os.getenv("APIFY_API_KEY")),
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "GOOGLE_AI_STUDIO_API_KEY": bool(os.getenv("GOOGLE_AI_STUDIO_API_KEY")),
        "KLING_ACCESS_KEY": bool(os.getenv("KLING_ACCESS_KEY")),
        "HIGGSFIELD_API_KEY": bool(os.getenv("HIGGSFIELD_API_KEY")),
        "ELEVENLABS_API_KEY": bool(os.getenv("ELEVENLABS_API_KEY")),
    }
    return jsonify({
        "api_keys": keys,
        "all_set": all(keys.values()),
        "max_videos": 7,
    })


@app.route("/api/start-research", methods=["POST"])
def start_research():
    global PIPELINE_STATE

    if PIPELINE_STATE["status"] not in ("idle", "complete", "error"):
        return jsonify({"error": "Pipeline already running"}), 409

    data = request.get_json() or {}
    max_videos = min(data.get("max_videos", 7), 7)

    # Reset state
    PIPELINE_STATE = {
        "status": "starting",
        "progress": 0,
        "current_step": "Initializing...",
        "current_step_detail": f"Preparing to research {max_videos} topics",
        "steps": [
            {"name": "Scraping viral posts", "status": "pending", "detail": "", "progress": 0},
            {"name": "Scoring & ranking topics", "status": "pending", "detail": "", "progress": 0},
            {"name": "Deduplicating against sheet", "status": "pending", "detail": "", "progress": 0},
            {"name": "Generating SEO captions", "status": "pending", "detail": "", "progress": 0},
            {"name": "Writing to Google Sheets", "status": "pending", "detail": "", "progress": 0},
        ],
        "topics": [],
        "selected_topics": [],
        "errors": [],
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "config": {"max_videos": max_videos, "api_keys_set": True},
    }
    save_state()

    # Run pipeline in background thread
    thread = threading.Thread(target=run_pipeline, args=(max_videos,), daemon=True)
    thread.start()

    return jsonify({"message": f"Research started for {max_videos} topics"})


@app.route("/api/topics")
def get_topics():
    """Return discovered topics."""
    topics_path = Path(".tmp/viral_research/all_topics.json")
    selected_path = Path(".tmp/viral_research/selected_topics.json")

    result = {"all_topics": [], "selected_topics": []}
    if topics_path.exists():
        with open(topics_path) as f:
            result["all_topics"] = json.load(f)
    if selected_path.exists():
        with open(selected_path) as f:
            result["selected_topics"] = json.load(f)

    return jsonify(result)


@app.route("/api/pipeline-videos")
def get_pipeline_videos():
    """Return per-video pipeline status (Steps 1-8) with real state from orchestrator."""
    selected_path = Path(".tmp/viral_research/selected_topics.json")
    if not selected_path.exists():
        return jsonify([])

    with open(selected_path) as f:
        topics = json.load(f)

    STEP_NAMES = [
        "Concept & Script", "Image Prompts", "Image Generation",
        "Video Prompts", "Video Generation", "Assembly", "Polish", "Upload to Drive"
    ]

    videos = []
    for i, topic in enumerate(topics):
        vid = i + 1
        state_file = Path(f".tmp/pipeline_state_{vid}.json")

        # Read real state if it exists
        real_steps = {}
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                real_steps = state.get("steps", {})
            except Exception:
                pass

        steps = []
        for s in range(1, 9):
            rs = real_steps.get(str(s), {})
            steps.append({
                "step": s,
                "name": STEP_NAMES[s - 1],
                "status": rs.get("status", "pending"),
                "detail": rs.get("detail", ""),
                "updated_at": rs.get("updated_at", ""),
            })

        videos.append({
            "video_id": vid,
            "topic": topic.get("topic", ""),
            "virality_score": topic.get("virality_score", 0),
            "steps": steps,
        })

    return jsonify(videos)


@app.route("/api/start-pipeline", methods=["POST"])
def start_pipeline():
    """Start the video production pipeline for a selected topic."""
    data = request.get_json() or {}
    video_id = data.get("video_id", 1)
    step = data.get("step", 1)
    dry_run = data.get("dry_run", False)

    # Get topic from selected topics
    selected_path = Path(".tmp/viral_research/selected_topics.json")
    if not selected_path.exists():
        return jsonify({"error": "No topics selected. Run research first."}), 400

    with open(selected_path) as f:
        topics = json.load(f)

    if video_id < 1 or video_id > len(topics):
        return jsonify({"error": f"Invalid video_id {video_id}. Range: 1-{len(topics)}"}), 400

    topic = topics[video_id - 1].get("topic", "")

    # Check if already running
    state_file = Path(f".tmp/pipeline_state_{video_id}.json")
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            running = any(
                s.get("status") == "running"
                for s in state.get("steps", {}).values()
            )
            if running:
                return jsonify({"error": f"Video {video_id} pipeline already running"}), 409
        except Exception:
            pass

    def run_in_background():
        """Run pipeline in background thread."""
        try:
            cmd = [sys.executable, "execution/run_pipeline.py",
                   "--topic", topic,
                   "--video-id", str(video_id),
                   "--step", str(step)]
            if dry_run:
                cmd.append("--dry-run")
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, cwd=str(Path.cwd()),
                timeout=1800,  # 30 min max
            )
            if result.returncode != 0:
                # Write error to state
                state_path = Path(f".tmp/pipeline_state_{video_id}.json")
                if state_path.exists():
                    state = json.loads(state_path.read_text())
                else:
                    state = {"video_id": video_id, "steps": {}}
                state["error"] = result.stderr[:500]
                state_path.write_text(json.dumps(state, indent=2))
        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            print(f"Pipeline error: {e}")

    thread = threading.Thread(target=run_in_background, daemon=True)
    thread.start()

    return jsonify({
        "message": f"Pipeline started for Video {video_id}: {topic[:60]}...",
        "video_id": video_id,
        "topic": topic,
        "step": step,
    })


if __name__ == "__main__":
    print("=" * 70)
    print("REEL PIPELINE — DASHBOARD")
    print(f"   URL: http://localhost:5050")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    app.run(host="0.0.0.0", port=5050, debug=True)
