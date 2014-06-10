"""
 settings.py

 Project site-specific directory and url paths :

    secret_key
    os_root
    courses_os_base
    courses_url_base

 See model.py for a discussion of how these are used.

"""
import sys, os

# TODO: generate this randomly for production deployment.
secret_key = "umber - SEEKRIT"

courses_url_base = 'umber'
courses_os_base = 'courses'

def _get_os_root():
    """ Return absolute path to project root folder without trailing slash."""
    # i.e. the folder above this src/settings.py file
    # e.g. /Users/mahoney/academics/umber
    # This is also $VIRTUAL_ENV/.. , as defined by pythonic virtualenv
    my_folder = os.path.dirname(os.path.realpath(__file__))
    parent_folder = os.path.abspath(my_folder + '/..')
    return parent_folder

os_root = _get_os_root()
