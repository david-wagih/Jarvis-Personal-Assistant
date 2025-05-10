# Imports
import json
from langfuse.openai import openai
from tools.calendar_tools import get_update_event_schema, list_events, create_event, get_list_events_schema, get_create_event_schema, update_event
from tools.mail_tools import list_emails, mark_email_as_read, send_email, get_list_emails_schema, get_send_email_schema
from tools.process_new_emails_tools import get_process_new_email_schema, process_new_email_tool
from tools.todos_tools import list_tasks, add_task, complete_task, get_list_tasks_schema, get_add_task_schema, get_complete_task_schema
from tools.oauth_integration import get_credentials  
from datetime import datetime
import threading
import time

# Load contacts
with open('contacts.json', 'r') as f:
    CONTACTS = json.load(f)['contacts']

# Format contacts for prompt
contacts_str = "\n".join([f"- {c['name']}: {c['email']}" for c in CONTACTS])

# System prompt for Jarvis assistant
current_date = datetime.now().strftime("%Y-%m-%d")
SYSTEM_PROMPT = (
    f"The current date is: {current_date}. "
    "You are Jarvis, a proactive AI assistant for David. "
    "You help manage David's emails, upcoming calendar events, and todos. "
    "You can read, summarize, and send emails, and manage Google Tasks. "
    "When David asks to schedule a meeting with a friend in his Contacts list, "
    "you must always first check David's calendar for availability at the requested time using the list_events tool. "
    "If David is available, create a calendar event and send a calendar invitation email to the friend. "
    "If David is not available, propose the next available time slot and repeat the process as needed. "
    "You always use the Contacts list to resolve names to email addresses. "
    "Here is the Contacts list (name: email):\n" + contacts_str + "\n" 
    "You are efficient, polite, and always keep David informed of any changes or confirmations. "
    "You never double-book David and always respect his existing commitments. "
    "You can also help David by summarizing his inbox, upcoming events, and pending todos. "
    "Be proactive, helpful, and act as a true personal assistant. "
    "When you receive a new email, you should always use the process_new_email tool to analyze and act upon the email content as needed."
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
    {"type": "function", "function": get_complete_task_schema()},
    {"type": "function", "function": get_process_new_email_schema()},
    {"type": "function", "function": get_update_event_schema()}
]

def fetch_and_clear_new_emails():
    import os
    import json
    if not os.path.exists("new_emails.json"):
        return []
    with open("new_emails.json", "r") as f:
        emails = json.load(f)
    # Clear the file
    with open("new_emails.json", "w") as f:
        json.dump([], f)
    return emails

