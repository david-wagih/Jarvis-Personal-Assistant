# Imports
import os
import sys
import json
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account
from langfuse.openai import openai

# Load environment variables
load_dotenv('.env')

# Configuration
openai_key = os.environ.get("OPENAI_API_KEY")
google_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
google_calendar_delegated_user = os.environ.get("GOOGLE_CALENDAR_DELEGATED_USER")

# Langfuse setup
# langfuse = Langfuse(
#     secret_key=os.environ["LANGFUSE_SECRET_KEY"],
#     public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
#     host="https://cloud.langfuse.com"
# )

# OpenAI session setup
# openai_session = OpenAI(api_key=openai_key)

openai.langfuse_auth_check()

# Google API setup
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

# Validate service account file
if not google_credentials:
    print("ERROR: GOOGLE_APPLICATION_CREDENTIALS is not set in the environment or .env file.")
    sys.exit(1)

print(f"[DEBUG] Loading credentials from: {google_credentials}")

if not os.path.isfile(google_credentials):
    print(f"ERROR: Service account file '{google_credentials}' does not exist.")
    sys.exit(1)

try:
    with open(google_credentials, 'r') as f:
        data = json.load(f)
    # Check for required fields
    for field in ["client_email", "private_key", "token_uri"]:
        if field not in data:
            print(f"ERROR: Service account file is missing required field: {field}")
            sys.exit(1)
except Exception as e:
    print(f"ERROR: Failed to read or parse service account file: {e}")
    sys.exit(1)

credentials = service_account.Credentials.from_service_account_file(
    google_credentials, scopes=SCOPES
).with_subject(google_calendar_delegated_user)

# Function definitions
def list_events(time_min, time_max):
    service = build('calendar', 'v3', credentials=credentials)
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])

def list_emails(query=''):
    service = build('gmail', 'v1', credentials=credentials)
    results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        snippet = msg_data.get('snippet', '')
        emails.append(snippet)
    return emails

# Function schemas for OpenAI function calling
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

def get_list_emails_schema():
    return {
        "name": "list_emails",
        "description": "List the most recent emails. Optionally filter with a Gmail search query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query (optional)."
                }
            },
            "required": []
        }
    }

# Register tools
TOOLS = [
    {"type": "function", "function": get_list_events_schema()},
    {"type": "function", "function": get_list_emails_schema()}
]

# Main execution
response = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are an assistant that can read my mail and calendar."},
        {"role": "user", "content": "Show me my next 3 calendar events and unread emails."}
    ],
    tools=TOOLS,
)

# Handle tool calls
message = response.choices[0].message
if hasattr(message, "tool_calls") and message.tool_calls:
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        if function_name == "list_events":
            result = list_events(**arguments)
            print("Calendar events:", result)
        elif function_name == "list_emails":
            result = list_emails(**arguments)
            print("Emails:", result)
else:
    print(message.content)