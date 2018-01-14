"""
 settings.py

 (1) Set an environment variable before running this :

       $ export UMBER_CONFIG = DEVELOPMENT | PRODUCTION

 (2) Edit the variables marked with "customize" to match your installation.

 ------------------------------------------------------
 
 The umber urls have this form :
                             
        PROTOCOL  SERVER_NAME    URL_BASE    page_path
   e.g. https://  umber.cc:433 / umber    /  demo/home

 Its named folders and file constants are

        OS_COURSES  e.g. OS_ROOT/courses   
        OS_DB       e.g. OS_ROOT/database/umber.sql
        OS_GIT      e.g. OS_ROOT

 as well as

        OS_ROOT    e.g. /Users/mahoney/sugar/academics/umber
        which is computed from the location of this file.

 -------------------------------------------------------------------

 See the Page class in model.py for more details for urls and paths.

 Note that this file is loaded from umber.py with app.config_from_file().
 (And its defined constants are ALL_CAPS to be consistent with Flask.)

"""
import os, sys, datetime
from os.path import abspath, join, realpath

OS_ROOT = abspath(join(realpath(__file__), '..'))

if os.environ('UMBER_CONFIG') == 'DEVELOPMENT':

    PROTOCOL = 'http://'
    SERVER_NAME = '127.0.0.1:5000'
    URL_BASE = 'umber'
    ADMIN_CONTACT_URL = '<a mailto:"adam@fake.fake">Adam Administrator</a>'  # ** Customize **
    
    OS_COURSES = os.path.join(OS_ROOT, 'courses')
    OS_DB = os.path.join(OS_ROOT, 'database', 'umber.sql')
    OS_GIT = OS_ROOT

    DEBUG = True
    TESTING = True
    SECRET_KEY = 'seekrit'
    SESSION_COOKIE_NAME = 'umber'
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=1)
    LOCALTIMEZONE = 'US/Eastern'
    LOCALTIMEZONEOFFSET = '-05:00'

elif os.environ('UMBER_CONFIG') == 'PRODUCTION':
                                                                       #
    PROTOCOL = 'http://'                                               # 
    SERVER_NAME = 'cs.marlboro.college'                                #  c
    URL_BASE = 'cours'                                                 #  u
    ADMIN_CONTACT_URL = '<a mailto:"jim@mahoney.cc">Jim Mahoney</a>'   #  s
                                                                       #  t
    OS_COURSES = '/var/www/cours'                                      #  m
    OS_DB = '/var/www/cours/_umber_marlboro.sql'                       #  i
    OS_GIT = '/var/www/cours'                                          #  z
                                                                       #  e
    DEBUG = False                                                      #
    TESTING = False                                                    #
    SECRET_KEY = 'seeekrit_marlboro'                                   #
    SESSION_COOKIE_NAME = 'umber_marlboro'                             #
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=1)            #
    LOCALTIMEZONE = 'US/Eastern'                                       #
    LOCALTIMEZONEOFFSET = '-05:00'                                     #
    
else:
    raise Exception('Oops: UMBER_CONFIG environment variable is undefined.')

UMBER_URL = PROTOCOL + SERVER_NAME + '/' + URL_BASE
ABOUT_URL = UMBER_URL + '/site/docs/about'
HELP_URL = UMBER_URL + '/site/docs/help'
PHOTOS_URL = UMBER_URL + '/site/photos'

OS_SRC = join(OS_ROOT, 'src')
OS_TEMPLATE = join(OS_ROOT, 'templates')
OS_STATIC = join(OS_ROOT, 'static')

# =============================================================================
#
# url_basename = 'umber'    # URL prefix for umber courses
# _os_basename = 'cours'    # course folder within project folder os_root
#
# git_base = 'courses'     # root of git repo; append page.path for its git path
#
# host = '127.0.0.1:5000'  # host:port      : for constructing breadcrumb url
# protocol = 'http'        # http | https
#
# umber_url_base = protocol + '://' + host + '/' + url_basename
#
# about_copyright_url = umber_url_base + '/site/docs/about'
# help_url = umber_url_base + '/site/docs/help'
#
# # ----------------------------------------------------------
#
# os_root = _get_os_root()
# os_src = os.path.join(os_root, 'src')
# os_template = os.path.join(os_root, 'templates')
# os_static = os.path.join(os_root, 'static')
#
# # ***
# # root of folder with course files
# os_base = os.path.join(os_root, _os_basename) 
#
# # user images , <username>.jpg ,
# # about (122 x 152) px (what nook.marlboro.edu is using Jan 2018)
# photo_folder_url = umber_url_base + '/site/photos/'
#
# db_path = os_root + '/database/umber.db'   # absolute sqlite3 file path
#
# os_config = os.path.join(os_src, 'settings.py')  # ... this file (!)
#
# # --------------
# # os_config = os.path.join(os_src, 'config.py')
# # -------------------
# # What's below here was in config.py ,
# # and may need multiple versions for different deployment situations.
# #
# # This part is the flask configuration file ;
# # see http://flask.pocoo.org/docs/0.12/config/
#
# import datetime
#
# TESTING = True                 # TEST & DEBUG 
# DEBUG = True                   # 
#
# SECRET_KEY = 'umber seekrit'   # TEST & DEBUG 
#
# SESSION_COOKIE_NAME = 'umber_session'
# PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=1)

