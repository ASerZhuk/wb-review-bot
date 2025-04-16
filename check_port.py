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

def check_port_open(port=8080, host='0.0.0.0'):
    """Проверяет, открыт ли порт для прослушивания."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

# Вывод информации, который будет доступен в логах
print("*" * 50)
print("Проверка доступности порта 8080")
print(f"Порт 8080 открыт: {check_port_open()}")
print("*" * 50)

# Попытаемся сами открыть порт для проверки
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 8080))
    s.listen(1)
    print("Успешно открыт порт 8080 для тестирования")
    s.close()
except Exception as e:
    print(f"Ошибка при открытии порта 8080: {e}")

print("Проверка порта завершена")
print("*" * 50)

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