def poll_unread_emails(process_new_email_tool, interval=60):
    from datetime import datetime
    while True:
        try:
            # Get today's date in YYYY/MM/DD format
            today = datetime.now().strftime('%Y/%m/%d')
            # Gmail query: unread emails after today 00:00
            gmail_query = f'is:unread after:{today}'
            unread_emails = list_emails(query=gmail_query, max_results=50)
            for email in unread_emails.get('emails', []):
                print(f"\n[Polling] New unread email from {email['from']}: {email['subject']}")
                result = process_new_email_tool({
                    'from': email.get('from', ''),
                    'subject': email.get('subject', ''),
                    'body': email.get('body', '')
                })
                print(f"Processed new email: {result}")
                mark_email_as_read(email['id'])
                print(f"Marked email {email['id']} as read.")

                # --- Inject as user message and run agent proactively ---
                email_prompt = (
                    f"You received a new email from {email['from']}. Subject: {email['subject']}. Body: {email['body']}. "
                    "If this is a reschedule request, find the relevant event and update it accordingly. "
                    "Always confirm with the user before making changes."
                )
                global messages
                messages.append({"role": "user", "content": email_prompt})
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
                        print(f"Calling tool: {function_name} with arguments: {arguments}")

                        # Human-in-the-loop confirmation for sensitive actions
                        if function_name in ["create_event", "send_email"]:
                            confirm = input(f"Do you want to proceed with {function_name.replace('_', ' ')}? (yes/no): ").strip().lower()
                            if confirm != "yes":
                                print(f"{function_name.replace('_', ' ').capitalize()} cancelled by user.")
                                result = {"status": "cancelled", "reason": "User declined confirmation."}
                                tool_outputs.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call.id,
                                    "name": function_name,
                                    "content": json.dumps(result)
                                })
                                continue  # Skip actual function call

                        # Proceed as before for all other tools or if confirmed
                        try:
                            if function_name == "list_events":
                                result = list_events(**arguments)
                            elif function_name == "create_event":
                                result = create_event(**arguments)
                                guests = arguments.get("guests")
                                if guests and result and result.get("status") == "confirmed":
                                    subject = f"Meeting Scheduled: {arguments.get('summary', 'No Title')}"
                                    start = arguments.get('start', '')
                                    end = arguments.get('end', '')
                                    for guest_email in guests:
                                        message_text = f"Hi,\n\nYou have been invited to a meeting.\n\nSummary: {arguments.get('summary', 'No Title')}\nStart: {start}\nEnd: {end}\n\nBest regards,\nDavid"
                                        send_email(to=guest_email, subject=subject, message_text=message_text)
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
                            elif function_name == "process_new_email":
                                result = process_new_email_tool(**arguments)
                            elif function_name == "update_event":
                                result = update_event(**arguments)
                                # After updating an event, if there are guests, send them an email
                                guests = arguments.get("guests")
                                if guests and result and result.get("status", "confirmed") == "confirmed":
                                    subject = f"Meeting Updated: {arguments.get('summary', 'No Title')}"
                                    start = arguments.get('start', '')
                                    end = arguments.get('end', '')
                                    for guest_email in guests:
                                        message_text = f"Hi,\n\nThe meeting has been updated.\n\nSummary: {arguments.get('summary', 'No Title')}\nStart: {start}\nEnd: {end}\n\nBest regards,\nDavid"
                                        send_email(to=guest_email, subject=subject, message_text=message_text)
                            else:
                                result = {"error": "Unknown tool"}
                        except Exception as e:
                            result = {"error": str(e)}
                        print(f"Tool result: {result}")
                        tool_outputs.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": json.dumps(result)
                        })
                    messages.append(msg)
                    messages.extend(tool_outputs)
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        tools=TOOLS,
                    )
                    msg = response.choices[0].message
                    if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                        break

                messages.append(msg)
                if hasattr(msg, "content") and msg.content:
                    print("\n--- Final Assistant Message (Proactive Email) ---")
                    print(msg.content)
            time.sleep(interval)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(interval)

