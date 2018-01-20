"""
 umber.wsgi - apache2 wsgi production python

 This version is for umber source files in /var/www/umber
 with its vitualenv python environment in /var/www/umber/venv/ .
 See the notes in ../env/shell_production - the paths need to be consistent.
"""
activate_this = '/var/www/umber/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
import sys; sys.path.insert(0,  '/var/www/umber/src')
from umber import app as application
