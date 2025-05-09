from googleapiclient.discovery import build
from config import get_google_credentials

# Mail tool function
def list_emails(query=''):
    credentials = get_google_credentials()
    service = build('gmail', 'v1', credentials=credentials)
    results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        snippet = msg_data.get('snippet', '')
        emails.append(snippet)
    return emails

# OpenAI function schema for mail tool
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