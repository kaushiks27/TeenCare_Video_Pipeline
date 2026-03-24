#!/usr/bin/env python3
"""
Google Sheets Updater — Unified script for all sheet operations

Writes/reads data to the project Google Sheet with 3 tabs:
  1. Viral Research — raw scored data
  2. Selected Topics — top 7 with workflow status
  3. SEO Captions — Instagram captions + hashtags

Falls back to CSV export if no Google credentials are available.

Usage:
    python3 execution/update_sheets.py --tab "Viral Research" --data .tmp/viral_research/scored_posts.json
    python3 execution/update_sheets.py --tab "Selected Topics" --data .tmp/viral_research/selected_topics.json
    python3 execution/update_sheets.py --tab "SEO Captions" --data .tmp/viral_research/seo_captions.json
    python3 execution/update_sheets.py --read-topics  # Read existing topics for dedup
    python3 execution/update_sheets.py --test  # Test connection
"""
from __future__ import annotations

import os
import sys
import csv
import json
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SHEET_ID = "13EWGhUcOxtF_jZ-KlO9vXsMbqIR8rKVMoe9CFgC6hnM"
OUTPUT_DIR = Path(".tmp/viral_research")
CSV_DIR = OUTPUT_DIR / "csv_export"

# Tab configurations
TABS = {
    "Viral Research": {
        "headers": [
            "Rank", "Topic", "Virality Score", "Velocity Score",
            "Resonance Score", "Shareability Score", "Platform",
            "Sample URL", "Post Count", "Scraped Date"
        ],
    },
    "Selected Topics": {
        "headers": [
            "Rank", "Topic", "Virality Score", "Status",
            "Video Config", "Platform", "Sample URL", "Selected Date"
        ],
    },
    "SEO Captions": {
        "headers": [
            "Topic", "Hook Line", "Caption Text", "Hashtags",
            "Generated Date", "Status"
        ],
    },
}


def get_sheets_client():
    """Initialize Google Sheets client via gspread. Returns None if no creds."""
    try:
        import gspread
    except ImportError:
        print("   ⚠ gspread not installed — will fall back to CSV export")
        return None

    # Try service account first, then OAuth
    cred_paths = [
        Path("credentials.json"),
        Path("service_account.json"),
        Path(os.path.expanduser("~/.config/gspread/service_account.json")),
    ]

    for cred_path in cred_paths:
        if cred_path.exists():
            try:
                gc = gspread.service_account(filename=str(cred_path))
                print(f"   ✓ Authenticated via {cred_path}")
                return gc
            except Exception as e:
                print(f"   ⚠ Failed with {cred_path}: {e}")

    # Fallback: try default auth
    try:
        gc = gspread.service_account()
        print("   ✓ Authenticated via default service account")
        return gc
    except Exception:
        pass

    # Final fallback: OAuth
    try:
        gc = gspread.oauth()
        print("   ✓ Authenticated via OAuth")
        return gc
    except Exception as e:
        print(f"   ⚠ No Google credentials found — falling back to CSV export")
        print(f"      To enable Sheets: place credentials.json or service_account.json in project root")
        return None


def ensure_tab(spreadsheet, tab_name: str, headers: list):
    """Ensure a tab exists with correct headers."""
    try:
        worksheet = spreadsheet.worksheet(tab_name)
        print(f"   ✓ Tab '{tab_name}' exists")
    except Exception:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=100, cols=len(headers))
        worksheet.update("A1", [headers])
        print(f"   ✓ Created tab '{tab_name}' with headers")
    return worksheet


# ─── CSV Fallback Functions ──────────────────────────────────────────────────

def write_csv(tab_name: str, headers: list, rows: list):
    """Write data to a CSV file as fallback when Sheets is unavailable."""
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = tab_name.lower().replace(" ", "_")
    csv_path = CSV_DIR / f"{safe_name}.csv"

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"   ✓ CSV fallback: wrote {len(rows)} rows to {csv_path}")
    return csv_path


def build_viral_research_rows(data: list) -> list:
    """Build rows for Viral Research tab."""
    rows = []
    for i, item in enumerate(data, 1):
        rows.append([
            i,
            item.get("topic", ""),
            item.get("virality_score", 0),
            item.get("velocity_score", 0),
            item.get("resonance_score", 0),
            item.get("shareability_score", 0),
            ", ".join(item.get("platforms", [])),
            item.get("sample_url", ""),
            item.get("post_count", 0),
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ])
    return rows


