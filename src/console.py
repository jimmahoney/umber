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

from settings import project_path

# umber.py is in in the project_path folder;
# this makes sure that it's in the import path.
import sys
sys.path.insert(0, project_path)

from umber import *

flask_context = app.test_request_context()
flask_context.push()

print "== Umber console =="

