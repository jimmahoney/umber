#!/usr/bin/env python
# -- coding: utf-8 --
"""
 umber.py

 To run this for development testing :
 
   $ ./database/reset_db ; ./console
   >>> # see src/model.py for what you can do

   $ python umber.py
   and then visit /test or /umber/demo/home
   at http://localhost:8080/ or https://localhost:8443

 Also see ./README.md, src/*, database/*, and docs/history.txt .

 Jim Mahoney | mahoney@marlboro.edu | June 2013 | MIT License
"""
import sys, datetime, re, os
from flask import Flask, request, session, g, \
     redirect, url_for, abort, flash, get_flashed_messages
from flask.ext.login import LoginManager, login_user, logout_user, current_user
from src.settings import secret_key, os_root, \
     courses_url_base, courses_os_base
from src.model import db_session, populate_db, anonymous_person, \
     Person, Role, Course, Registration, Assignment, Work, Page
from flask import render_template
from OpenSSL import SSL

sys.dont_write_bytecode = True   # don't create .pyc's during development

app = Flask('umber')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = anonymous_person

ssl_context = SSL.Context(SSL.SSLv23_METHOD)
ssl_context.use_privatekey_file('ssl/ssl.key')
ssl_context.use_certificate_file('ssl/ssl.crt')

@login_manager.user_loader
def load_user(user_session_id):
    """ Return Person corresponding to unicode session id, or None. """
    # see flask-login.readthedocs.org/en/latest/#flask.ext.login.LoginManager
    try:
        # TODO handle course & roles ; for now do something quick and simple.
        user = Person(username = user_session_id)
        user.set_status(logged_in = True, role = 'guest')  
    except:
        user = None
    return user

@app.teardown_request
def shutdown_db_session(exception=None):
    # Close the database cleanly,
    # per http://flask.pocoo.org/docs/patterns/sqlalchemy
    db_session.remove()

def get_message():
    # Intended for user interface messages, e.g. "incorrect login"
    messages = get_flashed_messages()
    if len(messages) > 0:
        return messages[0]
    else:
        return "&nbsp;"

@app.context_processor
def template_context():
    """ Set variables and/or functions for all template contexts."""
    # These are in addition to 
    #  (a) the names passed via render_template(template, name=value, ...)
    #  (b) the default Flask globals
    # And there can be many of these app.context_processor additions.
    # With mako templates, functions are also filters : ${f(x)} or ${x|f}
    return dict(static_url = lambda f: url_for('static', filename=f),
                message = get_message,
                # python functions imported into jinja2 template context
                dir = dir    # built-in python function dir()
                )

@app.before_request
def before_request():
    """ Do whatever needs doing before template handling """
    # e.g. set information to be passed to the template engine as in
    # stackoverflow.com/questions/13617231/how-to-use-g-user-global-in-flask .
    #
    # These are for firsttest.html :
    session['test'] = 'testing session'       # request thread variable
    g.alpha = 'beta'                          # a global variable

@app.route('/test')
def test():
    # The variables that Flask makes available by default within templates
    # (See http://flask.pocoo.org/docs/templating/ )
    #    config (jinja2), context (mako)
    #    g, request, session, current_user (both)
    # See @app.context_processor (above) where custom template vars can be set.
    return render_template('test/test.html',   # template
                           test1 = 'George',   # variables
                           test2 = 'foobar'
        )

@app.route('/' + courses_url_base + '/<path:path>', methods=['GET', 'POST'])
def mainroute(path):
    page = Page(path = path,
                request = request, 
                user = current_user, 
                )
    #print " mainroute: current_user = " + str(current_user)
    #print " mainroute: page = " + str(page)
    #print " mainroute: course = " + str(page.course)
    if request.method == 'POST':
        handle_post()
    return render_template('umber/main.html',
                           name = 'main',
                           page = page,
                           user = current_user,
                           debug = app.debug   # True or False; see app.run
                           )

def submit_logout():
    # invoked from handle_post()
    logout_user()

def submit_login():
    """ Process <input name='submit_login' ...> form submission. """
    # invoked from handle_post()
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
    return re.match('submit', string)
    
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
    app.permanent_session_lifetime = datetime.timedelta(days=1)

if __name__ == '__main__':
    setup()
    #try:
    #    pid = os.fork()
    #except:
    #    print "OOPS - couldn't fork"
    #    sys.exit(1)
    if os.environ.get('SSL'):
        app.run(host = '0.0.0.0',
                port = 8443, 
                debug = True,
                ssl_context = ssl_context)
    else:
        app.run(host = '0.0.0.0',
                port = 8080,
                debug = True,
                )

