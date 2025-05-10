import base64
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from tools.oauth_integration import get_credentials

# Mail tool function
def list_emails(query=''):
    credentials = get_credentials()
    service = build('gmail', 'v1', credentials=credentials)
    results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        snippet = msg_data.get('snippet', '')
        emails.append(snippet)
    return emails

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

                    