# -- coding: utf-8 --
"""
 src/console.py
 An interactive shell for the umber project.

 The intended invocation is from the umber/ project folder :
   $ ./run/console
   == Umber console ==
   >>>

 Jim Mahoney | mahoney@marlboro.edu | MIT License
"""

from settings import os_root
from pprint import pprint as pp

# umber.py is in in the os_root folder;
# make sure that umber.py is in python's import path.
# import sys
# sys.path.insert(0, os_root)

from umber import *

flask_context = app.test_request_context()
flask_context.push()

print "== Umber console =="

# variables for interactive tests
demo = Course.find_by(name='Demo Course')
jane = Person.find_by(username='janedoe')
home = Page('demo/home', user=jane)  # demo course home page as jane
# print "   variables: demo, jane, home"

# introspection :
# >>> pp(vars())

# a template page :
# >>> html = testroute()




