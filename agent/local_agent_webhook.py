from flask import Flask, request, jsonify
import json
import os
import threading

app = Flask(__name__)
lock = threading.Lock()

@app.route('/new-email', methods=['POST'])
def new_email():
    email_data = request.get_json()
    if not email_data:
        return jsonify({"error": "No email data received"}), 400

    with lock:
        if os.path.exists("new_emails.json"):
            with open("new_emails.json", "r") as f:
                emails = json.load(f)
        else:
            emails = []
        emails.append(email_data)
        with open("new_emails.json", "w") as f:
            json.dump(emails, f)
    print(f"Received and stored new email: {email_data}")
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(port=8081)