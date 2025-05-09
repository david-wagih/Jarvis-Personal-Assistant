from googleapiclient.discovery import build
from config import get_google_credentials

# Calendar tool function
def list_events(time_min, time_max):
    credentials = get_google_credentials()
    service = build('calendar', 'v3', credentials=credentials)
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

# OpenAI function schema for calendar tool
def get_list_events_schema():
    return {
        "name": "list_events",
        "description": "List all events in a calendar between two RFC3339 datetimes.",
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