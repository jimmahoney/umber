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
     http://127.0.0.1:5000/test
     http://127.0.0.1:5000/umber/demo/home

 Also see
   ./README.md, src/*, database/*, and docs/history.txt .
   http://flask.pocoo.org/docs/0.12/api/ .

 For production, at least change the TEST & DEBUG tags in
   src/umber.py
   src/config.py
   env/activate
   
 FIXME : get https working.
 
 Jim Mahoney | mahoney@marlboro.edu | May 2017 | MIT License
"""
import sys, re, os, json

## TEST & DEBUG only
# from OpenSSL import SSL

from flask import Flask, Response, request, session, g, \
     redirect, url_for, abort, flash, get_flashed_messages
from flask_login import LoginManager, login_user, logout_user, current_user
from flask import render_template
from settings import admin_email, about_copyright_url, \
     os_root, os_base, os_static, os_template, url_basename, os_config
from model import db, Person, Role, Course, \
     Registration, Assignment, Work, Page, Time
from utilities import in_console, split_url, static_url, size_in_bytes, \
     git, is_clean_folder_name, parse_access_string
from werkzeug import secure_filename

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
    return dict(static_url = static_url,
                message = get_message,
                # python functions imported into jinja2 template context
                dir = dir,                # built-in python function dir()
                pwd = os.getcwd,
               )

@app.before_request
def before_request():
    """ initialize database and session """

    # See http://docs.peewee-orm.com/en/latest/peewee/database.html .
    # This gives "connection already open" error if in console.
    # The current (kludgy) fix is to test for the console explicitly.
    if not in_console():
        db.connect()

    # See PERMANENT_SESSION_LIFETIME in config.py
    session.permanent = True

    # site settings
    g.admin_email = admin_email
    g.about_copyright_url = about_copyright_url
    g.now = Time()
    
    # Set information to be passed to the template engine as in
    # stackoverflow.com/questions/13617231/how-to-use-g-user-global-in-flask
    #
    # Test passing parameters.
    session['test'] = 'testing session'       # request thread variable
    g.alpha = 'beta'                          # test global variable

@app.teardown_request
def after_request(exception=None):
    db.close()
    
@app.route('/test')
def testroute():
    # The variables that Flask makes available by default within templates;
    # see http://flask.pocoo.org/docs/templating/ .
    # The global variables are :
    #    config, g, request, session, current_user, get_flashed_messages()
    # Also see @app.context_processor (above) for custom template variables.
    # ( I've looked at two templating engines: jinja2 & mako;
    #   The choice as of May 2017 is jinja2 due to better flask integration.
    #   mako globlas have 'context' instead of 'config'; otherwise the same.)
    return render_template('test/test.html',   # template 
                           test1 = 'George',   # variables
                           test2 = 'foobar'
        )

@app.route('/' + url_basename + '/<path:pagepath>', methods=['GET', 'POST'])
def mainroute(pagepath):

    print_debug('- '*30)
    print_debug(' mainroute: pagepath = "{}"'.format(pagepath))
    print_debug(' mainroute: request.url = "{}"'.format(request.url))
    print_debug(' mainroute: request.args = "{}"'.format(request.args))
    print_debug(' mainroute: current_user = {}'.format(current_user))

    # -- testing session & cookie ---    
    #print_debug(' mainroute: session = {}'.format(session))
    #color = 'red'
    #if color != '':
    #    session['color'] = color
    # -------------------------------

    # If the url is 'foo.md' then redirect to canonical url 'foo'.
    (basepath, extension) = os.path.splitext(pagepath)
    if extension ==  '.md':
        (ignore1, ignore2, query) = split_url(request.url)
        redirect_url = '/' + url_basename + '/' + basepath
        if query:
            redirect_url += '?' + query
        print_debug('redirecting to "{}"'.format(redirect_url))
        return redirect(redirect_url)
    
    # Get the corresponding Page object and its file settings.
    page = Page.get_from_path(pagepath,
                              revision=request.args.get('revision', None),
                              action=request.args.get('action', None),
                              user=current_user)

    print_debug(' mainroute: page.abspath = {}'.format(page.abspath))
    print_debug(' mainroute: course.name = "{}"'.format(page.course.name))
    print_debug(' mainroute: course.url = "{}"'.format(page.course.url))
    print_debug(' mainroute: page.access = {}'.format(page.access))
    print_debug(' mainroute: page can read = {}, write = {}'.format(
        page.can['read'], page.can['write']))
    print_debug((' mainroute: page exists = {},' + \
        ' is_file = {}, is_dir = {}').format(
        page.exists, page.is_file, page.is_dir))

    # Redirect directories which don't end in '/' to '/'.
    if page.is_dir and len(pagepath) > 0 and pagepath[-1] != '/':
        print_debug('redirecting directory to /')
        return redirect(url_for('mainroute', pagepath=pagepath) + '/')

    # Don't serve up any invisible "dot" files - reload enclosing folder.
    # This includes (.access.yaml, .keep) among possible others.
    if len(page.name) > 0 and page.name[0] == '.':
        url = page.url
        while page.url[-1] != '/' and len(page.url) > 0:
            url = url[:-1]

        if len(page.url) > 12 and page.url[-12:] == '.access.yaml':
            return redirect(page.url[:-12])
        else:
            return redirect(page.course.url)
    
    # Store the page object (and therefore page.course and page.user)
    # in the request, so that the request action handler doesn't need args.
    request.page = page

    if request.method == 'POST' and '__ajax__' in request.form:
        return ajax_upload()
    
    if request.method == 'POST':
        print_debug(' mainroute: POST')
        reload_url = form_post()
        if reload_url:
            return redirect(reload_url)
        
    if (not page.is_dir and
        not page.ext in ('.md') and
        page.can['read'] and
        page.exists):
        # readable pages that shouldn't be in umber's window pane :
        # just serve up their content.
        # (If the page isn't readable, then render_template(main.html) below
        # will show the error page within the umber setting.)
        # TODO: Do the right thing for actions like ?version=xxx or ?history ?
        # TODO: Handle what was _html for .py and .html
        #       with ?something (?html , ?source, ?pretty) ?
        # TODO: forward these sorts of requests to apache or other server??
        # TODO: handle unknown mimetype better, perhaps don't send file at all? 
        return Response(page.content(), mimetype=page.mimetype()) 
    else:
        #
        return render_template('umber/main.html',
                               name = 'main',
                               page = page,
                               user = page.user,
                               course = page.course,
                               debug = True
                               )

@app.route('/' + url_basename + '/', methods=['GET', 'POST'])
def mainroute_blank():
    mainroute('')
    
def ajax_upload():
    """ handle ajax file upload """
    page = request.page
    print_debug(' ajax_upload ')    
    print_debug('   request.form.keys() : {}'.format(request.form.keys()))
    print_debug('   destination : "{}"'.format(page.abspath))
    print_debug('   page.url : {}'.format(page.url))

    # Make sure that this user is authorized to put files here.
    if not (page.is_dir and page.can['write']):
        # TODO bail out in a better way
        return ajax_response(False, 'Oops - invalid permissions.') 
        
    for upload in request.files.getlist("file"):
        filename = secure_filename(upload.filename)
        print_debug('   file : "{}"'.format(filename))
        destination = os.path.join(page.abspath, filename)
        upload.save(destination)
        git.add_and_commit(page, abspath=destination)

    # Rather than return a bare ajax respose,
    # reload the edit folder page to see the new uploaded files.
    # return ajax_response(True, 'upload success') 
    return redirect(page.url + '?action=edit')

def ajax_response(status, msg):
    """ Return json data for an ajax request """
    status_code = "ok" if status else "error"
    return json.dumps(dict(status=status_code, msg=msg))

def form_post():
    """ Process a form submission (login, edit, etc) or ajax request."""
    # The input is stored in the Flask request global.
    # Each submitted form has an input field named 'submit_X' for some X,
    # and is handled by a corresponding function submit_X().

    keys_named_submit = filter(lambda s: re.match('submit', s),
                               request.form.keys())
    print_debug(' handle_post : submit keys = "{}" '.format(keys_named_submit))
    submit_what = keys_named_submit[0]
    print_debug(' handle_post : submit_what = "{}" '.format(submit_what))

    if submit_what not in ('submit_delete', 'submit_edit',
                           'submit_login', 'submit_logout',
                           'submit_createfolder'):
        print_debug(' handle_post: OOPS - illegal submit_what ');
        
    # invoke submit_X handler
    result = globals()[submit_what]()
    
    print_debug(' handle_post : submit result = "{}" '.format(result))
    return result

def submit_createfolder():
    """ handle folder creation """
    # example request.form is {'submit_createfolder': 'create',
    #                          'foldername': 'testfolder'}
    # page.abs path is current directory i.e. /User/mahoney/.../folder1/
    foldername = request.form['foldername']
    print_debug(' submit_createfolder : foldername="{}" '.format(foldername))
    if not is_clean_folder_name(foldername):
        print_debug(' submit_createfolder: illegal chars in foldername')
        flash('Oops: folder names may only contain ' + \
              'lowercase letters, numbers, or underbar.', 'folder')
        flash(foldername)
        return url_for('mainroute', pagepath=request.page.path, action='edit')
    folderpath = os.path.join(request.page.path, foldername)
    folderabspath = os.path.join(request.page.abspath, foldername)
    print_debug(' submit_createfolder : newfolderabspath="{}" '.format(
        folderabspath))
    try:
        os.mkdir(folderabspath)
    except:
        print_debug(' submit_createfolder: os.makedir failed')
        return request.base_url
    newfolder = Page.get_from_path(folderpath, user=request.page.user)
    git.add_and_commit(newfolder)
    return url_for('mainroute', pagepath=request.page.path, action='edit')    

def submit_permissions():
    """ handle setting folder permissions - .access.yaml stuff """
    rights = {'read':  parse_access_string( request.form['read_access'] ),
              'write': parse_access_string( request.form['write_access'] )}
    access_abspath = request.page.write_access_file(rights)
    print_debug(' submit_permissions : access path {} '.format(access_abspath))
    git.add_and_commit(request.page, access_abspath)
    return url_for('mainroute', pagepath=request.page.path, action='edit')    

def submit_delete():
    """ handle folder delete form """
    # example request.form would be {'submit_delete':'delete',
    #                                '/full/path/file1.md':'checkboxdelete',
    #                                '/full/path/folder2/':'checkboxdelete'}
    abspaths = list(filter(lambda path: request.form[path]=='checkboxdelete',
                           request.form.keys()))
    print_debug(' submit_delete : {}'.format(abspaths))
    git.rm_and_commit(request.page, abspaths)
    return url_for('mainroute', pagepath=request.page.path, action='edit')
    
def submit_edit():
    """ handle file edit form """
    # invoked from handle_post()
    # the form text data is in the form dict key, i.e. request.form['edit_text']
    #print_debug(' submit_edit: request.form : {}'.format(request.form.items()))
    #
    # request.form will look something like
    #  { 'submit_edit' : u'save page',                     # submit button
    #    'edit_text'   : u'page content\r\n===\r\n etc'    # textarea
    #  }
    #
    bytes_written = request.page.write_content(request.form['edit_text'])
    git.add_and_commit(request.page)
    return request.base_url  # ... and reload it without ?action=edit
    
def submit_logout():
    """ handle logout button click"""
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
    if user == None or not user.check_password(request.form['password']):
        flash('Oops: wrong username or password.', 'login')
        return url_for('mainroute', pagepath=request.page.path, action='login')
    else:
        user.logged_in = True
        login_user(user)

        # TODO: do I need to handle this case?
        # next = request.args.get('next')
        # print ' submit_login: next request = {}'.format(next)
        #
        return url_for('mainroute', pagepath=request.page.path)

