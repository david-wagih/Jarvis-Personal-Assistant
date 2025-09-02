from googleapiclient.discovery import build
from tools.oauth_integration import get_credentials

# Calendar tool function
def list_events(time_min, time_max):
    credentials = get_credentials()
    service = build('calendar', 'v3', credentials=credentials)
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

def create_event(summary, start, end, guests=None):
    credentials = get_credentials()
    service = build('calendar', 'v3', credentials=credentials)
    event = {
        'summary': summary,
        'start': {'dateTime': start, 'timeZone': 'Africa/Cairo'},
        'end': {'dateTime': end, 'timeZone': 'Africa/Cairo'}
    }
    if guests:
        event['attendees'] = [{'email': email} for email in guests]
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event

def update_event(event_id, summary=None, start=None, end=None, guests=None):
    credentials = get_credentials()
    service = build('calendar', 'v3', credentials=credentials)
    try:
        # Fetch the existing event
        existing_event = service.events().get(calendarId='primary', eventId=event_id).execute()
        event = {}
        # Use provided summary or fallback to existing
        event['summary'] = summary if summary else existing_event.get('summary', 'No title')
        if start:
            event['start'] = {'dateTime': start, 'timeZone': 'Africa/Cairo'}
        else:
            event['start'] = existing_event['start']
        if end:
            event['end'] = {'dateTime': end, 'timeZone': 'Africa/Cairo'}
        else:
            event['end'] = existing_event['end']
        if guests:
            event['attendees'] = [{'email': email} for email in guests]
        elif 'attendees' in existing_event:
            event['attendees'] = existing_event['attendees']
        updated_event = service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return updated_event
    except Exception as e:
        if "Not Found" in str(e) or "404" in str(e):
            return {"error": f"Event with ID {event_id} not found. It may have been deleted or doesn't exist."}
        else:
            return {"error": f"Failed to update event: {str(e)}"}

def delete_event(event_id):
    credentials = get_credentials()
    service = build('calendar', 'v3', credentials=credentials)
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return f"Event {event_id} deleted successfully."



# OpenAI function schema for calendar tool
def get_list_events_schema():
    return {
        "name": "list_events",
        "description": "List all events in a calendar between two RFC3339 datetimes. Use this tool to check if David is available before scheduling or creating any new event. Always use this before calling create_event.",
        "parameters": {
            "type": "object",
            "properties": {
                "time_min": {
                    "type": "string",
                    "description": "The minimum time to list events (RFC3339 format, e.g., '2022-01-01T00:00:00Z')"
                },
                "time_max": {
                    "type": "string",
                    "description": "The maximum time to list events (RFC3339 format, e.g., '2022-01-02T00:00:00Z')"
                }
            },
            "required": ["time_min", "time_max"]
        }
    }

def get_create_event_schema():
    return {
        "name": "create_event",
        "description": "Create a new event in the primary calendar. Only use this after confirming with list_events that David is available at the requested time. Never create an event without checking availability first. Optionally, add guests to the event by providing their email addresses.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "The summary of the event."
                },
                "start": {
                    "type": "string",
                    "description": "The start time of the event (RFC3339 format, e.g., '2022-01-01T00:00:00Z')"
                },
                "end": {
                    "type": "string",
                    "description": "The end time of the event (RFC3339 format, e.g., '2022-01-02T00:00:00Z')"
                },
                "guests": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of email addresses to add as guests/attendees to the event."
                }
            },
            "required": ["summary", "start", "end"]
        }
    }
        
def get_update_event_schema():
    return {
        "name": "update_event",
        "description": "Update an existing calendar event",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "The ID of the event to update"},
                "summary": {"type": "string", "description": "The new title of the event"},
                "guests": {"type": "array", "items": {"type": "string"}, "description": "List of guest emails"},
                "start": {
                    "type": "string",
                    "description": "The new start time of the event (RFC3339 format, e.g., '2022-01-01T00:00:00Z')"
                },
                "end": {
                    "type": "string",
                    "description": "The new end time of the event (RFC3339 format, e.g., '2022-01-02T00:00:00Z')"
                }
            },
            "required": ["event_id"],
        },
    }


def get_delete_event_schema():
    return {
        "name": "delete_event",
        "description": "Delete an existing event from the primary calendar. Use this to remove an event after it has been created.",
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "The ID of the event to delete."
                }
            },
            "required": ["event_id"]
        }
    }
