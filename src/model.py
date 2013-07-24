# -- coding: utf-8 --
"""
 sqlalchemy database model for umber

 --- examples / tests ---
 
 To initialize the database and run the tests from the command line :

   $ pwd
   .../umber
   $ . env/bin/activate
   (env)$ reset_db
   ...

   Then either
   
   (env)$ ./console
   >> test()

   or
   
   (env)$ python src/model.py -v
   ...
   Test passed.

 The tests and manual database changes can also be run in the console;
 run ./console from the umber directory.
   
 >>> populate_db()
 <BLANKLINE>
  Populating database with defaults and test data.
 >>> Course.init_demo()
  Initilizing directories and permissions for demo course.

 >>> demo = Course.find_by(name = 'Demo Course')
 >>> print demo.name
 Demo Course

 >>> usernames = sorted(demo.userdict().keys())
 >>> users = demo.userdict()
 >>> roles = demo.roledict()
 >>> for x in usernames:
 ...   print "{} is a {}.".format(users[x].name, roles[x].name)
 Jane Q. Doe is a student.
 Johnny Smith is a student.
 TedTeacher is a faculty.

 >>> dirs = {x : Directory.find_by(name=x, course=demo) 
 ...             for x in ('', 'protected', 'johnsmith')}
 >>> for who in usernames:
 ...     for where in dirs.values():
 ...       role = roles[who]
 ...       print "{} {} read, {} write '{}.'".format( 
 ...              users[who].name, 
 ...              'can' if where.can_read(users[who], roles[who]) else 'cannot',
 ...              'can' if where.can_write(users[who], roles[who]) else 'cannot',
 ...              where.name)
 Jane Q. Doe can read, cannot write '.'
 Jane Q. Doe cannot read, cannot write 'johnsmith.'
 Jane Q. Doe can read, cannot write 'protected.'
 Johnny Smith can read, cannot write '.'
 Johnny Smith can read, can write 'johnsmith.'
 Johnny Smith can read, cannot write 'protected.'
 TedTeacher can read, can write '.'
 TedTeacher can read, can write 'johnsmith.'
 TedTeacher can read, can write 'protected.'

 >>> (dirs['johnsmith'].name == 'johnsmith', 
 ...  dirs['johnsmith'].path == 'students/johnsmith',
 ...  dirs['johnsmith'].coursepath == 'demo_course/students/johnsmith')
 (True, True, True)
 
 >>> john = Person.find_by(username = 'johnsmith')      # get table row
 >>> print john.name                                    # display column
 Johnny Smith
 >>> john.name = 'John Z. Smith'                        # modify column
 >>> db_session.flush()                                 # save changes
 
 >>> demo.name = 'Demo Course - new name'
 >>> db_session.flush()
 >>> Course.find_all_by(name = 'Demo Course')           # Now can't find it.
 []

 Show the name of the first course John is in. 
 (There's a lot going on behind the scenes here - the relationship()
 method has setup a Person.courses field to follow the many-to-many connection
 from Person through Registration to Course.
 >>> print john.courses[0].name
 Demo Course - new name

 Find John's status in the demo course.
 (This is also doing some tricky stuff, since we're using objects - 
 not ids - to identify which registration to find.)
 >>> print Registration.find_by(person = john, course = demo).role.name
 student
 
 >>> db_session.rollback()     # Undo these uncommited database modifications,
 >>> db_session.remove()       # and close the session nicely.

 --- discussion ---
 
 Here are a few of the concepts behind all this.

 For more details, see e.g.
 http://flask.pocoo.org/docs/patterns/sqlalchemy/ ,
 http://docs.sqlalchemy.org/en/rel_0_7/orm/query.html ,
 and the other reams of stuff at docs.sqlalchemy.org
 
  * In sqlalchemy's view of the world, db_session holds the local
    memory state of this thread's interaction with the database.
    Objects (e.g. a Person or Course, an instance of which corresponds
    to a row in a sql table) exist in both the session and the
    database. 

    The picture looks something like this.

      sqlite -- engine --   db_session -- Umber objects
      data      software    memory        memory instances of rows
      file      connection  state         e.g. Person, Course, ...
    
 * I've set things up (see below) so that all new object instances are 
   added to db_session automatically. (This isn't the sqlalchemy default.)
    
 * Modifications to the objects can be sent to the database 
   in two ways: via 'flush' (which continues the current transaction)
   or 'commit' (which finishes this transaction). 'rollback' undoes
   everything to the previous commit. (These three are all db_session
   methods.) The flush or commit operations can be set to take
   place automatically, whenever an instance is modified.
   I've turned that off; see the creation of db_session below.

 For this project, the database tables themselves and their schema
 are defined with SQL, in database/create_umber_db.sql. Then the
 parent Umber class automatically defines the methods and matching
 fields within each inherited Person, Course, etc object.

 Often this is done the other way around, with the database tables defined
 by the python classes, and the SQL generated automatically. That way of
 working is for example described at flask.pocoo.org/docs/patterns/sqlalchemy,
 where the model is e.g.
      class User(Base):
          __tablename__ = 'users'
          id = Column(Integer, primary_key=True)
          name = Column(Integer, unique=True)
          # and so on
 Then the sqlite (or other) database itself can be created automatically 
 via something like
      Base.metadata.create_all(bind=engine)
 But here I'm working in the direction, starting from the SQL 
      CREATE TABLE Person (
          person_id INTEGER PRIMARY KEY NOT NULL,
          username TEXT UNIQUE NOT NULL,
          # and so on )
 and then use 'autoload' (see below) to generate the Person.username 
 and similar object interfaces.

 The Person and AnonymousPerson classes are consistent
 with Flask-Login's expectations.

 python-ldap may also be used for authentication,
 in addition to the password hashes in the database.
 
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from settings import project_os_path, pages_os_root, pages_url_root
from werkzeug.security import generate_password_hash, check_password_hash
import os

db_path = 'sqlite:///' + project_os_path + '/database/umber.db'
db_engine = create_engine(db_path, convert_unicode = True)
db_session = scoped_session(sessionmaker(autocommit = False, 
                                         autoflush = False, 
                                         bind = db_engine))

class Umber(object):
    """ All of this project's database objects inherit from this class. """

    @declared_attr
    def __tablename__(cls):
        """ Set name of database table from class name """
        # e.g. "class Person" corresponds to SQL table 'Person'
        return cls.__name__

    # Define fields in each table for each column automatically,
    # e.g. Person.username , since Person table has a 'username' column.
    __table_args__ = {'autoload': True, 'autoload_with': db_engine}

    @classmethod
    def col(cls, column):
        """ Return given SqlAlchemy column object """
        # e.g. Person.col('name') is same as Person.name
        return cls.__dict__[column]

    # Define shortcut methods for several database retrieval
    # operations using sqlalchemy's query, filter, like, one, all,
    # e.g. Class.filter(...) rather than Class.query.filter(...)
    
    @classmethod
    def filter(cls, *args):
        return cls.query.filter(*args)
    
    @classmethod
    def all(cls, *args):
        return cls.query.all(*args)
    
    @classmethod
    def filter_by(cls, **kwargs):
        """ Return query.filter_by(column=value, column=value, ...) """
        return cls.query.filter_by(*args)
    
    @classmethod
    def find_by(cls, **kwargs):
        """ Return database object with column=value, column=value, ... """
        # e.g. Person.find_by(name = 'Philip J. Fry', age = 32)
        # Throws an error if not found, or if more than one result found.
        return cls.query.filter_by(**kwargs).one()
    
    @classmethod
    def find_all_by(cls, **kwargs):
        """ Return list of database objects with column=value, column=value, ... """
        # e.g. Person.find_all_by(firstname = 'Jon')
        return cls.query.filter_by(**kwargs).all()
    
    @classmethod
    def filter_like(cls, **kwargs):
        """ Return query made using SQL 'LIKE' matches in column=like_value """
        # e.g. query = Person.query_like(name = '%Fry%')
        q = cls.query
        for (column, like_value) in kwargs:
            q = q.filter(cls.col(column).like(like_value))
        return q
        
    @classmethod
    def find_like(cls, **kwargs):
        """ Return the database object with column LIKE like_value. """
        # SQL uses % as the wildcard character
        # e.g. Person.find_like(name = '%Fry%')
        # (Throw an error if there's more than one; return None if not found)
        return cls.filter_like(**kwargs).one()
        
    @classmethod
    def find_all_like(cls, **kwargs):
        """ Return a list of objects with column LIKE like_value. """
        return cls.filter_like(**kwargs).all()

    @classmethod
    def find_or_create(cls, **kwargs):
        """ Fetch the object with given properties from the database
            or create a new one in the session."""
        # (See umber_init_object below : these newly created 
        # objects are db_session.add'ed automatically.)
        # e.g. jon = Person(username = 'jon') # get or create it
        #      jon.lastname = 'Smith'         # modifiy its data
        #      db_session.commit()            # save to database
        try:
            result = cls.find_by(**kwargs)     # throw error if > 1 result
            assert result != None              # throw error if < 1 result
        except:
            result = cls(**kwargs)
        return result

    def __repr__(self):
        """ Default object representation """
        # e.g. <Person name='Philip J. Fry' id=xxxx>
        try:
            name = self.name
            if name == None:
                return "<{} name=None id={}>".format(self.__class__.__name__, 
                                                     id(self))
            else:
                return "<{} name='{}' id={}>".format(self.__class__.__name__,
                                                     name, id(self))
        except:
            return "<{} id={}>".format(self.__class__.__name__, id(self))
            
