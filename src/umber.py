# -- coding: utf-8 --
"""
 umber.py

 Running this for development looks like this.

   set PATH 
   $ source env/activate

   initialize database
   $ umber_init_db

   interact with sql database
   $ umber_console
   >>> # see src/model.py for what you can do

   turn on http and https with the server script to browse & debug pages
   $ umber_server

   with a browser, visit urls like
     https://localhost:8443/test
     http://localhost:8080/umber/demo/home

 Also see
   ./README.md, src/*, database/*, and docs/history.txt .
   http://flask.pocoo.org/docs/0.11/api/ .

 For production, at least change the TEST & DEBUG tags in
   src/umber.py
   src/config.py
   env/activate
 And get SSL working, eh?
 
 Jim Mahoney | mahoney@marlboro.edu | June 2013 | MIT License
"""
import sys, re, os

## TEST & DEBUG only
# from OpenSSL import SSL

from flask import Flask, request, session, g, \
     redirect, url_for, abort, flash, get_flashed_messages
from flask_login import LoginManager, login_user, logout_user, current_user
from flask import render_template
from settings import http_port, https_port, \
     os_root, os_base, os_static, os_template, url_basename, os_config
from model import db, Person, Role, Course, \
     Registration, Assignment, Work, Page, Time
from utilities import ActionHTML
from markup import markup, nav_content

app = Flask('umber',
            static_folder=os_static,
            template_folder=os_template)
app.config.from_pyfile(os_config)

login_manager = LoginManager()
login_manager.anonymous_user = Person.get_anonymous
login_manager.init_app(app)
     
def print_debug(message):
    if app.config['DEBUG']:
        print message

## TEST & DEBUG only
# ssl_context = SSL.Context(SSL.SSLv23_METHOD)
# ssl_context.use_privatekey_file('../ssl/ssl.key')
# ssl_context.use_certificate_file('../ssl/ssl.crt')

@login_manager.user_loader
def load_user(user_session_id):
    """ Return Person corresponding to unicode session id, or None. """
    # see flask-login.readthedocs.org/en/latest/#flask.ext.login.LoginManager
    user = Person.by_username(user_session_id)
    # TODO : set logged_in and role correctly ... save in database??
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
    # Also can be more app.context_processor additions.
    return dict(static_url = lambda f: url_for('static', filename=f),
                message = get_message,
                # python functions imported into jinja2 template context
                dir = dir,                # built-in python function dir()
                pwd = os.getcwd,
                nav_content = nav_content,
                markup = markup
                )

@app.before_request
def before_request():
    """ initialize database and session """

    # See http://docs.peewee-orm.com/en/latest/peewee/database.html
    # FIXME : this gives "connection already open" error in console start.
    #db.connect()

    # See PERMANENT_SESSION_LIFETIME in config.py
    session.permanent = True

    # Set information to be passed to the template engine as in
    # stackoverflow.com/questions/13617231/how-to-use-g-user-global-in-flask
    #
    # Test passing parameters.
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

