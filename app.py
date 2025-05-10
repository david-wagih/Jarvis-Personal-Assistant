import streamlit as st
import json
from main import SYSTEM_PROMPT, TOOLS, list_events, create_event, list_emails, send_email, list_tasks, add_task, complete_task, process_new_email_tool, update_event
from langfuse.openai import openai
import datetime
import pytz
from datetime import datetime

from tools.calendar_tools import delete_event

st.set_page_config(page_title="Jarvis Assistant", page_icon="🤖")

st.title("🤖 Jarvis - Your AI Assistant")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
if "logs" not in st.session_state:
    st.session_state.logs = []

# Chat input
user_input = st.chat_input("Type your message for Jarvis...")

def handle_tool_calls(msg):
    logs = []
    while hasattr(msg, "tool_calls") and msg.tool_calls:
        result = None  # Set a default value
        for tool_call in msg.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            logs.append(f"Calling tool: {function_name} with arguments: {arguments}")
            # Example: handle add_task tool
            if function_name == "add_task":
                result = add_task(**arguments)
            elif function_name == "complete_task":
                result = complete_task(**arguments)
            elif function_name == "list_tasks":
                result = list_tasks(**arguments)
                # If result is empty, return a friendly message
                if isinstance(result, list) and len(result) == 0:
                    result = "You have no tasks to complete."
            elif function_name == "list_events":
                result = list_events(**arguments)
                # If result is empty, return a friendly message
                if isinstance(result, list) and len(result) == 0:
                    result = "You have no upcoming events in your calendar."
            elif function_name == "create_event":
                result = create_event(**arguments)
            elif function_name == "list_emails":
                result = list_emails(**arguments)
            elif function_name == "send_email":
                result = send_email(**arguments)
            elif function_name == "process_new_email":
                result = process_new_email_tool(**arguments)
            elif function_name == "update_event":
                result = update_event(**arguments)
            elif function_name == "delete_event":
                result = delete_event(**arguments)
            else:
                result = f"Tool {function_name} not implemented in UI."
            logs.append(f"Tool result: {result}")
        # Only append a message if result is not None
        if result is not None:
            st.session_state.messages.append({"role": "assistant", "content": str(result)})
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            tools=TOOLS,
        )
        msg = response.choices[0].message
    return msg, logs

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Jarvis is thinking..."):
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            tools=TOOLS,
        )
        msg = response.choices[0].message
        logs = []
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            msg, logs = handle_tool_calls(msg)
        st.session_state.messages.append({"role": "assistant", "content": msg.content})
        st.session_state.logs.extend(logs)

# Display chat history
for m in st.session_state.messages:
    if m["role"] == "user":
        st.chat_message("user").write(m["content"])
    elif m["role"] == "assistant":
        st.chat_message("assistant").write(m["content"])

# Display logs
with st.expander("Logs / Tool Calls", expanded=False):
    for log in st.session_state.logs:
        st.write(log)

def check_for_new_emails():
    today = datetime.datetime.now().strftime('%Y/%m/%d')
    gmail_query = f'is:unread after:{today}'
    unread_emails = list_emails(query=gmail_query, max_results=50)
    logs = []
    for email in unread_emails.get('emails', []):
        email_prompt = (
            f"You received a new email from {email['from']}. Subject: {email['subject']}. Body: {email['body']}. "
            "If this is a reschedule request, find the relevant event and update it accordingly. "
            "Always confirm with the user before making changes."
        )
        st.session_state.messages.append({"role": "user", "content": email_prompt})
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            tools=TOOLS,
        )
        msg = response.choices[0].message
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            msg, tool_logs = handle_tool_calls(msg)
            logs.extend(tool_logs)
        st.session_state.messages.append({"role": "assistant", "content": msg.content})
    return logs

if st.button("Check for New Emails"):
    logs = check_for_new_emails()
    st.session_state.logs.extend(logs)

cairo = pytz.timezone('Africa/Cairo')
start_time = cairo.localize(datetime(2025, 5, 10, 17, 0, 0))
start_time_iso = start_time.isoformat()