Base = declarative_base(cls = Umber)
Base.query = db_session.query_property()
            
# Define bare object class for each database table.
# Object methods for the table columns are created automatically.
# Relation methods (many-to-one etc) for objects corresponding
# to foreign keys are setup below; see 
# docs.sqlalchemy.org/en/rel_0_7/orm/extensions/declarative.html .
#
# The many-to-many relations defined through an intermediate table don't
# seem to be appropriate for editing; see 'viewonly' in declarative.html:
#   "not a good idea to use [..] “secondary” arg [..] mapped
#    to a class unless the relationship is declared with viewonly=True
#    Otherwise [..] may attempt duplicate INSERT and DELETE"
#

def umber_object_init(self, *args, **kwargs):
    # Seems that it isn't possible to put a default __init__ method in
    # the Umber class; sqlalchemy's Base apparent set up its own.
    # This is a workaround.
    #
    # Also the sqlalchemy philosophy apparently wants to separate db_session
    # from the model, which is why, I think, they want expect an 
    # explicit db_session.add() after earch object instantiation. 
    # But I'm unconvinced, and want each new object automatically added
    # to db_session. (Note that db_session.flush() or .commit() is 
    # still required after creating an object before the database is modified.)
    # db_session.expunge(obj) can undo the .add() before a .commit().
    #
    # Objects pulled from the database by the inherited
    # cls.find_by(...) methods do *not* invoke cls's own __init__
    # methods ... not the behavior I expected.
    #
    Base.__init__(self, *args, **kwargs)
    db_session.add(self)

