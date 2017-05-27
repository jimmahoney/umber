"""
 config.py

 flask configuration file
 see http://flask.pocoo.org/docs/0.12/config/

 See also ./settings.py which has among other app data
 the path to this file which is used by flask's app.config.from_pyfile

"""
import datetime

TESTING = True                 # TEST & DEBUG 
DEBUG = True                   # 

SECRET_KEY = 'umber seekrit'   # TEST & DEBUG 

SESSION_COOKIE_NAME = 'umber_session'
PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=1)


