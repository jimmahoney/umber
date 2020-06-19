"""
 wsgi.py

 uwsgi wrapper for umber application as deployed on bennington linode .
 See the environment variables defined in etc_systemd_system_umber.service .
"""
from umber import app
if __name__ == "__main__":
    app.run()