class Person(Base):
    # columns: person_id, ldap_id, username, firstname, lastname, email,
    #          password, crypto, notes
    # relations: courses, works, registrations
    # implements Flask-Login's 'User Class' 
    #   with is_authenticated(), is_active(), is_anonymous(), get_id()
    # password scheme from http://flask.pocoo.org/snippets/54/

    __init__ = umber_object_init
    #def __init__(self, *args, **kwargs):
    #    umber_object_init(self, *args, **kwargs)

    def is_authenticated(self):           # for Flask-Login
        try:
            return self.logged_in
        except:
            return False
    def is_active(self):                  # for Flask-Login
        return self.is_authenticated()
    def is_anonymous(self):               # for Flask-Login
        try:
            return self.anonymous
        except:
            return False
    def get_id(self):                     # for Flask-Login; stored in session
        if self.username == None:
            return unicode('')
        else:
            return unicode(self.username)
    def set_password(self, passwordtext):
        self.password = generate_password_hash(passwordtext)
        db_session.commit()
    def check_password(self, passwordtext):
        return check_password_hash(self.password, passwordtext)

    def set_status(self, logged_in=True, role=''):
        """ Set nondatbase data """
        self.logged_in = logged_in
        self.role = role
    
def anonymous_person():
    anony = Person(name=u'', username=u'')
    db_session.expunge(anon)   # don't write this one to the database
    anony.set_status(logged_in=False, role='any')
    anony.anonymous = True
    return anony

