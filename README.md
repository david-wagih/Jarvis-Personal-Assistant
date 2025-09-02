# Jarvis: Intelligent AI Personal Assistant

## Overview
Jarvis is an intelligent AI personal assistant that proactively manages emails, Google Calendar events, and Google Tasks. Built with OpenAI's GPT models and Google APIs, Jarvis provides a conversational interface for scheduling, email management, and task automation with human-in-the-loop confirmation for sensitive actions.

## 🚀 Key Features

### **Intelligent Email Processing**
- **Proactive Email Monitoring**: Automatically detects and processes new unread emails
- **Smart Email Analysis**: Analyzes email content to determine appropriate actions (reschedule requests, new meetings, cancellations, confirmations)
- **Automatic Response**: Handles email-based requests without manual intervention
- **Email Marking**: Automatically marks processed emails as read

### **Smart Calendar Management**
- **Availability Checking**: Always checks calendar availability before scheduling meetings
- **Timezone Awareness**: Properly handles Cairo timezone (UTC+2) for all scheduling
- **Conflict Prevention**: Prevents double-booking by checking existing commitments
- **Meeting Updates**: Handles reschedule requests by updating existing events
- **Guest Management**: Automatically sends calendar invitations to meeting participants

### **Task Management**
- **Google Tasks Integration**: List, add, and complete tasks
- **Task Organization**: Manage tasks across different task lists
- **Task Status Tracking**: Mark tasks as completed with status updates

### **Contact Management**
- **Local Contact Resolution**: Uses `contacts.json` to resolve names to email addresses
- **Automatic Guest Invitations**: Sends meeting invitations to contacts automatically
- **Contact Validation**: Ensures all scheduling uses verified contact information

### **Conversational Interface**
- **ChatGPT-like Experience**: Clean, minimal output without verbose logging
- **Natural Language Processing**: Understands natural language requests for scheduling
- **Context Awareness**: Maintains conversation context across interactions
- **Human-in-the-Loop**: Requires confirmation for sensitive actions (emails, calendar changes)

## 🏗️ Architecture

### **Core Components**
- **`main.py`**: Main CLI interface with email polling and conversation loop
- **`config.py`**: Environment configuration and API key management
- **`tools/`**: Modular tool system for different functionalities
  - `calendar_tools.py`: Google Calendar operations
  - `mail_tools.py`: Gmail operations
  - `todos_tools.py`: Google Tasks operations
  - `oauth_integration.py`: Google OAuth authentication
  - `process_new_emails_tools.py`: Email processing logic
  - `gmail_watch_tools.py`: Gmail webhook setup

### **Configuration Files**
- **`contacts.json`**: Contact list for name-to-email resolution
- **`credentials_oauth.json`**: Google OAuth credentials
- **`service_account.json`**: Google Service Account for calendar operations
- **`.env`**: Environment variables (API keys, configuration)

### **Authentication & Security**
- **OAuth 2.0**: Secure Google API authentication
- **Token Management**: Automatic token refresh and storage
- **Service Account**: Delegated access for calendar operations
- **Environment Variables**: Secure API key management

## 🛠️ Setup Instructions

### **1. Prerequisites**
- Python 3.13+
- Google Cloud Project with APIs enabled
- OpenAI API key
- Google OAuth credentials

### **2. Installation**
```bash
# Clone the repository
git clone <repository-url>
cd Jarvis-Personal-Assistant

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **3. Configuration**

#### **Environment Setup**
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=service_account.json
GOOGLE_CALENDAR_DELEGATED_USER=your_email@gmail.com
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

#### **Google API Setup**
1. **OAuth Credentials**: Place `credentials_oauth.json` in the agent directory
2. **Service Account**: Place `service_account.json` in the agent directory
3. **First Run**: Execute `python main.py` to authenticate and generate `token.pickle`

#### **Contact Configuration**
Edit `agent/contacts.json`:
```json
{
  "contacts": [
    {
      "name": "Mahmoud Gamil",
      "email": "mahmoudgamiel28@gmail.com"
    },
    {
      "name": "Ahmed Shehata", 
      "email": "ahmedshehata20047@gmail.com"
    },
    {
      "name": "David Wagih",
      "email": "davidwagih62@gmail.com"
    }
  ]
}
```

### **4. Running Jarvis**

#### **Command Line Interface**
```bash
cd agent
python main.py
```

#### **Docker Deployment**
```bash
# Build the container
docker build -t jarvis-assistant .

# Run with environment variables
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your_key \
  -e TOKEN_PICKLE_B64=$(base64 < token.pickle) \
  jarvis-assistant
