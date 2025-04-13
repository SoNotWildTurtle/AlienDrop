# MINC - recon_engine.py (Stealth + Advanced Recon Integration)

import requests
import socket
import json
import time
from urllib.parse import urlparse
from recon.recon_fingerprint import identify_platform, detect_cms
from modules.idgen import gen_shell_id

HEADERS_ROTATION = [
    {"User-Agent": "Mozilla/5.0 (AlienDrop/Recon1)"},
    {"User-Agent": "Mozilla/5.0 (AlienDrop/Recon2)", "Accept": "*/*"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept-Language": "en-US"},
    {"User-Agent": "curl/7.68.0"}
]

COMMON_PORTS = [21, 22, 23, 80, 443, 8080, 8443]
CMS_FINGERPRINT_PATHS = [
    "/readme.html", "/license.txt", "/robots.txt", "/admin", "/favicon.ico",
    "/wp-login.php", "/index.php?option=com_users", "/plus/index.php", "/dede/login.php"
]


def scan_ports(target):
    open_ports = []
    for port in COMMON_PORTS:
        try:
            with socket.create_connection((target, port), timeout=2):
                open_ports.append(port)
        except:
            continue
    return open_ports


def basic_http_probe(target, ports):
    scheme = "https" if 443 in ports else "http"
    headers = HEADERS_ROTATION[randint(0, len(HEADERS_ROTATION) - 1)]
    try:
        response = requests.get(f"{scheme}://{target}", headers=headers, timeout=5, verify=False)
        return {
            "scheme": scheme,
            "status": response.status_code,
            "headers": dict(response.headers),
            "body_sample": response.text[:300]
        }
    except Exception:
        return {}


def probe_paths(target, scheme="http"):
    found = []
    for path in CMS_FINGERPRINT_PATHS:
        try:
            url = f"{scheme}://{target}{path}"
            r = requests.get(url, headers=HEADERS_ROTATION[randint(0, len(HEADERS_ROTATION) - 1)], timeout=3, verify=False)
            if r.status_code in [200, 403]:
                found.append(path)
        except:
            continue
    return found


def resolve_target(target):
    try:
        return socket.gethostbyname(target)
    except:
        return target


def perform_recon(target):
    print(f"[Recon] Starting fingerprinting on {target}...")

    ip = resolve_target(target)
    shell_id = gen_shell_id()
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")

    ports = scan_ports(ip)
    http_data = basic_http_probe(ip, ports)
    scheme = http_data.get("scheme", "http")
    path_hits = probe_paths(ip, scheme=scheme)
    platform = identify_platform(http_data, ports)
    cms = detect_cms(http_data, path_hits)

    tags = []
    if "wp-login.php" in path_hits:
        tags.append("wordpress")
    if "/plus/index.php" in path_hits:
        tags.append("discuz")
    if "/dede/login.php" in path_hits:
        tags.append("dedecms")

    recon_data = {
        "target": target,
        "ip": ip,
        "timestamp": timestamp,
        "shell_id": shell_id,
        "open_ports": ports,
        "platform": platform,
        "cms": cms,
        "tags": tags,
        "http_data": http_data,
        "paths_detected": path_hits
    }

    log_path = f"output/sessions/{shell_id}_recon.json"
    with open(log_path, "w") as f:
        json.dump(recon_data, f, indent=2)

    print(f"[Recon] Recon complete. Saved to {log_path}")
    return recon_data