Role_name_rank = {'admin':5, 'faculty':4, 'student':3, 'guest':2, 'all':1}
class Role(Base):
    # columns: role_id, name, rank
    # Role.named('faculty') # memoized roles
    __init__ = umber_object_init
    name_rank = Role_name_rank
    names = set(Role_name_rank.keys())
    _roles_ = {}
    @classmethod
    def init_database(cls):
        for (name, rank) in Role_name_rank.items():
            Role.find_or_create(name=name, rank=rank)
        db_session.commit()
    @classmethod
    def named(cls, name):
        """ e.g. Role.named('faculty') # memoized """
        try:
            return Role._roles_[name]
        except:
            try:
                result =  Role.find_by(name=name)
                Role._roles_[name] = result
                return result
            except:
                return None

class Course(Base):
    # columns: course_id, name, name_as_title, path, credits,
    #          start_date, end_date, assignments_md5, active, notes
    # relations: persons, assignments, directories, root
    def __init__(self, *args, **kwargs):
        # Enforce coursepath=unique constraint, to avoid
        # e.g. 'demo_course/foo' to be in both
        # the 'Demo Course' and default 'Umber' courses.
        umber_object_init(self, *args, **kwargs)
    def uri(self):
        return '- uri -'
    def semester(self):
        return '- semester -'
    def os_path(self):
        return os.path.join(project_os_path, pages_os_root, self.path)
    def init_directories(self, course_defaults = True):
        """ Remove any old database directory objects and their permissions.
            Then create database directories and deafult permissions
            all folders in this course's file tree."""
        # print "-- init_directories( course.name='{}')".format(self.name)
        # print "  project_os_path = ", project_os_path
        # print "  pages_os_root   = ", pages_os_root
        # print "  course_os_path  = ", self.os_path()
        # for dir_os_path, dirnames, filenames in os.walk(self.os_path()):
        #     print "  ", dir_os_path

        ### GETTING ERRORS - I think I'm trying to delete 
        ### a directory without deleting its permission first.
        ### Perhaps set up a cascade delete ??
        for dir in self.directories:
            Directory.delete(dir)
            #db_session.execute('delete from Permission where directory_id=:id;',
            #                   {'id': dir.directory_id})
            #db_session.delete(dir)
        # There should always be a root os folder at self.os_path()
        #try:
        #    db_session.delete(Directory.find_by(coursepath=self.path))
        #    db_session.commit()
        #except:
        #    pass
        Directory.delete_coursepath(self.path)
        root_dir = Directory(name='', path='', coursepath=self.path, course=self)
        root_dir.set_permissions()
        db_session.commit()
    def userdict(self):
        """ Course.find_by(name=...).userdict()[username] => user """
        try:
            self._userdict_
        except:
            self._userdict_ = {p.username: p for p in self.persons}
        return self._userdict_
    def roledict(self):
        """ Course.find_by(name=...).roledict()[username] => role """
        try: 
            self._roledict_
        except:
            self._roledict_ = {}
            for p in self.persons:
                try:
                    self._roledict_[p.username] = \
                      Registration.find_by(course=self, person=p).role
                except:
                    pass
        return self._roledict_

    #def by_role(self, role):
    #    if isinstance(role, str):
    #        role = Role.named(role)
    #    return Person.filter_by(course=self).filter_by(role=role).all()
    #def students(self):
    #    return self.by_role('student')

    ####
    @classmethod
    def init_demo(cls):
        demo = Course.find_by(name='Demo Course')
        print " Initilizing directories and permissions for demo course."
        demo.init_directories()
    
class Registration(Base):
    # columns: registration_id, person_id, course_id, role_id,
    #          date, midterm, grade, credits, status
    # relations: person, course, role
    __init__ = umber_object_init

class Assignment(Base):
    # columns: assignment_id, course_id, name, uriname, due, nth,
    #          blurb, active, notes
    # relations: course
    __init__ = umber_object_init
    
class Work(Base):
    # columns: work_id, person_id, assignment_id, submitted, 
    #          studentLastSeen, studentLastModified,
    #          facultyLastSeen, facultyLastModified,
    #          grade, notes
    # relations: person, assignment, course
    __init__ = umber_object_init

