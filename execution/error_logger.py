#!/usr/bin/env python3
"""
Error Logger — Write pipeline errors to Google Sheets + local CSV fallback

Compliant with: Learning 23 (step gating, error logging)

Creates/writes to "Error Log" tab in the project Google Sheet.
Falls back to CSV if no credentials available.

Usage:
    from error_logger import log_error
    log_error(step=5, video_id=1, error="Kling failed", detail="HTTP 401")
"""
from __future__ import annotations

import os
import csv
import json
from pathlib import Path
from datetime import datetime

# ─── Load .env ────────────────────────────────────────────────────────────────
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

SHEET_ID = "13EWGhUcOxtF_jZ-KlO9vXsMbqIR8rKVMoe9CFgC6hnM"
CSV_DIR = Path(".tmp/viral_research/csv_export")
ERROR_LOG_HEADERS = ["Timestamp", "Video ID", "Step", "Step Name", "Error", "Detail", "Status"]

STEP_NAMES = {
    1: "Concept & Script",
    2: "Image Prompts",
    3: "Image Generation",
    4: "Video Prompts",
    5: "Video Generation",
    6: "Assembly",
    7: "Polish",
    8: "Upload to Drive",
}


def _get_sheets_client():
    """Get Google Sheets client. Returns None if unavailable."""
    try:
        import gspread
    except ImportError:
        return None

    cred_paths = [
        Path(__file__).resolve().parent.parent / "credentials.json",
        Path(__file__).resolve().parent.parent / "service_account.json",
        Path(os.path.expanduser("~/.config/gspread/service_account.json")),
    ]

    for cred_path in cred_paths:
        if cred_path.exists():
            try:
                return gspread.service_account(filename=str(cred_path))
            except Exception:
                pass

    try:
        return gspread.service_account()
    except Exception:
        pass

    return None


def log_error(step: int, video_id: int, error: str, detail: str = "",
              topic: str = "") -> bool:
    """Log a pipeline error to Google Sheets 'Error Log' tab + CSV fallback.

    Args:
        step: Step number (1-8)
        video_id: Video ID
        error: Short error description
        detail: Detailed error message / stack trace
        topic: Topic name (optional, for context)

    Returns:
        True if logged successfully
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    step_name = STEP_NAMES.get(step, f"Step {step}")
    row = [timestamp, str(video_id), str(step), step_name, error, detail[:500], "error"]

    # Try Google Sheets first
    gc = _get_sheets_client()
    if gc:
        try:
            spreadsheet = gc.open_by_key(SHEET_ID)
            try:
                ws = spreadsheet.worksheet("Error Log")
            except Exception:
                ws = spreadsheet.add_worksheet(title="Error Log", rows=100, cols=len(ERROR_LOG_HEADERS))
                ws.update(values=[ERROR_LOG_HEADERS], range_name="A1")

            ws.append_row(row, value_input_option="RAW")
            print(f"   📋 Error logged to Google Sheets: Step {step} ({step_name})")
            return True
        except Exception as e:
            print(f"   ⚠ Sheets error log failed: {e}")

    # CSV fallback
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = CSV_DIR / "error_log.csv"
    write_header = not csv_path.exists()

    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(ERROR_LOG_HEADERS)
        writer.writerow(row)

    print(f"   📋 Error logged to CSV: {csv_path}")
    return True


def log_blocked_steps(from_step: int, video_id: int, blocking_step: int):
    """Log all steps blocked by a failure.

    Args:
        from_step: First blocked step number
        video_id: Video ID
        blocking_step: The step that failed
    """
    for step in range(from_step, 9):
        log_error(
            step=step,
            video_id=video_id,
            error=f"Blocked by Step {blocking_step} failure",
            detail=f"Step {blocking_step} ({STEP_NAMES.get(blocking_step, '?')}) failed — pipeline halted",
        )
