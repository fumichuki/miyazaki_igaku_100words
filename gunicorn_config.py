"""
Gunicorn configuration for production deployment
"""
import multiprocessing
import os

# Server socket - 環境変数PORTを使用（Render対応）
port = os.getenv('PORT', '8002')
bind = f"0.0.0.0:{port}"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 240  # LLM応答待機時間を考慮（4分）
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "miyazaki_igaku_eisakubun"

# Preload application
preload_app = True

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None
