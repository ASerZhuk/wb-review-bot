import os
import sys
import requests
from time import sleep

def check_health():
    """Проверка здоровья приложения"""
    url = f"http://localhost:{os.getenv('PORT', '3000')}"
    max_retries = 5
    retry_delay = 2

    print("Starting health check...")
    
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print("Health check passed!")
                return True
            else:
                print(f"Attempt {i+1}/{max_retries}: Health check failed with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {i+1}/{max_retries}: Connection error: {str(e)}")
        
        if i < max_retries - 1:
            print(f"Waiting {retry_delay} seconds before next attempt...")
            sleep(retry_delay)
    
    print("Health check failed after all retries")
    return False

if __name__ == "__main__":
    sys.exit(0 if check_health() else 1) 