"""sound.py — lightweight fast sound sender
Sends a UDP datagram with the requested sound name if volume > 0.
Usage: py sound.py <SoundName>
"""
import os
import sys
import socket

# Configuration — match server settings
HOST = '127.0.0.1'
PORT = 65432
BUFFER_SIZE = 1024

# Determine repository base dir (script location)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SETTINGS_DIR = os.path.join(BASE_DIR, 'Settings')
VOLUME_FILE = os.path.join(SETTINGS_DIR, 'sound.txt')


def get_volume():
    """Return integer volume 0-10. Missing/invalid => 10."""
    try:
        with open(VOLUME_FILE, 'r', encoding='utf-8') as f:
            s = f.read().strip()
            if not s:
                return 10
            v = int(s)
            return max(0, min(10, v))
    except FileNotFoundError:
        return 10
    except Exception:
        return 10


if __name__ == '__main__':
    if len(sys.argv) < 2:
        # Silent, mirror previous behavior
        sys.exit(0)

    command = " ".join(sys.argv[1:]).strip()
    if not command:
        sys.exit(0)

    # Respect mute / volume setting
    vol = get_volume()
    if vol == 0:
        # Muted: don't bother sending
        sys.exit(0)

    # Fire-and-forget UDP send
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.5)
            s.sendto(command.encode('utf-8'), (HOST, PORT))
    except Exception:
        # Never raise on fire-and-forget, silent failure
        pass

    sys.exit(0)
