"""
 utilities.py
"""

from flask import url_for

def _get_project_path():
    """ Return absolute path to planet_express, without trailing slash"""
    # Assumes that the project folder is one up from here, at ./..
    import sys, os
    my_folder = os.path.dirname(os.path.realpath(__file__))
    parent_folder = os.path.abspath(my_folder + '/..')
    return parent_folder

project_path = _get_project_path()

# TODO: generate this randomly for production deployment.
secret_key = "umber - SEEKRIT"


