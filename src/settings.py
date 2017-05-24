"""
 settings.py

 Project site-specific constants (file and url paths, ports, etc)

    secret_key
    os_root         # e.g. /Users/mahoney/sugar/academics/umber
    os_basename     # e.g. courses , folder with content pages
    os_base         # e.g. /Users/mahoney/sugar/academics/umber/courses
    os_src          # e.g. /Users/mahoney/sugar/academics/umber/src
    url_base        # e.g. umber , url prefix http://host/umber/...
    http_port
    https_port
    timezone
    db_path

 URLs have the form
     host url_base path
 e.g.
     http://localhost:8080/  umber    /  demo       / home
            host             url_base    course_path  page_path

 os paths to files files are
     os_base path
 e.g.
     /Users/mahoney/academics/umber/courses  / demo        /   home
     os_base                                   course_path     page_path

 where (os_base = os_root os_basename)

 See the Page class in model.py for more details.
 
"""
import sys, os

url_basename = 'umber'   # URL prefix for umber courses
os_basename = 'courses'  # course folder within project folder os_root

http_port = 8080
https_port = 8433

timezone = 'US/Eastern'
timezoneoffset = '-05:00'  # for ISO GMT strings

admin_email = '<a mailto:"mahoney@marlboro.edu">Jim Mahoney</a>' 

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
os_src = os.path.join(os_root, 'src')
os_template = os.path.join(os_root, 'templates')
os_static = os.path.join(os_root, 'static')

os_config = os.path.join(os_src, 'config.py')

db_path = os_root + '/database/umber.db'   # absolute sqlite3 file path

