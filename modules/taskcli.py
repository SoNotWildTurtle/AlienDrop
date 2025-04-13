# MINC - Task CLI Interface (Interactive Shell Task Manager v2)

import os
import json
from modules.autogen import generate_task_file, load_auto_tasks
from modules.shell_logger import LOG_DIR
from datetime import datetime

LOG_DIR = "output/shells/"



def launch_task_cli():
    """Launches the interactive task manager for CLI"""
    taskcli()  # Call the existing taskcli function to handle the interaction


def list_shells():
    """Lists all available shells sorted by timestamp"""
    shells = []
    for file in os.listdir(LOG_DIR):
        if file.endswith(".json"):
            with open(os.path.join(LOG_DIR, file), "r") as f:
                shell = json.load(f)
                shells.append(shell)
    return sorted(shells, key=lambda x: x.get("timestamp", ""), reverse=True)

def print_shells(shells):
    """Prints the summary of available shells"""
    print("\n[Available Shells]")
    for s in shells:
        print(f"- {s['shell_id']} | Target: {s.get('target', 'n/a')} | Attitude: {s.get('attitude')} | Tags: {', '.join(s.get('tags', []))}")

def show_shell_summary(shell):
    """Displays a detailed summary of a selected shell"""
    print(f"\n[Shell: {shell['shell_id']}]")
    print(f"- Target: {shell.get('target')}")
    print(f"- IP: {shell.get('ip')}")
    print(f"- Tags: {', '.join(shell.get('tags', []))}")
    print(f"- Attitude: {shell.get('attitude')}")
    print(f"- Killmode: {shell.get('kill_flag')}")
    print(f"- Memory-only: {shell.get('memory_flag')}")
    print(f"- Modules: {', '.join(shell.get('modules', []))}")

def queue_auto_tasks(shell_id, modules):
    """Automatically generates tasks for given modules and queues them for a shell ID"""
    task_list = []
    for module in modules:
        task_list.append(f"Execute module: {module}")
    # Queue tasks
    generate_task_file(shell_id, task_list)
    print(f"[taskcli] Auto tasks generated and queued for shell {shell_id} with modules: {', '.join(modules)}")

def queue_task(shell_id, command):
    """Queues a task for a specific shell ID"""
    tasks = load_auto_tasks(shell_id)
    tasks.append(command)
    generate_task_file(shell_id, tasks)
    log_path = os.path.join("output/tasks_log/", f"{shell_id}.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        f.write(f"[{datetime.utcnow().isoformat()}] +TASK: {command}\n")

def remove_task(shell_id, task_name):
    """Removes a specified task from the task list for a shell ID"""
    tasks = load_auto_tasks(shell_id)
    if task_name in tasks:
        tasks.remove(task_name)
        generate_task_file(shell_id, tasks)
        print(f"[taskcli] Task removed: {task_name}")
    else:
        print("[taskcli] Task not found.")

def taskcli():
    """Main Task CLI Manager"""
    shells = list_shells()
    print_shells(shells)

    selected = input("\nEnter shell_id to manage: ").strip()
    matched = next((s for s in shells if s['shell_id'] == selected), None)

    if not matched:
        print("[taskcli] Shell not found.")
        return

    show_shell_summary(matched)

    while True:
        cmd = input(f"[{selected}]> ").strip()
        if cmd.lower() in ["exit", "quit"]:
            break
        if cmd.lower() == "show":
            print(f"\n[Current tasks for {selected}]:")
            tasks = load_auto_tasks(selected)
            for t in tasks:
                print(f"- {t}")
        elif cmd.lower().startswith("remove "):
            to_remove = cmd.split(" ", 1)[1].strip()
            remove_task(selected, to_remove)
        elif cmd.lower() == "meta":
            show_shell_summary(matched)
        elif cmd.lower() == "reload":
            shells = list_shells()
            matched = next((s for s in shells if s['shell_id'] == selected), None)
            print("[taskcli] Shell info reloaded.")
        elif cmd.lower().startswith("group "):
            tag = cmd.split(" ", 1)[1].strip()
            print(f"[taskcli] Group task mode: queued to all tagged `{tag}` shells.")
            targets = [s['shell_id'] for s in shells if tag in s.get("tags", [])]
            task = input("Enter task to queue for group: ").strip()
            for sid in targets:
                queue_task(sid, task)
            print(f"[taskcli] Pushed to {len(targets)} shells.")
        else:
            queue_task(selected, cmd)
            print(f"[taskcli] Task queued to {selected}.")

if __name__ == "__main__":
    taskcli()

