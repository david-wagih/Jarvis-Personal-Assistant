import os
import pickle
from urllib.request import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/tasks'
]

def get_credentials():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials_oauth.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def test_gmail():
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    messages = results.get('messages', [])
    print('Recent emails:')
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        print(msg_data.get('snippet', ''))

def test_calendar():
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    now = '2023-01-01T00:00:00Z'
    events_result = service.events().list(
        calendarId='primary', timeMin=now, maxResults=5, singleEvents=True, orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    print('Upcoming events:')
    for event in events:
        print(event.get('summary', 'No Title'), event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'Unknown')))

def test_tasks():
    creds = get_credentials()
    service = build('tasks', 'v1', credentials=creds)
    results = service.tasks().list(tasklist='@default').execute()
    tasks = results.get('items', [])
    print('Tasks:')
    for task in tasks:
        print(f"- {task.get('title', 'No Title')}")

if __name__ == '__main__':
    print('Testing Gmail API...')
    test_gmail()
    print('\nTesting Calendar API...')
    test_calendar()
    print('\nTesting Tasks API...')
    test_tasks()