class Directory(Base):
    # columns: directory_id, name, course_id, coursepath, path, parent_id
    # relations: course, parent, children, permissions
    __init__ = umber_object_init
    #def __init__(self, *args, **kwargs):
    #    #try:
    #    #    old_dir = Directory.find_by(coursepath=kwargs['coursepath'])
    #    #    db_session.delete(old_dir)
    #    #    db_session.commit()
    #   #except:
    #   #    pass
    #   umber_object_init(self, *args, **kwargs)
    no_access = 0
    read_access = 1
    write_access = 3
    # The following are in addition to the built-in
    # admin-write-everywhere, faculty-write-course.
    rights_defaults = {'':         { 'read': ('all', ),  'write' : ()},
                       'admin':    { 'read': (),         'write' : ()},                 
                       'faculty':  { 'read': (),         'write' : ()},
                       'private':  { 'read': (),         'write' : ()},                 
                       'protected':{ 'read': ('guest', ),'write' : ()},
                       'students': { 'read': (),         'write' : ()},
                       'wiki':     { 'read': ('all', ),  'write' : ('guest',)},
                      }
    @classmethod
    def delete_coursepath(cls, coursepath):
        try:
            dir = Directory.find_by(coursepath=coursepath)
            Directory.delete(dir)
        except:
            pass
    @classmethod 
    def delete(cls, directory):
        """ Course.delete(dir) 
            delete a directory and its permissions from the database """
        # syntax : Course.delete(dir)
        # 
        db_session.execute('delete from Permission where directory_id=:id;',
                               {'id': directory.directory_id})
        db_session.delete(directory)
        db_session.commit()
    def os_path(self):
        return os.path.join(self.course.os_path(), self.path)
    def set_1_permission(self, who, rights):
        if who in Role.names:
            r = Role.named(who)
            Permission(rights=rights, directory=self, person=None, role=r)
        else:
            try:
                if isinstance(who, str):
                    p = Person.find_by(username=who)
                else:
                    p = who
                x = Permission(rights=rights, directory=self, person=p, role=None)
            except:
                pass # quietly fail if given username isn't in the database
                     # TODO - think about edge case here more ...
                     # student/joe folder before joe is in database ??

    def set_permissions(self, course_defaults=True, recur=True,
                        readers=(), writers=()):
        """ Setup Permission database entries for this directory.
            defaults = True  =>  set readers() and writers() based
                                 on standard course folder names
                                 instead of readers() and writers()
                                 (e.g. protected, students, johnsmith, ...)
            recur = True     =>  recursively setup child directories
            readers, writers =>  list of username and role names
        """
        if course_defaults:
            users = self.course.userdict()
            if self.name in Directory.rights_defaults:
                readers = Directory.rights_defaults[self.name]['read']
                writers = Directory.rights_defaults[self.name]['write']
            elif self.name in users:
                readers = ()
                writers = (users[self.name], )
            else:
                pass   # if no name match, use given readers and writers
        db_session.execute('delete from Permission where directory_id=:id;',
                           {'id': self.directory_id})
        for who in writers:
            self.set_1_permission(who, rights = Directory.write_access)
        for who in (set(readers) - set(writers)):
            self.set_1_permission(who, rights = Directory.read_access)
        db_session.commit()
        for subname in os.walk(self.os_path()).next()[1]:
            subpath = os.path.join(self.path, subname)
            subcoursepath = os.path.join(self.course.path, subpath)
            #try:
            #    db_session.delete(Directory.find_by(coursepath=subcoursepath))
            #    db_session.commit()
            #except:
            #    pass
            Directory.delete_coursepath(subcoursepath)
            sub = Directory(course=self.course, 
                    name=subname, path=subpath, coursepath=subcoursepath)
            sub.set_permissions(course_defaults, recur, readers, writers)
    def can_read(self, user, role=None):
        return self.rights(user, role) >= Directory.read_access
    def can_write(self, user, role=None):
        return self.rights(user, role) >= Directory.write_access
    def rights(self, user, role=None):
        if role == None:
            role = Role.named('all')
        elif isinstance(role, str):
            role = Role.named(role)
        try:
            return self._result_[(user.person_id, role.role_id)]
        except:
            # I tried several variations on this sql syntax, expecting
            # to use the "select max() ..." to pull the largest value.
            # But various "join" efforts failed, i.e. when the first select
            # had no entries but the 2nd did, the join would be empty.
            # This is only one database query ... so good enough.
            rights_sql = """
              select rights from Permission 
                where directory_id = :directory_id and person_id = :person_id
              union
              select rights from Permission natural join Role 
                where directory_id = :directory_id and :rank >= rank;"""
            if role.name in ('admin', 'faculty'):
                # assuming faculty => faculty for this course
                result = Directory.write_access
            else:
                sql_result = db_session.execute(
                    rights_sql, {'directory_id' : self.directory_id, 
                                 'person_id' : user.person_id,
                                 'rank' : role.rank}).fetchall()
                if len(sql_result) == 0:
                    result = 0
                else:
                    result = max(sql_result[0])  # sql_result is e.g. [(3,)]
            try:
                self._result_
            except:
                self._result_ = {}
            self._result_[(user.person_id, role.role_id)] = result
            return result
        
