# -*- coding: utf-8 -*-
"""
 umber.wsgi - apache2 wsgi production python

 This version is for umber source files in /var/www/umber
 with its vitualenv python environment in /var/www/umber/venv/ .
 See the notes in ../env/shell_production - the paths need to be consistent.
"""
#   --- deprecated : this is python2 only syntax
#   activate_this = '/var/www/umber/venv/bin/activate_this.py'
#   execfile(activate_this, dict(__file__=activate_this))
#   --- see python-home directives in apache config file,
#   modwsgi.readthedocs.io/en/develop/user-guides/virtual-environments.html
#
import sys; sys.path.insert(0,  '/var/www/umber/src')
from umber import app as application
