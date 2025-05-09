from googleapiclient.discovery import build
from tools.oauth_integration import get_credentials  # Reuse your OAuth helper

def list_tasks(tasklist_id='@default'):
    creds = get_credentials()
    service = build('tasks', 'v1', credentials=creds)
    results = service.tasks().list(tasklist=tasklist_id, showCompleted=True).execute()
    return results.get('items', [])

def add_task(title, tasklist_id='@default'):
    creds = get_credentials()
    service = build('tasks', 'v1', credentials=creds)
    task = {'title': title}
    result = service.tasks().insert(tasklist=tasklist_id, body=task).execute()
    return result

def complete_task(task_id, tasklist_id='@default'):
    creds = get_credentials()
    service = build('tasks', 'v1', credentials=creds)
    task = service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
    task['status'] = 'completed'
    result = service.tasks().update(tasklist=tasklist_id, task=task_id, body=task).execute()
    return result

# Example OpenAI function schema for listing tasks
def get_list_tasks_schema():
    return {
        "name": "list_tasks",
        "description": "List all tasks in a Google Tasks list.",
        "parameters": {
            "type": "object",
            "properties": {
                "tasklist_id": {
                    "type": "string",
                    "description": "The ID of the task list (default: '@default')."
                }
            },
            "required": []
        }
    }