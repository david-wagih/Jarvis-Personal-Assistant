import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/calendar',  # Write access
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_credentials():
    """
    Loads credentials for Google APIs.
    - In production (CLOUD_RUN env var set), only loads from token.pickle and never runs the OAuth flow.
    - In local/dev, runs the OAuth flow if needed.
    """

    creds = None
    is_cloud_run = os.environ.get('CLOUD_RUN') == '1'
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif not is_cloud_run:
            # Use absolute path for credentials_oauth.json
            credentials_path = os.path.join(os.path.dirname(__file__), '..', '..', 'credentials_oauth.json')
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(port=8080)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        else:
            raise RuntimeError("No valid credentials found and cannot run OAuth flow in Cloud Run. Please generate token.pickle locally and deploy it.")
    return creds