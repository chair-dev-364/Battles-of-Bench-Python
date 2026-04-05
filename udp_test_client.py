"""udp_test_client.py — send UDP message and optionally wait for response
Usage:
  py udp_test_client.py PING      # sends PING and prints PONG if received
  py udp_test_client.py testname  # sends a play request and exits
"""
import socket
import sys
import time

HOST = '127.0.0.1'
PORT = 65432
TIMEOUT = 1.0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: py udp_test_client.py <MSG>")
        sys.exit(2)
    msg = sys.argv[1]
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(TIMEOUT)
        try:
            s.sendto(msg.encode('utf-8'), (HOST, PORT))
            if msg.upper() == 'PING':
                # Wait for PONG
                data, addr = s.recvfrom(1024)
                print('Received:', data.decode('utf-8').strip())
            else:
                # Short sleep to allow server to print diagnostics (optional)
                time.sleep(0.05)
                print('Sent:', msg)
        except socket.timeout:
            print('No response (timeout)')
        except Exception as e:
            print('Error:', e)
