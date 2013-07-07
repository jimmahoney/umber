#!/usr/bin/env python
# -- coding: utf-8 --
"""
 umber.py
 See ./README.txt
 Jim Mahoney | mahoney@marlboro.edu | June 2013 | MIT License
"""

from flask import Flask, request, session, g, redirect, url_for, abort, flash
from flask.ext.mako import MakoTemplates, render_template
from flask.ext.login import LoginManager, login_user, logout_user
from src.settings import secret_key, project_path
from src.model import db_session, populate_db, \
     Person, AnonymousPerson, Role, Course, Registration, Assignment, Work
from src.page import Page
from datetime import timedelta

app = Flask('umber')
MakoTemplates(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = AnonymousPerson

@login_manager.user_loader
def load_user(username):
    """ Return Person corresponding to unicode userid, or None if invalid. """
    # load user from id stored in the session
    # see flask-login.readthedocs.org/en/latest/#flask.ext.login.LoginManager
    try:
        user = Person(username=username)
    except:
        user = None
    return user

@app.teardown_request
def shutdown_db_session(exception=None):
    # Close the database cleanly, as suggested
    # at flask.pocoo.org/docs/patterns/sqlalchemy
    db_session.remove()

@app.context_processor
def template_context():
    """ Make variables and/or functions available to all template contexts."""
    # These are in addition to 
    #  (a) the names passed via render_template(template, name=value, ...)
    #  (b) the default Flask globals
    # And there can be many of these app.context_processor additions.
    # With mako templates, functions are also filters : ${f(x)} or ${x|f}
    return dict(static_url = lambda f: url_for('static', filename=f))

@app.before_request
def load_user():
    """ Before route triggers, get user from session data """
    # see http://stackoverflow.com/questions/13617231/how-to-use-g-user-global-in-flask
    ## for testing  :
    session['test'] = 'testing session'              # request thread variable
    g.bar = 'BAR'                                    # global variable

@app.route('/testing')
def testing():
    return render_template('misc/testing.html',        # template
                           name = 'index',
                           foo = 'foolish'           # context variables
        )

@app.route('/umber/<path:path>', methods=['GET', 'POST'])
def main():
    # The Flask global variables available by default within
    # within template contexts by are 
    #   config (but not in mako?)
    #   request, session, g, 
    #   url_for(), get_flashed_messages()
    # all of which are also within global app.*
    # Also see template_context(), which can set more template globals.
    if request.method == 'POST':
        do_something()
    return render_template('main.html', 
                           name ='main',
                           page = Page(path=path), 
                           course = Course(),
        )

def do_something():
    """ login, modify file, ... """
    pass

def setup():
    app.secret_key = secret_key
    app.session_cookie_name = __name__ + '_session'
    app.permanent_session_lifetime = timedelta(days=1)
    ## use Flask-Login patterns for this
    #session.permanent = True  # error : working outside of request context
    #session['username'] = ''

if __name__ == '__main__':
    setup()
    app.run(debug = True,
            port = 8090,
            host = '0.0.0.0')