def build_selected_topics_rows(data: list) -> list:
    """Build rows for Selected Topics tab."""
    rows = []
    for i, item in enumerate(data, 1):
        rows.append([
            i,
            item.get("topic", ""),
            item.get("virality_score", 0),
            "pending",
            "",
            ", ".join(item.get("platforms", [])),
            item.get("sample_url", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ])
    return rows


def build_seo_captions_rows(data: list) -> list:
    """Build rows for SEO Captions tab."""
    rows = []
    for item in data:
        rows.append([
            item.get("topic", ""),
            item.get("hook_line", ""),
            item.get("caption_text", ""),
            item.get("hashtags", ""),
            item.get("generated_date", datetime.now().strftime("%Y-%m-%d %H:%M")),
            "ready",
        ])
    return rows


ROW_BUILDERS = {
    "Viral Research": build_viral_research_rows,
    "Selected Topics": build_selected_topics_rows,
    "SEO Captions": build_seo_captions_rows,
}


# ─── Google Sheets Write Functions ────────────────────────────────────────────

def write_to_sheet(worksheet, tab_name: str, headers: list, rows: list):
    """Write rows to a Google Sheets worksheet."""
    if rows:
        worksheet.clear()
        worksheet.update("A1", [headers])
        worksheet.update("A2", rows)
        print(f"   ✓ Wrote {len(rows)} rows to Google Sheets tab '{tab_name}'")


def read_existing_topics(worksheet) -> list:
    """Read existing topic names for deduplication."""
    try:
        values = worksheet.col_values(2)  # Column B = Topic
        topics = [v for v in values[1:] if v]  # Skip header
        return topics
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description="Google Sheets updater")
    parser.add_argument("--tab", type=str, help="Tab name to write to")
    parser.add_argument("--data", type=str, help="JSON data file to write")
    parser.add_argument("--read-topics", action="store_true", help="Read existing topics for dedup")
    parser.add_argument("--test", action="store_true", help="Test connection")
    args = parser.parse_args()

    print("=" * 70)
    print("GOOGLE SHEETS UPDATER")
    print(f"   Sheet: {SHEET_ID}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    gc = get_sheets_client()

    if gc is not None:
        try:
            spreadsheet = gc.open_by_key(SHEET_ID)
            print(f"   ✓ Opened sheet: {spreadsheet.title}")
        except Exception as e:
            print(f"   ⚠ Could not open sheet: {e}")
            gc = None  # Fall back to CSV
    else:
        spreadsheet = None

    if args.test:
        if gc and spreadsheet:
            print("\n   ✓ TEST — Google Sheets connection verified.")
            for tab_name, config in TABS.items():
                ensure_tab(spreadsheet, tab_name, config["headers"])
        else:
            print("\n   ⚠ TEST — No Google credentials. CSV fallback will be used.")
            print(f"      CSVs will be saved to: {CSV_DIR}/")
        return

    if args.read_topics:
        if gc and spreadsheet:
            ws = ensure_tab(spreadsheet, "Selected Topics", TABS["Selected Topics"]["headers"])
            topics = read_existing_topics(ws)
        else:
            topics = []
            print("   ⚠ No sheets access — returning empty topic list for dedup")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        dedup_path = OUTPUT_DIR / "existing_topics.json"
        with open(dedup_path, "w") as f:
            json.dump(topics, f, indent=2)
        print(f"\n   ✓ Read {len(topics)} existing topics → {dedup_path}")
        return

    if not args.tab or not args.data:
        print("ERROR: --tab and --data are required")
        sys.exit(1)

    if args.tab not in TABS:
        print(f"ERROR: Unknown tab '{args.tab}'. Available: {list(TABS.keys())}")
        sys.exit(1)

    # Load data
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"ERROR: Data file not found: {data_path}")
        sys.exit(1)

    with open(data_path) as f:
        data = json.load(f)

    print(f"\n   Loaded {len(data)} items from {data_path}")

    # Build rows
    tab_config = TABS[args.tab]
    headers = tab_config["headers"]
    rows = ROW_BUILDERS[args.tab](data)

    # Write to Google Sheets OR CSV fallback
    if gc and spreadsheet:
        ws = ensure_tab(spreadsheet, args.tab, headers)
        write_to_sheet(ws, args.tab, headers, rows)
        print(f"\n{'=' * 70}")
        print(f"✅ GOOGLE SHEET UPDATED: {args.tab}")
        print(f"{'=' * 70}")
    else:
        csv_path = write_csv(args.tab, headers, rows)
        print(f"\n{'=' * 70}")
        print(f"✅ CSV EXPORTED (no Google credentials): {csv_path}")
        print(f"   To enable Google Sheets: place credentials.json in project root")
        print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