```

## 💬 Usage Examples

### **Scheduling Meetings**
```
User: "Schedule a meeting with Mahmoud at 3pm today"
Jarvis: [Checks availability] "I've scheduled a meeting with Mahmoud at 3:00 PM Cairo time. Mahmoud has been invited."
```

### **Email Processing**
```
[Email arrives]: "Can we push the meeting to tomorrow at the same time?"
Jarvis: [Automatically processes] "I've updated the meeting to tomorrow at the same time."
```

### **Task Management**
```
User: "Add a task to review the project proposal"
Jarvis: "I've added the task 'review the project proposal' to your task list."
```

### **Calendar Queries**
```
User: "What meetings do I have today?"
Jarvis: "You have a meeting with David today from 11:00 PM to 12:00 AM Cairo time."
```

## 🔧 Technical Implementation

### **Email Processing Flow**
1. **Polling**: Background thread checks for new unread emails every 30 seconds
2. **Analysis**: AI analyzes email content to determine action type
3. **Tool Selection**: Appropriate tools are called based on email content
4. **Execution**: Actions are performed automatically (with error handling)
5. **Notification**: User is informed of completed actions

### **Scheduling Logic**
1. **Availability Check**: `list_events` tool checks calendar for conflicts
2. **Timezone Handling**: All times converted to Cairo timezone (+03:00)
3. **Event Creation**: `create_event` tool creates calendar events
4. **Guest Invitation**: Automatic email invitations sent to participants
5. **Confirmation**: User receives confirmation with calendar link

### **Error Handling**
- **404 Errors**: Graceful handling of missing events
- **API Failures**: Comprehensive error messages and fallbacks
- **Timezone Issues**: Proper Cairo timezone conversion
- **Network Problems**: Retry logic for API calls

## 🔒 Security Features

### **Authentication**
- **OAuth 2.0**: Secure Google API access
- **Token Refresh**: Automatic token renewal
- **Service Account**: Delegated calendar access

### **Data Protection**
- **Environment Variables**: Secure API key storage
- **Local Storage**: Credentials stored locally only
- **No Hardcoding**: No sensitive data in code

### **User Control**
- **Confirmation Required**: User approval for sensitive actions
- **Audit Trail**: All actions logged and visible
- **Manual Override**: User can cancel any automated action

## 📊 Monitoring & Logging

### **Activity Tracking**
- **Email Processing**: Logs of processed emails and actions taken
- **Calendar Changes**: Records of created/updated/deleted events
- **Task Management**: Tracking of task operations
- **Error Logging**: Comprehensive error reporting

### **Performance Metrics**
- **Response Time**: Tool execution timing
- **Success Rates**: API call success tracking
- **User Interactions**: Conversation flow monitoring

## 🚀 Advanced Features

### **Proactive Assistance**
- **Email Monitoring**: Automatic processing of incoming emails
- **Smart Suggestions**: AI-driven recommendations for scheduling
- **Conflict Resolution**: Automatic handling of scheduling conflicts

### **Intelligent Processing**
- **Context Awareness**: Maintains conversation context
- **Natural Language**: Understands various ways to express requests
- **Error Recovery**: Graceful handling of edge cases

### **Extensibility**
- **Modular Tools**: Easy to add new functionalities
- **Plugin Architecture**: Tool-based system for easy extension
- **API Integration**: Ready for additional service integrations

## 🔧 Development

### **Adding New Tools**
1. Create new tool file in `tools/` directory
2. Implement tool function and schema
3. Add to `TOOLS` list in `main.py`
4. Update documentation

### **Testing**
- **Local Testing**: Use `local_agent_webhook.py` for email simulation
- **API Testing**: Individual tool testing available
- **Integration Testing**: Full workflow testing

### **Deployment**
- **Docker**: Containerized deployment ready
- **Environment Variables**: Secure configuration management
- **Scaling**: Designed for horizontal scaling

## 📝 Dependencies

### **Core Dependencies**
- `openai`: AI model integration
- `langfuse`: AI observability
- `google-api-python-client`: Google APIs
- `google-auth-oauthlib`: OAuth authentication
- `python-dotenv`: Environment management

### **Optional Dependencies**
- `pyaudio`: Voice input (experimental)
- `elevenlabs`: Text-to-speech (experimental)
- `streamlit`: Web UI (if needed)

## 🤝 Contributing

### **Code Structure**
- **Modular Design**: Tools are independent and reusable
- **Clear Interfaces**: Well-defined tool schemas
- **Error Handling**: Comprehensive error management
- **Documentation**: Inline code documentation

### **Best Practices**
- **Environment Variables**: Use for all sensitive data
- **Error Handling**: Graceful degradation
- **Logging**: Comprehensive activity tracking
- **Testing**: Test new features thoroughly

## 📄 License

This project is developed for demonstration and personal use. Please review and adapt for production environments.

---

**Jarvis** - Your intelligent personal assistant for email, calendar, and task management.
