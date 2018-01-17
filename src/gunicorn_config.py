""" gunicorn_config.py 

    # from umber root folder, parent of this one
    $ . venv/bin/activate
    $ gunicorn --config src/gunicorn_config.py umber:app

    or as explicit options

          --check-config
          --env KEY=value 
          --chdir /full/path/to/folder
          --access-logfile FILE                - for stdout
          --error-logfile FILE                 - for stderr
          --spew                               trace every execution line
          --loglevel                           debug|info|warning|error|critical
          --capture-output                     stdout,stderr to error log
          --pythonpath /one/a,/one/b

"""

UMBER_ROOT = '/Users/mahoney/sugar/academics/umber'

import os
os.environ['UMBER_CONFIG'] = 'DEVELOPMENT'
os.environ['UMBER_ROOT'] = UMBER_ROOT

# -----------------------------------------------

loglevel = 'debug'
errorlog = '-'
accesslog = '-'

pythonpath = UMBER_ROOT + '/src'
bind = "127.0.0.1:4000"
workers = 4
capture_output = True


