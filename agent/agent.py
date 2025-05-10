from tools.calendar_tools import list_events, create_event
from tools.mail_tools import list_emails, send_email
from datetime import datetime, timedelta
import dateutil.parser


def calculate_end_time(start_time_str, duration_minutes):
    """
    Given a start time string (RFC3339), return the end time string after duration_minutes.
    """
    start_dt = dateutil.parser.isoparse(start_time_str)
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    return end_dt.isoformat()


def find_next_available_slot(time_min, duration_minutes=60, search_hours=8):
    """
    Find the next available slot of the given duration after time_min.
    Searches up to search_hours ahead.
    Returns (start_time, end_time) as RFC3339 strings.
    """
    start_dt = dateutil.parser.isoparse(time_min)
    end_search_dt = start_dt + timedelta(hours=search_hours)
    current_start = start_dt
    while current_start + timedelta(minutes=duration_minutes) <= end_search_dt:
        current_end = current_start + timedelta(minutes=duration_minutes)
        # Check for events in this slot
        events = list_events(
            time_min=current_start.isoformat(),
            time_max=current_end.isoformat()
        )
        if not events:
            return current_start.isoformat(), current_end.isoformat()
        # Move to the end of the next event
        next_event_end = max(
            dateutil.parser.isoparse(ev['end'].get('dateTime', ev['end'].get('date')))
            for ev in events
        )
        current_start = next_event_end
    return None, None  # No slot found


def schedule_meeting_with_person(person_email, requested_time, duration_minutes=60):
    """
    Try to schedule a meeting with person_email at requested_time (RFC3339).
    If not available, propose the next available slot.
    """
    events = list_events(time_min=requested_time, time_max=calculate_end_time(requested_time, duration_minutes))
    if not events:
        # Free! Schedule and send email
        create_event(
            summary=f"Meeting with {person_email}",
            start=requested_time,
            end=calculate_end_time(requested_time, duration_minutes)
        )
        send_email(
            to=person_email,
            subject="Meeting Scheduled",
            message_text=f"Hi, I've scheduled a meeting with you at {requested_time}."
        )
        print("Meeting scheduled and email sent.")
    else:
        # Not free, find next slot
        next_start, next_end = find_next_available_slot(requested_time, duration_minutes)
        if next_start:
            send_email(
                to=person_email,
                subject="Reschedule Meeting",
                message_text=f"I'm not available at {requested_time}. Are you free at {next_start}?"
            )
            print(f"Proposed new time to person: {next_start}")
        else:
            print("No available slot found in the next search window.")