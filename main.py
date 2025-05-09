# Imports
import json
from langfuse.openai import openai
from tools.calendar_tools import list_events, create_event, get_list_events_schema, get_create_event_schema
from tools.mail_tools import list_emails, send_email, get_list_emails_schema, get_send_email_schema
from tools.todos_tools import list_tasks, add_task, complete_task, get_list_tasks_schema, get_add_task_schema, get_complete_task_schema

# System prompt describing the agent's capabilities
SYSTEM_PROMPT = (
    "You are a smart AI scheduling assistant. "
    "You can read and manage the user's Google Calendar and Gmail, send and read emails, "
    "schedule meetings with others, propose new times if there is a conflict, and handle replies. "
    "You can also manage the user's Google Tasks. "
    "When asked to schedule a meeting, always check the user's calendar for availability, "
    "and if not available, propose the next available slot. "
    "Communicate with other participants via email as needed. "
    "Be proactive, polite, and efficient."
)

# Initial user/system messages
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "Schedule a meeting with Mahmoud at 3:30pm today."}
]

TOOLS = [
    {"type": "function", "function": get_list_events_schema()},
    {"type": "function", "function": get_create_event_schema()},
    {"type": "function", "function": get_list_emails_schema()},
    {"type": "function", "function": get_send_email_schema()},
    {"type": "function", "function": get_list_tasks_schema()},
    {"type": "function", "function": get_add_task_schema()},
    {"type": "function", "function": get_complete_task_schema()}
]

openai.langfuse_auth_check()

response = openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages,
    tools=TOOLS,
)
msg = response.choices[0].message

while hasattr(msg, "tool_calls") and msg.tool_calls:
    tool_outputs = []
    for tool_call in msg.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        if function_name == "list_events":
            result = list_events(**arguments)
        elif function_name == "create_event":
            result = create_event(**arguments)
        elif function_name == "list_emails":
            result = list_emails(**arguments)
        elif function_name == "send_email":
            result = send_email(**arguments)
        elif function_name == "list_tasks":
            result = list_tasks(**arguments)
        elif function_name == "add_task":
            result = add_task(**arguments)
        elif function_name == "complete_task":
            result = complete_task(**arguments)
        else:
            result = {"error": "Unknown tool"}
        tool_outputs.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": function_name,
            "content": json.dumps(result)
        })
    # Add tool outputs to the conversation
    messages.append(msg)
    messages.extend(tool_outputs)
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        tools=TOOLS,
    )
    msg = response.choices[0].message
    # If no more tool calls, break
    if not (hasattr(msg, "tool_calls") and msg.tool_calls):
        break

# Print the final message from the agent
if hasattr(msg, "content") and msg.content:
    print(msg.content)