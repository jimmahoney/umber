"""
 settings.py

 Project site-specific constants (file and url paths, ports, etc)

    secret_key
    os_root         # e.g. /Users/mahoney/sugar/academics/umber
    os_basename     # e.g. courses , folder with content pages
    os_base         # e.g. /Users/mahoney/sugar/academics/umber/courses
    url_base        # e.g. umber , url prefix http://host/umber/...
    http_port
    https_port
    timezone
    db_path

 URLs have the form
     host url_base path
 e.g.
     http://localhost:8080/  umber    /  demo/home
            host             url_base    path

 os paths to files files are
     os_base path
 e.g.
     /Users/mahoney/academics/umber/courses  /  demo/home
     os_base                                    path

 where (os_base = os_root os_basename)
         
"""
import sys, os

# TODO: generate this randomly for production deployment.
secret_key = "umber - SEEKRIT"

url_base = 'umber'       # URL prefix for umber courses
os_basename = 'courses'  # course folder within project folder os_root

http_port = 8080
https_port = 8433

timezone = 'US/Eastern'

def _get_os_root():
    """ Return absolute path to project folder, without trailing slash."""
    # i.e. the folder above src/ which is what this settings.py file is in.
    # On my mac develepment laptop this is /Users/mahoney/academics/umber
    # (This is also UMBER_ROOT in the project environment.)
    my_folder = os.path.dirname(os.path.realpath(__file__))
    parent_folder = os.path.abspath(my_folder + '/..')
    return parent_folder

os_root = _get_os_root()
os_base = os.path.join(os_root, os_basename)

# sqlite3 version, used in sqlalchemy's create_engine() function
db_path = 'sqlite:///' + os_root + '/database/sqlite3/umber.db'

