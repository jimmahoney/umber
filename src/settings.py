"""
 settings.py

 Project site-specific paths and names :

    secret_key
    project_os_path
    pages_os_root
    pages_url_root

"""
import sys, os

# TODO: generate this randomly for production deployment.
secret_key = "umber - SEEKRIT"

pages_url_root = 'umber'   # e.g. http://<host>/umber/demo_course/home
pages_os_root = 'pages'    # e.g. project_path/pages/demo_course/home

def _get_project_os_path():
    """ Return absolute path to project folder without trailing slash."""
    # i.e. the folder above the one containing this file.
    my_folder = os.path.dirname(os.path.realpath(__file__))
    parent_folder = os.path.abspath(my_folder + '/..')
    return parent_folder

project_os_path = _get_project_os_path()



