loglevel = 'debug'
accesslog = '/var/log/gunicorn/access_log_yourapp'
acceslogformat ="%(h)s %(l)s %(u)s %(t)s %(r)s %(s)s %(b)s %(f)s %(a)s"
errorlog =  '/var/log/gunicorn/error_log_yourapp'