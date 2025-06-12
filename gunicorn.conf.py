import multiprocessing

# Bind sur toutes les interfaces
bind = "0.0.0.0:10000"

# Un seul worker pour limiter l'utilisation de la mémoire
workers = 1

# Type de worker synchrone
worker_class = "sync"

# Limite de mémoire par worker (en Mo)
worker_memory_limit = "450M"

# Redémarrer les workers périodiquement
max_requests = 50
max_requests_jitter = 5

# Timeout
timeout = 120

# Précharger l'application
preload_app = True

# Réduire l'utilisation de la mémoire
worker_tmp_dir = "/dev/shm"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Limit worker memory usage
limit_request_line = 0
limit_request_fields = 100
limit_request_field_size = 8190
