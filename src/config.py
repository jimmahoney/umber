"""
 config.py

 flask configuration file
 see http://flask.pocoo.org/docs/0.11/config/
 
"""
import datetime

TESTING = True                 # TEST & DEBUG 
DEBUG = True                   # 

SECRET_KEY = 'umber seekrit'   # TEST & DEBUG 

SESSION_COOKIE_NAME = 'umber_session'
PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=1)
