def process_new_email_tool(email_data):
    """
    Tool for the agent to process a new email and decide what to do.
    """
    sender = email_data['from']
    subject = email_data['subject']
    body = email_data['body']
    # The agent can now use its other tools (list_events, create_event, etc.)
    # to reason about what to do.
    # You can return a summary or just pass the email content to the agent.
    return {
        "sender": sender,
        "subject": subject,
        "body": body
    }

def get_process_new_email_schema():
    return {
        "name": "process_new_email",
        "description": "Process a new email and intelligently determine required actions. For rescheduling requests from contacts: check calendar availability using list_events, propose alternative times, and await user confirmation before updating. For meeting confirmations: notify user without requiring action. Handle scheduling conflicts, calendar updates, and meeting coordination while keeping user informed of all changes and requests. Integrate with calendar and email tools as needed based on email content and context.",
        "parameters": {
            "type": "object",
            "properties": {
                "email_data": {
                    "type": "object",
                    "properties": {
                        "from": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["from", "subject", "body"]
                }
            },
            "required": ["email_data"]
        }
    }