"""
Apple Notes integration via AppleScript.
Reads notes from the macOS Notes app using osascript.
"""

import json
import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def _run_applescript(script: str, timeout: int = 15) -> str:
    """Run an AppleScript and return the output."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            logger.error(f"AppleScript error: {result.stderr}")
            return ""
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        logger.error("AppleScript timed out")
        return ""
    except FileNotFoundError:
        logger.error("osascript not found (not on macOS?)")
        return ""


def get_notes(limit: int = 50) -> list[dict]:
    """Get recent notes from Apple Notes."""
    script = f"""
    tell application "Notes"
        set noteList to {{}}
        set noteCount to count of notes
        if noteCount > {limit} then set noteCount to {limit}
        repeat with i from 1 to noteCount
            set n to note i
            set noteTitle to name of n
            set noteBody to plaintext of n
            set noteDate to modification date of n as string
            set noteFolder to "Unknown"
            try
                set noteFolder to name of container of n
            end try
            set noteId to id of n
            set end of noteList to noteId & "|||" & noteTitle & "|||" & noteBody & "|||" & noteDate & "|||" & noteFolder
        end repeat
        set AppleScript's text item delimiters to "###"
        return noteList as text
    end tell
    """

    raw = _run_applescript(script)
    if not raw:
        return []

    notes = []
    entries = raw.split("###")
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("|||")
        if len(parts) >= 5:
            notes.append(
                {
                    "id": parts[0].strip(),
                    "title": parts[1].strip(),
                    "body": parts[2].strip()[:2000],  # Truncate large notes
                    "modified": parts[3].strip(),
                    "folder": parts[4].strip(),
                }
            )
        elif len(parts) >= 2:
            notes.append(
                {
                    "id": parts[0].strip(),
                    "title": parts[1].strip(),
                    "body": parts[2].strip()[:2000] if len(parts) > 2 else "",
                    "modified": parts[3].strip() if len(parts) > 3 else "",
                    "folder": parts[4].strip() if len(parts) > 4 else "",
                }
            )

    return notes


def search_notes(query: str, limit: int = 10) -> list[dict]:
    """Search Apple Notes by keyword in title or body."""
    all_notes = get_notes(limit=200)

    query_lower = query.lower()
    matched = []
    for note in all_notes:
        if (
            query_lower in note.get("title", "").lower()
            or query_lower in note.get("body", "").lower()
        ):
            # Add a snippet
            body = note.get("body", "")
            idx = body.lower().find(query_lower)
            if idx >= 0:
                start = max(0, idx - 100)
                end = min(len(body), idx + len(query) + 100)
                snippet = body[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(body):
                    snippet = snippet + "..."
                note["snippet"] = snippet
            else:
                note["snippet"] = body[:200]

            matched.append(note)
            if len(matched) >= limit:
                break

    return matched


def get_note_by_title(title: str) -> Optional[dict]:
    """Get a specific note by title."""
    notes = get_notes(limit=500)
    for note in notes:
        if note.get("title", "").lower() == title.lower():
            return note
    return None
