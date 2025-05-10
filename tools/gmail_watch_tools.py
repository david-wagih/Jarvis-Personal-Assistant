from googleapiclient.discovery import build
from tools.oauth_integration import get_credentials

def start_gmail_watch(topic_name):
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    request = {
        'labelIds': ['INBOX'],
        'topicName': topic_name
    }
    response = service.users().watch(userId='me', body=request).execute()
    print("Gmail watch response:", response)