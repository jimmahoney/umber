"""
 settings.py

 Project site-specific constants (file and url paths, ports, etc)

    secret_key
    os_root         # e.g. /Users/mahoney/sugar/academics/umber
    os_basename     # e.g. courses , folder with content pages
    os_base         # e.g. /Users/mahoney/sugar/academics/umber/courses
    os_src          # e.g. /Users/mahoney/sugar/academics/umber/src
    url_basename    # e.g. umber , url prefix http://host/umber/...
    http_port
    https_port
    timezone
    db_path

 URLs have the form
     host url_basename path
 e.g.
     http://localhost:8080/  umber         /  demo       / home
            host             url_basename    course_path  page_path

 os paths to files files are
     os_base path
 e.g.
     /Users/mahoney/academics/umber/courses  / demo        /   home
     os_base                                   course_path     page_path

 where (os_base = os_root os_basename)

 See the Page class in model.py for more details.

 ------------

 Part of this file is also acting as flask's configuration file;
 its path is fed to the flask app. See the config.py notes below.
 
"""
import sys, os

url_basename = 'umber'    # URL prefix for umber courses
_os_basename = 'cours'    # course folder within project folder os_root

git_base = 'courses'     # root of git repo; append page.path for its git path

host = '127.0.0.1:5000'  # host:port      : for constructing breadcrumb url
protocol = 'http'        # http | https

umber_url_base = protocol + '://' + host + '/' + url_basename

admin_email = '<a mailto:"mahoney@marlboro.edu">Jim Mahoney</a>' 
about_copyright_url = umber_url_base + '/site/docs/about'
help_url = umber_url_base + '/site/docs/help'

localtimezone = 'US/Eastern'
localtimezoneoffset = '-05:00'  # for ISO GMT strings

def _get_os_root():
    """ Return absolute path to project folder, without trailing slash."""
    # i.e. the folder above src/ which is what this settings.py file is in.
    # On my mac develepment laptop this is /Users/mahoney/academics/umber
    # (This is also UMBER_ROOT in the project environment.)
    my_folder = os.path.dirname(os.path.realpath(__file__))
    parent_folder = os.path.abspath(my_folder + '/..')
    return parent_folder

os_root = _get_os_root()
os_src = os.path.join(os_root, 'src')
os_template = os.path.join(os_root, 'templates')
os_static = os.path.join(os_root, 'static')

# ***
# root of folder with course files
os_base = os.path.join(os_root, _os_basename) 

# user images , <username>.jpg ,
# about (122 x 152) px (what nook.marlboro.edu is using Jan 2018)
photo_folder_url = umber_url_base + '/site/photos/'

db_path = os_root + '/database/umber.db'   # absolute sqlite3 file path

os_config = os.path.join(os_src, 'settings.py')  # ... this file (!)

# --------------
# os_config = os.path.join(os_src, 'config.py')
# -------------------
# What's below here was in config.py ,
# and may need multiple versions for different deployment situations.
#
# This part is the flask configuration file ;
# see http://flask.pocoo.org/docs/0.12/config/

import datetime

TESTING = True                 # TEST & DEBUG 
DEBUG = True                   # 

SECRET_KEY = 'umber seekrit'   # TEST & DEBUG 

SESSION_COOKIE_NAME = 'umber_session'
PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=1)

