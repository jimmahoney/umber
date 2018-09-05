# -*- coding: utf-8 -*-
"""
 umber.py
 
 Jim Mahoney | mahoney@marlboro.edu | May 2017 | MIT License
"""
import sys, re, os, json, safe
from flask import Flask, Response, request, session, g, \
     redirect, url_for, abort, flash, get_flashed_messages, render_template
from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug import secure_filename
from model import db, Person, Role, Course, \
     Registration, Assignment, Work, Page, Time
from utilities import in_console, split_url, static_url, size_in_bytes, \
     git, is_clean_folder_name, parse_access_string, parse_assignment_data, \
     print_debug, pygmentize, name_to_htmltitle, path_to_startdate
from settings import umber_flask_configure, umber_url, contact_url, help_url, \
     about_url, site_url, url_base, os_root, umber_debug, route_prefix, \
     os_courses, markup_url

app = Flask('umber',
            static_folder=os.path.join(os_root, 'static'),
            template_folder=os.path.join(os_root, 'templates'))
umber_flask_configure(app)

login_manager = LoginManager()
login_manager.anonymous_user = Person.get_anonymous
login_manager.init_app(app)

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
    #  (b) the default Flask globals, g.* (see before_request())
    # Also can be more app.context_processor additions.
    return dict(static_url = static_url,
                message = get_message,
                dir = dir,                # built-in python function dir()
                pwd = os.getcwd,
                Person = Person,
                Course = Course,
                Role = Role
               )

@app.before_request
def do_before_request():
    """ initialize database and session """

    # See http://docs.peewee-orm.com/en/latest/peewee/database.html .
    # This gives "connection already open" error if in console.
    # The current (kludgy) fix is to test for the console explicitly.
    if not in_console():
        db.connect()

    #print " db={}".format(db)
    #print " request={}".format(request)

    # See PERMANENT_SESSION_LIFETIME in env/settings.py
    session.permanent = True

    # site settings
    g.debug = umber_debug
    g.contact_url = contact_url
    g.about_url = about_url
    g.help_url = help_url
    g.umber_url = umber_url
    g.markup_url = markup_url
    g.site_url = site_url
    g.now = Time()
    
    ## Set information to be passed to the template engine as in
    ## stackoverflow.com/questions/13617231/how-to-use-g-user-global-in-flask
    ## Test passing parameters.
    #session['test'] = 'testing session'       # request thread variable

@app.teardown_request
def do_after_request(exception=None):
    db.close()

### TESTING ###
@app.route('/uploadtest', methods=['GET', 'POST'])
def upload():
    return render_template('uploadtest.html')

@app.route(route_prefix + '/', methods=['GET', 'POST'])
def mainroute_blank():
    return mainroute('')
    
