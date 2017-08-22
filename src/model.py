# -- coding: utf-8 --
"""
 model.py
 
 The data class definitons and methods,
 built on the pewee ORM with a sqlite3 database.

 The following tests assumes that the database has been created
 and that populate_database() has been run; see ../database/init_db.
   
 The script ../bin/umber_test runs these and other tests.

   # Find the people and their role in a course given its name.
   >>> democourse = Course.get(Course.name == 'Demo Course')
   >>> for (username, role) in sorted(democourse.username_to_role.items()):
   ...   user = Person.by_username(username)
   ...   print "{} is {} in {}.".format(user.name, role.name, democourse.name)
   ...
   Jane Q. Doe is student in Demo Course.
   Johnny Smith is student in Demo Course.
   Ted Teacher is faculty in Demo Course.
 
   # Find a person from their username.
   >>> john = Person.get(username='johnsmith')
   >>> print john.name
   Johnny Smith

   # Change their name.
   >>> john.name = 'John Z. Smith'
   >>> rows_changed = john.save()

   # See the change.
   >>> newjohn = Person.get(username='johnsmith')
   >>> print newjohn.name
   John Z. Smith

   # Change it back.
   >>> john.name = 'Johnny Smith'
   >>> rows_changed = john.save()

 Jim Mahoney | mahoney@marlboro.edu | MIT License
"""

import os, subprocess, yaml, re
from werkzeug.security import generate_password_hash, check_password_hash
from peewee import SqliteDatabase, Model, \
     TextField, IntegerField, PrimaryKeyField, ForeignKeyField
from bs4 import BeautifulSoup
from settings import db_path, protocol, host, url_basename, os_base
from utilities import markdown2html, link_translate, static_url, \
               ext_to_filetype, filetype_to_icon, size_in_bytes, \
               git, Time

db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db   # (peewee requires this 'database' name)

    def __repr__(self):
        # e.g. 
        fields = ', '.join(map(lambda x: "{}={}".format(x[0],repr(x[1])),
                           self.__dict__['_data'].items()))
        return '<{}({}) at 0x{:X}>'.format(self.__class__.__name__,
                                       fields, id(self))
        
    @classmethod
    def first(cls):
        return cls.select().first()
    
    @classmethod
    def all(cls):
        return list(cls.select().execute())
    
class Person(BaseModel):
    class Meta:
        db_table = 'Person'

    person_id = PrimaryKeyField(db_column='person_id')
        
    username = TextField(unique=True)
    password = TextField()
    name = TextField()
    email = TextField()                
    notes = TextField()

    def works(self, course):
        query = (Work.select()
                     .where( Work.person == self,
                             Work.course == course ))
        return list(query.execute())

    def _save(self):
        """ save to database and invalidate caches """
        try:
            del Person._by_username[self.username]
        except KeyError:
            pass
        Person._admins = None
        self.save()
    
    def set_password(self, passwordtext):
        self.password = generate_password_hash(passwordtext)
        self._save()
        
    def check_password(self, passwordtext):
        return check_password_hash(self.password, passwordtext)

    def get_role(self, course):
        """ Return role of this person in that course """
        if self.username in course.username_to_role:
            return course.username_to_role[self]
        else:
            return Role.by_name('visitor')

    # -- Flask-Login methods & tools --

    @staticmethod
    def get_anonymous():
        """ Create and return an anonymous Person """
        # Not saved to database (i.e. save() not called).
        # Not logged in.
        anon = Person(name=u'anonymous', username=u'')
        anon.anonymous = True
        return anon
        
    def is_authenticated(self):
        return not self.is_anonymous()
        
    def is_active(self):
        return not self.is_anonymous()
    
    def is_anonymous(self):
        try:
            return self.anonymous
        except:
            return False

    def is_admin(self):
        """ return True if this user is an admin, false otherwise """
        return self.username in Person.admins()

    def get_id(self):
        if self.username == None:
            return unicode('')
        else:
            return unicode(self.username)

    _by_username = {} # cache
        
    @staticmethod
    def by_username(username):
        if username not in Person._by_username:
            person = Person.select().where(Person.username==username).first()
            Person._by_username[username] = person
        return Person._by_username[username]
        
    @staticmethod
    def by_rolename(rolename):
        """ Return list of users who have a given type of registration """
        # ... in any registration record i.e. any course
        return list(Person.select()
                          .join(Registration)
                          .where(Registration.role == Role.by_name(rolename))
                          .execute())

    _admins = None  # cache - TODO reset when someone gets admin status
    
    @staticmethod
    def admins():
        """ Return list of administrators """
        if not Person._admins:
            Person._admins =  Person.by_rolename('admin')
        return Person._admins
    
