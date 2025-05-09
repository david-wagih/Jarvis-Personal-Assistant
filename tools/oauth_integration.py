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
    'https://www.googleapis.com/auth/tasks'  # Write access
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

def test_create_calendar_event():
    """Create a new event in the primary calendar."""
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    event = {
        'summary': 'Test Event from API',
        'start': {'dateTime': '2025-05-10T10:00:00+00:00'},
        'end': {'dateTime': '2025-05-10T11:00:00+00:00'},
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    print('Created event:')
    print(f"Summary: {created_event.get('summary')}, ID: {created_event.get('id')}")

def test_tasks():
    creds = get_credentials()
    service = build('tasks', 'v1', credentials=creds)
    results = service.tasks().list(tasklist='@default').execute()
    tasks = results.get('items', [])
    print('Tasks:')
    for task in tasks:
        print(f"- {task.get('title', 'No Title')}")

def test_create_task():
    """Create a new task in the default task list."""
    creds = get_credentials()
    service = build('tasks', 'v1', credentials=creds)
    task = {
        'title': 'Test Task from API'
    }
    created_task = service.tasks().insert(tasklist='@default', body=task).execute()
    print('Created task:')
    print(f"Title: {created_task.get('title')}, ID: {created_task.get('id')}")

def send_email(to, subject, message_text):
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    message = MIMEText(message_text)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}
    sent_message = service.users().messages().send(userId='me', body=body).execute()
    print(f"Email sent! Message ID: {sent_message['id']}")

if __name__ == '__main__':
    print('Testing Gmail API...')
    test_gmail()
    print('\nTesting Calendar API...')
    test_calendar()
    print('\nTesting Tasks API...')
    test_tasks()
    print('\nCreating a new calendar event...')
    test_create_calendar_event()
    print('\nCreating a new task...')
    test_create_task()
    print('\nSending a test email...')
    send_email(
        to='davidwagih62@gmail.com',
        subject='Test Email from API',
        message_text='This is a test email sent from the Gmail API!'
    )