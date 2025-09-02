"""
System Configuration
Handles system setup, contacts, prompts, and configuration management.
"""

import json
import os
from datetime import datetime
import pytz
from typing import List, Dict, Any

class SystemConfig:
    def __init__(self):
        self.cairo_tz = pytz.timezone('Africa/Cairo')
        self.current_date = datetime.now(self.cairo_tz).strftime("%Y-%m-%d")
        self.contacts = self._load_contacts()
        self.contacts_str = self._format_contacts()
        self.system_prompt = self._create_system_prompt()
        
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
    
    def get_contacts(self) -> List[Dict[str, str]]:
        """Get the list of contacts."""
        return self.contacts
    
    def get_contact_email(self, name: str) -> str:
        """Get email address for a contact by name."""
        for contact in self.contacts:
            if contact['name'].lower() == name.lower():
                return contact['email']
        return None
    
    def get_current_date(self) -> str:
        """Get the current date in Cairo timezone."""
        return self.current_date
    
    def refresh_date(self):
        """Refresh the current date (useful for long-running sessions)."""
        self.current_date = datetime.now(self.cairo_tz).strftime("%Y-%m-%d")
        self.system_prompt = self._create_system_prompt()
