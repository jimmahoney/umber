"""
 config.py

 flask configuration file
 see http://flask.pocoo.org/docs/0.12/config/
 
"""
import datetime

TESTING = True                 # TEST & DEBUG 
DEBUG = True                   # 

SECRET_KEY = 'umber seekrit'   # TEST & DEBUG 

SESSION_COOKIE_NAME = 'umber_session'
PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=1)

# (localhost has no . and is apparently therefore bad.)
# Trying to set port ... but still on 5000 (!?) 
# SERVER_NAME = '127.0.0.1:8080' 

