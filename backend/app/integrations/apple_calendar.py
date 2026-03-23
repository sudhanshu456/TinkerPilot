"""
Apple Calendar integration via pyobjc (EventKit).
Reads calendar events from the macOS Calendar app.
"""

import logging
import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _get_event_store():
    """Get the EventKit event store with permission."""
    try:
        import EventKit
    except ImportError:
        raise ImportError(
            "pyobjc-framework-EventKit required. Install: pip install pyobjc-framework-EventKit"
        )

    store = EventKit.EKEventStore.alloc().init()

    # Request access (synchronous wait)
    import threading

    granted = threading.Event()
    access_result = {"granted": False, "error": None}

    def callback(granted_flag, error):
        access_result["granted"] = granted_flag
        access_result["error"] = error
        granted.set()

    store.requestAccessToEntityType_completion_(EventKit.EKEntityTypeEvent, callback)
    granted.wait(timeout=10)

    if not access_result["granted"]:
        raise PermissionError(
            "Calendar access denied. Grant access in System Settings > Privacy & Security > Calendars."
        )

    return store


def get_today_events() -> list[dict]:
    """Get today's calendar events."""
    return get_events_for_date(datetime.date.today())


def get_events_for_date(date: datetime.date) -> list[dict]:
    """Get calendar events for a specific date."""
    try:
        import EventKit
        import Foundation
    except ImportError:
        logger.warning("EventKit not available, returning empty events")
        return []

    try:
        store = _get_event_store()
    except PermissionError as e:
        logger.warning(f"Calendar access denied: {e}")
        return []

    # Create date range for the day
    cal = Foundation.NSCalendar.currentCalendar()

    components_start = Foundation.NSDateComponents.alloc().init()
    components_start.setYear_(date.year)
    components_start.setMonth_(date.month)
    components_start.setDay_(date.day)
    components_start.setHour_(0)
    components_start.setMinute_(0)
    start_date = cal.dateFromComponents_(components_start)

    components_end = Foundation.NSDateComponents.alloc().init()
    components_end.setYear_(date.year)
    components_end.setMonth_(date.month)
    components_end.setDay_(date.day)
    components_end.setHour_(23)
    components_end.setMinute_(59)
    end_date = cal.dateFromComponents_(components_end)

    # Fetch events
    predicate = store.predicateForEventsWithStartDate_endDate_calendars_(start_date, end_date, None)
    events = store.eventsMatchingPredicate_(predicate)

    result = []
    for event in events or []:
        try:
            ev_start = event.startDate()
            ev_end = event.endDate()

            result.append(
                {
                    "title": str(event.title() or "Untitled"),
                    "start": str(ev_start),
                    "end": str(ev_end),
                    "location": str(event.location() or ""),
                    "notes": str(event.notes() or ""),
                    "is_all_day": bool(event.isAllDay()),
                    "calendar": str(event.calendar().title()) if event.calendar() else "",
                }
            )
        except Exception as e:
            logger.debug(f"Error reading event: {e}")
            continue

    # Sort by start time
    result.sort(key=lambda x: x["start"])
    return result


def get_upcoming_events(days: int = 7) -> list[dict]:
    """Get events for the next N days."""
    all_events = []
    today = datetime.date.today()
    for i in range(days):
        date = today + datetime.timedelta(days=i)
        events = get_events_for_date(date)
        for ev in events:
            ev["date"] = date.isoformat()
        all_events.extend(events)
    return all_events
