# MINC - Session Tracker (Operator Interaction Log)

import os
import json
from datetime import datetime

TRACKER_FILE = "output/session_log.json"

def ensure_log_file():
    if not os.path.exists("output"):
        os.makedirs("output")

    if not os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "w") as f:
            json.dump([], f, indent=2)

def log_action(shell_id, action, context=None):
    ensure_log_file()

    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "shell_id": shell_id,
        "action": action,
        "context": context or {}
    }

    try:
        with open(TRACKER_FILE, "r") as f:
            logs = json.load(f)
    except Exception:
        logs = []

    logs.append(record)

    with open(TRACKER_FILE, "w") as f:
        json.dump(logs, f, indent=2)

    print(f"[session_tracker] Logged: {action} on {shell_id}")

def get_logs(shell_id=None):
    if not os.path.exists(TRACKER_FILE):
        return []

    with open(TRACKER_FILE, "r") as f:
        logs = json.load(f)

    if shell_id:
        return [entry for entry in logs if entry["shell_id"] == shell_id]

    return logs

def export_log(shell_id):
    logs = get_logs(shell_id)
    if not logs:
        print(f"[session_tracker] No logs for shell {shell_id}")
        return

    export_path = f"output/sessions/{shell_id}_session.md"
    os.makedirs("output/sessions", exist_ok=True)

    with open(export_path, "w") as f:
        f.write(f"# Session Log for {shell_id}\n\n")
        for entry in logs:
            f.write(f"- [{entry['timestamp']}] `{entry['action']}`\n")
            if entry["context"]:
                f.write(f"  ➜ Context: `{json.dumps(entry['context'])}`\n")
            f.write("\n")

    print(f"[session_tracker] Exported session log to: {export_path}")

