import os

port = int(os.environ.get('PORT', 3000))
bind = f"0.0.0.0:{port}"
workers = 2
threads = 4
timeout = 120 