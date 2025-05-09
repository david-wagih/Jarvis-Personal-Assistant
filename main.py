# Imports
import json
from langfuse.openai import openai
from config import get_openai_key
from tools.calendar_tools import list_events, get_list_events_schema
from tools.mail_tools import list_emails, get_list_emails_schema

# Initial user/system messages
messages = [
    {"role": "system", "content": "You are an assistant that can read my mail and calendar."},
    {"role": "user", "content": "Show me my next 3 calendar events and unread emails."}
]

TOOLS = [
    {"type": "function", "function": get_list_events_schema()},
    {"type": "function", "function": get_list_emails_schema()}
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
        elif function_name == "list_emails":
            result = list_emails(**arguments)
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