class Course(BaseModel):
    class Meta:
        db_table = 'Course'
        
    course_id = PrimaryKeyField(db_column='course_id')
    
    active = IntegerField()
    assignments_md5 = TextField()
    credits = IntegerField()
    end_date = TextField()
    name = TextField()
    name_as_title = TextField()
    notes = TextField()
    path = TextField(unique=True)
    start_date = TextField()

    def person_to_role(self, person):
        """ Return role of person in course, or visitor """
        return self.username_to_role.get(person.username,
                                         Role.by_name('visitor'))
    
    def prepared(self):
        """ setup this instance after it's attributes are set """
        # This is essentially __init__ for these database objects.
        self.username_to_role = {reg.person.username : reg.role
            for reg in (Registration.select(Registration.person,
                                            Registration.role)
                                    .where(Registration.course == self))}
        self.semester = Time(self.start_date).semester()
        # url without request though that info is also in request
        self.url = protocol + '://' + host + '/' + \
                   url_basename + '/' + self.path

    def os_path(self):
        return os.path.join(os_base, self.path)

    def nav_page(self, user):
        """ return course's navigation page """
        # TODO: should this be cached to self._nav_page ?
        # (Need it for both displaying and editing course's navigation page.)
        return Page.get_from_path(self.path + '/sys/' + 'navigation.md',
                                  user=user)
    
    def nav_html(self, user, page):
        """ Return html for course's navigation menu 
            for a given user & a given page """
        return self.nav_page(user).nav_content_as_html(page)

