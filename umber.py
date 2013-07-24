#!/usr/bin/env python
# -- coding: utf-8 --
"""
 umber.py
 See ./README.txt
 Jim Mahoney | mahoney@marlboro.edu | June 2013 | MIT License
"""
import sys 
sys.dont_write_bytecode = True   # development

from flask import Flask, request, session, g, redirect, url_for, abort, \
     flash, get_flashed_messages
from flask.ext.mako import MakoTemplates, render_template
from flask.ext.login import LoginManager, login_user, logout_user, current_user
from src.settings import secret_key, project_os_path, \
     pages_url_root, pages_os_root
from src.model import db_session, populate_db, anonymous_person, \
     Person, Role, Course, Registration, Assignment, Work, \
     Directory, Permission, Page
from datetime import timedelta
from re import match

app = Flask('umber')
MakoTemplates(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = anonymous_person

@login_manager.user_loader
def load_user(user_session_id):
    """ Return Person corresponding to unicode session id, or None. """
    # see flask-login.readthedocs.org/en/latest/#flask.ext.login.LoginManager
    try:
        user = Person(username = user_session_id)
        user.set_status(logged_in = True, role = 'guest')  # TODO handle course & roles
    except:
        user = None
    return user

@app.teardown_request
def shutdown_db_session(exception=None):
    # Close the database cleanly, as suggested
    # at flask.pocoo.org/docs/patterns/sqlalchemy
    db_session.remove()

def get_message():
    messages = get_flashed_messages()
    if len(messages) > 0:
        return messages[0]
    else:
        return "&nbsp;"

@app.context_processor
def template_context():
    """ Make variables and/or functions available to all template contexts."""
    # These are in addition to 
    #  (a) the names passed via render_template(template, name=value, ...)
    #  (b) the default Flask globals
    # And there can be many of these app.context_processor additions.
    # With mako templates, functions are also filters : ${f(x)} or ${x|f}
    return dict(static_url = lambda f: url_for('static', filename=f),
                message = get_message
                )

@app.before_request
def load_stuff():
    """ Before route triggers, do some stuff """
    # see http://stackoverflow.com/questions/13617231/how-to-use-g-user-global-in-flask
    ## for testing  :
    session['test'] = 'testing session'              # request thread variable
    g.bar = 'BAR'                                    # global variable

@app.route('/testing')
def testingroute():
    return render_template('misc/testing.html',        # template
                           name = 'index',
                           foo = 'foolish'           # context variables
        )

@app.route('/' + pages_url_root + '/<path:pagepath>', methods=['GET', 'POST'])
def mainroute(pagepath):
    # The Flask global variables available by default within
    # within template contexts by are 
    #   config (but not in mako?)
    #   request, session, g, 
    #   url_for(), get_flashed_messages()
    # all of which are also within global app.*
    # Also see template_context(), which can set more template globals.

    page = Page(pagepath = pagepath,
                request = request, 
                user = current_user,
                insecure_login = not app.has_ssl
        )

    if request.method == 'POST':
        handle_post()
    return render_template('main.html', 
                           name ='main',
                           page = page,
                           debug = app.debug
        )

def submit_logout():
    logout_user()

def submit_login():
    """ Process <input name='submit_login' ...> form submission. """
    try:
        user = Person.find_by(username = request.form['username'])
    except:
        flash('Oops: wrong username or password.')
        return
    if user.check_password(request.form['password']):
        user.set_status(logged_in = True, role = 'guest')
        login_user(user, force=True)
        return
    else:
        flash('Oops: wrong username or password.')
        return

def starts_with_submit(string):
    return match('submit', string)
    
def handle_post():
    """ Process a form submission (login, edit, upload, ...) """
    # Each form has an input field named 'submit_X' for some X,
    # and is handled by a corresponding function submit_X().
    # The data is in the Flask request global.
    try:
        keys_named_submit = filter(starts_with_submit, request.form.keys())
        submit_what = keys_named_submit[0]
        globals()[submit_what]()  # get function given its name & invoke it
    except:
        print " OOPS : handle_post() couldn't handle request.keys() = ", \
          request.keys()

def setup():
    app.secret_key = secret_key
    app.session_cookie_name = 'umber_session'
    app.permanent_session_lifetime = timedelta(days=1)
    app.has_ssl = False

if __name__ == '__main__':
    setup()
    app.run(debug = True,
            port = 8090,
            host = '0.0.0.0')

