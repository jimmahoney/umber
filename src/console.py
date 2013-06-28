# -- coding: utf-8 --
"""
 src/console.py
 An interactive shell for the umber project.

 The intended invocation is from the umber/ folder :
   $ ./console
   >>>          

 Jim Mahoney | mahoney@marlboro.edu | MIT License
"""

from utilities import project_path

# umber.py is in in the project_path folder.
import sys
sys.path.insert(0, project_path)
from umber import *

# Create a "context" variable
c = app.test_request_context()
c.push()

print "Welcome to Umber."