class Page(BaseModel):

    #  --- path, filename, url definitions ---
    #  With settings on my laptop development machine as
    #    os_base    /Users/mahoney/academics/umber/courses
    #    url_base                            umber
    #  then for the 'notes/week1' file within a course at 'fall/math' ,
    #  the parts are
    #    url:  http://localhost:8090/  umber    /  fall/math / notes/week1
    #          protocol  host          url_base    path...................
    #    file: /Users/mahoney/academics/umber/courses / fall/math / notes/week1
    #          os_base                                  path...................
    #  Following python's os.path phrasing, other terms used here are
    #    basename     last word in address (same as os.path.basename)
    #    abspath      e.g. /Users/mahoney/.../fall/math/notes/week1
    #    dirname      e.g. /Users/mahoney/.../fall/math/notes
    #  This url would have in its flask request object the attributes
    #    request.url_root        'http://localhost:8090/'
    #    request.path            '/umber/fall/math/notes/week1'
    #
    # Note that Page.path (e.g. fall/math/notes/week1)
    # does not have a leading slash or contain the url_base,
    # while request.path (e.g. /umber/fall/math/notes/week1) does.
    #
    # The Page object will also contain various extra data 
    # that isn't stored in the sql database but is instead
    # pulled from the filesystem.

    class Meta:
        db_table = 'Page'
        
    page_id = PrimaryKeyField(db_column='page_id')

    as_html = TextField()
    content_hash = IntegerField()
    notes = TextField()
    path = TextField(unique=True)
    
    course = ForeignKeyField(rel_model=Course,
                             db_column='course_id',
                             to_field='course_id')

    @classmethod
    def get_from_path(cls, path, revision=None, action=None, user=None):
        """ Get or create a Page and set up all its internal data 
            i.e. course, file info, user permissions, etc """
        (page, iscreated) = Page.get_or_create(path=path)
        page.user = user
        page.action = action
        page.revision = revision
        page.allow_insecure_login = True  # TODO : figure out https stuff
        page._setup_file_properties()       # sets page.isfile etc
        page.course = page.get_course()
        if user:
            page._setup_user_permissions()  # sets page.can['read'] etc
        if revision or action=='history':
            page._setup_revision_data()     # sets page.history etc
        return page

    def get_course(self):
        """ return this page's course """  # TODO : cache in sql database ??
        # extract path pieces e.g. ['demo', 'home']
        path_parts = self.path.split('/')
        # build partial paths e.g. ['demo', 'demo/home']
        # (stackoverflow.com/questions/13221896/python-partial-sum-of-numbers)
        paths = reduce(lambda x,y: x + [x[-1]+'/'+y],
                       path_parts[1:], path_parts[0:1])
        # build peewee's "where condition" to find matching courses.
        condition = Course.path % ''     # Note: '' is Umber's default course
        for c in paths:
            condition = condition | Course.path % c
        # get list of matching courses from database
        query = Course.select().where(condition)
        courses = list(query.execute())
        # choose the one with the longest path
        return max(courses, key=lambda c: len(c.path))

    def get_access(self):
        """ Return .access dict from .access.yaml in an enclosing folder """
        self.access = {'read':'', 'write':''}
        if self.is_dir:
            abspath = self.abspath
        else:
            abspath = os.path.dirname(self.abspath)
        while len(abspath) >= len(os_base):
            accesspath = abspath + '/.access.yaml'
            if os.path.exists(accesspath):
                accessfile = open(accesspath)
                access_dict = yaml.load(accessfile)
                accessfile.close()
                break
            abspath = os.path.dirname(abspath) # i.e. "cd .."
        return access_dict

    def _setup_user_permissions(self):
        """ Set page.access, page.can['read'], page.can['write'],
                page.user, page.user_role, page.user_rank """
        # Note that admins who are faculty in a given course
        # will have a displayed role of 'faculty' in that course
        # but will have admin access to nav menus etc.
        assert self.course != None  # call self.set_course() first.
        self.access = self.get_access()
        self.user_role = self.course.person_to_role(self.user)
        self.user_rank = self.user_role.rank
        if self.user.is_admin():
            self.can = {'read':True, 'write':True}
            self.user_rank = Role.by_name('admin').rank
            if self.user_role.name != 'faculty':
                    self.user_role = Role.by_name('admin')
        else:
            self.can = {'read':False, 'write':False} # initial default
        for permission in ('read', 'write'):
            access_needed = Role.by_name('faculty').rank
            for who in self.access[permission].split(','):
                if who == self.user.username:
                    self.can[permission] = True
                    break
                elif who in Role.name_alias:
                    access_needed = min(Role.by_name(who).rank,
                                        access_needed)
            if self.user_rank >= access_needed:
                self.can[permission] = True

    def children(self):
        """ return page for each file or folder below this folder """
        result = []
        if self.is_dir:
            for name in os.listdir(self.abspath):
                # loop over e.g. [u'.access.yaml', u'home.md', u'students']
                if name[0] == '.':  # skip invisible files e.g. .access.yaml
                    continue
                result.append(Page.get_from_path(
                    os.path.join(self.abspath, name)))
        return result

    def icon_url(self):
        """ return url for icon for this file type """
        return static_url(filetype_to_icon[self.filetype])

    def formatted_name(self, width=24):
        """ return name_with_ext string padded to width characters """
        # This is for directory listings; see templates/umber/folder.html .
        # If the name is too long to fit in width characters, it is just
        # returned anyway - formatting for that line in the listing will be
        # ugly.  Another approach would be truncate to perhaps
        # 'very_long_name_or_som...' or 'very_lon..._end.txt' .
        length = len(self.name_with_ext)
        if length > width:
            return self.name_with_ext
        else:
            return self.name_with_ext + ' '*(width - length)

    def _setup_revision_data(self):
        """ read and store within page the git file revision data """
        log = git.log(self)        # All revisions : [(revision, date, author)]
        if  len(log) == 0:
            link = self.url
            date = self.lastmodified.daydatetimesec()
            author = ''
            self.revisions = ()
            self.history = ((link, date, author, True),)
            self.revision_date = date
        else:
            self.revisions = tuple(revision for (revision, date, author) in log)
            self.history = tuple((self.url + '?revision={}'.format(revision),
                                  date, author, revision == self.revisions[0])
                                 for (revision, date, author) in log)
            self.revision_date = self.history[0][1]
        
    def _setup_file_properties(self):
        """ given self.path, set a bunch of information about the file
            including self.absfilename, self.exists, self.is_file, self.is_dir,
            self.lastmodified, self.breadcrumbs
         """
        self.abspath = os.path.join(os_base, self.path)
        if not os.path.exists(self.abspath):
            for ext in ['.md', '.html']:
                if ext == '.md' and os.path.exists(self.abspath + ext):
                    self.abspath = self.abspath + ext
        (ignore, self.ext) = os.path.splitext(self.abspath)
        self.exists = os.path.exists(self.abspath)
        self.name_with_ext = os.path.split(self.abspath)[-1]
        if self.ext == '':
            self.name = self.name_with_ext
        else:
            self.name = self.name_with_ext[: - len(self.ext) ]
        self.name_underlined = self.name + '\n' + '='*len(self.name)
        self.path_no_name = self.path[: - len(self.name) ]
        self.is_file = os.path.isfile(self.abspath)
        self.is_dir = os.path.isdir(self.abspath)
        self.is_sys = self.path[:3] == 'sys'
        if self.exists:
            stat = os.stat(self.abspath)
            self.lastmodified = Time(stat.st_mtime)
            if self.is_dir:
                self.size = None
                self.filetype = 'directory'
                self.name_with_ext += '/'
            elif self.is_file:
                self.size = stat.st_size
                self.filetype = ext_to_filetype.get(self.ext, 'unknown')
            else:
                self.size = None
                self.filetype = 'unknown'
        else:
            self.lastmodified = None
            self.size = None
        # -- build url links for page breadcrumbs --
        ## request.base_url should have also have this page's url.
        ## But here instead I'm building it from what's defined in settings.py,
        ## namely (protocol, host, url_basename), along with self.path.
        url_list = [url_basename] + self.path.split('/')
        urlsofar = protocol + '://' + host
        self.breadcrumbs = '<a href="{}">{}</a>'.format(urlsofar, urlsofar)
        while url_list:
            pathpart = '/' + url_list.pop(0)
            urlsofar += pathpart
            self.breadcrumbs += '&nbsp;' + '<a href="{}">{}</a>'.format(
                urlsofar, pathpart)
        self.url = protocol+'://'+host+'/'+url_basename+'/'+self.path
        self.url_for_print_version = self.url + '?print=1'
        self.bytesize = size_in_bytes(self.size)

    def revision_content_as_html(self):
        return git.get_revision(self)

    def content(self):
        """ Return data from page if it exists and is a file. """
        # TODO: should this be cached as self._content ?
        if self.exists and self.is_file:
            with open(self.abspath, 'r') as _file:
                return _file.read()
        else:
            return ''

    def write_content(self, new_content):
        """ Write new data to page's file; return number of bytes written """
        if self.can['write']:  # shouldn't get here without this anyway
            with open(self.abspath, 'w') as _file:
                bytes_written = _file.write(new_content)
        return bytes_written

    def content_as_html(self):
        """ Return markdown file converted to html. """
        if not self.exists:
            return ''
        elif self.ext == '.md':
            html = markdown2html(self.content())
        # elif self.ext == '.wiki':
        #    html = subprocess.check_output(['wiki2html', self.abspath])
        else:
            html = '<h2>Oops</h2> unsupported file type "{}"'.format(self.ext)
        html = link_translate(self.course, html)     # expand ~/ and ~~/
        return html

    def nav_content_as_html(self, page):
        """ Return authorized parts of html & markdown at html . """
        # Here self is the navigation.md page.
        #   TODO: unlinkify current page
        #   TODO: This implementation is pretty ugly.
        #         Perhaps just do this explicitly without BeautifulSoup?
        #         And make some tests ...
        # Each course has a menu navigation page which is a mixture of html
        # and markdown, including access tags that look like this :
        #    <div access='student'>
        #    ...
        #    </div>
        # This method converts the content of that file to html,
        # keeping only the parts that this user is allowed to see.
        parser = BeautifulSoup(self.content(), 'html.parser')
        for role in ['admin', 'student', 'faculty', 'guest', 'all']:
            divs = parser.find_all('div', access=role)
            if self.user_rank < Role.by_name(role).rank:
                for div in divs:
                    div.extract() # remove this div from its parent parser
        insides = []
        marker = '.~*#!#*~.'  # something that won't be in the html.
        for divm in parser.find_all('div', markdown=1):
            contents = ''.join(divm.stripped_strings)
            mstring = markdown2html(contents)
            insides.append(mstring)
            divm.string = marker
        html = str(parser)
        while insides:
            inside = insides.pop(0)
            html = html.replace(marker, inside, 1)
        html = link_translate(self.course, html)
        # If the current page is one of the links in the nav menu,
        # that link should be unlinkified ... which I'm doing
        # with another (ugh) pass through BeautifulSoup,
        # now that markdown has run.
        # -------------
        # TODO do the right thing for file.md, file.html,
        # and folder ; currently only "file" and "folder/" will work
        # in the nav markdown; the other non-canonical with redirectrs won't.
        # (So check other options in a loop, eh?)
        parser = BeautifulSoup(html, 'html.parser')
        anchor = parser.find('a', href=page.url)
        if anchor:
            span = parser.new_tag('span')
            span['class'] = 'thispage'
            span.string = anchor.string
            parser.find('a', href=page.url).replace_with(span)
        html = str(parser)
        return html
    
