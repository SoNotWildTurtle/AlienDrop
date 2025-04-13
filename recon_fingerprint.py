# MINC - recon_fingerprint.py (Heuristic + Tag-based Fingerprint Engine)

def identify_platform(http_data, open_ports):
    headers = http_data.get("headers", {})
    body_sample = http_data.get("body_sample", "").lower()
    server = headers.get("server", "").lower()
    x_powered = headers.get("x-powered-by", "").lower()

    score = 0
    platform = "unknown"
    tags = []

    if "php" in x_powered:
        platform = "linux"
        score += 30
    if "asp" in x_powered or "microsoft" in x_powered:
        platform = "windows"
        score += 30

    if "iis" in server or "asp.net" in server:
        platform = "windows"
        score += 20
    if "nginx" in server or "apache" in server:
        platform = "linux"
        score += 20

    if "index of /" in body_sample and "cgi-bin" in body_sample:
        platform = "linux"
        score += 15

    if 445 in open_ports or 3389 in open_ports:
        platform = "windows"
        score += 15
    if 22 in open_ports or 80 in open_ports:
        score += 10

    # Add tags
    if "cloudflare" in server or "cf-ray" in headers:
        tags.append("cdn_detected")
    if "akamai" in server or "akamai" in headers.get("x-cache", "").lower():
        tags.append("cdn_detected")
    if "waf" in server or "secure" in server:
        tags.append("waf_detected")

    return {
        "platform": platform,
        "confidence": min(score, 100),
        "tags": list(set(tags))
    }


def detect_cms(http_data, path_hits):
    body = http_data.get("body_sample", "").lower()
    headers = http_data.get("headers", {})
    x_generator = headers.get("x-generator", "").lower()

    cms = "unknown"
    score = 0
    tags = []

    def mark(name, s, t=[]):
        return {"cms": name, "confidence": s, "tags": t}

    if "wp-content" in body or "wp-json" in body or "wordpress" in x_generator:
        return mark("wordpress", 95, ["php", "blog"])
    if "joomla" in body or "index.php?option=com_" in body:
        return mark("joomla", 90, ["php", "modular"])
    if "discuz" in body or "/uc_server/" in body:
        return mark("discuz", 90, ["china", "forum"])
    if "dedecms" in body or "/plus/" in body:
        return mark("dedecms", 90, ["china", "blog"])
    if "metinfo" in body:
        return mark("metinfo", 85, ["china", "cms"])
    if "drupal" in body or "sites/all" in body:
        return mark("drupal", 85, ["php", "modular"])
    if "typo3" in body or "typo3conf" in body:
        return mark("typo3", 80, ["php", "enterprise"])
    if "/admin" in path_hits and "/readme.html" in path_hits:
        return mark("generic_php", 60, ["unknown_php"])

    return mark("unknown", 20, ["needs_analysis"])


def fingerprint_target(recon_data):
    return {
        "platform": recon_data.get("platform", "unknown"),
        "cms": recon_data.get("cms", "unknown"),
        "open_ports": recon_data.get("open_ports", []),
        "paths": recon_data.get("paths_detected", []),
        "target": recon_data.get("target")
    }

