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
from src.model import db_session, populate_db, \
     Person, Role, Course, Registration, Assignment, Work
from page import Page

app = Flask('umber')

@app.teardown_request
def shutdown_db_session(exception=None):
    # Close the database cleanly, as suggested
    # at flask.pocoo.org/docs/patterns/sqlalchemy
    db_session.remove()

@app.template_filter('static_url')
def static_url(filename):
    """ shortcut for static urls """
    # Use {{'path/to/file' | static_url}} in templates 
    # rather than {{url_for('static', filename='path/to/file')}}
    return url_for('static', filename=filename)

# See http://flask.pocoo.org/docs/api/#url-route-registrations
# for the details on matching URLs to function calls.

@app.context_processor
def template_context():
    """ Make variables and/or functions available to all template contexts."""
    # These are in addition to 
    # (a) the names passed via render_template(template, name=value, ...) and
    # (b) the default Flask globals
    # And there can be many of these app.context_processor additions.
    return dict(
        dir = lambda x: dir(x),   # template language pythonic additions
        str = lambda x: str(x)
        )


@app.before_request
def load_user():
    """ Before route triggers, get user from session data """
    # see http://stackoverflow.com/questions/13617231/how-to-use-g-user-global-in-flask
    

@app.route('/umber/<path:path>', methods=['GET', 'POST'])
def index():
    # The Flask global variables available by default within
    # within template contexts by are 
    #   config , request, session, g, url_for(), get_flashed_messages()
    # all of which are also within global app.*
    # Also see template_context(), which can set more template globals.
    user = g.user
    page = g.page = Page(path=path)
    course g.course = Course() # TODO : from page's parsed path and data
    if request.method == 'POST':
        do_something()
    return render_template('main.html', page=page, user=user, course=course)

def do_something():
    """ login, modify file, ... """
    pass

## testing
#@app.route('/')
#def index():
#    g.bar = 'BAR'                                   # globals
#    return render_template('misc/index.html',       # template
#                           foo = 'foolish'          # context variables
#                          )

## sample route
#@app.route('/about')
#def about():
#    return render_template('about.html')

def setup():
    app.secret_key = secret_key
    app.session_cookie_name = __name__ + '_session'
    app.permanent_session_lifetime = datetime.timedelta(1) # 1 day
    session.permanent = True
    session['username'] = ''

if __name__ == '__main__':
    setup()
    app.run(debug = True,
            port = 8090,
            host = '0.0.0.0')

