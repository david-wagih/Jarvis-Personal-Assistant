"""
Conversation Manager
Handles conversation flow, message management, and user interactions.
"""

import json
from typing import List, Dict, Any
from langfuse.openai import openai
from config import get_openai_key

# Configure OpenAI client with API key
openai.api_key = get_openai_key()
from tools.calendar_tools import get_list_events_schema, get_create_event_schema, get_update_event_schema, get_delete_event_schema
from tools.mail_tools import get_list_emails_schema, get_send_email_schema
from tools.todos_tools import get_list_tasks_schema, get_add_task_schema, get_complete_task_schema
from tools.process_new_emails_tools import get_process_new_email_schema

class ConversationManager:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": ""}
        ]
        self.tools = self._initialize_tools()
        
    def _initialize_tools(self) -> List[Dict[str, Any]]:
        """Initialize all available tools."""
        return [
            {"type": "function", "function": get_list_events_schema()},
            {"type": "function", "function": get_create_event_schema()},
            {"type": "function", "function": get_list_emails_schema()},
            {"type": "function", "function": get_send_email_schema()},
            {"type": "function", "function": get_list_tasks_schema()},
            {"type": "function", "function": get_add_task_schema()},
            {"type": "function", "function": get_complete_task_schema()},
            {"type": "function", "function": get_process_new_email_schema()},
            {"type": "function", "function": get_update_event_schema()},
            {"type": "function", "function": get_delete_event_schema()}
        ]
    
    def add_user_message(self, content: str):
        """Add a user message to the conversation."""
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: str):
        """Add an assistant message to the conversation."""
        self.messages.append({"role": "assistant", "content": content})
    
    def add_tool_message(self, tool_call_id: str, name: str, content: str):
        """Add a tool message to the conversation."""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
            "content": content
        })
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get the current conversation messages."""
        return self.messages
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get the available tools."""
        return self.tools
    
    def create_chat_completion(self, require_confirmation: bool = True):
        """Create a chat completion and return the response."""
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            tools=self.tools,
        )
        return response.choices[0].message
    
    def reset_conversation(self):
        """Reset the conversation to initial state."""
        self.messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": ""}
        ]