@app.route(route_prefix + '/<path:pagepath>', methods=['GET', 'POST'])
def mainroute(pagepath):

    # home page for default 'umber' course 
    if pagepath == '' or pagepath == 'home':
        return redirect('/' + url_base + '/site/docs/home')
    
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
        redirect_url = '/' + url_base + '/' + basepath
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

    # If a course for the isn't found, a special 'error' course
    # will be returned as a signal.
    if page.course.name == 'error':
        return abort(404)            # "not found"

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

    # Redirect directories to index.md or index.html if either exists.
    if page.is_dir:
        for index in ('index.md', 'index.html'):
            if os.path.exists(os.path.join(page.abspath, index)):
                    indexpath = os.path.join(pagepath, index)
                    return redirect(url_for('mainroute', pagepath=indexpath))
    
    # Redirect nonexisting nonystem editable pages to ?action=edit
    # ... but not if this is the POST that is trying to create it.
    if page.can['write'] and not page.exists and not page.action and \
                             not page.is_sys and not page.is_dir and \
                             not request.method == 'POST' :
        return redirect(page.url + '?action=edit')
    
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

    if request.method == 'POST' and 'dropzone' in request.args:
        print_debug('-- dropzone file upload --') # i.e. handle dropzonejs.com
        return ajax_upload()
    
    elif request.method == 'POST':
        print_debug(' mainroute: POST')
        reload_url = form_post()
        return redirect(reload_url)
        
    elif (not page.is_dir and
          (page.ext == '' or not page.ext in ('.md')) and
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

        print_debug(' -- mainroute - raw-ish content ')
        print_debug('   mimetype={}'.format(page.get_mimetype()))
        print_debug('   page.name_with_ext = {}'.format(page.name_with_ext))
        print_debug('   page.path = {}'.format(page.path))
        print_debug('   request.args = {}'.format(str(request.args)))
        _content = page.content()
        _mimetype = page.get_mimetype()
        if 'html' in request.args:
            print_debug('   pygmentizing ...')
            _content = pygmentize(_content, filename=page.name_with_ext)
            _mimetype = 'text/html'
        return Response(_content, mimetype=_mimetype)

    else:

        # umber page : folder or *.md or sys/* 
        return render_template('main.html',
                               name = 'main',
                               page = page,
                               user = page.user,
                               course = page.course,
                               debug = True
                               )

## debugging route : any url
#@app.route('/', defaults={'path':''})
#@app.route('/<path:path>')
#def catchall(path):
#    print "==> route catchall "
#    return "umber catchall path : '{}'".format(path)

# ===================================
# Flask "request context" issues ...
#
# I tried to move the rest of this into another file forms.py
# which I could use from this one with "from forms import form_post, ajax_upload".
# However, this failed when flask couldn't connect the "request" context
# with the actual web request. In the debugger, the "request" object
# within umber.py had the actual web request, but in the forms.py file it
# didn't, it was instead just some sort of <Local...> thingy without any data.
#
# See for example http://flask.pocoo.org/docs/0.12/appcontext/#locality-of-the-context .
# I likely need to pass the "app" variable to the forms.py file, and
# then execute code with an app.app_context() block or some such ...
# but for now I have just avoided the problem by leaving all the callbacks in this file.

# --- ajax ---

def ajax_upload():
    """ handle ajax file upload """
    # dropzone sends one ajax request per file, so this invocation is for
    # one file even if multiple files have been dropped on the web page.
    
    page = request.page
    print_debug(' ajax_upload ')    
    print_debug('   request.form.keys() : {}'.format(request.form.keys()))
    print_debug('   destination : "{}"'.format(page.abspath))
    print_debug('   page.url : {}'.format(page.url))

    # Make sure that this user is authorized to put files here.
    if not page.can['write']:
        return ajax_response(False, 'Oops - invalid permissions for file upload.') 

    if page.is_dir:
        abspath = page.abspath
    else:
        # create .attachments folder if need be
        abspath = page.attachments_folder()
        if not os.path.exists(abspath):
            try:
                os.mkdir(abspath)
            except:
                print_debug(' submit_createfolder: os.makedir failed')
                return ajax_response(False, 'error creating attachments folder') 
    
    for upload in request.files.getlist("file"):
        # Should be only one file when using dropbox, I think.
        
        # TODO: send something other than success if there's a problem here,
        # probably with a try: except: block.

        filename = secure_filename(upload.filename)
        print_debug('   file : "{}"'.format(filename))
        destination = os.path.join(abspath, filename)
        upload.save(destination)

        # TODO: do the github stuff asyncronously ?        
        git.add_and_commit(page, abspath=destination)         

    print_debug(" sending ajax response ")
    return ajax_response(True, 'upload success')

def ajax_response(status, msg):
    """ Return json data for an ajax request """
    status_code = "ok" if status else "error"
    return json.dumps(dict(status=status_code, msg=msg))

# --- forms ---

# The input to the submit_* and authorize_* handlers
# is through the request global;
# see http://flask.pocoo.org/docs/0.12/api/#incoming-request-data :
#   request.form      multidict with parsed form data from POST or PUT
#   request.args      multidict with parsed contents of url query string
#   request.values    both .form and .args
#   request.data
#   request.environ   WSGI environmnet
#   request.method
#   request.path
#   request.full_path
#   request.url
#   request.base_url
#   request.url_root
#   ... and others
# I've also added to it
#   request.page            umber Page object
#   request.page.user       umber Person object


def submit_done():
    # just reload the page
    return request.base_url

def submit_enroll():
    """ Enroll someone in this course. """
    username = request.form['username']
    rolename = request.form['submit_enroll']
    print_debug(' submit_enroll: user={}, role={}'.format(username, rolename))
    user = Person.by_username(username)
    request.page.course.enroll(user, rolename,
                               create_work=(rolename=='student'))
    return request.page.url

def submit_removeuser():
    """ The user clicked "remove" on the sys/users page """
    print_debug(' submit_removeuser: ' + str(request.form))
    username = request.form['choose_remove']
    if username :
        message = request.page.course.drop(username)
        if message:
            flash(message, 'drop')
    return request.page.url

def submit_searchuser():
    """ The user clicked "search" looking for some users.
        Return the result as ?usernames=... in the URL. """
    partialname = request.form['partialname']
    maxresults = 24
    usernames = Person.searchname(partialname, maxresults=maxresults)
    if len(usernames) == 0:
        flash('No results found for name="{}".'.format(partialname), 'search')
        return request.page.url
    if len(usernames) == maxresults:
        flash("Too many results - only showing first {}.".format(maxresults),
                  'search')
    return request.page.url + '?search=' + partialname + '&usernames=' + ','.join(usernames)

def submit_newuser():
    """ create new user """
    username = request.form['username']
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    print_debug(' create_person: ' + \
                'username={} name="{}" email={} password=""'.format(
                username, name, email, password))
    Person.create_person(username, name, email, password)
    return url_base + '/sys/user?username=' + username

def submit_newcourse():
    """ create new course """
    #print_debug('submit_newcourse: {}'.format(request.form))
    name = request.form['name']   # e.g. "Intro Programming"
    path = request.form['path']   # should have form term/folder e.g. fall2018/cs1
    copyfrom = request.form['copyfrom'] # e.g. "fall2017/cs1"
    startdate = path_to_startdate(path)
    title = name_to_htmltitle(name)
    print_debug(' submit_newcourse: name = "{}"'.format(name))
    print_debug('                   path = "{}"'.format(path))
    print_debug('                   copyfrom = "{}"'.format(copyfrom))
    newcourse = Course.create_course(name, path,
                                     start = startdate,
                                     name_as_title = title,
                                     copyfrom = copyfrom)
    for name in request.form['faculty'].split(','):
        try:
            faculty = Person.get(username = name.strip())
        except:
            faculty = None
        if not faculty:
            try:
                faculty = Person.get(username = name.strip())
            except:
                faculty = None
        if faculty:
            today = str(Time())[:10]
            newcourse.enroll(faculty, 'faculty', today, create_work=False)
    return newcourse.url

def submit_edituser():
    """ edit existing user - admin only """
    username = request.form['username']
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    print_debug(' submit_edituser: ' + \
                'username={} name="{}" email={} password=""'.format(
                username, name, email, password))
    Person.edit_person(username, name, email, password)
    return request.base_url + '?username=' + username

def submit_password():
    password = request.form['password']
    if not safe.check(password):
        flash('Oops: that password is too easily guessed. ' + \
              'Try again with a longer one using a mix of numbers, ' + \
              'symbols, upper and lower case.', 'user')
        print_debug(' submit_password: failed safe.check("{}")'.format(password))              
        return request.base_url + '?action=edit'
    else:
        request.page.user.set_password(password)
        print_debug(' submit_password: password reset')
        return request.base_url

def submit_assignments():
    """ handle assignment editing """
    print_debug(' submit_assignments: ')
    print_debug('   request.form is {}'.format(request.form))
    assignment_data = parse_assignment_data(request.form)
    print_debug('   len(assignment_data) = {}'.format(len(assignment_data)))
    request.page.course.update_assignments(assignment_data)
    return request.base_url    #  reload assignments page without edit

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
    Page.new_folder(folderabspath, user=request.page.user)
    return url_for('mainroute', pagepath=request.page.path, action='edit')    

def submit_grades():
    """ handle setting all course grades from grid """
    print_debug('submit grades')
    print_debug(request.form)
    Work.edit_grades(request.form)
    return url_for('mainroute', pagepath=request.page.path)

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
    # ... including student work pages.
    # invoked from handle_post()
    # the form text data is in the form dict key, i.e. request.form['edit_text']
    # print_debug(' submit_edit: request.form : {}'.format(request.form.items()))
    #
    # request.form will look something like
    #  { 'submit_edit' : u'save page',                     # submit button
    #    'edit_text'   : u'page content\r\n===\r\n etc'    # textarea
    #  }
    #
    # If this is a work page, then update the Work database object.
    # (The Work object is created in Page.get_from_path)
    if request.page.is_work:
        now = str(Time())  # string with current time
        with db.atomic():
            if request.page.user_role.name == 'faculty':
                page = request.page
                page.work.faculty_modified = now
                # If checkbox for 'submitted' and that didn't have a value,
                # then set it - used to mark work as submitted,
                # i.e. student emails work & faculty submits.
                if "submitted_checkbox" in request.form \
                     and not page.work.submitted:
                    due = Time(page.work_due)
                    print_debug(" submit_edit: due = {}".format(str(due)))
                    if "on_time_checkbox" in request.form:
                        due.shift_minutes(-5)
                    else:
                        due.shift_minutes(5)
                    page.work.submitted = str(due)
                    print_debug(" submit_edit: submitted set to {}".format( \
                                page.work.submitted))
                if 'grade' in request.form:
                    page.work.grade = str(request.form['grade'])
            else:
                request.page.work.student_modified = now
                if not request.page.work.submitted:
                    request.page.work.submitted = now    
            request.page.work.save()
    # Save the page content to a file and to git.
    bytes_written = request.page.write_content(request.form['edit_text'])
    print_debug(' submit_edit: bytes_written = {}'.format(bytes_written))
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
    if user.is_anonymous() or \
       not user.check_password(request.form['password']):
        flash('Oops: wrong username or password.', 'login')
        return url_for('mainroute', pagepath=request.page.path, action='login')
    else:
        user.logged_in = True
        login_user(user)
        return url_for('mainroute', pagepath=request.page.path)

def authorize_is_logged_in():
    return request.page.user.is_authenticated()

def authorize_change_password():
    users_own_password = request.page.user.username == request.form['username']
    return users_own_password or request.page.user.is_admin()

def authorize_can_write():
    return request.page.can['write']

def authorize_is_faculty():
    return request.page.user_role.name in ('faculty', 'admin')

def authorize_is_admin():
    return request.page.user.is_admin()

form_handlers = {
    'submit_login' :      {'handler':    submit_login,
                           'authorize':  lambda: True},
    'submit_logout' :     {'handler':    submit_logout,
                           'authorize':  authorize_is_logged_in},

    'submit_password' :   {'handler':    submit_password,
                           'authorize':  authorize_change_password},
    
    'submit_delete' :     {'handler':    submit_delete,
                           'authorize':  authorize_can_write},
    'submit_edit' :       {'handler':    submit_edit,
                           'authorize':  authorize_can_write},
    'submit_createfolder':{'handler':    submit_createfolder,
                           'authorize':  authorize_can_write},
    'submit_done' :       {'handler':    submit_done,
                           'authorize':  authorize_can_write},
    
    'submit_assignments': {'handler':    submit_assignments,
                           'authorize':  authorize_is_faculty},
    'submit_permissions': {'handler':    submit_permissions,
                           'authorize':  authorize_is_faculty},
    'submit_grades':      {'handler':    submit_grades,
                           'authorize':  authorize_is_faculty},
    'submit_searchuser' : {'handler':    submit_searchuser,
                           'authorize':  authorize_is_faculty},
    'submit_enroll' :     {'handler':    submit_enroll,
                           'authorize':  authorize_is_faculty},
    'submit_removeuser' : {'handler':    submit_removeuser,
                           'authorize':  authorize_is_faculty},

    'submit_edituser' :   {'handler':    submit_edituser,
                           'authorize':  authorize_is_admin},
    'submit_newuser' :    {'handler':    submit_newuser,
                           'authorize':  authorize_is_admin},
    'submit_newcourse' :  {'handler':    submit_newcourse,
                           'authorize':  authorize_is_admin},

    }
    
def form_post():
    """ Process a form submission (login, edit, etc)."""
    # The input is stored in Flask's request global.
    # Each submitted form has an input field named 'submit_X' for some X,
    # and is handled by a corresponding function submit_X()
    # if it passes its authorize_* permissions check.

    keys_named_submit = filter(lambda s: re.match('submit', s),
                               request.form.keys())
    print_debug(' handle_post : submit keys = "{}" '.format(keys_named_submit))
    submit_what = keys_named_submit[0]
    print_debug(' handle_post : submit_what = "{}" '.format(submit_what))
    
    if submit_what not in form_handlers:
        print_debug(' handle_post: OOPS - illegal submit_what ');
        flash('* incorrect form submission *', 'formerror')        
        return request.base_url
    elif form_handlers[submit_what]['authorize']():
        result = form_handlers[submit_what]['handler']()
        print_debug(' handle_post : submit result = "{}" '.format(result))
        return result
    else:
        print_debug(' handle_post: form submission authorization failed ');
        flash('* authorization error *', 'formerror')
        return request.base_url