@app.route('/' + url_basename + '/<path:pagepath>', methods=['GET', 'POST'])
def mainroute(pagepath):

    print_debug(' mainroute: pagepath = "{}"'.format(pagepath))
    print_debug(' mainroute: current_user = {}'.format(current_user))

    # -- testing session & cookie ---    
    #print_debug(' mainroute: session = {}'.format(session))
    #color = raw_input(' ... session color = ')
    #if color != '':
    #    session['color'] = color
    # -------------------------------

    # If the url is e.g. 'foo.markdown', redirect to canonical form 'foo'.
    if len(pagepath) > 9 and pagepath[-9:] == '.markdown':
        print_debug('redirecting to .markdown')
        return redirect(url_for('mainroute', pagepath=pagepath[:-9]))
    
    # Get the corresponding Page object and its file settings.
    #
    page = Page.get_from_path(pagepath)
    print_debug(' mainroute: page.abspath = {}'.format(page.abspath))

    # If this is a directory but doesn't end in '/', redirect to '/'.
    if page.isdir and len(pagepath) > 0 and pagepath[-1] != '/':
        print_debug('redirecting directory to /')
        return redirect(url_for('mainroute', pagepath=pagepath) + '/')

    # Find the corresponding course.
    # (Do this before access : even a "not found" or "no access"
    #  will give an error that shows the course.)
    page.set_course()    # store in page.course
    page.course.url = request.url_root + url_basename + '/' + \
                      page.course.path + '/'
                      
    print_debug(' mainroute: course.name = "{}"'.format(page.course.name))
    print_debug(' mainroute: course.url = "{}"'.format(page.course.url))

    # Given page.course and current_user,
    # store into the page object the access permissions and roles.
    page.set_user_permissions(current_user)
    
    print_debug(' mainroute: page.access = {}'.format(page.access))
    print_debug(' mainroute: page can read = {}, write = {}'.format(
        page.can['read'], page.can['write']))
    print_debug((' mainroute: page exists = {},' + \
        ' isfile = {}, isdir = {}').format(
        page.exists, page.isfile, page.isdir))
    
    page.allow_insecure_login = True           # TEST & DEBUG ONLY

    # Store the page object (and therefore page.course and page.user)
    # in the request, so that the request is all the action handler needs.
    request.page = page
    
    if request.method == 'POST':
        reload_url = handle_post()
        if reload_url:
            return redirect(reload_url)

    return render_template('umber/main.html',
                           name = 'main',
                           page = page,
                           user = page.user,
                           course = page.course,
                           actionHTML = ActionHTML(page),
                           debug = True           # TEST & DEBUG ONLY
                           )

@app.route('/' + url_basename + '/', methods=['GET', 'POST'])
def mainroute_blank():
    mainroute('')

def handle_post():
    """ Process a form submission (login, edit, upload, ...) """
    # Each form has an input field named 'submit_X' for some X,
    # and is handled by a corresponding function submit_X().
    # The data is in the Flask request global.
    print_debug(' handle_post ... ')
    
    #try:
    keys_named_submit = filter(lambda s: re.match('submit', s),
                                   request.form.keys())
    submit_what = keys_named_submit[0]
    # get function given its name & invoke it        
    return globals()[submit_what]()
    #except:
    # print " OOPS: handle_post() couldn't handle request = {}".format(request)

def submit_logout():
    """ handle logout action """
    # invoked from handle_post()
    logout_user()
    return request.base_url

def submit_login():
    """ handle <input name='submit_login' ...> form submission. """
    # invoked from handle_post()
    print_debug(' submit_login: username = "{}" '
                .format(request.form['username']))
    user = Person.by_username(request.form['username'])
    print_debug(' submit_login: user = "{}"'.format(user))
    if user == None or \
       not user.check_password(request.form['password']):
        flash('Oops: wrong username or password.')
        return None
    else:
        user.logged_in = True
        login_user(user)

        # TODO: do I need to handle this case?
        # next = request.args.get('next')
        # print ' submit_login: next request = {}'.format(next)
        #
        return request.base_url

# ---- older code - delete when things are stable  ----------------
#
# -- config has changed in 0.11 ... see app.config at top of file
# def app_setup():
#    app.secret_key = secret_key
#    app.session_cookie_name = 'umber_session'
#    app.permanent_session_lifetime = datetime.timedelta(days=1)
#    
# app_setup()
#
# -- invocation has changed in flask 0.11 ... still exploring
#    how things work with "flask run" and "flask shell"
#    at the command line; see umber_server and umber_shell
#
#    $ cd umber
#    $ export FLASK_APP=src/umber.py
#    $ export FLASK_DEBUG=1
#    $ flask run    OR       flask shell
#
# --- invocation was this in an earlier version of flask ---
#  
# if __name__ == '__main__':
#     if len(sys.argv) > 1 and sys.argv[1] == 'ssl':
#         app.run(host = '0.0.0.0',
#                 port = https_port,
#                 debug = True,
#                 ssl_context = ssl_context)
#     else:
#         app.run(host = '0.0.0.0',
#                 port = http_port,
#                 debug = True,
#                 )

