import environ

env = environ.Env()

# general
bind = 'unix:/tmp/demo.sock'
workers = 8
worker_class = 'sync'
daemon = False
timeout = 300
worker_tmp_dir = '/tmp'

# requires futures module for threads > 1
threads = 1

# During development, this will cause the server to reload when the code changes.
# noinspection PyShadowingBuiltins
reload = env.bool('GUNICORN_RELOAD', default=False)

# If remote debugging is enabled set the timeout very high, so one can pause for a long time in the debugger.
# Also set the number of workers to 1, which improves the debugging experience by not overwhleming the remote debugger.
if env.bool('REMOTE_DEBUG_ENABLED', default=False):
    timeout = 9999
    workers = 1

# Logging.
accesslog = '-'
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
errorlog = '-'
syslog = False

# statsd settings need to have defaults provided, because dev sites don't use statsd.
host = env('STATSD_HOST', default=None)
port = env.int('STATSD_PORT', default=8125)
if host and port:
    statsd_host = "{}:{}".format(host, port)
else:
    statsd_host = None
statsd_prefix = env('STATSD_PREFIX', default=None)
