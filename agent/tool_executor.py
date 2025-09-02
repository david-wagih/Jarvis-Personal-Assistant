"""
Tool Executor
Handles tool calling, execution, and result processing.
"""

import json
from typing import Dict, Any, List, Optional
from tools.calendar_tools import list_events, create_event, update_event, delete_event
from tools.mail_tools import list_emails, send_email, mark_email_as_read
from tools.todos_tools import list_tasks, add_task, complete_task
from tools.process_new_emails_tools import process_new_email_tool

class ToolExecutor:
    def __init__(self, require_confirmation: bool = True):
        self.require_confirmation = require_confirmation
        
    def execute_tool(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with the given arguments."""
        try:
            if function_name == "list_events":
                result = list_events(**arguments)
            elif function_name == "create_event":
                result = self._execute_create_event(arguments)
            elif function_name == "list_emails":
                result = list_emails(**arguments)
            elif function_name == "send_email":
                result = self._execute_send_email(arguments)
            elif function_name == "list_tasks":
                result = list_tasks(**arguments)
            elif function_name == "add_task":
                result = add_task(**arguments)
            elif function_name == "complete_task":
                result = complete_task(**arguments)
            elif function_name == "process_new_email":
                result = process_new_email_tool(**arguments)
            elif function_name == "update_event":
                result = self._execute_update_event(arguments)
            elif function_name == "delete_event":
                result = delete_event(**arguments)
            else:
                result = {"error": f"Unknown tool: {function_name}"}
                
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    def _execute_create_event(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute create_event with guest email handling."""
        result = create_event(**arguments)
        
        # Send emails to guests if event was created successfully
        guests = arguments.get("guests")
        if guests and result and result.get("status") == "confirmed":
            self._send_meeting_invitations(arguments, guests, "Scheduled")
            
        return result
    
    def _execute_update_event(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute update_event with guest email handling."""
        result = update_event(**arguments)
        
        # Check if update was successful
        if isinstance(result, dict) and "error" in result:
            print(f"Failed to update event: {result['error']}")
            return result
        
        # Send emails to guests if event was updated successfully
        guests = arguments.get("guests")
        if guests and result:
            self._send_meeting_invitations(arguments, guests, "Updated")
            
        return result
    
    def _execute_send_email(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute send_email with confirmation if required."""
        if self.require_confirmation:
            confirm = input(f"Do you want to proceed with send email? (yes/no): ").strip().lower()
            if confirm != "yes":
                return {"status": "cancelled", "reason": "User declined confirmation."}
        
        return send_email(**arguments)
    
    def _send_meeting_invitations(self, arguments: Dict[str, Any], guests: List[str], action: str):
        """Send meeting invitations to guests."""
        subject = f"Meeting {action}: {arguments.get('summary', 'No Title')}"
        start = arguments.get('start', '')
        end = arguments.get('end', '')
        
        for guest_email in guests:
            message_text = f"Hi,\n\nYou have been invited to a meeting.\n\nSummary: {arguments.get('summary', 'No Title')}\nStart: {start}\nEnd: {end}\n\nBest regards,\nDavid"
            send_email(to=guest_email, subject=subject, message_text=message_text)
    
    def process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple tool calls and return results."""
        tool_outputs = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            
            result = self.execute_tool(function_name, arguments)
            
            tool_outputs.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(result)
            })
            
        return tool_outputs
