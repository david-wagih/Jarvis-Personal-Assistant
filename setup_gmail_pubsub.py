from flask import Flask, request

app = Flask(__name__)

@app.route('/gmail-webhook', methods=['POST'])
def gmail_webhook():
    envelope = request.get_json()
    # Process the notification (e.g., pull the new email, check sender, etc.)
    print("Received Gmail notification:", envelope)
    # Here, you can trigger your agent logic to check/respond to the new email
    return '', 204

if __name__ == '__main__':
    app.run(port=8081)