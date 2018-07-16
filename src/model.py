# -*- coding: utf-8 -*-
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

 See docs/model_notes.txt for more about the database model.

 Jim Mahoney | mahoney@marlboro.edu | MIT License
"""

import os, subprocess, yaml, re, mimetypes, shutil
from werkzeug.security import generate_password_hash, check_password_hash
from peewee import SqliteDatabase, Model, \
     TextField, IntegerField, PrimaryKeyField, ForeignKeyField
from bs4 import BeautifulSoup
from utilities import markdown2html, link_translate, static_url, \
     ext_to_filetype, filetype_to_icon, size_in_bytes, \
     git, Time, stringify_access, print_debug, clean_access_dict
from settings import os_db, umber_url, protocol, hostname, umber_mime_types, \
    os_root, os_courses, photos_url, url_base, os_generic_course

db = SqliteDatabase(os_db)

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

    _by_username = {} # cache
    _admins = None

    @staticmethod
    def from_comma_string(comma_string):
        """ Return list of people from a string of usernames e.g. "john,mary" """
        return map(Person.by_username, comma_string.split(','))
    
    @staticmethod
    def searchname(partialname, maxresults=32):
        """ search for a name or username - returning up to a given number """
        people = Person.select().where( \
                    Person.name.contains(partialname) | \
                    Person.username.contains(partialname)) \
                    .order_by(Person.username).limit(maxresults)
        return [p.username for p in people]
    
    @staticmethod
    def create_person(username, name, email, password='', is_admin=False):
        with db.atomic():
            (user, created) = Person.get_or_create(username=username)
            user.name = name
            user.email = email
            user.set_password(password)
            user.save()
        Course.enroll_site(user, is_admin=is_admin)
        return user

    @staticmethod
    def edit_person(username, name, email, password):
        try:
            with db.atomic():
                user = Person.by_username(username)
                user.name = name
                user.email = email
                if password != '':
                    user.set_password(password)
                user.save()
        except:
            print_debug('OOPS : Person.edit_user(username="{}") failed' \
                                .format(username))
                    
    def course_data(self):
        """ return courses that this person is registered in 
            as a dict with keys role,course,url,semester """
        registrations = list(Registration.select(Registration.role, Registration.course)
                                         .where(Registration.person == self))
        registrations.sort(key=lambda r: r.course.start_date + ' ' + r.course.name)
        registrations.reverse()  # put most recent courses first
        return [{'role':r.role.name, 'course':r.course.name,
                 'url':r.course.url, 'semester':Time(r.course.start_date).semester()}
                for r in registrations if not r.course.name == 'Umber']

    def get_username(self, username):
        return Person.by_username(username)
    
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
        with db.atomic():
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

    def get_photo_url(self):
        return photos_url + '/' + self.username + '.jpg'

    @staticmethod
    def generic_photo_url():
        return photos_url + '/generic_student.png'
    
    @staticmethod
    def by_username(username):
        """ Returns anonymous person if not found """
        if username not in Person._by_username:
            try:
                person = Person.get(username = username)
                #person = Person.select() \
                #               .where(Person.username==username).first()
            except:
                return Person.get_anonymous()
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
    
    @staticmethod
    def admins():
        """ Return list of administrators """
        if not Person._admins:
            Person._admins = {p.username : True
                              for p in Person.by_rolename('admin')}
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

    _site_course = None  # course for site data

    def prepared(self):
        """ setup this instance after it's attributes are set """
        # This method is essentially __init__ for these database objects.
        self._set_users()
        self.assignments = self._get_assignments()
        self.semester = Time(self.start_date).semester()
        # url without request though that info is also in request
        self.url = umber_url + '/' + self.path
        self.abspath = os.path.join(os_courses, self.path)

    def _set_users(self):
        """ define self.students, .faculty, .guests, .username_to_role """
        registrations = list(Registration.select(Registration.person,
                                                 Registration.role)
                                         .where((Registration.course == self)
                                          &  (Registration.status != 'drop')))
        self.students = [reg.person for reg in registrations
                               if reg.role == Role.by_name('student')]
        self.faculty = [reg.person for reg in registrations
                               if reg.role == Role.by_name('faculty')]
        self.guests = [reg.person for reg in registrations
                               if reg.role == Role.by_name('guest')]
        self.students.sort(key=lambda s: s.name)
        self.faculty.sort(key=lambda s: s.name)
        self.username_to_role = {reg.person.username : reg.role
                                 for reg in registrations}
    
    @staticmethod
    def get_all():
        """ Return all but the 'Umber' course, sorted by semester """
        result = [c for c in Course.all() if not c.name == 'Umber']
        result.sort(key=lambda c: c.start_date + ' ' + c.name)
        result.reverse()
        return result

    @staticmethod
    def create_course(name, path, start='', name_as_title='',
                      copy_generic=False):
        if name_as_title == '':
            name_as_title = name
        if start == '':
            now = str(Time())
            now_year = now[:4]
            now_month = now[5:7]
            if now_month < '06':
                start = now_year + '-' + '01-01'  # spring
            elif now_month < '09':
                start = now_year + '-' + '06-01'  # summer
            else:
                start = now_year + '-' + '09-01'  # fall
        with db.atomic():
            (course, created) = Course.get_or_create(
                name = name,
                path = path,
                start_date = start,
                name_as_title = name_as_title
                )
        if copy_generic:
            shutil.copytree(os_generic_course, course.abspath)
        return course
    
    @staticmethod
    def get_site():
        """ return site admin course 'Umber' """
        if not Course._site_course:
            Course._site_course = Course.get(name='Umber')
        return Course._site_course

    @staticmethod
    def create_site():
        """ create site couse 'Umber' """
        # for site resoruces i.e. help files, user id photos etc.
        with db.atomic():
            (sitecourse, created) = Course.get_or_create(
                name = 'Umber',
                name_as_title = 'Umber<div>a course<br>managment<br>system</div>',
                path = '',
                start_date = '2018-01-01')
        return sitecourse
    
    def person_to_role(self, person):
        """ Return role of person in course, or visitor """
        return self.username_to_role.get(person.username,
                                         Role.by_name('visitor'))
    
    def username_is_member(self, username):
        return username in self.username_to_role
    
    def _get_assignments(self):
        return list(Assignment.select() \
                              .where(Assignment.course == self) \
                              .order_by(Assignment.nth))
    def drop(self, user):
        """ Drop user (Person or username) from this course """
        # (Students who are registered may have submitted work.
        # Rather than delete their files and database records,
        # I'm just changing their status to 'drop', and ignoring
        # those people in _set_users
        try:
            person = user
            name = person.name                 # Is this a Person object?
        except AttributeError:
            person = Person.by_username(user)  # No - treat it as a username.
            name = person.name
        if name == 'anonymous' or name == '':
            return "error in drop with user '{}'".format(str(user))
        with db.atomic():
            registration = Registration.get(person=person, course=self)
            registration.status = 'drop'
            registration.date = str(Time())
            registration.save()
        # refresh course data
        self._set_users()
        return "OK, dropped {}.".format(name)

    def get_profile_url(self):
        # site course ends with / ; others don't ... slightly different behavior.
        if self.url[-1] == '/':
            return self.url + 'sys/user'
        else:
            return self.url + '/sys/user'

    def get_home_url(self):
        return os.path.join(self.url, 'home')

    def get_registered(self):
        return self.students + self.guests + self.faculty

    def email_everyone_html(self):
        return "mailto:" + ','.join([p.email for p in self.get_registered()])
    
    def has_username(self, username):
        return username in self.username_to_role
    
    def get_faculty_data(self):
        """ return {'email', 'name'} of faculty """
        return [{'email':person.email, 'name':person.name} for person in self.faculty]

    def grade_data_list(self, student):
        """ return student's view grade list for templates/grades.html """
        # See the description below for the faculty grid.
        result = list(self.get_assignments_with_extras())
        for ass in result:
            # Hmmm - not sure why this needs .person_id here, but errors without.
            # Maybe something about how the jinja2 template treats variables?
            # Or because the assignment has had its fields modified??
            ass.work = ass.get_work(student.person_id)
            (grade, css_grade) = ass.work.get_grade_css(faculty_view=True)
            ass.work_grade = grade
            ass.work_css_grade = "grade-{}".format(css_grade)
            ass.duedate = Time(ass.due).assigndate()
        return result
    
    def grade_data_grid(self):
        """ return faculty's grade grid for templates/grades.html """
        # Returned data is list of dicts, one per student.
        # Each student dict includes list of student works, one per assignment.
        # The grade will be shown as
        #    '…'          if not submitted and not yet due
        #    'overdue'    if not submitted and past due date
        #    'ungraded'   if submitted and not graded
        #    work.grade   if submitted and graded
        #
        # The grade css class is "grade-*"
        # where * is one of (green,darkgreen,darkred,red,black)
        #   for faculty viewing the color is :
        #     red          overdue : due > today and not submitted
        #     brown        faculty modified date > student seen date
        #     darkgreen    student modified date > faculty seen date
        #     green        ungraded : student has submitted; faculty hasn't graded
        #     black        none of above
        #   for student viewing the color is : 
        #     brown        ungraded : student has submitted; faculty hasn't graded
        #     brown        student modified; faculty hasn't seen
        #     dark green   faculty modified; student hasn't seen
        #     green        overdue : due > today and not submitted
        #     black        none of above
        #
        # The basic idea of the colors is that
        #    green-ish means the viewer should respond (i.e. "go")
        #    red-ish   means that the other person should do something (i.e. a problem)
        #
        result = []
        for stud in self.students:
            works = []
            for ass in self.assignments:
                work = ass.get_work(stud)
                (grade, css_grade) = work.get_grade_css(faculty_view=True)
                works.append({'url':        work.get_url(),
                              'css_grade':  'grade-{}'.format(css_grade),
                              'grade':      grade,
                              'id':         work.work_id
                              })
            result.append({'email': stud.email,
                           'name' : stud.name,
                           'works': works
                           })
        return result
    
    def get_assignment_by_nth(self, nth):
        """ Return nth assignment in this course """
        try:
            return Assignment.select() \
                             .where(Assignment.course == self, \
                                    Assignment.nth == nth) \
                             .first()
        except:
            return None
                              
    def update_assignments(self, assignments_data):
        """ Update course assignments from 
            a dict of assignments_data[nth][name, due, blurb] """
        # Note: passed argument is *not* made up of Assignment objects.
        # Note: this is designed to update *all* assignments.
        db_assignments = {a.nth : a for a in self._get_assignments()}
        with db.atomic():
            for nth in assignments_data:
                if nth not in db_assignments:
                    (db_assignments[nth], status) = Assignment.get_or_create(
                        course=self, nth=nth)
                db_assignments[nth].name = assignments_data[nth]['name']
                db_assignments[nth].due = \
                  str(Time.parse(assignments_data[nth]['due']))
                db_assignments[nth].blurb = assignments_data[nth]['blurb']
                db_assignments[nth].save()
        self.assignments = self._get_assignments()

    def get_assignments_with_extras(self):
        """ Return list of assignments in this course with extra info """
        # ... i.e. prepare the data for html display
        now = Time()
        # print(" now = " + str(now))
        if len(self.assignments) == 0:
            self.assignment_nth_plus1 = 1
        else:
            self.assignment_nth_plus1 = self.assignments[-1].nth + 1
        for ass in self.assignments:
            duedate = Time(ass.due)
            if duedate < now:
                #print(" PAST : duedate = " + str(duedate))
                ass.dateclass = 'assign-date-past'
            else:
                #print(" FUTURE : duedate = " + str(duedate))
                ass.dateclass = 'assign-date'
            ass.date = duedate.assigndate()         # for assignment list display
            ass.ISOdate = duedate.assignISOdate()   # for assignment list editing
            ass.blurb_html = markdown2html(ass.blurb)
        return self.assignments
    
    def nav_page(self, user):
        """ return course's navigation page """
        # TODO: put this in a "try" and do something reasonable if it fails.
        #       (otherwise, pages in courses without sys/navigation.md will crash.)
        # TODO: should this be cached to self._nav_page ?
        # (Need it for both displaying and editing course's navigation page.)
        return Page.get_from_path(os.path.join(self.path,
                            'sys', 'navigation.md'), user=user)
    
    def nav_html(self, user, page):
        """ Return html for course's navigation menu 
            for a given user & a given page """
        return self.nav_page(user).nav_content_as_html(page)

    @staticmethod
    def enroll_site(person, datestring=None, is_admin=False):
        """ enroll a person in the site course """
        # All users should be in this course.
        if not datestring:
            datestring = str(Time())
        site_course = Course.get_site()
        if is_admin:
            site_role = Role.by_name('admin')
        else:
            site_role = Role.by_name('member')
        with db.atomic():
            (reg, created) = Registration.get_or_create(
                person = person,
                course = site_course)
            if created or is_admin:   # update role & date
                reg.role = site_role
                reg.date = datestring
            reg.status = ''
            reg.save()
        site_course._set_users()

    def make_student_work_folders(self):
        for person in self.students:
            student_abspath = os.path.join(self.abspath,
                                           'students', person.username)
            if not os.path.exists(student_abspath):
                Page.new_folder(student_abspath, user=person,
                                accessdict= {'read':person.username,
                                         'write':person.username})
            work_abspath = os.path.join(student_abspath, 'work')
            if not os.path.exists(work_abspath):
                Page.new_folder(work_abspath, user=person)
                    
    def enroll(self, person, rolename, datestring=None, create_work=False):
        """ Enroll a person in this course with this role. """
        # If there is an existing registration for the course&person, modify it.
        # Also enroll this person in the site couse if they aren't already
        # and if this isn't the site course itself.
        # Optionally create their work folder (if it doesn't already exist)
        if not datestring:
            datestring = str(Time())
        with db.atomic():
            (reg, created) = Registration.get_or_create(
                person = person,
                course = self)
            reg.role = Role.by_name(rolename)
            reg.status = ''     # if re-enrolling would have been 'drop'
            reg.date = datestring
            reg.save()
            if not self.name == 'Umber':
                Course.enroll_site(person, datestring=datestring)
        if create_work:
            # Create folder for student work within the course folder.
            # The absolute path for their student work folder is
            # e.g. course/students/johnsmith/    with its .access.yaml
            #   &  course/students/johnsmith/work/
            student_abspath = os.path.join(self.abspath,
                                           'students', person.username)
            Page.new_folder(student_abspath, user=person,
                            accessdict= {'read':person.username,
                                         'write':person.username})
            work_abspath = os.path.join(student_abspath, 'work')
            Page.new_folder(work_abspath, user=person)
        # refresh students
        self._set_users()

