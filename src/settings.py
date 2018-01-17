"""
 settings.py

 Edit these to match your situation.

 The environment variables 
    UMBER_CONFIG        (either DEVELOPMENT or PRODUCTION)
    UMBER_SECRET_KEY    (sesstion crypto key)
 must be defined elsewhere before this runs.

 See ../env/shell_* .

 ------------------------------------------------------------
 
 The urls have this form :
                             
        protocol  hostname       url_base    page_path
   e.g. https://  umber.cc:433 / umber    /  demo/home

 The os_* variables are absolute operating system paths, 
 without a trailing slash e.g. /var/www/umber

 See the Page class in models.py for more details.

"""
import os, sys, datetime
from os.path import realpath, join, dirname

os_root = realpath(join(dirname(realpath(__file__)), '..'))

localtimezone = 'US/Eastern'
localtimezoneoffset = '-05:00'

def umber_flask_configure(app):
    """ Configure some of Flask's internal settings. """
    app.config['DEBUG'] = (os.environ['UMBER_CONFIG'] == 'DEVELOPMENT')
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)
    app.config['SESSION_COOKIE_NAME'] = 'umber'
    app.config['SECRET_KEY'] = os.environ['UMBER_SECRET_KEY']

if os.environ['UMBER_CONFIG'] == 'DEVELOPMENT':
    umber_debug = True
    protocol = 'http://'
    hostname = '127.0.0.1:5000'
    url_base = 'umber'            # used for generating URLs
    route_prefix = '/umber'       # used for route match of URL
    contact_url = '<a href="mailto:adam@fake.fake">Adam Admin</a>'
    site_url = 'http://127.0.0.1:5000/umber/demo/home'
    os_courses = os.path.join(os_root, 'courses')
    os_git = os_courses
    os_db = os.path.join(os_root, 'database', 'umber.db')
    
elif os.environ['UMBER_CONFIG'] == 'PRODUCTION':
    umber_debug = False
    protocol = 'https://'
    hostname = 'cs.marlboro.college'
    url_base = 'cours'      
    route_prefix = ''  # in apache wsgi config route already has /cours/
    contact_url = '<a href="mailto:jim@mahoney.cc">Jim Mahoney</a>'
    site_url = 'https://cs.marlboro.edu'
    os_db = '/var/www/cours/umber_mboro.db'
    os_courses = '/var/www/cours'
    os_git = '/var/www/cours'

else:
    raise Exception('Oops: UMBER_CONFIG environment variable is undefined.')

umber_url = protocol + hostname + '/' + url_base
about_url = umber_url + '/site/docs/about'
help_url = umber_url + '/site/docs/help'
photos_url = umber_url + '/site/photos'

debug_logfilename = None