class Assignment(BaseModel):
    class Meta:
        db_table = 'Assignment'

    assignment_id = PrimaryKeyField(db_column='assignment_id')
    
    active = IntegerField()
    blurb = TextField()
    due = TextField(null=True)
    name = TextField()
    notes = TextField()
    nth = IntegerField(null=True)
    uriname = TextField()

    course = ForeignKeyField(rel_model=Course,
                             db_column='course_id',
                             to_field='course_id')
    
class Role(BaseModel):
    class Meta:
        db_table = 'Role'

    role_id = PrimaryKeyField(db_column='role_id')
    
    name = TextField()
    rank = IntegerField()

    name_rank = {'admin': 5,
                 'faculty': 4,
                 'student': 3,
                 'guest': 2,
                 'visitor': 1
                 }
    name_alias = {'admin':           'admin',
                  'administrator':   'admin',
                  'faculty':         'faculty',
                  'student':         'student',
                  'students':        'student',
                  'class':           'student',
                  'guest':           'guest',
                  'all':             'visitor',
                  'any':             'visitor',
                  'visitor':         'visitor'
                  }

    _cache = {}

    @staticmethod
    def by_name(name):
        if not name in Role.name_rank:
            if name in Role.name_alias:
                name = Role.name_alias[name]
            else:
                name = 'visitor'
        if not name in Role._cache:
            Role._cache[name] = Role.get(name=name)
        return Role._cache[name]

    @staticmethod
    def unalias(alias):
        """ Convert alias to its standard role name. """
        return Role.name_alias[alias]

    @staticmethod
    def create_defaults():
        with db.transaction():
            for (name, rank) in Role.name_rank.items():
                Role.get_or_create(name=name, rank=rank)
                
