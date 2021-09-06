"""
 settings.py

 Edit these to match your situation.

 The environment variables 
    UMBER_CONFIG          either DEVELOPMENT or PRODUCTION
    UMBER_SECRET_KEY      session crypto key
    GOOGLE_CLIENT_ID      google authentication keys
    GOOGLE_CLIENT_SECRET 
 must be defined elsewhere before this runs.

 See ../env/shell_* and ../src/etc_systemd_...

 ------------------------------------------------------------
 
 The urls for this app have this form :
                             
        protocol  hostname       url_base    page_path
   e.g. https://  umber.cc:433 / umber    /  demo/home

 The os_* variables are absolute operating system paths, 
 without a trailing slash e.g. /var/www/umber

 See the Page class in models.py for more details.

"""
import os, sys, datetime
from os.path import realpath, join, dirname

os_root = realpath(join(dirname(realpath(__file__)), '..'))

os_db = os.environ['UMBER_DATA']

localtimezone = 'US/Eastern'
# is EST (eastern standard time) UTC-05:00  in autumn & winter
# is EDT (eastern daylight time) UTC-04:00  in spring & summer
# This timezone designation must be understood by the python arrow library;
# see http://arrow.readthedocs.io/en/latest & arrow.get().to(localtimezone) .

# time after assignment due when they're marked late
# ... if server is UTC (4 or 5 off), this makes sure
# assignments aren't until after midnight ;  see model.py
due_grace_hours = 6

# The 'Umber' course has site docs, home, etc; this is its course URL path.
site_course_path = 'umber'
site_home = 'docs/home'

def umber_flask_configure(app):
    """ Configure some of Flask's internal settings. """
    app.config['DEBUG'] = (os.environ.get('UMBER_CONFIG') == 'DEVELOPMENT')
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)
    app.config['SESSION_COOKIE_NAME'] = 'umber'
    app.config['SECRET_KEY'] = os.environ.get('UMBER_SECRET_KEY')
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')
    # 5MB file upload limit
    # see https://blog.miguelgrinberg.com/post/handling-file-uploads-with-flask
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024   

if os.environ['UMBER_CONFIG'] == 'DEVELOPMENT':
    umber_debug = True
    protocol = 'http://'
    hostname = '127.0.0.1:5000'
    url_base = 'courses'        # all URLs start with this ... except static
    route_prefix = '/courses'   # for URL route matching
    contact_url = '<a href="mailto:adam@fake.fake">Adam Admin</a>'
    site_url = 'http://127.0.0.1:5000/courses/umber/docs/home'
    static_prefix = '/static/'
    os_courses = os.path.join(os_root, 'courses')
    os_default_course = os.path.join(os_root, 'courses/default_course')
    #umber_cleanup = ''
    debug_logfilename = ''
    umber_authentication = 'password'

elif os.environ['UMBER_CONFIG'] == 'PRODUCTION':
    # TODO : find a better way to pull all this out of the source tree.
    umber_debug = False  # i.e. don't print debug stuff to console
    protocol = 'https://'
    hostname = 'cs.bennington.college'
    url_base = 'courses'      
    route_prefix = '/courses'    # consistent with uwsgi; apache mod_wsgi needed ''
    contact_url = '<a href="mailto:jimmahoney@bennington.college">Jim Mahoney</a>'
    site_url = 'https://cs.bennington.college'
    static_prefix = '/courses_static/'
    os_courses = '/var/www/courses'
    os_default_course = '/var/www/courses/default_course'
    #umber_cleanup = '/var/www/courses/etc/bin/umber_cleanup'
    #umber_cleanup = '' # TODO : figure out what's needed for bennington deploy
    # debugging: see also
    #   * uwsgi errors in /var/log/umber/uwsgi.log
    #   * systemctl mwssages , command line "journalctl -u umber"
    #   * uwsgi stats; command line "uwsgitop /var/run/umber/stats.sock"
    #debug_logfilename = '/var/log/umber/umber.log'  # ... lots of output
    debug_logfilename = False   # disable debug logging
    umber_authentication = 'google'

else:
    raise Exception('Oops: UMBER_CONFIG environment variable is undefined.')

GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

umber_url = protocol + hostname + '/' + url_base
about_url = umber_url + '/umber/docs/about'
help_url = umber_url + '/umber/docs/help'
markup_url = umber_url + '/umber/docs/markup'
photos_url = umber_url + '/umber/photos'

# Custom mime-types for dynamic files (i.e. within courses);
# note that this may not change mime types for static files.
umber_mime_types = {x:'text/plain' for x in
    ('.py', '.c', '.cc', '.cpp', '.c++', '.c#', '.dot', '.lisp',
     '.java', '.hs', '.clisp', '.pl', '.tex', '.rb', '.yvtm', '.vtm', '.csv',
     '.i', '.s', '.objdump', '.sql', '.scm', '.rkt', 
    )}
# image mime type variations
umber_mime_types['.PNG'] = 'image/png'
umber_mime_types['.JPG'] = 'image/jpeg'
umber_mime_types['.JPEG'] = 'image/jpeg'
# pdf's
umber_mime_types['.pdf'] = 'application/pdf'
umber_mime_types['.PDF'] = 'application/pdf'
