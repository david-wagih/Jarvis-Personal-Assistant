"""
System Configuration
Handles system setup, contacts, prompts, configuration management, and environment variables.
"""

import json
import os
import sys
from datetime import datetime
import pytz
from typing import List, Dict, Any
from dotenv import load_dotenv
from google.oauth2 import service_account

class SystemConfig:
    def __init__(self):
        # Load environment variables
        self._load_environment_variables()
        
        # Initialize timezone and date
        self.cairo_tz = pytz.timezone('Africa/Cairo')
        self.current_date = datetime.now(self.cairo_tz).strftime("%Y-%m-%d")
        
        # Load contacts and create system prompt
        self.contacts = self._load_contacts()
        self.contacts_str = self._format_contacts()
        self.system_prompt = self._create_system_prompt()
        
        # Initialize Google API scopes
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        
    def _load_environment_variables(self):
        """Load environment variables from .env file."""
        # Try multiple possible paths for .env file
        env_paths = [
            '../.env',  # When running from agent directory
            '.env',     # When running from root directory
            os.path.join(os.path.dirname(__file__), '..', '.env'),  # Absolute path
        ]

        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path)
                break
        
        # Load configuration variables
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        if not self.openai_key:
            print("WARNING: OPENAI_API_KEY not found in environment variables")
            print(f"Available environment variables: {list(os.environ.keys())}")
        else:
            print(f"OpenAI API key loaded successfully (length: {len(self.openai_key)})")
            
        self.google_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        self.google_calendar_delegated_user = os.environ.get("GOOGLE_CALENDAR_DELEGATED_USER")
        
    def _load_contacts(self) -> List[Dict[str, str]]:
        """Load contacts from contacts.json file."""
        contacts_path = os.path.join(os.path.dirname(__file__), 'contacts.json')
        try:
            with open(contacts_path, 'r') as f:
                return json.load(f)['contacts']
        except FileNotFoundError:
            print(f"Warning: contacts.json not found at {contacts_path}")
            return []
        except json.JSONDecodeError:
            print("Warning: Invalid JSON in contacts.json")
            return []
    
    def _format_contacts(self) -> str:
        """Format contacts for the system prompt."""
        return "\n".join([f"- {c['name']}: {c['email']}" for c in self.contacts])
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt with current date and contacts."""
        return (
            f"The current date is: {self.current_date}. "
            "You are Jarvis, a proactive AI assistant for David. "
            "You help manage David's emails, upcoming calendar events, and todos. "
            "You can read, summarize, and send emails, and manage Google Tasks. "
            "When David asks to schedule a meeting with a friend in his Contacts list, "
            "you must always first check David's calendar for availability at the requested time using the list_events tool. "
            "If David is available, create a calendar event and send a calendar invitation email to the friend. "
            "If David is not available, propose the next available time slot and repeat the process as needed. "
            "You always use the Contacts list to resolve names to email addresses. "
            "Here is the Contacts list (name: email):\n" + self.contacts_str + "\n" 
            "IMPORTANT: David is located in Cairo, Egypt (UTC+2). When scheduling events, always interpret times as Cairo time. "
            "For example, if David says '10pm', interpret it as 10:00 PM Cairo time (UTC+2), not UTC. "
            "Convert all times to RFC3339 format with the correct Cairo timezone offset (+03:00). "
            "When creating events, use format like '2025-09-02T22:00:00+03:00' for 10:00 PM Cairo time. "
            "You are efficient, polite, and always keep David informed of any changes or confirmations. "
            "You never double-book David and always respect his existing commitments. "
            "You can also help David by summarizing his inbox, upcoming events, and pending todos. "
            "Be proactive, helpful, and act as a true personal assistant. "
            "When you receive a new email, you should always use the process_new_email tool to analyze and act upon the email content as needed."
        )
    
    def get_system_prompt(self) -> str:
        """Get the current system prompt."""
        return self.system_prompt
    
    def get_openai_key(self) -> str:
        """Get the OpenAI API key."""
        return self.openai_key
    
    def get_google_credentials(self):
        """Get Google service account credentials."""
        if not self.google_credentials:
            print("ERROR: GOOGLE_APPLICATION_CREDENTIALS is not set in the environment or .env file.")
            sys.exit(1)
        if not os.path.isfile(self.google_credentials):
            print(f"ERROR: Service account file '{self.google_credentials}' does not exist.")
            sys.exit(1)
        try:
            with open(self.google_credentials, 'r') as f:
                data = json.load(f)
            for field in ["client_email", "private_key", "token_uri"]:
                if field not in data:
                    print(f"ERROR: Service account file is missing required field: {field}")
                    sys.exit(1)
        except Exception as e:
            print(f"ERROR: Failed to read or parse service account file: {e}")
            sys.exit(1)
        credentials = service_account.Credentials.from_service_account_file(
            self.google_credentials, scopes=self.scopes
        ).with_subject(self.google_calendar_delegated_user)
        return credentials

