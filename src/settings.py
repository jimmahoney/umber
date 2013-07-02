"""
 settings.py

 Project site-specific paths and names :

    project_path
    secret_key
 
"""

# from flask import url_for

def _get_project_path():
    """ Return absolute path to project folder without trailing slash."""
    # i.e. the folder above the one containing this file.
    import sys, os
    my_folder = os.path.dirname(os.path.realpath(__file__))
    parent_folder = os.path.abspath(my_folder + '/..')
    return parent_folder

project_path = _get_project_path()

url_course_prefix = '/courses'

# TODO: generate this randomly for production deployment.
secret_key = "umber - SEEKRIT"


