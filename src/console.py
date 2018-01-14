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

import os, sys
from pprint import pprint as pp
from flask import request, url_for
from settings import OS_ROOT, URL_BASE

# Make sure that umber.py is in python's import path
sys.path.insert(0, os.path.join(OS_ROOT, 'src'))

from umber import *
from utilities import markdown2html

# Set context for a typical page request.
# ( adapted from http://flask.pocoo.org/docs/0.11/shell/ )
democoursehomeurl = '/' + URL_BASE + '/demo/home'
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


