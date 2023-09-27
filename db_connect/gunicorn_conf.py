from multiprocessing import cpu_count

# Socket Path
bind = 'unix:/home/ubuntu/fast_api_apps/db_connect/gunicorn.sock'

# Worker Options
workers = cpu_count() + 1
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging Options
loglevel = 'debug'
accesslog = '/home/ubuntu/fast_api_apps/db_connect/access_log'
errorlog = '/home/ubuntu/fast_api_apps/db_connect/error_log'
