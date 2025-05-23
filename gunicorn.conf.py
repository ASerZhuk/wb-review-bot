import os

port = int(os.environ.get('PORT', 8080))
bind = f"0.0.0.0:{port}"
workers = 2
threads = 4
timeout = 60
accesslog = "-"  # Логи в stdout
errorlog = "-"  # Ошибки в stdout
capture_output = True
loglevel = "info" 