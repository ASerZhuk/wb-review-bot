import socket
import time
import sys

def check_port(port, host='localhost', timeout=30):
    """Проверяет, доступен ли порт, с указанным таймаутом."""
    print(f"Checking if port {port} is open on {host}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"Port {port} is open on {host}!")
                return True
            
            print(f"Port {port} is not open yet, retrying...")
            time.sleep(1)
            
        except Exception as e:
            print(f"Error checking port: {e}")
            time.sleep(1)
    
    print(f"Timed out waiting for port {port} to open.")
    return False

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            sys.exit(1)
    
    if check_port(port, host='0.0.0.0'):
        sys.exit(0)
    else:
        sys.exit(1) 