class Permission(Base):
    # columns: permission_id, rights, directory_id, role_id, person_id
    # relations: directory, role, person
    ##
    ##   These default permissions are *not* in the database :
    ##      'admin'  can always read & write everything. 
    ##      'faculty'can alway read & write their course
    ##   All other read/write directory permissions are configuable,
    ##   and therefore have corresponding Permission database entries.
    ##
    ##   The rights column is either 3 (write & read) or 1 (read),
    ##   and in the code here a 0 means no rights.
    ##     
    ##   a Permission has either a role (e.g. 'all') or person (e.g. 'smith')
    ##
    ##
    __init__ = umber_object_init
    
Person.registrations = relationship(Registration)
Person.works = relationship(Work)
Person.courses = relationship(Course, viewonly = True,
                              secondary = Registration.__table__)

Course.assignments = relationship(Assignment)
Course.directories = relationship(Directory)
Course.persons = relationship(Person, viewonly = True,
                              secondary = Registration.__table__)

Registration.person = relationship(Person)
Registration.course = relationship(Course)
Registration.role = relationship(Role)

Assignment.course = relationship(Course)

Work.person = relationship(Person)
Work.assignment = relationship(Assignment)

Directory.course = relationship(Course)
# Setting up the following .parent, .child relationships was nasty -
# lots of trial and error. For a time, I was exlplicitly setting
#   primaryjoin = Directory.parent_id == Directory.directory_id
# which parses correctly, but apparently is deduced from the sqlite3
# CONSTRAINT syntax correctly and wasn't the source of my problems.
# Without the uselist=False, the system sets up parent as a list, not
# a singe one-child-to-one-parent, and Directory(parent=x) would
# crash. The remote_side= argument seems to be correctly setting which
# end is which, but finding it in the sqlalchemy docs was not trivial.
Directory.parent = relationship(Directory, 
                   remote_side=Directory.directory_id, uselist=False)
Directory.children = relationship(Directory, remote_side=Directory.parent_id)
Directory.permissions = relationship(Permission)

Permission.role = relationship(Role)
Permission.person = relationship(Person)
Permission.directory = relationship(Directory)

class Page(object):
    """ a url-accessable file in a Course """
    # pages (i.e. files other than directories) are *not* in the database
    # ... though student Work objects do have a corresponding file.
    # Instead, they're used during the lifetime of a URL request
    # to manage access to the corresponding wiki or markdown or whatever
    # file resource.
    def __init__(self, 
                 pagepath=None, # string from URL host/pages_url_root/pagepath
                 request=None,  # Flask request object
                 user=None,     # Person
                 insecure_login=False
                 ):

        self.insecure_login = insecure_login  # False if via https
        self.request = request
        self.secure_url = 'https://' + request.host + request.path
        self.pagepath = pagepath
        self.user = user
        self.path = request.path if request != None else ''

        # Find directory corresponding to this page from pagepath
        # by walking upwards. The fallback if nothing else is found
        # is the top 'Umber' course,
        # with pagepath=''.
        try:
            self.is_directory = True
            self.directory = Directory.find_by(path = pagepath)
        except:
            self.is_directory = False
            directorypath, self.name,  = os.path.split(pagepath)
            self.directory = Directory.find_by(path = directorypath)

        self.course = Course()
        self.uri_links = '- uri_links -'
        self.full_path = request.full_path if request != None else ''
        self.title = '- title -'
        self.has_error = False
        self.has_lastmodified = True
        self.lastmodified = ' - MODIFIED DATE -'

