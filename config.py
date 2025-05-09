import os
import sys
import json
from dotenv import load_dotenv
from google.oauth2 import service_account

# Load environment variables
load_dotenv('.env')

# Configuration
openai_key = os.environ.get("OPENAI_API_KEY")
google_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
google_calendar_delegated_user = os.environ.get("GOOGLE_CALENDAR_DELEGATED_USER")

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

def get_openai_key():
    return openai_key

def get_google_credentials():
    if not google_credentials:
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS is not set in the environment or .env file.")
        sys.exit(1)
    if not os.path.isfile(google_credentials):
        print(f"ERROR: Service account file '{google_credentials}' does not exist.")
        sys.exit(1)
    try:
        with open(google_credentials, 'r') as f:
            data = json.load(f)
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
    return credentials 