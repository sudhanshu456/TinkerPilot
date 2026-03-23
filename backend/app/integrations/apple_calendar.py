"""
Apple Calendar integration via AppleScript.
Reads calendar events from the macOS Calendar app using osascript.

This approach triggers the proper macOS permission dialog (unlike pyobjc
EventKit which silently fails for unbundled Python scripts on macOS 17+).
"""

import json
import logging
import subprocess
import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _run_applescript(script: str) -> str:
    """Run an AppleScript and return stdout."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "not allowed" in stderr.lower() or "denied" in stderr.lower():
                raise PermissionError(
                    "Calendar access denied. When macOS prompts, click Allow.\n"
                    "Or grant manually: System Settings > Privacy & Security > Automation > Terminal > Calendar"
                )
            raise RuntimeError(f"AppleScript error: {stderr}")
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError("AppleScript timed out (Calendar may be unresponsive)")
    except FileNotFoundError:
        raise RuntimeError("osascript not found (not on macOS?)")


def get_today_events() -> list[dict]:
    """Get today's calendar events."""
    return get_events_for_date(datetime.date.today())


def get_events_for_date(date: datetime.date) -> list[dict]:
    """Get calendar events for a specific date."""
    # Use current date construction to avoid locale-dependent date parsing
    year = date.year
    month = date.month
    day = date.day

    script = f"""
    set output to ""

    -- Build date in a locale-independent way
    set dayStart to current date
    set year of dayStart to {year}
    set month of dayStart to {month}
    set day of dayStart to {day}
    set time of dayStart to 0

    set dayEnd to current date
    set year of dayEnd to {year}
    set month of dayEnd to {month}
    set day of dayEnd to {day}
    set time of dayEnd to 86399

    tell application "Calendar"
        set allCalendars to every calendar
        repeat with cal in allCalendars
            set calName to name of cal
            set dayEvents to (every event of cal whose start date >= dayStart and start date <= dayEnd)
            repeat with evt in dayEvents
                set evtTitle to summary of evt
                set evtStart to start date of evt
                set evtEnd to end date of evt
                set evtLoc to ""
                try
                    set evtLoc to location of evt
                end try
                if evtLoc is missing value then set evtLoc to ""
                set evtAllDay to allday event of evt
                set output to output & evtTitle & "||" & (evtStart as string) & "||" & (evtEnd as string) & "||" & evtLoc & "||" & evtAllDay & "||" & calName & linefeed
            end repeat
        end repeat
    end tell
    return output
    """

    try:
        raw = _run_applescript(script)
    except PermissionError as e:
        logger.warning(f"Calendar access denied: {e}")
        return []
    except RuntimeError as e:
        logger.warning(f"Calendar error: {e}")
        return []

    if not raw.strip():
        return []

    events = []
    for line in raw.strip().split("\n"):
        parts = line.split("||")
        if len(parts) >= 6:
            events.append(
                {
                    "title": parts[0].strip(),
                    "start": parts[1].strip(),
                    "end": parts[2].strip(),
                    "location": parts[3].strip(),
                    "notes": "",
                    "is_all_day": parts[4].strip().lower() == "true",
                    "calendar": parts[5].strip(),
                }
            )

    events.sort(key=lambda x: x["start"])
    return events


def get_upcoming_events(days: int = 7) -> list[dict]:
    """Get events for the next N days."""
    all_events = []
    today = datetime.date.today()
    for i in range(days):
        date = today + datetime.timedelta(days=i)
        day_events = get_events_for_date(date)
        for ev in day_events:
            ev["date"] = date.isoformat()
        all_events.extend(day_events)
    return all_events
