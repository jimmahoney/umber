"""
 umber.wsgi - production runner for apache2 wsgi
 See ../env/shell_production
"""
activate_this = '/var/www/umber/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
import sys; sys.path.insert(0,  '/var/www/umber/src')
from umber import app as application
