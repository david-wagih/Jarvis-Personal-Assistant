# Jarvis: Proactive AI Assistant for Email, Calendar, and Tasks

## Overview
Jarvis is a proactive AI assistant designed to help you manage your emails, Google Calendar events, and Google Tasks. It leverages OpenAI's GPT models and integrates with Google APIs to automate scheduling, email handling, and task management. Jarvis can be used via a command-line interface or a modern Streamlit web UI.

## Features
- **Proactive Email Handling:** Detects new emails, summarizes, and suggests/acts on meeting requests or reschedules.
- **Smart Scheduling:** Checks your Google Calendar for availability before creating or updating events. Avoids double-booking.
- **Task Management:** Lists, adds, and completes Google Tasks.
- **Contact Resolution:** Uses a local contacts list to resolve names to email addresses for scheduling and communication.
- **Human-in-the-Loop:** Asks for confirmation before sending emails or creating events.
- **Web UI:** Chat with Jarvis using a Streamlit interface.
- **Push Notification Support:** Can receive Gmail push notifications via Google Pub/Sub and webhooks.
- **Experimental Voice Assistant:** (See `ELEVEN_LABS_TEST.Py`) Record speech, transcribe with Whisper, and respond with ElevenLabs TTS.

## Architecture
- **main.py:** Core CLI agent loop, polling for new emails, handling user input, and orchestrating tool calls.
- **app.py:** Streamlit web UI for chatting with Jarvis and viewing logs.
- **tools/**: Modular tools for calendar, mail, tasks, OAuth, and email processing.
- **setup_gmail_pubsub.py:** Flask app for handling Gmail push notifications and storing new emails for the agent to process.
- **local_agent_webhook.py:** Local webhook for testing email ingestion.
- **agent.py:** Helper functions for advanced scheduling logic.
- **contacts.json:** List of known contacts (name/email) for resolving scheduling requests.
- **config.py:** Environment/configuration helpers.
- **Dockerfile & entrypoint.sh:** Containerization and deployment scripts.

## Setup Instructions

### 1. Clone the Repository
```sh
git clone <your-repo-url>
cd stakpak-hackathon-day
```

### 2. Install Python Dependencies
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Or use `pyproject.toml` with your preferred tool (e.g., `pip install .`).

### 3. Environment Variables & Credentials
- **Google OAuth:**
  - Place your `credentials_oauth.json` (OAuth client) and `service_account.json` (for Pub/Sub, if needed) in the project root.
  - The first run will prompt you to authenticate and generate `token.pickle`.
- **OpenAI API Key:**
  - Set `OPENAI_API_KEY` in your environment or `.env` file.
- **Other Variables:**
  - See `config.py` for additional options (e.g., `GOOGLE_APPLICATION_CREDENTIALS`).

### 4. Add Contacts
Edit `contacts.json` to include your frequent contacts:
```json
{
  "contacts": [
    { "name": "Mahmoud Gamil", "email": "mahmoudgamiel28@gmail.com" },
    { "name": "Ahmed Shehata", "email": "ahmedshehata20047@gmail.com" }
  ]
}
```

### 5. Running Locally (CLI)
```sh
python main.py
```
- Jarvis will prompt for your commands and proactively process new emails.
- Sensitive actions (sending emails, creating events) require confirmation.

### 6. Running the Web UI
```sh
streamlit run app.py
```
- Chat with Jarvis in your browser.
- View logs and tool call details.

### 7. Running with Docker
Build and run the container:
```sh
docker build -t jarvis-assistant .
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=... \
  -e TOKEN_PICKLE_B64=$(base64 < token.pickle) \
  jarvis-assistant
```
- The container runs the Flask webhook for Gmail Pub/Sub by default.
- Mount credentials and contacts as needed.

### 8. Gmail Push Notifications (Optional)
- Set up a Google Pub/Sub topic and subscription for Gmail push notifications.
- Deploy `setup_gmail_pubsub.py` (Flask app) and configure Gmail to send notifications to `/gmail-webhook`.
- See Google documentation for [Gmail push setup](https://developers.google.com/gmail/api/guides/push).

## How It Works
- **Email Polling:** Jarvis regularly checks for new unread emails. When a new email arrives, it is processed and, if relevant, triggers scheduling or task actions.
- **Scheduling:** When asked to schedule a meeting, Jarvis checks your calendar for conflicts, proposes alternatives if needed, and sends invites/emails to contacts.
- **Task Management:** Add, list, and complete Google Tasks via chat or CLI.
- **Contacts:** All scheduling uses the `contacts.json` file to resolve names to emails.
- **Human-in-the-Loop:** For sensitive actions, Jarvis asks for your confirmation before proceeding.

## Developer Notes
- **Modular Tools:** All Google API interactions are in `tools/` for easy extension.
- **Credentials:** Never commit your real credentials or tokens. Use environment variables and `.env` files for secrets.
- **Experimental Voice Assistant:** `ELEVEN_LABS_TEST.Py` demonstrates voice input (Whisper) and output (ElevenLabs TTS). Requires extra dependencies and API keys.
- **Testing Webhooks:** Use `local_agent_webhook.py` to simulate incoming emails for local development.
- **Extending:** Add new tools in `tools/` and register their schemas in `main.py` and `app.py`.

## Dependencies
See `requirements.txt` and `pyproject.toml` for a full list. Key packages:
- `flask`, `streamlit` (web UI & webhooks)
- `google-api-python-client`, `google-auth-oauthlib` (Google APIs)
- `openai`, `langfuse` (AI models)
- `python-dotenv` (env management)
- `pyaudio`, `noisereduce`, `elevenlabs` (voice assistant, optional)

## License
This project is for demonstration and hackathon purposes. Please review and adapt for production use.
