import environ

env = environ.Env()

# general
bind = "unix:/tmp/demo.sock"
workers = 8
worker_class = "sync"
daemon = False
timeout = 300
worker_tmp_dir = "/tmp"  # noqa: S108

# requires futures module for threads > 1
threads = 1

# During development, this will cause the server to reload when the code changes.
# noinspection PyShadowingBuiltins
reload = env.bool("GUNICORN_RELOAD", default=False)

# Logging.
accesslog = "-"
access_log_format = (
    '%({X-Forwarded-For}i)s %(l)s %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
)
errorlog = "-"
syslog = False

# statsd settings need to have defaults provided, because dev sites don't use statsd.
host = env("STATSD_HOST", default=None)
port = env.int("STATSD_PORT", default=8125)
statsd_host = f"{host}:{port}" if host and port else None
statsd_prefix = env("STATSD_PREFIX", default=None)
