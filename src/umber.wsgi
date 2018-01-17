"""
 umber.wsgi - production runner for apache2 wsgi
 See ../env/shell_production
"""

import os, sys

os.environ['UMBER_CONFIG'] = 'PRODUCTION'
os.environ['UMBER_ROOT'] = '/var/www/umber'
os.environ['UMBER_SECRET_KEY'] = 'e7c6f2e8ae0c3450994d0416a07d969dd53aac96b7adc73e'

activate_this = '/var/www/umber/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

sys.path.insert(0,  '/var/www/umber/src')

from umber import app as application
