"""
 console.py

 user's interactive flash shell console 
 initialization with flask's python packages and variables
 for development debugging and testing

 called from bin/umber_console 

   $ umber_console
   ...
   >>> jane
   Person(username=u'janedoe', ...)

"""

from settings import os_src, os_root, url_basename
from pprint import pprint as pp
from flask import request, url_for

# Make sure that umber.py is in python's import path
import sys
sys.path.insert(0, os_src)

from umber import *
from utilities import markdown2html

# Set context for a typical page request.
# ( adapted from http://flask.pocoo.org/docs/0.11/shell/ )
democoursehomeurl = '/' + url_basename + '/demo/home'
request_context = app.test_request_context(democoursehomeurl)
request_context.push()        # make it active
app.preprocess_request()      # code that runs before request

# variables for interactive tests
democourse = Course.get(name='Demo Course')
homepage = Page.get_from_path('demo/home')
jane = Person.get(username='janedoe')

print "== Umber console | flask shell =="
print "Available variables include (democourse, homepage, jane, app, request)."
print "For formatted output of all defined names : >>> pp(vars())."

# -------------------------
# 
# >>> pp(vars())
# >>> dir()
# >>> dir(homepage)

