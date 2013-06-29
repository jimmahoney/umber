#!/usr/bin/env python
# -- coding: utf-8 --
"""
 umber.py
 See ./README.txt
 Jim Mahoney | mahoney@marlboro.edu | June 2013 | MIT License
"""

from flask import Flask, request, session, g, redirect, \
                  url_for, abort, render_template, flash
from src.settings import secret_key, project_path
from src.model import db_session, \
     Person, Role, Course, Registration, Assignment, Work

app = Flask(__name__)

#@app.context_processor
#def template_context():
#    """ Add variables and/or functions to all template context """
#    return dict(name=value, func=func_name, ...)

@app.teardown_request
def shutdown_db_session(exception=None):
    # As suggested in http://flask.pocoo.org/docs/patterns/sqlalchemy/
    db_session.remove()

@app.template_filter('static_url')
def static_url(filename):
    """ shortcut for static urls """
    # Use {{'path/to/file' | static_url}} in templates 
    # rather than {{url_for('static', filename='path/to/file')}}
    return url_for('static', filename=filename)

@app.route('/')
def index():
    return render_template('index.html')

#@app.route('/about')
#def about():
#    return render_template('about.html')

if __name__ == '__main__':
    app.secret_key = secret_key
    app.session_cookie_name = __name__ + '_session'
    app.run(debug = True,
            port = 8090,
            host = '0.0.0.0')

