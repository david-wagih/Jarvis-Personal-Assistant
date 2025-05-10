import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from tools.oauth_integration import get_credentials

# Mail tool function
def list_emails(labelIds=None, query='', max_results=50):
    credentials = get_credentials()
    service = build('gmail', 'v1', credentials=credentials)
    kwargs = {'userId': 'me', 'maxResults': max_results}
    if labelIds:
        kwargs['labelIds'] = labelIds
    if query:
        kwargs['q'] = query
    else:
        # Default to unread if no query provided
        kwargs['q'] = 'is:unread'
    results = service.users().messages().list(**kwargs).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = {h['name'].lower(): h['value'] for h in msg_data['payload'].get('headers', [])}
        body = ''
        if 'parts' in msg_data['payload']:
            for part in msg_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        else:
            if 'data' in msg_data['payload']['body']:
                body = base64.urlsafe_b64decode(msg_data['payload']['body']['data']).decode('utf-8')
        emails.append({
            'id': msg['id'],
            'from': headers.get('from', ''),
            'reply_to': headers.get('reply-to', ''),
            'subject': headers.get('subject', ''),
            'body': body
        })
    return {'emails': emails}

def send_email(to, subject, message_text):
    credentials = get_credentials()
    service = build('gmail', 'v1', credentials=credentials)
    message = MIMEText(message_text)
    message['to'] = to
    message['subject'] = subject    
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}
    sent_message = service.users().messages().send(userId='me', body=body).execute()
    print(f"Email sent! Message ID: {sent_message['id']}")

def mark_email_as_read(email_id):
    credentials = get_credentials()
    service = build('gmail', 'v1', credentials=credentials)
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={'removeLabelIds': ['UNREAD']}
    ).execute()
    print(f"Marked email {email_id} as read.")

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

def get_send_email_schema():
    return {
        "name": "send_email",
        "description": "Send an email to a specified recipient.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "The email address of the recipient."
                },
                "subject": {
                    "type": "string",
                    "description": "The subject of the email."
                },
                "message_text": {
                    "type": "string",
                    "description": "The body of the email."
                }
            },
            "required": ["to", "subject", "message_text"]
        }
    }


                    