class Registration(BaseModel):
    class Meta:
        db_table = 'Registration'
        
    registration_id = PrimaryKeyField(db_column='registration_id')
    
    credits = IntegerField()
    date = TextField(null=True)
    grade = TextField()
    midterm = TextField()
    status = TextField()

    course = ForeignKeyField(rel_model=Course,
                             db_column='course_id',
                             to_field='course_id')
    person = ForeignKeyField(rel_model=Person,
                             db_column='person_id',
                             to_field='person_id')
    role = ForeignKeyField(rel_model=Role,
                           db_column='role_id',
                           to_field='role_id')
        
class Work(BaseModel):
    class Meta:
        db_table = 'Work'

    work_id = PrimaryKeyField(db_column='work_id')
                
    facultylastmodified = TextField(db_column='facultyLastModified')
    facultylastseen = TextField(db_column='facultyLastSeen')
    grade = TextField()
    notes = TextField()
    studentlastmodified = TextField(db_column='studentLastModified')
    studentlastseen = TextField(db_column='studentLastSeen')
    submitted = TextField()

    assignment = ForeignKeyField(rel_model=Assignment,
                                 db_column='assignment_id',
                                 to_field='assignment_id')
    person = ForeignKeyField(rel_model=Person,
                             db_column='person_id',
                             to_field='person_id')
    page = ForeignKeyField(rel_model=Page,
                           db_column='page_id',
                           to_field='page_id')


