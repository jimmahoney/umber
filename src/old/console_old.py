# -- coding: utf-8 --
"""
 console.py
 
 An interactive shell for the umber project.

   $ source env/activate       # from umber root folder - do this onece.
   (umber)$ umber_console
   == Umber console ==
   >>>

 Jim Mahoney | mahoney@marlboro.edu | MIT License
"""

from settings import os_src, os_root, os_basename, url_basename
from pprint import pprint as pp

# umber.py is in in the os_src folder;
# make sure that is in python's import path.
import sys
sys.path.insert(0, os_src)

# from umber import *
from model import *    # temporary - use umber eventually

# flask_context = app.test_request_context()
# flask_context.push()

print "== Umber console =="

# variables for interactive tests
democourse = Course.get(name='Demo Course')
jane = Person.get(username='janedoe')

#home = Page('demo/home', user=jane)  # demo course home page as jane
# print "   variables: demo, jane, home"

# Flask application
# app_setup()

# introspection :
# >>> pp(vars())

# a template page :
# >>> html = testroute()

