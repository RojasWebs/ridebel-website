# Bind privately; only Nginx should reach Gunicorn.
bind = '127.0.0.1:8000'
workers = 2
timeout = 30
accesslog = None
errorlog = '-'
loglevel = 'warning'
# Django handles HTTPS using the header overwritten by Nginx.
forwarded_allow_ips = '127.0.0.1'
