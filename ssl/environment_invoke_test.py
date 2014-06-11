"""
 $ python environment_invoke_test.py
 SSL is off

 $ SSL=true python environment_invoke_test.py
 SSL is on

"""

import os
if os.environ.get('SSL'):
    print "SSL is on"
else:
    print "SSL is off"


