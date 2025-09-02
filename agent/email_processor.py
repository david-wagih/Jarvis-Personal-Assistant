"""
Email Processor
Handles email polling, processing, and proactive email handling.
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any
from tools.mail_tools import list_emails, mark_email_as_read
from tools.process_new_emails_tools import process_new_email_tool

class EmailProcessor:
    def __init__(self, conversation_manager, tool_executor):
        self.conversation_manager = conversation_manager
        self.tool_executor = tool_executor
        
    def fetch_and_clear_new_emails(self) -> List[Dict[str, Any]]:
        """Fetch and clear new emails from the webhook storage."""
        if not os.path.exists("new_emails.json"):
            return []
            
        with open("new_emails.json", "r") as f:
            emails = json.load(f)
            
        # Clear the file
        with open("new_emails.json", "w") as f:
            json.dump([], f)
            
        return emails
    
    def poll_unread_emails(self, interval: int = 60):
        """Poll for unread emails and process them."""
        while True:
            try:
                # Get today's date in YYYY/MM/DD format
                today = datetime.now().strftime('%Y/%m/%d')
                # Gmail query: unread emails after today 00:00
                gmail_query = f'is:unread after:{today}'
                unread_emails = list_emails(query=gmail_query, max_results=50)
                
                for email in unread_emails.get('emails', []):
                    self._process_single_email(email)
                    
                time.sleep(interval)
                
            except Exception as e:
                print(f"Polling error: {e}")
                time.sleep(interval)
    
    def _process_single_email(self, email: Dict[str, Any]):
        """Process a single email."""
        print(f"\n[Polling] New unread email from {email['from']}: {email['subject']}")
        
        # Process the email
        result = process_new_email_tool({
            'from': email.get('from', ''),
            'subject': email.get('subject', ''),
            'body': email.get('body', '')
        })
        print(f"Processed new email: {result}")
        
        # Mark email as read
        mark_email_as_read(email['id'])
        print(f"Marked email {email['id']} as read.")
        
        # Process email proactively
        self._process_email_proactively(email)
    
    def _process_email_proactively(self, email: Dict[str, Any]):
        """Process email proactively using the AI agent."""
        email_prompt = self._create_email_prompt(email)
        
        # Add to conversation
        self.conversation_manager.add_user_message(email_prompt)
        
        # Get AI response
        msg = self.conversation_manager.create_chat_completion()
        
        # Process tool calls
        while hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_outputs = self.tool_executor.process_tool_calls(msg.tool_calls)
            
            # Add messages to conversation
            self.conversation_manager.messages.append(msg)
            for tool_output in tool_outputs:
                self.conversation_manager.add_tool_message(
                    tool_output["tool_call_id"],
                    tool_output["name"],
                    tool_output["content"]
                )
            
            # Get next response
            msg = self.conversation_manager.create_chat_completion()
            
            if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                break
        
        # Add final message
        self.conversation_manager.messages.append(msg)
        
        # Print response
        if hasattr(msg, "content") and msg.content:
            print("\n--- Final Assistant Message (Proactive Email) ---")
            print(msg.content)
    
    def _create_email_prompt(self, email: Dict[str, Any]) -> str:
        """Create a prompt for email processing."""
        return (
            f"You received a new email from {email['from']}. Subject: {email['subject']}. Body: {email['body']}. "
            "ANALYZE THE EMAIL CONTENT AND TAKE APPROPRIATE ACTION: "
            "1. If it's a reschedule request: FIRST use list_events to find the existing meeting, THEN use update_event to modify it "
            "2. If it's a new meeting request: check availability and create if possible "
            "3. If it's a cancellation: find and delete the meeting "
            "4. If it's a confirmation: acknowledge and mark as confirmed "
            "5. If it's a general inquiry: respond appropriately "
            "6. Always use the correct tools (list_events, create_event, update_event, delete_event, send_email) "
            "7. Always confirm with the user before making any calendar changes "
            "8. Use the exact details mentioned in the email (names, times, dates) "
            "9. For reschedule requests: ALWAYS find the existing meeting first, NEVER create a new one "
            "10. If the email says 'push to next day', find today's meeting and move it to tomorrow"
        )
    
    def process_webhook_emails(self):
        """Process emails from webhook storage."""
        new_emails = self.fetch_and_clear_new_emails()
        
        for email in new_emails:
            email_prompt = (
                f"You received a new email from {email['from']}. Subject: {email['subject']}. Body: {email['body']}. "
                "If this is a reschedule request, find the relevant event and update it accordingly. "
                "Always confirm with the user before making changes."
            )
            
            print(f"\n[Proactive] {email_prompt}")
            self.conversation_manager.add_user_message(email_prompt)
            
            # Get AI response
            msg = self.conversation_manager.create_chat_completion()
            
            # Process tool calls
            while hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_outputs = self.tool_executor.process_tool_calls(msg.tool_calls)
                
                # Add messages to conversation
                self.conversation_manager.messages.append(msg)
                for tool_output in tool_outputs:
                    self.conversation_manager.add_tool_message(
                        tool_output["tool_call_id"],
                        tool_output["name"],
                        tool_output["content"]
                    )
                
                # Get next response
                msg = self.conversation_manager.create_chat_completion()
                
                if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                    break
            
            # Add final message
            self.conversation_manager.messages.append(msg)
            
            # Print response
            if hasattr(msg, "content") and msg.content:
                print("\n--- Final Assistant Message (Proactive Email) ---")
                print(msg.content)
