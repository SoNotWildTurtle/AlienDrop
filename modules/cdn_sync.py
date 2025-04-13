# MINC - CDN Synchronizer (Blob Replication Engine)
import os
import json
import requests
import time
from hashlib import sha256
from cdn_rotator import load_sources, score_mirrors, verify_blob_integrity

MODULE_DIR = "output/modules/"
UPLOAD_PATH = "modules/"
RETRY_LIMIT = 2
DRY_RUN = False  # Set True for log-only mode

def list_blobs():
    return [f for f in os.listdir(MODULE_DIR) if f.endswith(".blob.json")]

def upload_blob_to_cdn(blob_file, cdn_url):
    full_path = os.path.join(MODULE_DIR, blob_file)
    blob_data = open(full_path, "rb").read()
    url = f"{cdn_url.rstrip('/')}/{UPLOAD_PATH}{blob_file}"

    try:
        r = requests.put(url, data=blob_data, timeout=5)
        if r.status_code in [200, 201, 204]:
            print(f"[cdn_sync] ✅ Uploaded to {cdn_url}")
            return True
    except:
        pass
    print(f"[cdn_sync] ❌ Failed: {cdn_url}")
    return False

def verify_upload(blob_file, cdn_url):
    url = f"{cdn_url.rstrip('/')}/{UPLOAD_PATH}{blob_file}"
    try:
        r = requests.get(url, timeout=4)
        remote_hash = sha256(r.content).hexdigest()
        local_hash = verify_blob_integrity(os.path.join(MODULE_DIR, blob_file))
        return remote_hash == local_hash
    except:
        return False

def sync_all_blobs():
    mirrors = load_sources()
    scores = score_mirrors(mirrors)

    blobs = list_blobs()
    if not blobs:
        print("[cdn_sync] No blob files to sync.")
        return

    for blob in blobs:
        print(f"\n[cdn_sync] Syncing {blob} to healthy mirrors...")

        for tier in ["primary", "secondary", "stealth"]:
            urls = mirrors.get(tier, [])
            for mirror in urls:
                if scores.get(mirror, 0) < 1:
                    print(f"[cdn_sync] Skipping dead mirror: {mirror}")
                    continue

                for attempt in range(RETRY_LIMIT):
                    if DRY_RUN:
                        print(f"[dry_run] Would upload {blob} → {mirror}")
                        break

                    if upload_blob_to_cdn(blob, mirror):
                        if verify_upload(blob, mirror):
                            print(f"[cdn_sync] ✅ Verified upload: {mirror}")
                        else:
                            print(f"[cdn_sync] ⚠️ Upload mismatch (hash fail): {mirror}")
                        break
                    else:
                        print(f"[cdn_sync] Retry {attempt+1}/{RETRY_LIMIT} failed.")

def main():
    print("== CDN SYNC INITIALIZED ==")
    sync_all_blobs()
    print("== SYNC COMPLETE ==")

if __name__ == "__main__":
    main()

