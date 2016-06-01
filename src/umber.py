# -- coding: utf-8 --
"""
 umber.py

 Running this for development looks like this.

   set PATH 
   $ source env/activate

   initialize database (   
   $ umber_init_db

   interact with sql database
   $ umber_console
   >>> # see src/model.py for what you can do

   turn on http and https with the server script to browse & debug pages
   $ umber_server

   with a browser, visit urls like
     https://localhost:8443/test
     http://localhost:8080/umber/demo/home

 Also see ./README.md, src/*, database/*, and docs/history.txt .

 Jim Mahoney | mahoney@marlboro.edu | June 2013 | MIT License
"""
import sys, datetime, re, os

# from OpenSSL import SSL

from flask import Flask, request, session, g, \
     redirect, url_for, abort, flash, get_flashed_messages
from flask.ext.login import LoginManager, login_user, logout_user, current_user
from flask import render_template

from settings import secret_key, os_root, os_base, url_base,
     http_port, https_port
from model import db, anonymous_person, \
     Person, Role, Course, Registration, Assignment, Work
from page import Page, ArrowTime

sys.dont_write_bytecode = True   # don't create .pyc's during development

app = Flask('umber')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = anonymous_person

# ssl_context = SSL.Context(SSL.SSLv23_METHOD)
# ssl_context.use_privatekey_file('../ssl/ssl.key')
# ssl_context.use_certificate_file('../ssl/ssl.crt')

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

def get_message():
    # Intended for user interface messages, e.g. "incorrect login"
    messages = get_flashed_messages()
    if len(messages) > 0:
        return messages[0]
    else:
        return " "

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
    """ initialize database and session """
    #
    # See http://docs.peewee-orm.com/en/latest/peewee/database.html
    db.connect()
    #   
    # Set information to be passed to the template engine as in
    # stackoverflow.com/questions/13617231/how-to-use-g-user-global-in-flask
    #
    # These are for firsttest.html :
    session['test'] = 'testing session'       # request thread variable
    g.alpha = 'beta'                          # a global variable

@app.teardown_request
def after_request(exception=None):
    db.close()
    
@app.route('/test')
def testroute():
    # The variables that Flask makes available by default within templates
    # (See http://flask.pocoo.org/docs/templating/ )
    #    config (jinja2), context (mako)
    #    g, request, session, current_user (both)
    # See @app.context_processor (above) where custom template vars can be set.
    return render_template('test/test.html',   # template
                           test1 = 'George',   # variables
                           test2 = 'foobar'
        )

@app.route('/' + url_base + '/<path:pagepath>', methods=['GET', 'POST'])
def mainroute(pagepath):
    page = Page(path = pagepath,  # e.g. 'demo/home'
                request = request, 
                user = current_user, 
                )

    # if user not allowed access to this folder: reply access denied
    # else if is folder but url without trailing slash : redirect to url/
    # 
    
    # print " mainroute: pagepath = '{}'".format(pagepath)
    # print " mainroute: current_user = {}".format(current_user)
    # print " mainroute: page = {}".format(page)
    # print " mainroute: course = " + str(page.course)
    
    if request.method == 'POST':
        handle_post()
    
    return render_template('umber/main.html',
                           name = 'main',
                           page = page,
                           user = current_user,
                           debug = app.debug   # True or False; see app.run
                           )

@app.route('/' + url_base + '/', methods=['GET', 'POST'])
def mainroute_blank():
    mainroute('')

def handle_post():
    """ Process a form submission (login, edit, upload, ...) """
    # Each form has an input field named 'submit_X' for some X,
    # and is handled by a corresponding function submit_X().
    # The data is in the Flask request global.
    try:
        keys_named_submit = filter(lambda s: re.match('submit', s),
                                   request.form.keys())
        submit_what = keys_named_submit[0]
        globals()[submit_what]()  # get function given its name & invoke it
    except:
        print " OOPS : handle_post() couldn't handle request.keys() = ", \
          request.keys()

def submit_logout():
    """ handle logout action """
    # invoked from handle_post()
    logout_user()

def submit_login():
    """ handle <input name='submit_login' ...> form submission. """
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
          
def setup():
    app.secret_key = secret_key
    app.session_cookie_name = 'umber_session'
    app.permanent_session_lifetime = datetime.timedelta(days=1)

# Do this for the console as well as __main__ e.g. "python umber.py"
setup()
    
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'ssl':
        app.run(host = '0.0.0.0',
                port = https_port,
                debug = True,
                ssl_context = ssl_context)
    else:
        app.run(host = '0.0.0.0',
                port = http_port,
                debug = True,
                )

