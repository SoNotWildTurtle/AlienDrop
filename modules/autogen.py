# MINC - Auto Task Generator & Manager (Shell/Tag-Aware)

import os
import json
from datetime import datetime

AUTO_TASK_DIR = "modules/auto_tasks/"

def ensure_dir():
    os.makedirs(AUTO_TASK_DIR, exist_ok=True)

def generate_task_file(shell_id, task_list, meta=None):
    ensure_dir()
    file_path = os.path.join(AUTO_TASK_DIR, f"{shell_id}.tasks")

    task_obj = {
        "shell_id": shell_id,
        "generated": datetime.utcnow().isoformat(),
        "tasks": task_list,
        "meta": meta or {}
    }

    with open(file_path, "w") as f:
        json.dump(task_obj, f, indent=2)

    print(f"[autogen] Auto-task file generated for shell `{shell_id}`.")

def generate_group_task(tag_name, task_list, meta=None):
    ensure_dir()
    file_path = os.path.join(AUTO_TASK_DIR, f"group_{tag_name}.tasks")

    task_obj = {
        "tag": tag_name,
        "generated": datetime.utcnow().isoformat(),
        "tasks": task_list,
        "meta": meta or {}
    }

    with open(file_path, "w") as f:
        json.dump(task_obj, f, indent=2)

    print(f"[autogen] Group task file generated for tag `{tag_name}`.")

def load_auto_tasks(shell_id, tags=None):
    tasks = []
    # Load shell-specific tasks
    path = os.path.join(AUTO_TASK_DIR, f"{shell_id}.tasks")
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
            tasks.extend(data.get("tasks", []))

    # Load tag-based group tasks
    if tags:
        for tag in tags:
            tag_path = os.path.join(AUTO_TASK_DIR, f"group_{tag}.tasks")
            if os.path.exists(tag_path):
                with open(tag_path, "r") as f:
                    data = json.load(f)
                    tasks.extend(data.get("tasks", []))

    # De-dupe task list
    return list(sorted(set(tasks)))

def list_task_files():
    ensure_dir()
    return [f for f in os.listdir(AUTO_TASK_DIR) if f.endswith(".tasks")]

def describe_task_file(filename):
    path = os.path.join(AUTO_TASK_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

def list_tasks_for_shell(shell_id, tags=None):
    tasks = load_auto_tasks(shell_id, tags)
    print(f"[autogen] Resolved tasks for shell `{shell_id}`:")
    for t in tasks:
        print(f"- {t}")