class Page(BaseModel):

    #  --- path, filename, url definitions ---
    #  With settings on my laptop development machine as
    #    os_courses    /Users/mahoney/academics/umber/courses
    #  then for the 'notes/week1' file within a course at 'fall/math' ,
    #  the parts are
    #    url:  http://127.0.0.1:5000/  umber    /  fall/math / notes/week1
    #          protocol  hostname   url_base    path...................
    #    file: /Users/mahoney/academics/umber/courses / fall/math / notes/week1
    #          os_courses                               path...................
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

    # Each course has some sys/* pages which get special treatment.
    # Also here are site/sys/* pages for editing users and courses,
    # which are only accessible within the 'site' course.
    system_pages = ('assignments', 'navigation', 'error', 'folder',
                    'grades', 'roster', 'user', 'users', 'course',
                    'courses', 'registration', 'newuser', 'newcourse')
    editable_system_pages = ('assignments', 'navigation',
                             'grades', 'user', 'course')
        
    page_id = PrimaryKeyField(db_column='page_id')

    as_html = TextField()
    content_hash = IntegerField()
    notes = TextField()
    path = TextField(unique=True)
    
    course = ForeignKeyField(rel_model=Course,
                             db_column='course_id',
                             to_field='course_id')

    _mime_types = None

    @staticmethod
    def new_folder(abspath, accessdict=None, user=None):
        """ Create a new folder with the given abspath.
            Add it into the github repo. 
            Optionally create its .access.yaml file. """
        if os.path.exists(abspath):
            # bail without doing anything of this already exists
            # print_debug(' new_folder {} already exists '.format(abspath))
            return None
        try:
            os.makedirs(abspath)  # makes intermediate folders if need be.
        except:
            # bail with error message if the OS system won't do it.
            print_debug(' os.makdir("{}") failed '.format(abspath))
            return None
        path = os.path.relpath(abspath, os_courses)
        folder = Page.get_from_path(path, user=user)
        git.add_and_commit(folder)
        if accessdict:
            folder.write_access_file(accessdict)
        return folder
    
    @classmethod
    def get_from_path(cls, path, revision=None, action=None, user=None):
        """ Get or create a Page and set up all its internal data 
            i.e. course, file info, user permissions, etc """
        (page, iscreated) = Page.get_or_create(path=path)
        if user == None:
            user = Person.get_anonymous()
        page.user = user
        page.action = action
        page.revision = revision
        page._setup_file_properties()           # sets page.isfile etc
        page.gitpath = os.path.join(os_courses, page.path_with_ext)
        page.course = page.get_course()
        if page.course.name == 'error':
            ### Unexpected (to me anyway) behavior here :
            ###     page.course = None
            ###     if page.course:        # This throws an error!
            ###        ...
            ### Apparently the peewee database code has put hooks into
            ### the Page object to do tricky stuff for "page.course",
            ### seems to drop into peewee and complain.
            ### I've avoided the issue by creating a special "error" course
            return page     # In umber.py will turn into a 404 - not found.
        page.relpath = page._get_relpath()
        page._setup_sys()                   # do this before .get_access()
        page.access = page.get_access()     # gets .access.yaml property.
        page._setup_user_permissions()      # sets page.can['read'] etc
        if revision or action=='history':
            page._setup_revision_data()     # sets page.history etc
        page._setup_attachments()           # sets .has_attachments
        page._setup_work()                  # 
        return page

    def _get_relpath(self):
        """ Return path of page relative to course path, 
            e.g. notes/home for path=demo/notes/home in course 'demo' """
        # self.course must be already set.
        return os.path.relpath(self.path, self.course.path)
    
    def attachments_folder(self):
        return self.abspath.replace(self.ext, '.attachments')
    
    def _setup_attachments(self):
        if self.is_file and self.ext == '.md':
            attach_dir = self.attachments_folder()
            if os.path.exists(attach_dir) and os.path.isdir(attach_dir):
                self.attachments = self.children(abspath=attach_dir)
            else:
                self.attachments = []
            self.has_attachments = len(self.attachments) > 0
        else:
            self.attachments = []
            self.has_attachments = False
            
    def _setup_work(self):
        """ see if this is a students/<name>/work/<number> student work page; 
            define .is_work and .work, set up .work for html display,
            update 
        """
        # print(' _setup_work : relpath = {}'.format(self.relpath))
        m = re.match(r'students/(\w+)/work/(\d+)(\?.*)?', self.relpath)
        if m:
            now = Time()
            self.is_work = True
            (work_username, work_nth, ignore) = m.groups()
            work_nth = int(work_nth)
            self.work_person = Person.by_username(work_username)
            self.work_assignment = self.course.get_assignment_by_nth(work_nth)
            self.work = self.work_assignment.get_work(self.work_person)
            duedate = Time(self.work_assignment.due)
            self.work_due = duedate.assigndate()
            if self.work.submitted:
                submitdate = Time(self.work.submitted)
                self.work_submitted = submitdate.assigndate()
                self.work_is_late = submitdate > duedate
            else:
                self.work_submitted = ''
                self.work_is_late = now > duedate
            self.work_grade = self.work.grade
            # update *_seen fields in the database
            # TODO : think about whether there's a better
            #        transactional way to update the database here.
            if self.user_role.name == 'faculty':
                self.work.faculty_seen = str(now)
                self.work.save()
            if self.user.username == work_username:
                self.work.student_seen = str(now)
                self.work.save()
        else:
            self.is_work = False
            #self.work = None
            #self.work_assignment = None
            #self.work_person = None
            #self.work_due = ''
            #self.work_submitted = ''
            #self.work_is_late = False
            #self.work_grade = ''
    
    def _setup_sys(self):
        """ define .is_sys.
            if it is, also define .sys_template, ./sys_edit_template """
        # If relpath is 'sys/assignments', then is_sys will be true,
        # the template will be 'umber/sys/assignments.html'
        # and the edit template will be 'umber/sys/edit_assignments.html',
        # (and the access permissions will be in the first line of the template.)
        self.is_sys = self.relpath[:4] == 'sys/'
        # -- default values for sys templates for all pages --
        if self.is_sys:
            which = self.relpath[4:]
            if which == '':
                which = 'folder'
            if which not in Page.system_pages:
                which = 'error'
            self.sys_template = 'sys/' + which + '.html'
            if which in Page.editable_system_pages:
                self.sys_edit_template = 'sys/edit_' + which + '.html'
            else:
                self.sys_edit_template = 'sys/editerror.html'
                
            #if self.sys_edit_template == 'umber/sys/editerror.html':
            #    if hasattr(self, 'can'):
            #        self.can['write'] = False
            ## ---- special cases ----
            # students can edit their passwords
            #if self.relpath == 'sys/user' and \
            #  self.user_rank >= Role.name_rank['member']:
            #    self.can['write'] = True         
            # public can see assignments
            #if self.relpath == 'sys/assignments':
            #    self.can['read'] = True

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
        if courses:
            return max(courses, key=lambda c: len(c.path))
        else:
            return Course.get_site()

    def write_access_file(self, accessdict):
        """ Given an access dict from user input e.g. 
            {'read':'students', 'write':['faculty','bob']} ,
            write it to a .access.yaml file, and return its abspath. """
        assert self.is_dir  # this page should be a folder
        accesspath = os.path.join(self.abspath, '.access.yaml')
        accessfile = open(accesspath, 'w')     # open or create
        # replace yaml permissions
        # (yaml.dump turns u'string' into ugly stuff so I convert to str().
        accessfile.write(yaml.dump(clean_access_dict(accessdict)))
        accessfile.close()
        git.add_and_commit(self, accesspath)
        return accesspath
    
    def get_access(self):
        """ Return .access dict from .access.yaml in an enclosing folder 
            or from the first line of a sys_template
        """
        # e.g. {'read': ['janedoe', 'johnsmith'], 'write': 'faculty'}
        # default if we don't find it.
        #access_dict = {'read':'all', 'write':'faculty'}  
        if self.is_sys:
            ## navigation is a special case : since it's a faculty editable file,
            ## I'll fill it it manually and not require that it have
            ## the {# #} first line.
            if self.relpath == 'sys/navigation' or \
               self.relpath == 'sys/navigation.md':
                access_dict = {'read':'member', 'write':'faculty'}
            else:
                ## all other system files have an access spec as their first line
                ## e.g.  {# {'read':'all', 'write':'faculty' #}
                template = os.path.join(os_root, 'templates', self.sys_template)
                firstline = open(template).readline()
                access_dict = eval(firstline.replace('{#','').replace('#}',''))
        else:
            if self.is_dir:
                abspath = self.abspath
            else:
                abspath = os.path.dirname(self.abspath)
            while len(abspath) >= len(os_courses):
                accesspath = os.path.join(abspath, '.access.yaml')
                if os.path.exists(accesspath):
                    accessfile = open(accesspath)
                    access_dict = yaml.load(accessfile)
                    accessfile.close()
                    if type(access_dict) == type({}):
                        # OK, we found an access dict, so stop here.
                        break
                abspath = os.path.dirname(abspath) # i.e. "cd .."
        if 'read' not in access_dict:
            access_dict['read'] = ''
        if 'write' not in access_dict:
            access_dict['write'] = ''
        # clean up for display :
        self.read_access = stringify_access(access_dict['read'])
        self.write_access = stringify_access(access_dict['write'])
        return access_dict

    def _setup_user_permissions(self):
        """ Set page.can['read'], page.can['write'],
                page.user_role, page.user_rank 
                from page.user, page.access, and page.course """
        # Note that admins who are faculty in a given course
        # will have a displayed role of 'faculty' in that course
        # but will have admin access to nav menus etc.
        assert self.course != None  # call self.set_course() first.
        assert self.access != None  # call self.set_access() first.
        assert self.user != None    #
        self.user_role = self.course.person_to_role(self.user)
        self.user_rank = self.user_role.rank
        
        if self.user_role.name in ('faculty', 'admin') and not self.is_sys:
            # faculty & admin can read or write anything 
            # ... but not system pages - I don't want 'edit' tab on all pages.
            self.can = {'read': True, 'write': True}
            return
        
        if self.user.is_admin():
            # Let site admins do what they want in any course.
            # But don't change their display name.
            # self.user_role = Role.by_name('admin')
            self.user_rank = Role.by_name('admin').rank
    
        self.can = {'read':False, 'write':False} # default is deny access
        for permission in ('read', 'write'):
            yaml_rights = self.access[permission]
            access_needed = 10  # i.e. more than anyone has by default
            # can be list e.g. ['faculty', 'bob'] or string 'students'
            if type(yaml_rights) == type(''):
                yaml_rights = [ yaml_rights ]
            for name_or_role in yaml_rights:
                if name_or_role == self.user.username:
                    self.can[permission] = True
                    break
                elif name_or_role in Role.name_alias:
                    access_needed = min(access_needed, \
                                        Role.by_name(name_or_role).rank)
            if self.user_rank >= access_needed:
                self.can[permission] = True

    def get_mimetype(self):
        """ Return e.g. 'image/jpeg' for '.jpg' file """
        if not Page._mime_types:
            mimetypes.init()
            Page._mime_types = mimetypes.types_map.copy()
            for key in umber_mime_types:
                Page._mime_types[key] = umber_mime_types[key]
        if self.ext == '':
            return 'text/plain'
        return Page._mime_types.get(self.ext, 'application/octet-stream')

    def keep(self):
        """ for folders, essentially 'touch .keep' at the command line """
        # This is a workaround for git's ignorance of folders.  Since git
        # tracks only files, it is not good at noticing new empty
        # folders. Worse, git seems to sometimes delete empty parent folders
        # when "git rm" removes all its contents.  The workaround is to add an
        # empty '.keep' file to a folder so that git can essentially see the
        # folder by the presence of the .keep file.  This method creates a
        # '.keep' file if the page is a folder.
        if self.is_dir:
            self.keepabspath = os.path.join(self.abspath, '.keep')
            keepfile = open(self.keepabspath, 'w')
            keepfile.close()
        else:
            # For consistency between files and folder, 
            # I'll set this to the page's path. 
            # That way both folders & files can use this for git commits.
            self.keepabspath = self.abspath

    def children(self, abspath=''):
        """ return page for each file or folder below this folder """
        result = []
        if abspath == '':
            abspath = self.abspath
        try:
            path = os.path.relpath(abspath, os_courses)
            for name in sorted(os.listdir(abspath)):
                if name[0] == '.':  # skip invisible files e.g. .access.yaml
                    continue
                result.append(Page.get_from_path(os.path.join(path, name), user=self.user))
        except OSError:  # i.e. if abspath isn't a directory.
            pass
        return result

    def icon_url(self):
        """ return url for icon for this file type """
        return static_url(filetype_to_icon[self.filetype])

    def _setup_revision_data(self):
        """ read and store within page the git file revision data """
        log = git.log(self)  # has the form [(githash, date, author)]
        if len(log) == 0:
            link = self.url
            date = self.lastmodified.daydatetimesec()
            author = ''
            self.githashes = tuple()
            self.history = [link, 'current', date, author]
            self.revision_date = date
            self.revision_prev_url = ''
            self.revision_next_url = ''
            self.revision_count = 1
            self.revision = None  # No git revision stored.
        else:
            self.githashes = tuple((githash for (githash, date, author) in log))
            self.history = [None] * len(log)
            for i in range(len(log)):
                #   say len(log) == 4 
                #     nth =>  (new) current 3 2 1 (old)
                #     i   =>        0       1 2 3 (old)
                if i == 0:
                    nth = 'current'
                    url = self.url
                else:
                    nth = len(log) - i
                    url = self.url + '?revision={}'.format(nth)
                #  history =>           0:url  1:nth  2:date     3:author
                self.history[i] = tuple((url,   nth,   log[i][1], log[i][2]))
            self.revision_count = len(log)
            self.revision_date = self.history[0][2]
            if self.revision:
                self.revision = int(self.revision)
                index = self.revision_count - self.revision
                self.revision_date = self.history[index][2]
                self.revision_next_url = self.url + '?revision={}'.format(
                    min(self.revision + 1, len(log)))
                self.revision_prev_url = self.url + '?revision={}'.format(
                    max(self.revision - 1, 1))

    def _setup_file_properties(self):
        """ given self.path, set a bunch of information about the file
            including self.absfilename, self.exists, self.is_file, self.is_dir,
            self.lastmodified, self.breadcrumbs
         """
        self.abspath = os.path.join(os_courses, self.path)
        self.path_with_ext = self.path  # default, unless modified below
        if not os.path.exists(self.abspath):
            for ext in ['.md', '.html']:
                if ext == '.md' and os.path.exists(self.abspath + ext):
                    self.abspath = self.abspath + ext
                    self.path_with_ext = self.path + ext
        (ignore, self.ext) = os.path.splitext(self.abspath)
        self.exists = os.path.exists(self.abspath)
        if not self.exists and self.ext == '':
            # creating a new file, so make it a .md markdown file
            self.ext = '.md'
            self.abspath += '.md'
        self.name_with_ext = os.path.split(self.abspath)[-1]
        if self.ext == '':
            self.name = self.name_with_ext
        else:
            self.name = self.name_with_ext[: - len(self.ext) ]
        # self.name_underlined = self.name + '\n' + '='*len(self.name)
        self.path_no_name = self.path[: - len(self.name) ]
        self.is_file = os.path.isfile(self.abspath)
        self.is_dir = os.path.isdir(self.abspath)
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
        url_list = [url_base] + self.path.split('/')
        urlsofar = protocol + hostname 
        self.breadcrumbs = '<a href="{}">{}</a>'.format(urlsofar, urlsofar)
        while url_list:
            pathpart = '/' + url_list.pop(0)
            urlsofar += pathpart
            self.breadcrumbs += '&nbsp;' + '<a href="{}">{}</a>'.format(
                urlsofar, pathpart)
        self.url = umber_url + '/' + self.path
        self.url_for_print_version = self.url + '?print=1'
        self.bytesize = size_in_bytes(self.size)

    def revision_content_as_html(self):
        content = git.get_revision(self)
        html = markdown2html(content)
        html_with_links = link_translate(self.course, html)
        return html_with_links

    def content(self):
        """ Return file or github (revision) data for a page """
        # TODO: should this be cached as self._content ?
        if self.exists and self.is_file:
            if self.revision:
                text = git.get_revision(self)
            else:
                with open(self.abspath, 'r') as _file:
                    text = _file.read()
                    try:
                        text = text.decode('utf8')
                    except:
                        pass    # i.e. jpg image files
        else:
            text = u''
        #print_debug(" page.content : page.action = '{}'".format(page.action))
        return text

    def write_content(self, new_content):
        """ Write new data to page's file; return number of bytes written """
        if self.can['write']:  # shouldn't get here without this anyway
            with open(self.abspath, 'w') as _file:
                try:
                    new_content = new_content.encode('utf8')
                except:
                    pass
                bytes_written = _file.write(new_content)
        return bytes_written

    def content_as_html(self):
        """ Return file contents as html. """
        # This also handles revisions since self.content() does.
        if not self.exists:
            return ''
        elif self.ext == '.md':
            content = self.content()
            html = markdown2html(content)
        # elif self.ext == '.wiki':
        #    html = subprocess.check_output(['wiki2html', self.abspath])
        else:
            # Just send the file as-is : txt, html, img, .... 
            html = self.content()
            # html = '<h2>Oops</h2> unsupported file type "{}"'.format(self.ext)
        html = link_translate(self.course, html)     # expand ~/ and ~~/
        return html

    def action_query(self):
        """ Return empty string or '&action=edit' if editing """
        if self.action == 'edit':
            return '&action=edit'
        else:
            return ''
    
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
        for role in Role.name_rank.keys():
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
        html = unicode(parser) # convert beautiful soup object to formatted unicode
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
        html = unicode(parser)
        return html
    
