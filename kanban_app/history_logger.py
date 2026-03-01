import os
import datetime
from django.conf import settings

HISTORY_DIR = os.path.join(settings.BASE_DIR, "task_history")


def get_history_file_path(project_id: int) -> str:
    """Returns the path to the task history file for the given project"""
    return os.path.join(HISTORY_DIR, f"project_{project_id}.txt")


def log_task_change(project_id: int, username: str, task_title: str, action: str):
    """Appends a task modifications record to the project's task history file"""
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)

    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Format: date -> username -> subject -> object
    line = f"{date_str} -> {username} -> {task_title} -> {action}\n"

    with open(get_history_file_path(project_id), "a") as f:
        f.write(line)
