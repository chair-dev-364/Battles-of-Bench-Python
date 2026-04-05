# send_command.py
import socket
import sys
import os

# --- Configuration ---
# Should match the server script
HOST = '127.0.0.1'
PORT = 65432
# --- End Configuration ---

def send_command(command):
    """Connects to the server, sends a command, and closes."""
    try:
        # Create a socket object using IPv4 and TCP
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Short timeouts for fast failure; keep responsive
            s.settimeout(0.25)
            try:
                s.connect((HOST, PORT))
                # Use a very short timeout for send/recv after connect
                s.settimeout(0.25)
            except socket.timeout:
                print(f"Error: Connection to {HOST}:{PORT} timed out. Is the server running?", file=sys.stderr)
                sys.exit(1) # Exit with error code
            except ConnectionRefusedError:
                 print(f"Error: Connection to {HOST}:{PORT} refused. Is the server running?", file=sys.stderr)
                 sys.exit(1) # Exit with error code
            except Exception as e:
                 print(f"Error connecting to {HOST}:{PORT}: {e}", file=sys.stderr)
                 sys.exit(1) # Exit with error code


            # Send the command, encoded as UTF-8 bytes
            try:
                s.sendall(command.encode('utf-8'))
            except Exception as e:
                 print(f"Error sending command '{command}': {e}", file=sys.stderr)
                 sys.exit(1) # Exit with error code

            # print(f"Sent: {command}") # Optional: for debugging

            # If the command was PING, try to receive a response (optional)
            if command.upper() == "PING":
                 try:
                    # Set a shorter timeout for receiving data to be responsive
                    s.settimeout(0.25)
                    response = s.recv(1024) # Buffer size
                    if response:
                        print(f"Server response: {response.decode('utf-8').strip()}")
                    else:
                        print("Server closed connection without PONG (or PONG already received and connection closed).")
                 except socket.timeout:
                     print("Warning: Did not receive PONG response from server within timeout.")
                 except Exception as e:
                     print(f"Error receiving PING response: {e}", file=sys.stderr)


    except socket.error as e:
        # General socket errors (e.g., if server isn't running)
        print(f"Socket Error: {e}", file=sys.stderr)
        sys.exit(1) # Exit with error code
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1) # Exit with error code

if __name__ == "__main__":
    # Check if a command-line argument was provided
    if len(sys.argv) < 2:
        print("Usage: python send_command.py <SoundName|QUIT|PING>", file=sys.stderr)
        sys.exit(1)

    # Get the command from the first argument
    command_to_send = sys.argv[1]
    send_command(command_to_send)
    # Exit successfully
    sys.exit(0)