# MINC - Encrypted Module Generator / Deployer (XOR + Fernet + Metadata Blob)

from cryptography.fernet import Fernet
import base64
import os
import random
import json

MODULE_PATH = "modules/"
OUTPUT_PATH = "output/modules/"
ENCODED_BLOBS = {}

os.makedirs(OUTPUT_PATH, exist_ok=True)

def xor_encrypt(data, key):
    key = key.encode() if isinstance(key, str) else key
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def generate_payload_blob(filename, drop_type="generic", uid=None, use_xor=True):
    raw_path = os.path.join(MODULE_PATH, filename)
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"[encrypt_module] File not found: {raw_path}")

    with open(raw_path, "rb") as f:
        content = f.read()

    key = Fernet.generate_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(content)

    if use_xor:
        xor_key = base64.b64encode(os.urandom(8)).decode()
        double_layer = xor_encrypt(encrypted, xor_key)
        encoded = base64.b64encode(double_layer).decode()
    else:
        xor_key = None
        encoded = base64.b64encode(encrypted).decode()

    blob = {
        "key": base64.b64encode(key).decode(),
        "xor": xor_key,
        "payload": encoded,
        "type": drop_type,
        "uid": uid or f"{filename}_{random.randint(1000,9999)}",
        "size": len(encoded),
        "loader": "memory",
    }

    ENCODED_BLOBS[filename] = blob
    return blob

def deploy_encrypted_module(target, shell_id, module_name):
    print(f"[encrypt_module] Deploying '{module_name}' to {target} (shell {shell_id})...")
    blob = generate_payload_blob(module_name, uid=shell_id)
    outpath = os.path.join(OUTPUT_PATH, f"{shell_id}_{module_name}.blob.json")
    with open(outpath, "w") as f:
        json.dump(blob, f, indent=2)
    print(f"[encrypt_module] Saved encrypted module blob: {outpath}")
    return outpath

def cli_encrypt_module(filename):
    blob = generate_payload_blob(filename)
    outpath = os.path.join(OUTPUT_PATH, filename + ".enc")
    with open(outpath, "w") as f:
        json.dump(blob, f, indent=2)
    print(f"[encrypt_module] Module encrypted and saved to: {outpath}")

def cli_decrypt_module(filepath, fernet_key, xor_key=None):
    with open(filepath, "r") as f:
        blob = json.load(f)

    encrypted = base64.b64decode(blob['payload'])
    if xor_key or blob.get("xor"):
        xor_bytes = base64.b64decode(xor_key or blob['xor'])
        encrypted = xor_encrypt(encrypted, xor_bytes)

    key = base64.b64decode(fernet_key or blob['key'])
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted)
    return decrypted

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Module Encryptor")
    parser.add_argument("--encrypt", help="Encrypt and save module by filename")
    parser.add_argument("--decrypt", help="Decrypt module blob (JSON)")
    parser.add_argument("--key", help="Fernet key (Base64)")
    parser.add_argument("--xor", help="XOR key (Base64)", default=None)

    args = parser.parse_args()

    if args.encrypt:
        cli_encrypt_module(args.encrypt)
    elif args.decrypt and args.key:
        output = cli_decrypt_module(args.decrypt, args.key, args.xor)
        print(output.decode(errors="ignore"))