def populate_db():
    """ Create and commit the initial database objects """
    # The database should have already been created; see database/init_db.  
    #
    # The various .find*(...) methods look for things in the database,
    # not just in the current session, so they must already be
    # committed before they can be used. And the *_id fields don't
    # have values until after the object is in the database.  However, 
    # when accessing (or setting) related objects directly, other
    # objects may be used, e.g. "work1.person = john". And that even
    # can work with objects in the arguments - see my >>> tests above.
    #
    print "\n Populating database with defaults and test data."
    Role.init_database()

    umbercourse = Course.find_or_create(name = 'Umber',
                                        path = '',
                                        start_date = '2013-01-01')
    # This must be before any other courses are created.
    umbercourse.init_directories()
    
    student = Role.find_by(name = 'student')
    faculty = Role.find_by(name = 'faculty')    
    jane = Person.find_or_create(username = 'janedoe',
                                 firstname = 'Jane',
                                 lastname = 'Doe',
                                 name = 'Jane Q. Doe',
                                 email = 'janedoe@fake.address')
    jane.set_password('test')
    john = Person.find_or_create(username = 'johnsmith',
                                 firstname = 'John',
                                 lastname = 'Smith',
                                 name = 'Johnny Smith',
                                 email = 'johnsmith@fake.address')
    john.set_password('test')
    tedt = Person.find_or_create(username = 'tedteacher',
                                 firstname = 'Ted',
                                 lastname = 'Teacher',
                                 name = 'TedTeacher',
                                 email = 'ted@fake.address')
    tedt.set_password('test')
    democourse = Course.find_or_create(name = 'Demo Course',
                                       path = 'demo_course',
                                       start_date = '2013-01-01')
    db_session.commit()
    Registration.find_or_create(person_id = john.person_id,
                                course_id = democourse.course_id,
                                role_id = student.role_id,
                                date = '2013-01-02')
    Registration.find_or_create(person_id = jane.person_id,
                                course_id = democourse.course_id,
                                role_id = student.role_id,
                                date = '2013-01-03')
    Registration.find_or_create(person_id = tedt.person_id,
                                course_id = democourse.course_id,
                                role_id = faculty.role_id,
                                date = '2013-01-04')
    a1 = Assignment.find_or_create(course_id = democourse.course_id,
                                   nth = 1,
                                   name = 'week 1',
                                   uriname = 'week_1',
                                   due = '2013-01-20',
                                   blurb = 'Do chap 1 exercises 1 to 10.')
    a2 = Assignment.find_or_create(course_id = democourse.course_id,
                                   nth = 1,
                                   name = 'week 2',
                                   uriname = 'week_2',
                                   due = '2013-01-27',
                                   blurb = 'Write a four part fugue.')
    db_session.commit()
    Work.find_or_create(person_id = john.person_id,
                        assignment_id = a1.assignment_id,
                        submitted = '2013-01-20 18:19:20',
                        grade = 'B')
    Work.find_or_create(person_id = jane.person_id,
                        assignment_id = a1.assignment_id,
                        submitted = '2013-01-21 16:01:01',
                        grade = 'B-')
    db_session.commit()    

    
if __name__ == "__main__":
    import doctest
    doctest.testmod()

"""
 other testing from the console

 Check that directory courspaths are indeed unique and 
 are in their correct courses :
 >> pprint(sorted([(d.coursepath, d.course.name) for d in Directory.all()]))
 [(u'', u'Umber'),
  (u'admin', u'Umber'),
  (u'demo_course', u'Demo Course'),
  (u'demo_course/faculty', u'Demo Course'),
  (u'demo_course/media', u'Demo Course'),
  (u'demo_course/notes', u'Demo Course'),
  (u'demo_course/protected', u'Demo Course'),
  (u'demo_course/special', u'Demo Course'),
  (u'demo_course/students', u'Demo Course'),
  (u'demo_course/students/janedoe', u'Demo Course'),
  (u'demo_course/students/johnsmith', u'Demo Course'),
  (u'demo_course/wiki', u'Demo Course'),
  (u'testing', u'Umber')]

"""
