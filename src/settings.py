"""
 settings.py

 Project site-specific constants (file and url paths, ports)

    secret_key
    os_root
    os_base
    url_base
    http_port
    https_port

 URLs have the form
     host url_base path
 e.g.
     http://localhost:8080/  umber    /    demo/home
            host             url_base      path

 files are at
     os_root os_base path
 e.g.
     /Users/mahoney/academics/umber /  courses  /  demo/home
     os_root                           os_base     path
    
"""
import sys, os

# TODO: generate this randomly for production deployment.
secret_key = "umber - SEEKRIT"

url_base = 'umber'
os_base = 'courses'

http_port = 8080
https_port = 8433

def _get_os_root():
    """ Return absolute path to project root folder without trailing slash."""
    # i.e. the folder above src/ which is what this settings.py file is in.
    # On my mac develepment laptop this is /Users/mahoney/academics/umber
    # Another way to get this is from the parent of virtualenv folder (env/),
    # i.e. $VIRTUAL_ENV/..
    my_folder = os.path.dirname(os.path.realpath(__file__))
    parent_folder = os.path.abspath(my_folder + '/..')
    return parent_folder

os_root = _get_os_root()
