#!/usr/bin/env python3
"""
Drive Uploader — Upload pipeline assets to Google Drive with date/topic folders

Folder structure:
    GOOGLE_DRIVE_FOLDER_ID/
    └── 2026-03-24/
        └── 01_signs_your_teen_is_struggling/
            ├── images/     (anchor + B-roll PNGs)
            ├── videos/     (individual clips)
            └── final/      (video_XX_final.mp4)

Reuses auth pattern from upload_to_drive.py.

Usage:
    from drive_uploader import upload_pipeline_assets
    upload_pipeline_assets(video_dir, topic, video_id)
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1QjGFlsJQKISipQqaQjsBNkc6Z1bph3HU")


def _get_drive_service():
    """Initialize Google Drive API service. Returns None on failure."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        print("   ⚠ Google API client not installed. Run: pip install google-api-python-client google-auth")
        return None

    cred_paths = [
        Path(__file__).resolve().parent.parent / "credentials.json",
        Path(__file__).resolve().parent.parent / "service_account.json",
        Path(os.path.expanduser("~/.config/gspread/service_account.json")),
    ]

    for cred_path in cred_paths:
        if cred_path.exists():
            try:
                creds = service_account.Credentials.from_service_account_file(
                    str(cred_path),
                    scopes=["https://www.googleapis.com/auth/drive.file"]
                )
                service = build("drive", "v3", credentials=creds)
                print(f"   ✓ Drive authenticated via {cred_path.name}")
                return service
            except Exception as e:
                print(f"   ⚠ Drive auth failed with {cred_path.name}: {e}")

    print("   ⚠ No valid Drive credentials — upload skipped")
    return None


def _find_or_create_folder(service, name: str, parent_id: str) -> str:
    """Find existing subfolder by name, or create it. Returns folder ID."""
    query = (
        f"name='{name}' and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
    files = results.get("files", [])

    if files:
        print(f"   📂 Found existing folder: {name}")
        return files[0]["id"]

    # Create folder
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    print(f"   📂 Created folder: {name}")
    return folder["id"]


def _upload_file(service, file_path: Path, folder_id: str) -> str | None:
    """Upload a single file to a Drive folder. Returns file ID or None."""
    from googleapiclient.http import MediaFileUpload

    suffix = file_path.suffix.lower()
    mime_map = {
        ".mp4": "video/mp4", ".mov": "video/quicktime",
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".json": "application/json", ".txt": "text/plain",
    }
    mime_type = mime_map.get(suffix, "application/octet-stream")

    metadata = {"name": file_path.name, "parents": [folder_id]}
    media = MediaFileUpload(str(file_path), mimetype=mime_type, resumable=True)

    size_kb = file_path.stat().st_size // 1024
    try:
        result = service.files().create(body=metadata, media_body=media, fields="id").execute()
        print(f"      ✓ {file_path.name} ({size_kb}KB)")
        return result.get("id")
    except Exception as e:
        print(f"      ✗ {file_path.name}: {e}")
        return None


def _sanitize_folder_name(topic: str) -> str:
    """Convert topic to safe folder name: '01_signs_your_teen_is_struggling'"""
    clean = topic.lower().strip()
    clean = re.sub(r'[^a-z0-9\s]', '', clean)
    clean = re.sub(r'\s+', '_', clean)
    return clean[:60]  # Limit length


def upload_pipeline_assets(video_dir: Path, topic: str, video_id: int,
                           root_folder_id: str = "") -> dict:
    """Upload all pipeline assets to Google Drive with date/topic folder structure.

    Creates: YYYY-MM-DD / XX_topic_name / {images, videos, final}

    Args:
        video_dir: Local assets directory (e.g., assets/video_01/)
        topic: Video topic name
        video_id: Video number (1-based)
        root_folder_id: Override Drive folder ID (defaults to env var)

    Returns:
        Dict with folder IDs and upload status
    """
    folder_id = root_folder_id or FOLDER_ID
    service = _get_drive_service()
    if not service:
        return {"status": "skipped", "reason": "no_credentials"}

    date_str = datetime.now().strftime("%Y-%m-%d")
    topic_folder_name = f"{video_id:02d}_{_sanitize_folder_name(topic)}"

    print(f"\n   📤 Uploading to Drive: {date_str}/{topic_folder_name}/")

    # Create folder hierarchy: date → topic → subfolders
    date_folder = _find_or_create_folder(service, date_str, folder_id)
    topic_folder = _find_or_create_folder(service, topic_folder_name, date_folder)
    images_folder = _find_or_create_folder(service, "images", topic_folder)
    videos_folder = _find_or_create_folder(service, "videos", topic_folder)
    final_folder = _find_or_create_folder(service, "final", topic_folder)

    uploaded = {"images": 0, "videos": 0, "final": 0}

    # Upload images
    images_dir = video_dir / "images"
    if images_dir.exists():
        print(f"\n   📷 Uploading images...")
        for img_dir in sorted(images_dir.iterdir()):
            if img_dir.is_dir():
                for img_file in img_dir.glob("*.png"):
                    if _upload_file(service, img_file, images_folder):
                        uploaded["images"] += 1
                for img_file in img_dir.glob("*.jpg"):
                    if _upload_file(service, img_file, images_folder):
                        uploaded["images"] += 1

    # Upload individual video clips
    videos_dir = video_dir / "videos"
    if videos_dir.exists():
        print(f"\n   🎬 Uploading video clips...")
        for vid_dir in sorted(videos_dir.iterdir()):
            if vid_dir.is_dir():
                for vid_file in vid_dir.glob("*.mp4"):
                    if _upload_file(service, vid_file, videos_folder):
                        uploaded["videos"] += 1

    # Upload final polished video
    print(f"\n   🎯 Uploading final video...")
    final_patterns = [
        video_dir / "videos" / f"video_{video_id:02d}_final.mp4",
        video_dir / "videos" / "video_01_final.mp4",
    ]
    for final_path in final_patterns:
        if final_path.exists():
            if _upload_file(service, final_path, final_folder):
                uploaded["final"] += 1
            break

    # Upload script.json for reference
    script_path = video_dir / "script.json"
    if script_path.exists():
        _upload_file(service, script_path, topic_folder)

    print(f"\n   ✅ Upload summary: {uploaded['images']} images, "
          f"{uploaded['videos']} clips, {uploaded['final']} final")

    return {
        "status": "done",
        "date_folder": date_str,
        "topic_folder": topic_folder_name,
        "uploaded": uploaded,
        "folder_ids": {
            "date": date_folder,
            "topic": topic_folder,
            "images": images_folder,
            "videos": videos_folder,
            "final": final_folder,
        },
    }
