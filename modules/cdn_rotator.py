# MINC - CDN Rotator v3 (Tiered Mirror Engine + Health-Based Fallback)

import json
import os
import random
import requests
import time
from hashlib import sha256

ROTATOR_FILE = "config/cdn_sources.json"
HEALTH_FILE = "output/cdn_health.json"
TEST_FILE = "status/ping.txt"
DEFAULT_SOURCES = {
    "primary": [
        "https://cdn1.midnight-camo.net",
        "https://cdn2.shadowtrack.org"
    ],
    "secondary": [
        "https://cdn3.mirrorpoint.co"
    ],
    "stealth": [
        "https://cdn4.stealthlink.cc"
    ]
}

# === FILE I/O HELPERS ===
def load_sources():
    if not os.path.exists(ROTATOR_FILE):
        return DEFAULT_SOURCES
    with open(ROTATOR_FILE, "r") as f:
        return json.load(f)

def save_sources(sources):
    os.makedirs("config", exist_ok=True)
    with open(ROTATOR_FILE, "w") as f:
        json.dump(sources, f, indent=2)

def load_health():
    if not os.path.exists(HEALTH_FILE):
        return {}
    with open(HEALTH_FILE, "r") as f:
        return json.load(f)

def save_health(data):
    os.makedirs("output", exist_ok=True)
    with open(HEALTH_FILE, "w") as f:
        json.dump(data, f, indent=2)

# === CDN TESTING ===
def test_cdn(url):
    try:
        r = requests.get(f"{url.rstrip('/')}/{TEST_FILE}", timeout=3)
        return r.status_code == 200
    except:
        return False

def score_mirrors(sources):
    scores = {}
    health = load_health()

    for tier, urls in sources.items():
        for url in urls:
            alive = test_cdn(url)
            if url not in health:
                health[url] = {
                    "tier": tier,
                    "score": 0,
                    "last_checked": 0
                }
            health[url]["score"] += 1 if alive else -1
            health[url]["score"] = max(0, health[url]["score"])
            health[url]["last_checked"] = time.time()
            scores[url] = health[url]["score"]

    save_health(health)
    return scores

def get_current_cdn_url(strict=True):
    sources = load_sources()
    scores = score_mirrors(sources)

    all_urls = []
    for tier in ["primary", "secondary", "stealth"]:
        tier_urls = sources.get(tier, [])
        if strict:
            tier_urls = [url for url in tier_urls if scores.get(url, 0) > 0]
        if tier_urls:
            chosen = random.choice(tier_urls)
            return chosen
    return random.choice(list(scores.keys()))

# === CDN CONTROL ===
def add_mirror(url, tier="secondary"):
    sources = load_sources()
    if url not in sources.get(tier, []):
        sources.setdefault(tier, []).append(url)
        save_sources(sources)
        print(f"[cdn_rotator] Added mirror: {url} (tier: {tier})")

def remove_mirror(url):
    sources = load_sources()
    for tier in sources:
        if url in sources[tier]:
            sources[tier].remove(url)
    save_sources(sources)
    print(f"[cdn_rotator] Removed mirror: {url}")

def promote_mirror(url, to_tier="primary"):
    sources = load_sources()
    found = False
    for tier in sources:
        if url in sources[tier]:
            sources[tier].remove(url)
            found = True
    if found:
        sources.setdefault(to_tier, []).append(url)
        save_sources(sources)
        print(f"[cdn_rotator] Promoted {url} → {to_tier}")
    else:
        print(f"[cdn_rotator] Mirror not found: {url}")

# === BLOB VERIFICATION ===
def verify_blob_integrity(blob_path):
    if not os.path.exists(blob_path):
        print("[cdn_rotator] Blob not found.")
        return None
    with open(blob_path, "rb") as f:
        content = f.read()
    return sha256(content).hexdigest()

# === CLI ===
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CDN Mirror Rotator & Health Checker")
    parser.add_argument("--list", action="store_true", help="List current mirrors by tier")
    parser.add_argument("--add", help="Add a mirror URL")
    parser.add_argument("--tier", help="Tier for --add (default: secondary)", default="secondary")
    parser.add_argument("--remove", help="Remove a mirror URL")
    parser.add_argument("--promote", help="Promote mirror to tier")
    parser.add_argument("--pick", action="store_true", help="Return current CDN URL")
    parser.add_argument("--verify", help="Verify blob hash")
    parser.add_argument("--scores", action="store_true", help="Show live CDN scores")

    args = parser.parse_args()

    if args.list:
        print(json.dumps(load_sources(), indent=2))
    elif args.add:
        add_mirror(args.add, args.tier)
    elif args.remove:
        remove_mirror(args.remove)
    elif args.promote:
        promote_mirror(args.promote, to_tier=args.tier)
    elif args.pick:
        print(f"[cdn_rotator] Selected CDN: {get_current_cdn_url()}")
    elif args.verify:
        result = verify_blob_integrity(args.verify)
        print(f"SHA256: {result}" if result else "Failed to verify.")
    elif args.scores:
        scores = score_mirrors(load_sources())
        print(json.dumps(scores, indent=2))

