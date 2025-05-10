from flask import Flask, request
from tools.mail_tools import list_emails  # or a new function to fetch by ID
from tools.calendar_tools import create_event, list_events
from tools.todos_tools import add_task
from tools.oauth_integration import get_credentials
import base64
import json
import os

app = Flask(__name__)

# Load contacts
with open('contacts.json', 'r') as f:
    CONTACTS = json.load(f)['contacts']

HISTORY_ID_FILE = "last_history_id.txt"

def save_last_history_id(history_id):
    with open(HISTORY_ID_FILE, "w") as f:
        f.write(str(history_id))

def load_last_history_id():
    if not os.path.exists(HISTORY_ID_FILE):
        return None
    with open(HISTORY_ID_FILE, "r") as f:
        return f.read().strip()

def extract_message_id(envelope):
    # Google Pub/Sub Gmail notification format
    # https://developers.google.com/gmail/api/guides/push
    try:
        message_id = envelope['message']['data']
        # The data field is base64-encoded JSON
        decoded_data = base64.urlsafe_b64decode(message_id + '==').decode('utf-8')
        data_json = json.loads(decoded_data)
        history_id = data_json.get('historyId')
        # You may want to return history_id or trigger a history fetch
        # For simplicity, let's return the historyId (you may want to fetch the latest message in production)
        return history_id
    except Exception as e:
        print(f"Failed to extract message id: {e}")
        return None

def fetch_new_emails_since(history_id):
    creds = get_credentials()
    from googleapiclient.discovery import build
    service = build('gmail', 'v1', credentials=creds)
    try:
        # Get all history records since the last historyId
        results = service.users().history().list(userId='me', startHistoryId=history_id, historyTypes=['messageAdded']).execute()
        history = results.get('history', [])
        new_messages = []
        for record in history:
            for msg in record.get('messages', []):
                msg_id = msg['id']
                msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                headers = {h['name'].lower(): h['value'] for h in msg_data['payload'].get('headers', [])}
                body = ''
                if 'parts' in msg_data['payload']:
                    for part in msg_data['payload']['parts']:
                        if part['mimeType'] == 'text/plain':
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            break
                else:
                    body = base64.urlsafe_b64decode(msg_data['payload']['body']['data']).decode('utf-8')
                new_messages.append({
                    'id': msg_id,
                    'from': headers.get('from', ''),
                    'subject': headers.get('subject', ''),
                    'body': body
                })
        return new_messages
    except Exception as e:
        print(f"Failed to fetch new emails since history id: {e}")
        return []

def process_incoming_email(email_data, contacts):
    sender = email_data['from']
    subject = email_data['subject']
    body = email_data['body']
    # Check if sender is in contacts
    if sender in [c['email'] for c in contacts]:
        # If it's a reply to a meeting, or contains 'reschedule', etc.
        if 'reschedule' in body.lower():
            # Trigger reschedule logic
            print(f"Reschedule requested by {sender}.")
        elif 'confirm' in body.lower():
            # Trigger confirmation logic
            print(f"Confirmation received from {sender}.")
        else:
            print(f"Email from contact {sender}: {subject}")
    else:
        print(f"Email from non-contact: {sender}")
    append_new_email(email_data)

def append_new_email(email_data):
    import threading
    import json
    import os
    lock = threading.Lock()
    with lock:
        try:
            if os.path.exists("new_emails.json"):
                with open("new_emails.json", "r") as f:
                    emails = json.load(f)
            else:
                emails = []
            emails.append(email_data)
            with open("new_emails.json", "w") as f:
                json.dump(emails, f)
        except Exception as e:
            print(f"Failed to append new email: {e}")

@app.route('/gmail-webhook', methods=['POST'])
def gmail_webhook():
    envelope = request.get_json()
    if not envelope:
        print("No JSON received!")
        return ('', 400)
    if not isinstance(envelope, dict) or 'message' not in envelope:
        print("Invalid Pub/Sub message format:", envelope)
        return ('', 400)
    pubsub_message = envelope['message']
    # Decode the message data
    data = base64.b64decode(pubsub_message['data']).decode('utf-8')
    print("Decoded data:", data)
    history_id = extract_message_id(envelope)
    last_history_id = load_last_history_id()
    if history_id:
        if last_history_id:
            new_emails = fetch_new_emails_since(last_history_id)
            for email_data in new_emails:
                process_incoming_email(email_data, CONTACTS)
        save_last_history_id(history_id)
    return '', 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))