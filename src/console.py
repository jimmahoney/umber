# - user console initialization -
# flask python shell packages and variables
#
# This is called from bin/umber_console , which invokes "flask shell"
#

from settings import os_src, os_root, os_basename, url_basename
from pprint import pprint as pp
from flask import request, url_for

# umber.py is in in the os_src folder;
# make sure that is in python's import path.
import sys
sys.path.insert(0, os_src)

from umber import *

print
print "== Umber console | flask shell =="
print

# variables for interactive tests
democourse = Course.get(name='Demo Course')
jane = Person.get(username='janedoe')

# adapted from http://flask.pocoo.org/docs/0.11/shell/
democoursehomeurl = '/' + url_basename + '/demo/home'
request_context = app.test_request_context(democoursehomeurl)
request_context.push()        # make it active
app.preprocess_request()      # code that runs before request

#home = Page('demo/home', user=jane)  # demo course home page as jane
# print "   variables: demo, jane, home"

# introspection :
# >>> pp(vars())

# a template page :
# >>> html = testroute()

