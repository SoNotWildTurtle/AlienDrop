# MINC - Shell Logger & Transfer Packager (Finalized)

import json
import os
import hashlib
import zipfile
from datetime import datetime

LOG_DIR = "output/shells/"
TRANSFER_DIR = "output/transfers/"
MAP_FILE = "output/transfer_map.json"

def ensure_dirs():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(TRANSFER_DIR, exist_ok=True)

def log_shell_report(shell_id, tags, tasks, metadata):
    ensure_dirs()

    report = {
        "shell_id": shell_id,
        "timestamp": datetime.utcnow().isoformat(),
        "tags": tags,
        "attitude": metadata.get("attitude", "unknown"),
        "kill_flag": metadata.get("kill_flag", False),
        "tasks": tasks,
        "target": metadata.get("target", "n/a"),
        "platform": metadata.get("platform", "unknown"),
        "modules": metadata.get("modules", []),
        "memory_flag": metadata.get("memory_flag", False),
        "recon_fingerprint": metadata.get("fingerprint", {}),
        "ip": metadata.get("ip", "unknown"),
        "uuid": metadata.get("uuid", shell_id),
    }

    # Save full .json
    with open(os.path.join(LOG_DIR, f"{shell_id}.json"), "w") as f:
        json.dump(report, f, indent=2)

    # Markdown summary
    md_path = os.path.join(LOG_DIR, f"{shell_id}.md")
    with open(md_path, "w") as f:
        f.write(f"# Shell Report: `{shell_id}`\n")
        f.write(f"- Timestamp: `{report['timestamp']}`\n")
        f.write(f"- Target: `{report['target']}`\n")
        f.write(f"- Platform: `{report['platform']}`\n")
        f.write(f"- IP: `{report['ip']}`\n")
        f.write(f"- UUID: `{report['uuid']}`\n")
        f.write(f"- Attitude: `{report['attitude']}`\n")
        f.write(f"- Memory-only: `{report['memory_flag']}`\n")
        f.write(f"- Killmode Flag: `{report['kill_flag']}`\n")
        f.write(f"- Tags: `{', '.join(tags)}`\n")
        f.write(f"- Modules: `{', '.join(report['modules'])}`\n")
        f.write("\n## Tasks Executed\n")
        for t in tasks:
            f.write(f"- {t}\n")
        if report["recon_fingerprint"]:
            f.write("\n## Recon Fingerprint\n")
            for k, v in report["recon_fingerprint"].items():
                f.write(f"- **{k}**: `{v}`\n")

def package_shell_transfer(shell_id):
    ensure_dirs()

    json_path = os.path.join(LOG_DIR, f"{shell_id}.json")
    md_path = os.path.join(LOG_DIR, f"{shell_id}.md")

    if not os.path.exists(json_path):
        print(f"[shell_logger] No JSON log found for {shell_id}")
        return

    # Load blob
    with open(json_path, "rb") as f:
        blob = f.read()

    # SHA256 hash
    hash = hashlib.sha256(blob).hexdigest()
    hash_path = os.path.join(TRANSFER_DIR, f"verify_{shell_id}.hash")
    with open(hash_path, "w") as f:
        f.write(hash)

    # Extract metadata
    with open(json_path, "r") as f:
        data = json.load(f)

    metadata = {
        "shell_id": shell_id,
        "created": data.get("timestamp"),
        "tags": data.get("tags", []),
        "attitude": data.get("attitude", "unknown"),
        "platform": data.get("platform", "unknown"),
        "uuid": data.get("uuid", shell_id),
        "kill_flag": data.get("kill_flag", False),
        "memory_flag": data.get("memory_flag", False),
        "ip": data.get("ip", "unknown"),
        "size": len(blob),
        "hash": hash
    }

    meta_path = os.path.join(TRANSFER_DIR, f"{shell_id}.pkgmeta.json")
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # Write raw .pkg (still used elsewhere)
    pkg_path = os.path.join(TRANSFER_DIR, f"transfer_{shell_id}.pkg")
    with open(pkg_path, "wb") as f:
        f.write(blob)

    # Create final .zip archive
    zip_path = os.path.join(TRANSFER_DIR, f"{shell_id}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(json_path, arcname=f"{shell_id}.json")
        z.write(md_path, arcname=f"{shell_id}.md")
        z.write(hash_path, arcname=f"{shell_id}.hash")
        z.write(meta_path, arcname=f"{shell_id}.pkgmeta.json")

    print(f"[shell_logger] ✅ Packaged: {zip_path}")
    print(f"[shell_logger] 🔐 SHA256: {hash}")