def populate_database():
    """ Create (and commit) the default database objects """
    #
    # Put some initial data into the database tables:
    # Roles, Course 'demo' and its example Persons,
    # Registrations, Assignments, and Works.
    #
    # The Roles data must be in place for the login system to work.
    # The rest of this is just for examples and tests.
    #
    # The sqlite database must already exist before this is run.
    # Create it with ../database/init_db.
    #
    # populate_db() is mostly idempotent; that is, runing multiple times
    # is no different than running it once. The one thing that will
    # change is the random seeds for the demo course sample users.

    print "* Populating database with default data."
    
    Role.create_defaults()
    
    with db.transaction():
        
        student = Role.get(name = 'student')
        faculty = Role.get(name = 'faculty')
        
        (democourse, created) = Course.get_or_create(
                name = 'Demo Course',
                name_as_title = 'Demo<br>Course',
                path = 'demo',
                start_date = '2013-01-01')

        (umbercourse, created) = Course.get_or_create(
                name = 'Umber',
                name_as_title = 'Umber',
                path = '',
                start_date = '2013-01-01')
                 
        (jane, created) = Person.get_or_create(
            username = 'janedoe',
            name = 'Jane Q. Doe',
            email = 'janedoe@fake.address')
        
        (john, created) = Person.get_or_create(
            username = 'johnsmith',
            name = 'Johnny Smith',
            email = 'johnsmith@fake.address')
        
        (ted, created)  = Person.get_or_create(
            username = 'tedteacher',
            name = 'Ted Teacher',
            email = 'ted@fake.address')
        
        # The hashed seeded passwords are different each time,
        # so they shouldn't be put in args to find_or_create. Otherwise, the
        # new passwords won't be found and duplicate people would be created.
        jane.set_password('test')
        john.set_password('test')
        ted.set_password('test')
        
        Registration.get_or_create(
            person = john,
            course = democourse,
            role = student,
            date = '2013-01-02')
        
        Registration.get_or_create(
            person = jane,
            course = democourse,
            role = student,
            date = '2013-01-03')
        
        Registration.get_or_create(
            person = ted,
            course = democourse,
            role = faculty,
            date = '2013-01-04')
        
        (assign1, created) = Assignment.get_or_create(
            course = democourse,
            nth = 1,
            name = 'week 1',
            uriname = 'week_1',
            due = '2013-01-20',
            blurb = 'Do chap 1 exercises 1 to 10.')
        
        (assign2, created) = Assignment.get_or_create(
            course_id = democourse,
            nth = 1,
            name = 'week 2',
            uriname = 'week_2',
            due = '2013-01-27',
            blurb = 'Write a four part fugue.')
        
        Work.get_or_create(
            person = john,
            assignment = assign1,
            submitted = '2013-01-20 18:19:20',
            grade = 'B')
        
        Work.get_or_create(
            person = jane,
            assignment = assign1,
            submitted = '2013-01-21 16:01:01',
            grade = 'B-')


