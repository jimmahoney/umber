"""
 settings.py

 (1) Edit env/set_shell_variables to set the UMBER_CONFIG shell variable :

       $ export UMBER_CONFIG = DEVELOPMENT | PRODUCTION

 (2) Edit the variables marked with "customize" to fit your situation.

 ------------------------------------------------------
 
 The urls have this form :
                             
        PROTOCOL  SERVER_NAME    URL_BASE    page_path
   e.g. https://  umber.cc:433 / umber    /  demo/home

 The OS_* variables are absolute operating system paths, 
 without a trailing slash e.g. /var/www/umber

 See the Page class in model.py for more details for urls and paths.

 This file is loaded from umber.py with app.config_from_file(),
 and its defined constants are ALL_CAPS to be consistent with Flask.

"""
import os, sys, datetime
from os.path import realpath, join, dirname

OS_ROOT = realpath(join(dirname(realpath(__file__)), '..'))

if os.environ['UMBER_CONFIG'] == 'DEVELOPMENT':

    PROTOCOL = 'http://'
    SERVER_NAME = '127.0.0.1:5000'
    URL_BASE = 'umber'
    CONTACT_URL = '<a href="mailto:adam@fake.fake">Adam Admin</a>'
    SITE_URL = 'http://127.0.0.1:5000/umber/demo/home'
    
    OS_COURSES = os.path.join(OS_ROOT, 'courses')
    OS_DB = os.path.join(OS_ROOT, 'database', 'umber.db')
    OS_GIT = OS_COURSES

    DEBUG = True
    TESTING = True
    SECRET_KEY = 'seekrit'
    SESSION_COOKIE_NAME = 'umber_development'
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=1)
    LOCALTIMEZONE = 'US/Eastern'
    LOCALTIMEZONEOFFSET = '-05:00'

elif os.environ['UMBER_CONFIG'] == 'PRODUCTION':
                                                                       #
    PROTOCOL = 'https://'                                              # 
    SERVER_NAME = 'cs.marlboro.college'                                #  
    URL_BASE = 'cours'                                                 #  c
    CONTACT_URL = '<a href="mailto:jim@mahoney.cc">Jim Mahoney</a>'    #  u
    SITE_URL = 'https://cs.marlboro.edu'                               #  s
                                                                       #  t
    OS_DB = '/var/www/cours/_umber_marlboro.sql'                       #  o
    OS_COURSES = '/var/www/cours'                                      #  m
    OS_GIT = '/var/www/cours'                                          #  i
                                                                       #  z
    DEBUG = False                                                      #  e
    TESTING = False                                                    #
    SECRET_KEY = 'reeely_reely_seeekrit'                               #
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

