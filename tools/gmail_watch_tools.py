from googleapiclient.discovery import build
from tools.oauth_integration import get_credentials

def start_gmail_watch():
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    # Get the authenticated user's email
    profile = service.users().getProfile(userId='me').execute()
    print("Authenticated as:", profile.get('emailAddress'))
    request = {
        'labelIds': ['INBOX'],
        'topicName': 'projects/stakpack-hackathon/topics/gmail-push'
    }
    print("Attempting to register Gmail watch with request:", request)
    try:
        response = service.users().watch(userId='me', body=request).execute()
        print("Gmail watch response:", response)
    except Exception as e:
        print("Error registering Gmail watch:", e)

if __name__ == "__main__":
    start_gmail_watch()