class Assignment(BaseModel):
    class Meta:
        db_table = 'Assignment'

    assignment_id = PrimaryKeyField(db_column='assignment_id')
    
    nth = IntegerField(null=False, unique=True)
    active = IntegerField()
    blurb = TextField()
    due = TextField(null=True)
    name = TextField()
    notes = TextField()
    
    course = ForeignKeyField(rel_model=Course,
                             db_column='course_id',
                             to_field='course_id')

    def get_url(self):
        return '{}/sys/assignments#{}'.format(self.course.url, self.nth)

    def name_smaller(self):
        """ return html version of assignment name with <br> instead of spaces """
        return self.name.replace(' ', '<br>')
    
    def get_work(self, person):
        """ Return Work for this assignment by given student """
        # i.e. work = assignment.get_work(student)
        with db.atomic():
            (work, created) = Work.get_or_create(assignment = self,
                                                 person = person)
            if created:
                work.grade = ''     # | I would have expected this to be 
                work.notes = ''     # | created with the sql defaults ...
                work.submitted = '' # | but apparently not.
                work.student_modified = ''
                work.faculty_modified = ''
                work.student_seen     = ''
                work.faculty_seen     = ''
                work.page = 0
                work.save()
        return work
    
class Role(BaseModel):
    class Meta:
        db_table = 'Role'

    role_id = PrimaryKeyField(db_column='role_id')
    
    name = TextField()
    rank = IntegerField()

    name_rank = {'admin': 5,
                 'faculty': 4,
                 'student': 3,
                 'member': 2,
                 'visitor': 1
                 }
    name_alias = {'admin':           'admin',
                  'administrator':   'admin',
                  'faculty':         'faculty',
                  'student':         'student',
                  'students':        'student',
                  'class':           'student',
                  'guests':          'member',
                  'guest':           'member',
                  'member':          'member',
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
        with db.atomic():
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
                
    grade = TextField()
    notes = TextField()
    submitted = TextField()
    student_modified = TextField(db_column='student_modified')
    student_seen = TextField(db_column='student_seen')
    faculty_modified = TextField(db_column='faculty_modified')
    faculty_seen = TextField(db_column='faculty_seen')

    assignment = ForeignKeyField(rel_model=Assignment,
                                 db_column='assignment_id',
                                 to_field='assignment_id')
    person = ForeignKeyField(rel_model=Person,
                             db_column='person_id',
                             to_field='person_id')
    page = ForeignKeyField(rel_model=Page,
                           db_column='page_id',
                           to_field='page_id')

    @staticmethod
    def edit_grades(id_grade_dict):
        """ id_grade_dict is web form with some {'work_<id>':new_grade}
            extract id's & change grades """
        # the dict also has other keys i.e. 'submit_work'; ignore them.
        try:
            with db.atomic():
                for key in id_grade_dict:
                    if key[:5] == 'work_':  
                        id = int(key[5:])
                        work = Work.get(work_id=id)
                        work.grade = id_grade_dict[key]
                        work.save()
        except:
            print_debug('OOPS : Work.edit_grades(id_grade_dict="{}") failed' \
                                .format(id_grade_dict))
    
    def get_url(self):
        # Also see templates/assignments.html
        return '{}/students/{}/work/{}.md'.format(self.assignment.course.url,
                                                  self.person.username,
                                                  self.assignment.nth)

    def get_grade_css(self, faculty_view):
        css_class = 'black'      # the default
        before_due_date = Time() < Time(self.assignment.due)
        # Set blank times to '1901' to avoid errors.
        faculty_modified = self.faculty_modified or '1901'
        faculty_seen = self.faculty_seen or '1901'
        student_modified = self.student_modified or '1901'
        student_seen = self.student_seen or '1901'
        #print_debug("   faculty_modified = '{}'".format(faculty_modified))
        #print_debug("   faculty_seen = '{}'".format(faculty_seen))
        #print_debug("   student_modified = '{}'".format(student_modified))
        #print_debug("   student_seen = '{}'".format(student_seen))
        if faculty_view:
            if Time(faculty_modified) > Time(student_seen):
                css_class = 'brown'
            if Time(student_modified) > Time(faculty_seen):
                css_class = 'darkgreen'
            if not self.submitted:
                if before_due_date:
                    grade = u'…'
                else:
                    grade = 'overdue'
                    css_class = 'red'
            else:
                if not self.grade:
                    grade = 'ungraded'
                    css_class = 'green'
                else:
                    grade = self.grade
        else:
            if Time(student_modified) > Time(faculty_seen):
                css_class = 'brown'
            if Time(faculty_modified) > Time(student_seen):
                css_class = 'darkgreen'
            if not self.submitted:
                if before_due_date:
                    grade = u'…'
                else:
                    grade = 'overdue'
                    css_class = 'green'
            else:
                if not self.grade:
                    grade = 'ungraded'
                    css_class = 'brown'
                else:
                    grade = self.grade
        if self.grade:             # If a grade has been assigned, show it. Period.
            grade = self.grade
        return (grade, css_class)

def init_db():
    """ Create base database objects """
    # i.e. roles & site course.
    # The Roles data must be in place for the login system to work.
    # And the Umber course must exist for user photos and site docs
    # and admin user role.
    # The sql database must already exist; see bin/init_db .
    # All these are "get_or_create", so running 'em multiple times won't hurt.
    Role.create_defaults()
    Course.create_site()
    
def populate_db():
    """ Create test & example development objects """
    # i.e. democourse, jane, ted, john, adam; examples and tests.
    #print "Populating development database."
    
    with db.atomic():
        student = Role.by_name('student')
        faculty = Role.by_name('faculty')

        democourse = Course.create_course(
            name = 'Demo Course',
            name_as_title = 'Demo<br>Course',
            path = 'demo',
            start = '2018-01-01' )
         
        jane = Person.create_person(
            username = 'janedoe',
            name = 'Jane Q. Doe',
            email = 'janedoe@fake.address',
            password = 'test' )
        
        john = Person.create_person(
            username = 'johnsmith',
            name = 'Johnny Smith',
            email = 'johnsmith@fake.address',
            password = 'test' )
        
        ted = Person.create_person(
            username = 'tedteacher',
            name = 'Ted Teacher',
            email = 'ted@fake.address',
            password = 'test' )

        adam = Person.create_person(
            username = 'adamadmin',
            name = 'Adam Administrator',
            email = 'adam@fake.address',
            password = 'test',
            is_admin = True )
        
        default_date = '2018-01-02'
        democourse.enroll(john, 'student', default_date, create_work=False)
        democourse.enroll(jane, 'student', default_date, create_work=False)
        democourse.enroll(ted,  'faculty', default_date, create_work=False)

        # Assignments are set with a dict {nth: {name, due, blurb}.
        assignments_data = {
            1: {'name': 'week 1',
                'due': '2018-01-23',
                'blurb': 'Do chap 1 exercises 1 to 10.'},
            2: {'name': 'week 2',
                'due': 'Jan 28 2018 5pm',
                'blurb': 'Write a four part fugue.'}
            }
        democourse.update_assignments(assignments_data)
        assign1 = democourse.get_assignment_by_nth(1)

        johns_work = assign1.get_work(john)
        johns_work.grade = 'B'
        johns_work.submitted = '2018-01-22T18:20:23-05:00'      # on time
        johns_work.student_seen = johns_work.submitted
        johns_work.student_modified = johns_work.submitted
        johns_work.faculty_seen = '2018-01-28T16:00:00-05:00'
        johns_work.faculty_modified = johns_work.faculty_seen
        johns_work.save()

        janes_work = assign1.get_work(jane)
        janes_work.submitted = '2018-02-04T22:23:24-05:00',   # past due
        # janes_work.grade = ''                               # not graded yet
        janes_work.student_seen = janes_work.submitted
        janes_work.student_modified = janes_work.submitted
        janes_work.save()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