def main():
    openai.langfuse_auth_check()
    get_credentials()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # Start polling thread
    polling_thread = threading.Thread(target=poll_unread_emails, args=(process_new_email_tool, 30), daemon=True)
    polling_thread.start()

    while True:
        user_input = input("What would you like Jarvis to do? ")
        if user_input.strip().lower() in ["thank you", "goodbye"]:
            print("Session ended. Have a great day!")
            break
        messages.append({"role": "user", "content": user_input})
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
                print(f"Calling tool: {function_name} with arguments: {arguments}")

                # Human-in-the-loop confirmation for sensitive actions
                if function_name in ["create_event", "send_email"]:
                    confirm = input(f"Do you want to proceed with {function_name.replace('_', ' ')}? (yes/no): ").strip().lower()
                    if confirm != "yes":
                        print(f"{function_name.replace('_', ' ').capitalize()} cancelled by user.")
                        result = {"status": "cancelled", "reason": "User declined confirmation."}
                        tool_outputs.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": json.dumps(result)
                        })
                        continue  # Skip actual function call

                # Proceed as before for all other tools or if confirmed
                try:
                    if function_name == "list_events":
                        result = list_events(**arguments)
                    elif function_name == "create_event":
                        result = create_event(**arguments)
                        # After creating an event, if there are guests, send them an email
                        guests = arguments.get("guests")
                        if guests and result and result.get("status") == "confirmed":
                            subject = f"Meeting Scheduled: {arguments.get('summary', 'No Title')}"
                            start = arguments.get('start', '')
                            end = arguments.get('end', '')
                            for guest_email in guests:
                                message_text = f"Hi,\n\nYou have been invited to a meeting.\n\nSummary: {arguments.get('summary', 'No Title')}\nStart: {start}\nEnd: {end}\n\nBest regards,\nDavid"
                                send_email(to=guest_email, subject=subject, message_text=message_text)
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
                    elif function_name == "process_new_email":
                        result = process_new_email_tool(**arguments)
                    elif function_name == "update_event":
                        result = update_event(**arguments)
                        # After updating an event, if there are guests, send them an email
                        guests = arguments.get("guests")
                        if guests and result and result.get("status", "confirmed") == "confirmed":
                            subject = f"Meeting Updated: {arguments.get('summary', 'No Title')}"
                            start = arguments.get('start', '')
                            end = arguments.get('end', '')
                            for guest_email in guests:
                                message_text = f"Hi,\n\nThe meeting has been updated.\n\nSummary: {arguments.get('summary', 'No Title')}\nStart: {start}\nEnd: {end}\n\nBest regards,\nDavid"
                                send_email(to=guest_email, subject=subject, message_text=message_text)
                    else:
                        result = {"error": "Unknown tool"}
                except Exception as e:
                    result = {"error": str(e)}
                print(f"Tool result: {result}")
                tool_outputs.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(result)
                })
            messages.append(msg)
            messages.extend(tool_outputs)
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                tools=TOOLS,
            )
            msg = response.choices[0].message
            if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                break

        # Print the full conversation for E2E visibility
        print("\n--- Conversation ---")
        for m in messages:
            role = getattr(m, 'role', None) or (m['role'] if isinstance(m, dict) and 'role' in m else '')
            content = getattr(m, 'content', None) or (m['content'] if isinstance(m, dict) and 'content' in m else '')
            name = getattr(m, 'name', None) or (m['name'] if isinstance(m, dict) and 'name' in m else '')
            if content:
                print(f"{role.upper()}: {content}")
            else:
                print(f"{role.upper()} ({name}): {content}")

        if hasattr(msg, "content") and msg.content:
            print("\n--- Final Assistant Message ---")
            print(msg.content)

        # --- Proactive email processing ---
        new_emails = fetch_and_clear_new_emails()
        for email in new_emails:
            # Convert email to a user message for the agent
            email_prompt = (
                f"You received a new email from {email['from']}. Subject: {email['subject']}. Body: {email['body']}. "
                "If this is a reschedule request, find the relevant event and update it accordingly. "
                "Always confirm with the user before making changes."
            )
            print(f"\n[Proactive] {email_prompt}")
            messages.append({"role": "user", "content": email_prompt})
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
                    print(f"Calling tool: {function_name} with arguments: {arguments}")

                    # Human-in-the-loop confirmation for sensitive actions
                    if function_name in ["create_event", "send_email"]:
                        confirm = input(f"Do you want to proceed with {function_name.replace('_', ' ')}? (yes/no): ").strip().lower()
                        if confirm != "yes":
                            print(f"{function_name.replace('_', ' ').capitalize()} cancelled by user.")
                            result = {"status": "cancelled", "reason": "User declined confirmation."}
                            tool_outputs.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": function_name,
                                "content": json.dumps(result)
                            })
                            continue  # Skip actual function call

                    # Proceed as before for all other tools or if confirmed
                    try:
                        if function_name == "list_events":
                            result = list_events(**arguments)
                        elif function_name == "create_event":
                            result = create_event(**arguments)
                            guests = arguments.get("guests")
                            if guests and result and result.get("status") == "confirmed":
                                subject = f"Meeting Scheduled: {arguments.get('summary', 'No Title')}"
                                start = arguments.get('start', '')
                                end = arguments.get('end', '')
                                for guest_email in guests:
                                    message_text = f"Hi,\n\nYou have been invited to a meeting.\n\nSummary: {arguments.get('summary', 'No Title')}\nStart: {start}\nEnd: {end}\n\nBest regards,\nDavid"
                                    send_email(to=guest_email, subject=subject, message_text=message_text)
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
                        elif function_name == "process_new_email":
                            result = process_new_email_tool(**arguments)
                        elif function_name == "update_event":
                            result = update_event(**arguments)
                            # After updating an event, if there are guests, send them an email
                            guests = arguments.get("guests")
                            if guests and result and result.get("status", "confirmed") == "confirmed":
                                subject = f"Meeting Updated: {arguments.get('summary', 'No Title')}"
                                start = arguments.get('start', '')
                                end = arguments.get('end', '')
                                for guest_email in guests:
                                    message_text = f"Hi,\n\nThe meeting has been updated.\n\nSummary: {arguments.get('summary', 'No Title')}\nStart: {start}\nEnd: {end}\n\nBest regards,\nDavid"
                                    send_email(to=guest_email, subject=subject, message_text=message_text)
                        else:
                            result = {"error": "Unknown tool"}
                    except Exception as e:
                        result = {"error": str(e)}
                    print(f"Tool result: {result}")
                    tool_outputs.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(result)
                    })
                messages.append(msg)
                messages.extend(tool_outputs)
                response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    tools=TOOLS,
                )
                msg = response.choices[0].message
                if not (hasattr(msg, "tool_calls") and msg.tool_calls):
                    break

            messages.append(msg)
            if hasattr(msg, "content") and msg.content:
                print("\n--- Final Assistant Message (Proactive Email) ---")
                print(msg.content)

if __name__ == "__main__":
    main()