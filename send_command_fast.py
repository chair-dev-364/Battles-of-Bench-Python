"""send_command_fast.py — UDP fire-and-forget client for sound server.
Sends a single datagram and exits immediately. This avoids TCP handshake and Python connect overhead
for common play requests. Keep behavior simple: no blocking, no output.
"""
import socket
import sys

HOST = '127.0.0.1'
PORT = 65432

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(0)
    msg = sys.argv[1]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(msg.encode('utf-8'), (HOST, PORT))
    except Exception:
        # Fire-and-forget: never fail loudly
        pass
    sys.exit(0)