if __name__ == '__main__':
    import doctest
    doctest.testmod()

# ------------------------------------------------------
# peewee database notes
#
# * installation
#     $ pip install peewee
#
# * its source : https://github.com/coleifer/peewee
#
# * features
#     playhouse.flask_utils : open/close db correctly during web request
#     playhouse.reflection  : extracting classes from an existing database
#
# * foreign keys and relationships
#     the correspondance between database column names and class fields
#     is set explicitly in the pewee class definition.
#     See the docs for ForeignKeyField
#
# * performance & foreign keys
#     See http://docs.peewee-orm.com/en/latest/peewee/querying.html#nplusone
#
# * notes on many-to-many methods
#     http://docs.peewee-orm.com/en/latest/peewee/querying.html#manytomany
#
# * meta data
#     Their classes store database & table stuff in a meta namespace
#     which isn't well documented.
#       > a = Assignment.select().first()
#       > a._meta.database, a._meta.db_table  # see output from pwiz
#
# * starting from an existing sql database
#
#     Peewee does allow models to be pulled from an existing sql
#     database.  However, after some playing around I found this too
#     limiting - modifing their generated classes was awkward. The
#     code for that approach would be
#       > from playhouse.reflection import Introspector.
#       > introspector = Introspector.from_database(db)
#       > models = introspector.generate_models()
#       > Person       = models['Person']
#       > Role         = models['Role']
#       > Course       = models['Course']
#       > Registration = models['Registration']
#       > Assignment   = models['Assignment']
#       > Work         = models['Work']
#     ... and then perhaps some python ugliness with things like "class
#     Person(Person)" to build custom classes on top of those.
#
#    Instead I have chosen to use their "pwiz" tool to generate class code
#    that matches the database declarations, and then edited and extended
#    that code:
#       $ cd ../database
#       $ python -m pwiz -e sqlite3 umber.db > pwiz_model.py
#    And then used that pwiz_model.py code as a starting point.
#
# * __init__() => prepared()
#
#    To extend their classes, the __init__ method is problematic
#    because it runs before the field data has been loaded.
#    Peewee data classes have a prepared() method which
#    is called after that data is loaded ... which is
#    the right place to put what would otherwise go in __init__.
#
#    For example, in Course.prepared I construct a course.username_to_role
#    dictionary that's is used for who's in the course and their permissions.
#
# * transactions
#
#    See http://docs.peewee-orm.com/en/latest/peewee/transactions.html :
#    peewee has some syntax for marking blocks as atomic
#    However, peewee's sqlite egine, based on pysql, is autocommit
#    by default and somewhat awkward to use otherwise.
#    (Turning off autocommit requires explict "begin" or "transaction".)
#    The suggested syntax is either
#      with db.transaction():
#        do_stuff()
#    or
#      @db.transaction()
#      def do():
#        stuff()
#    I think the "with" syntax is clearer - see
#    http://effbot.org/zone/python-with-statement.htm
#    for a discussion of what it is for in python -
#    and doesn't require a function definition.
#
# * get
#
#    peewee spells "find" as "get".
#    In other ORMs, get seems to often be only "get by id",
#    whereas find() or fetch() is by select() specifications.
#
# * flask
#
#    See docs.peewee-orm.com/en/latest/peewee/playhouse.html#flask-utils .
#    "automatically set up request ... handlers to ensure your connections
#    are managed properly"
#
#      from playhouse.flask_utils import FlaskDB
#      db = SqliteDatabase(db_path)
#      app = Flask(__name__)
#      flask_db = FlaskDB(app)
#
#    BUT it seems that this approach expects that flask_db
#    is in all the model meta information ... and that in
#    that case, testing the database or accessing it from
#    the command line doesn't work.
#
#    Looking at the source code, all that this really does is set
#       app.before_request(self.connect_db)
#       app.teardown_request(self.close_db)
#    where   connect_db => "database.connect()"
#    and    close_db    => "if not database.is_closed(): database.close()"
#    ... which seems simple enough for me to do myself in the flask app.
#
