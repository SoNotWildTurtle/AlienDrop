# MINC - Shell ID Generator (Entropy-Based + Tracking + Killmode Aware)

import hashlib
import random
import string
import json
import os
from datetime import datetime

IDMAP_FILE = "output/transfer_map.json"

def random_entropy_string(length=12):
    pool = string.ascii_letters + string.digits
    return ''.join(random.choices(pool, k=length))

def gen_shell_id(profile=None):
    entropy = random_entropy_string(24)
    timestamp = datetime.utcnow().isoformat()
    raw_id = f"{entropy}-{timestamp}"
    hash_id = hashlib.sha256(raw_id.encode()).hexdigest()[:16]
    save_shell_id_map(hash_id, profile)
    return hash_id

def save_shell_id_map(shell_id, profile_data):
    os.makedirs("output", exist_ok=True)
    if not os.path.exists(IDMAP_FILE):
        with open(IDMAP_FILE, "w") as f:
            json.dump({}, f)

    with open(IDMAP_FILE, "r") as f:
        try:
            current = json.load(f)
        except:
            current = {}

    entry = {
        "created": datetime.utcnow().isoformat(),
        "profile": profile_data or {},
        "attitude": (profile_data.get("attitude") if profile_data else "unknown"),
        "tags": profile_data.get("tags") if profile_data and "tags" in profile_data else [],
        "origin_ip": profile_data.get("ip") if profile_data and "ip" in profile_data else "unknown",
        "kill_flag": True if profile_data and profile_data.get("attitude") == "killmode" else False
    }

    current[shell_id] = entry

    with open(IDMAP_FILE, "w") as f:
        json.dump(current, f, indent=2)

