# -- coding: utf-8 --
"""
 src/console.py
 An interactive shell for the umber project.

 The intended invocation is from the umber/ folder :
   $ ./console
   == Umber console ==
   >>>

 Jim Mahoney | mahoney@marlboro.edu | MIT License
"""

from settings import os_root

# umber.py is in in the os_root folder;
# this makes sure that's in python's import path.
import sys
sys.path.insert(0, os_root)

from umber import *

flask_context = app.test_request_context()
flask_context.push()

# some variables that may be useful for testing
# 

umber = Course.find_by(name='Umber')
demo = Course.find_by(name='Demo Course')

print "== Umber console =="

