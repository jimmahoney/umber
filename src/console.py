"""
 console.py -  interactive flask shell console 

    $ umber_console     # This is invoked from bin/umber_console.
    ...
    >>> jane
    Person(username=u'janedoe', ...)
"""

import os, sys
from pprint import pprint as pp
from flask import request, url_for
from settings import *

# Make sure that umber.py is in python's import path
sys.path.insert(0, os.path.join(os_root, 'src'))

from umber import *
from admintools import *
from utilities import markdown2html

# Set a context for a page request (see flask.pocoo.org/docs/0.11/shell/).
request_context = app.test_request_context('')
request_context.push()        # Make it active.
app.preprocess_request()      # Run the pre-requrest code.

print("== Umber console | flask shell | {} ==".format(
    os.environ['UMBER_CONFIG'].lower()))
print("Database file is {}".format(os_db))
print("To see all defined names : pp(vars()) .")

if os.environ['UMBER_CONFIG'] == 'DEVELOPMENT':
    democourse = Course.get(name='Demo Course')
    homepage = Page.get_from_path('demo/home')
    jane = Person.get(username='janedoe')
    print("Variables include (democourse, homepage, jane, app, request).")
