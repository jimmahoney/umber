# -- coding: utf-8 --
"""
 sqlalchemy database model for umber

 --- examples / tests ---
 
 To initialize the database and run the tests from the command line,
 from the 'umber' directory.

   $ . env/bin/activate           # turn on virtualenv paths for this project
   (env)$ reset_db                # create database & populate with defaults
   (env)$ python src/model.py -v  # run these model tests
   ...
   Test passed.

 These tests (and any other adhoc database changes)
 can of course also be run directly from the console
 via "./console" from the umber directory.
   
 >>> populate_db()
  Populating database with default data.

 >>> demo = Course.find_by(name='Demo Course')
 >>> print demo.name
 Demo Course

 >>> usernames = sorted(demo.userdict.keys())
 >>> users = demo.userdict
 >>> roles = demo.roledict
 >>> for x in usernames:
 ...   print "{} is a {}.".format(users[x].name, roles[x].name)
 Jane Q. Doe is a student.
 Johnny Smith is a student.
 Ted Teacher is a faculty.

 Fetch a row from the Person database table. (Several tests below use this.)
 >>> john = Person.find_by(username='johnsmith')

 >>> print john.name                           # value of column from instance
 Johnny Smith
 >>> john.name = 'John Z. Smith'               # modify column
 >>> db_session.flush()                        # save changes to database
 
 >>> demo.name = 'Demo Course - new name'
 >>> db_session.flush()
 >>> Course.find_all_by(name = 'Demo Course')  # ... and now it isn't there.
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
 >>> print Registration.find_by(person=john, course=demo).role.name
 student
 
 >>> db_session.rollback()     # Undo these uncommited database modifications,
  
 >> dirs = {x : Directory.find_by(name=x, course=demo) 
 ...             for x in ('', 'protected', 'johnsmith')}
 >> for who in usernames:
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

 >> for path in ('demo/students/johnsmith/foo', 
 ...              'demo/syllabus', 
 ...              'demo/protected',  
 ...              'one/two/three'):
 ...   p = Page(pagepath=path, user=john)
 ...   print "--- pagepath = {}".format(p.pagepath)
 ...   print "    name = '{}'".format(p.name)
 ...   print "    is_directory = {}".format(p.is_directory)
 ...   ## (os_fullpath is installation folder dependendet; not a good test.)
 ...   # print "    os_fullpath = '{}'".format(p.os_fullpath()) 
 ...   print "    can_read, can_write = {}, {}".format(p.can_read, p.can_write)
 ...   print "    course '{}' path='{}'".format(p.course.name, p.course.path)
 ...   print "    directory path='{}'".format(p.directory.path)
 --- pagepath = demo/students/johnsmith/foo
     name = 'foo'
     is_directory = False
     can_read, can_write = True, True
     course 'Demo Course' path='demo'
     directory path='students/johnsmith'
 --- pagepath = demo/syllabus
     name = 'syllabus'
     is_directory = False
     can_read, can_write = True, False
     course 'Demo Course' path='demo'
     directory path=''
 --- pagepath = demo/protected
     name = 'protected'
     is_directory = True
     can_read, can_write = True, False
     course 'Demo Course' path='demo'
     directory path='protected'
 --- pagepath = one/two/three
     name = 'three'
     is_directory = False
     can_read, can_write = True, False
     course 'Umber' path=''
     directory path=''

 Check to see that work.course (derived from work.assignment.course) is OK,
 and that finding instances from other instances behaves as expected.
 >>> Work.find_by(person=john).course.name
 u'Demo Course'
 
 >> (dirs['johnsmith'].name == 'johnsmith', 
 ...  dirs['johnsmith'].path == 'students/johnsmith',
 ...  dirs['johnsmith'].pathincourse == 'demo/students/johnsmith')
 (True, True, True)


 --- test deletion of Permission when Directory is deleted.
     (This fake Directory doesn't correspond to an actual disk folder.)
 >>> permission_count = len(Permission.all())
 >>> fakefolder = Directory(name='fakefolder', course=demo)
 >>> fakefolder.set_permissions(readers=['student'])
 >>> db_session.commit()
 >>> len(Permission.all()) == permission_count + 1 # added one permission
 True
 >>> Directory.delete(fakefolder)
 >>> db_session.commit()
 >>> len(Permission.all()) == permission_count     # ... which is now gone.
 True

 
 >>> db_session.remove()       # close the session nicely.
 
 --- discussion ---
 
 Here are a few of the concepts behind all this.

 For more details, see e.g.
   http://flask.pocoo.org/docs/patterns/sqlalchemy/ ,
   http://docs.sqlalchemy.org/en/rel_0_7/orm/query.html ,
   and the other reams of stuff at docs.sqlalchemy.org
 
 In sqlalchemy's view of the world, db_session holds the local
 memory state of this thread's interaction with the database.
 Objects (e.g. a Person or Course, an instance of which corresponds
 to a row in a sql table) exist in both the session and the
 database. 

 The picture looks something like this.

      sqlite -- engine --   db_session -- Umber objects
      data      software    memory        memory instances of rows
      file      connection  state         e.g. Person, Course, ...

 SqlAlchemy is more explicit than some ORM systems in distinguishing
 between the data memory (in db_session) vs what's in the sql disk file.
 Check out db_session.new and db_session.dirty to see some of this.

 The expected workflow in SqlAlchemy to create a new row and
 put it into the sql database looks like this.

      # SqlAlchemy default
      jane = Person(name='Jane')      # create a python object
      db_session.add(jane)            # stick it in the current session
      db_session.commit()             # output it to the sql database
 
 However, I've set things up (see below) so that the second step
 happens automatically when an object is created.

      # my default 
      jane = Person(name='Jane')      # create python object & add to db_session
      db_session.commit()             # output it to the sql database

 This still leaves open possible confusion between what's in
 db_session vs what's in the sql database. I've found this to
 be particularly true for SqlAlchemy's .find*() methods,
 which look only in the database, not in db_session.
 For example, this code fails

      jane = Person(name='Jane')
      ...
      who = Person.find_by(name='Jane')   # Fails!
 
 because jane is not yet in the sql database when the .find_by is called.
 This, on the other hand, works fine.

      jane = Person(name='Jane')
      db_session.commit()
      ...
      who = Person.find_by(name='Jane')   # Succeeds!

 I considered overriding SqlAlchemy's find_by (at least) method to
 look in db_session and avoid this issue but decided that was overkill.
      
 I've also been confused by SqlAlchemy's notion of "reconstruction":
 objects which are pulled from the database don't have their __init__
 methods invoked. See the orm.reconstructor notes and workarounds below.
    
 Modifications to the objects can be sent to the database
 using one of several db_session methods :
    * flush      which continues the current transaction
    * commit     which finishes this transaction.
 Related db_session methods include
    * begin      start a transaction (implied; not needed explicitly)
    * rollback   undo everything back to the last commit
 The flush or commit operations can be set to happen automatically
 whenever an instance is modified. I've turned that off.
 (See the creation of db_session below.)

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

 IN PROGRESS    

 Check that directories are unique and are in their correct courses :
 >> pprint(sorted([(d.path, d.name, d.course.name) for d in Directory.all()]))

  
"""

from sqlalchemy import create_engine, orm
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from settings import os_root, courses_os_base, courses_url_base
from werkzeug.security import generate_password_hash, check_password_hash
from random import randint
import os

db_path = 'sqlite:///' + os_root + '/database/umber.db'
db_engine = create_engine(db_path, convert_unicode = True)
db_session = scoped_session(sessionmaker(autocommit = False, 
                                         autoflush = False, 
                                         bind = db_engine))

default_date = '2001-01-01'

def month_to_semester(month):
    """ Convert two digit string month '01' to '12' to semester """
    if month in ('01', '02', '03', '04'):
        return 'Spring'
    elif month in ('05', '06', '07', '08'):
        return 'Summer'
    else:
        return 'Fall'

def randstring(base='', digits=3):
    """ Return a string with some random digits at the end
        >>> x = randstring('foo')           # e.g. 'foo326'
        >>> len(x) == 6 and x[0:3] == 'foo'
        True
    """
    (low, high) = (10**(digits-1), 10**digits - 1)
    return base + str(randint(low, high))

class Umber(object):
    """ All of this project's database objects inherit from this class. """

    ## SqlAlchemy does *not* call this __init__ for its inherited objects,
    ## do don't put any initialization here. 
    # def __init__(self):
    #    print "in Umber.init id={}".format(id(self))
    
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

def umber_object_init(self, *args, **kwargs):
    #
    # This workaround defines a method which can be be used as (or in)
    # the __init__ method for all the database classes. It will be
    # called when a new instance is created (i.e. jim=Person(username='jim'))
    # and will automatically add that instance to db_seesion. 
    #
    # Putting a default __init__ method in the Umber class or
    # in the Base class is not supported by sqlalchemy, which bypasses both.
    #
    # Moreover, a class's __init__ methods aren't called at all when
    # instances are "reconstructed" (sqlalchemy's term) by reading
    # them in from the database with e.g. Course.all() or
    # Person.find_by_name(username='johnsmith').  Instead sqlalchemy
    # supplies an 'orm.reconstructor' decorator to mark methods to be
    # called when the object is read in.
    # (These 'reconstructed' instances are automatically in db_session.
    # See db_session.new and db_session.dirty for lists of instances
    # that have been created but not yet inserted into the database,
    # and instances which have been modified but not yet updated in the db.
    # And try list(db_session) for the loaded objects.)
    #
    # The discussions at 
    # http://stackoverflow.com/questions/16156650/sqlalchemy-init-not-runnning
    # and  http://docs.sqlalchemy.org/en/rel_0_8/orm/
    #      mapper_config.html#constructors-and-object-initialization
    # have some related information.
    # 
    # The sqlalchemy philosophy apparently wants to separate db_session
    # from the model, which is why, I think, they expect an 
    # explicit db_session.add() after each object instantiation. 
    # But I'm unconvinced, and want each new object automatically added
    # to db_session. (Note that db_session.flush() or .commit() is 
    # still required after creating an object before the database is modified.)
    # db_session.expunge(obj) can undo the .add() before a .commit().
    #
    Base.__init__(self, *args, **kwargs)
    db_session.add(self)
    ## debugging :
    # print "in umber_object_init id={}".format(id(self))

# OK, now we're ready to define object class for each database table.
#
#  * instance interfaces for the table columns are created automatically,
#    for example
#       Person.find_by(username='johnsmith').name
#    is 'John Smith'.
#    The database columns may be modified by changing these values
#    and then flushing or committing the changes to the database, i.e.
#      Person.find_by(username='johnsmith').name = 'Fred Smith'
#      db_session.flush()
#
#  * Relation interfaces for objects corresponding to foreign keys (e.g.
#    many-to-one relations) are defined below, after the class definitions ;
#    See docs.sqlalchemy.org/en/rel_0_7/orm/extensions/declarative.html .
#    Thus for example
#      Person.find_by(username='johnsmith').courses
#    is a collection (effectively a list) of all Course instances that have
#    a person_id field that matches 'johnsmith' database entry.
#
#  * The many-to-many relations defined through an intermediate table are
#    not to be used for editing; see 'viewonly' in declarative.html:
#      "not a good idea to use [..] “secondary” arg [..] mapped
#      to a class unless the relationship is declared with viewonly=True
#      Otherwise [..] may attempt duplicate INSERT and DELETE"
#    An example would be
#      Person.find_by(username='johnsmith').courses
#    which gives a list of all courses that johnsmith is in.
#    This can be used to find those courses; however, modifying which
#    courses he's in by changing this list is not supported.

class Person(Base):
    # columns: person_id, ldap_id, username, firstname, lastname, email,
    #          password, crypto, notes
    # relations: courses, works, registrations
    # implements Flask-Login's 'User Class' 
    #   with is_authenticated(), is_active(), is_anonymous(), get_id()
    # password scheme from http://flask.pocoo.org/snippets/54/
    def __init__(self, *args, **kwargs):
        if 'name' in kwargs and 'username' not in kwargs:
            kwargs['username'] = kwargs['name'].lower().replace(' ', '_')
        kwargs['username'] = kwargs.get('username') or randstring('randperson')
        kwargs['name'] = kwargs.get('name') or kwargs['username']
        umber_object_init(self, *args, **kwargs)
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
    db_session.expunge(anony)   # don't write this one to the database
    anony.set_status(logged_in=False, role='any')
    anony.anonymous = True
    return anony

Role_name_rank = {'admin':5, 'faculty':4, 'student':3, 'guest':2, 'all':1}
class Role(Base):
    # columns: role_id, name, rank
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
    # relations: persons, assignments, directories
    # derived: url, semester, os_fullpath, folder (top folder)
    def __init__(self, *args, **kwargs):
        # print "debug: Course.__init__ kwargs = {}".format(kwargs)
        kwargs['name'] = kwargs.get('name') or randstring('randcourse')
        kwargs['name_as_title'] = kwargs.get('name_as_title') or kwargs['name']
        if 'path' not in kwargs:   # Note : '' is a valid path ('Umber' course)
            kwargs['path'] = kwargs['name'].replace(' ', '_')
        kwargs['start_date'] = kwargs.get('start_date') or default_date
        umber_object_init(self, *args, **kwargs)
        self.init_folder()
        self.init_derived()
    @orm.reconstructor
    def init_derived(self):
        self.url = self._url()
        self.semester = self._semester()
        self.os_fullpath = self._os_fullpath()
        self.userdict = self._userdict()
        self.roledict = self._roledict()
        try:
            self.folder
        except AttributeError:
            self.folder = Directory.find_by(path=self.path)
    def _semester(self):
        month = self.start_date[5:7]
        year = self.start_date[0:4]
        return month_to_semester(month) + ' ' + year
    def _url(self):
        if self.path == '':
            return '/'.join([courses_url_base, 'home'])
        else:
            return '/'.join([courses_url_base, self.path, 'home'])
        #url_path = '/' + self.path if self.path != '' else ''
        #return '/' + courses_url_base + url_path + '/home'
    def _os_fullpath(self):
        if self.path == '':
            # skip self.path; else end up with trailing /
            return os.path.join(os_root, courses_os_base)
        else:
            return os.path.join(os_root, courses_os_base, self.path)
    def init_folder(self):
        """ initialize top folder database Directory object """
        # This will show up in self.directories after commit
        self.folder = Directory(name='', course=self)
        self.folder.set_permissions()

    #    """ Remove any old database directory objects and their permissions.
    #        Then create database directories and deafult permissions
    #        all folders in this course's file tree."""
    #    # print "-- init_directories( course.name='{}')".format(self.name)
    #    # print "  os_root = ", os_root
    #    # print "  courses_os_base   = ", courses_os_base
    #    # print "  course_os_fullpath  = ", self.os_fullpath()
    #    # for dir_os_fullpath, dirnames, filenames in os.walk(self.os_fullpath()):
    #    #     print "  ", dir_os_fullpath
    #
    #    ### GETTING ERRORS - I think I'm trying to delete 
    #    ### a directory without deleting its permission first.
    #    ### Perhaps set up a cascade delete ??
    #    for dir in self.directories:
    #        Directory.delete(dir)
    #        #db_session.execute('delete from Permission where directory_id=:id;',
    #        #                   {'id': dir.directory_id})
    #        #db_session.delete(dir)
    #    # There should always be a root os folder at self.os_fullpath()
    #    #try:
    #    #    db_session.delete(Directory.find_by(pathincourse=self.path))
    #    #    db_session.commit()
    #    #except:
    #    #    pass
    #    Directory.delete_pathincourse(self.path)
    #    root_dir = Directory(name='', path='', pathincourse=self.path, course=self)
    #    root_dir.set_permissions()
    #    db_session.commit()

    def _userdict(self):
        """ Course.find_by(name=...).userdict[username] => user """
        return {p.username: p for p in self.persons}
    def _roledict(self):
        """ Course.find_by(name=...).roledict[username] => role """
        result = {}
        for p in self.persons:
            try:
                result[p.username] = \
                    Registration.find_by(course=self, person=p).role
            except:
                pass
        return result
    #
    #def by_role(self, role):
    #    if isinstance(role, str):
    #        role = Role.named(role)
    #    return Person.filter_by(course=self).filter_by(role=role).all()
    #def students(self):
    #    return self.by_role('student')
    #
    #@classmethod
    #def init_demo(cls):
    #    demo = Course.find_by(name='Demo Course')
    #    print " Initializing directories and permissions for demo course."
    #    #demo.init_directories()
    
class Registration(Base):
    # columns: registration_id, person_id, course_id, role_id,
    #          date, midterm, grade, credits, status
    # relations: person, course, role
    #
    __init__ = umber_object_init

class Assignment(Base):
    # columns: assignment_id, course_id, name, uriname, due, nth,
    #          blurb, active, notes
    # relations: course
    #
    __init__ = umber_object_init
    
class Work(Base):
    # columns: work_id, person_id, assignment_id, submitted, 
    #          studentLastSeen, studentLastModified,
    #          facultyLastSeen, facultyLastModified,
    #          grade, notes
    # relations: person, assignment
    # derived: course
    #
    def __init__(self, *args, **kwargs):
        umber_object_init(self, *args, **kwargs)
        self.init_derived()
    @orm.reconstructor
    def init_derived(self):
        self.course = self.assignment.course

class Directory(Base):
    # columns: directory_id, course_id, path, parent_id
    # relations: course, parent, children, permissions
    # derived: name (folder path relative to course top folder), os_fullpath
    #          basename (last folder in name, like os.path.basename)
    #
    # The folder's location within courses_os_base folder is its 'path'.
    # (Each course has the same notion of 'path', under courses_os_base.)
    # This implies that
    #    * the top-level default course has path=='', e.g. /.../umber/courses
    #    * the absolute location of other directories is 
    #      os.path.join(os_root, courses_os_base, path)
    #      e.g. /.../umber/courses/a/b when path=='a/b'
    #    * the folder's 'name' (its relative path within the course)
    #      is os.path.relpath(course.path, path)
    #    * the top folder for a course has directory.path==course.path

    # from http://docs.sqlalchemy.org/en/doc_nav/orm/mapper_config.html
    # and warning generated when deleting a folder.
    __mapper_args__ = { 'confirm_deleted_rows' : False }
    
    no_access = 0
    read_access = 1
    write_access = 3
    # The following are in addition to the built-in
    # admin-write-everywhere, faculty-write-course.
    rights_defaults = {'':         { 'read': ['all'],   'write' : []},
                       'admin':    { 'read': [],        'write' : []},                 
                       'faculty':  { 'read': [],        'write' : []},
                       'private':  { 'read': [],        'write' : []},                 
                       'protected':{ 'read': ['guest'], 'write' : []},
                       'students': { 'read': [],        'write' : []},
                       'wiki':     { 'read': ['all'],   'write' : ['guest']},
                      }
    
    def __init__(self, *args, **kwargs):
        if 'course' in kwargs and 'name' in kwargs:
            kwargs['path'] = os.path.join(kwargs['course'].path,
                                          kwargs['name'])
            del kwargs['name']
        if 'path' in kwargs and len(kwargs['path']) > 0 \
          and kwargs['path'][-1] == '/':
            kwargs['path'] = kwargs['path'][:-1]
        # print "Directory.__init__ kwargs={}".format(kwargs)
        umber_object_init(self, *args, **kwargs)
        self.init_derived()
    @orm.reconstructor
    def init_derived(self):
        # print " Directory.init_derived self.path={} self.course={}".format(
        #    self.path, self.course)
        self.name = self._name()
        self.basename = os.path.basename(self.name)
        self.os_fullpath = self._os_fullpath()
    def _name(self):
        if self.path != '':
            name = os.path.relpath(self.path, self.course.path)
        else:
            name = self.path
        if name == '.':
            name = ''
        return name
    def _os_fullpath(self):
        if self.path == '':
            fullpath = os.path.join(os_root, courses_os_base)
        else:
            fullpath = os.path.join(os_root, courses_os_base, self.path)
        if fullpath[-1] == '/':
            return fullpath[:-1]
        else:
            return fullpath

    @classmethod
    def delete_pathincourse(cls, pathincourse):
        try:
            dir = Directory.find_by(pathincourse=pathincourse)
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

    def set_permissions(self, course_defaults=True, readers=(), writers=()):
        """ Setup Permission database entries for this directory.
            defaults = True  =>  set readers() and writers() based
                                 on standard course folder names
                                 instead of readers() and writers()
                                 (e.g. protected, students, johnsmith, ...)
            recur = True     =>  recursively setup child directories
            readers, writers =>  list of username and role names
        """
        if course_defaults:
            if self.name in Directory.rights_defaults:
                readers = Directory.rights_defaults[self.name]['read']
                writers = Directory.rights_defaults[self.name]['write']
            elif os.path.dirname(self.name) == 'students' and \
              self.basename in self.course.userdict:
                readers = ()
                writers = (users[self.name], )
            else:
                pass   # if no name match, use given readers and writers
        # delete old permissions
        db_session.execute('delete from Permission where directory_id=:id;',
                           {'id': self.directory_id})
        for who in writers:
            self.set_1_permission(who, rights = Directory.write_access)
        for who in (set(readers) - set(writers)):
            self.set_1_permission(who, rights = Directory.read_access)
        #db_session.commit()
        #for sub in os.walk(self.os_fullpath):
        #    subdir_fullpath = sub[0]
        #    subpath = os.path.join(self.path, subname)
        #    subpathincourse = os.path.join(self.course.path, subpath)
        #    #try:
        #    #    db_session.delete(Directory.find_by(pathincourse=subpathincourse))
        #    #    db_session.commit()
        #    #except:
        #    #    pass
        #    Directory.delete_pathincourse(subpathincourse)
        #    sub = Directory(course=self.course, 
        #            name=subname, path=subpath, pathincourse=subpathincourse)
        #    sub.set_permissions(course_defaults, recur, readers, writers)
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
# http://docs.sqlalchemy.org/en/rel_0_9/orm/collections.html#passive-deletes ;
# http://www.sqlite.org/foreignkeys.html#fk_actions
# umber_db.sql has matching Permission( ... directory_id ON DELETE CASCADE) .
Directory.permissions = relationship(Permission, cascade="all, delete-orphan",
                                     passive_deletes=True)

Permission.role = relationship(Role)
Permission.person = relationship(Person)
Permission.directory = relationship(Directory)

class Page(object):
    """ a url-accessable file in a Course """
    #
    # Page objects (corresponding to files) are *not* in the sql database
    # and therefore don't inherit from the sqlalchemy Base class.
    # A Page object exists during the lifetime of a URL request
    # to manage access to the corresponding disk file and its content.
    #
    # Directories (corresponding to folders) are in the sql database,
    # so that (a) the enclosing Course can be found quickly and
    # (b) they can be given permissions.
    #
    # Work objects, representing a student's response to an
    # Assignment (and which does match a file) are also in the sql database.
    #
    # TODO (maybe) : the conversion of markdown or wiki files to html
    # could be cached in sql database Page objects. If so, a hash
    # would be needed to keep track of whether the file had changed
    # since the sql data had been cached. That could speed things up
    # (assuming the hash computation is faster than the markdown conversion)
    # at the cost of database size and code complexity.
    #
    def __str__(self):
        return "<Page pagepath='{}' id={}>".format(self.pagepath, id(self))
    def os_fullpath(self):
        if self.pagepath == '':
            # skip self.path; else end up with trailing /
            return os.path.join(os_root, courses_os_base)
        else:
            return os.path.join(os_root, courses_os_base, self.pagepath)
    def find_directory(self, pagepath):
        """ Find the directory in the database for this pagepath """
        # pagepath is e.g. one/two/three  (no leading or trailing slash)
        # This recursive procedure will try to find successively
        #    'one/two/three', 'one/two', 'one', ''
        # as a Directory's (unique) pathincourse. 
        # Since the 'Umber' course has pathincourse '', 
        # this should always terminate there if not before.
        #    os.path.split('/one/two/three')  => ('/one/two', 'three')
        #    os.path.join(a, b)                   dirname     basename
        #    os.path.isdir(path)
        #    os.path.isfile(path)
        #    os.path.abspath(path)          normalized absolute path
        #    os.path.relpath(path, [start]) default is relative to os.curdir  
        #    os.chdir(path)        Note that on unix, os.curdir = '.'
        #    os.getcwd()
        #    os.curdir, os.pardir    ('.', '..') on unix
        # TODO : put missing directories into the database?
        try:
            return Directory.find_by(pathincourse = pagepath)
        except:
            return self.find_directory(os.path.dirname(pagepath))
    def __init__(self, 
                 pagepath=None, # string from URL host/page_url_base/pagepath
                 request=None,  # Flask request object
                 user=None,     # Person
                 allow_insecure_login = False
                 ):
        if not user:
            user = anonymous_person()
        self.user = user
        self.pagepath = pagepath
        self.directory = self.find_directory(self.pagepath)
        self.name = os.path.basename(self.pagepath)
        self.is_directory = self.os_fullpath() == self.directory.os_fullpath()
        self.course = self.directory.course
        self.title = self.course.name + " - " + self.name
        try:
            self.role = Registration.find_by(course=self.course, 
                                             person=self.user).role
        except:
            self.role = Role.named('all')
        self.can_write = self.directory.can_write(self.user, self.role)
        self.can_read = self.directory.can_read(self.user, self.role)
        if request:
            self.request = request
            self.secure_url = 'https://' + request.host + request.path
            self.url = 'http://' + request.host + request.path            
            # self.path = request.path
            # self.full_path = request.full_path
        else: # debugging only
            self.request = None
            self.secure_url = ''
            self.url = ''
            # self.path = pagepath
            # self.full_path = pagepath
        self.allow_insecure_login = allow_insecure_login # require https login?
        if allow_insecure_login:
            self.secure_url = self.url   # e.g. debugging without https
        #
        self.uri_links = '- uri_links -'
        self.has_error = False
        self.has_lastmodified = True
        self.lastmodified = ' - MODIFIED DATE -'  # TODO : what should this be?

def populate_db():
    """ Create and commit the default database objects """
    # i.e. Roles, the 'umber' course and its root Directory,
    # and the 'demo' course along with its sample Persons,
    # Registrations, Assignments, and Works.
    #
    # The sqlite database must already exist before this is run;
    # to create it, run database/init_db.
    #
    # populate_db() is idempotent; that is, runing multiple times
    # is no different than running it once.
    #
    # Although objects don't *_id fields until after they've been committed
    # to the database, and it's those *_id fields that are used in
    # the relations between objects, SqlAlchemy will fill in the relations
    # properly if they're all committed at the end.
    #
    print " Populating database with default data."
    Role.init_database()

    umbercourse = Course.find_or_create(name = 'Umber',
                                        path = '',
                                        start_date = default_date)
    student = Role.named('student')
    faculty = Role.named('faculty')    
    jane = Person.find_or_create(username = 'janedoe',
                                 name = 'Jane Q. Doe',
                                 email = 'janedoe@fake.address')
    jane.set_password('test')
    john = Person.find_or_create(username = 'johnsmith',
                                 name = 'Johnny Smith',
                                 email = 'johnsmith@fake.address')
    john.set_password('test')
    tedt = Person.find_or_create(username = 'tedteacher',
                                 name = 'Ted Teacher',
                                 email = 'ted@fake.address')
    tedt.set_password('test')
    democourse = Course.find_or_create(name = 'Demo Course',
                                       name_as_title = 'Demo<br>Course',
                                       path = 'demo',
                                       start_date = '2013-01-01')
    Registration.find_or_create(person = john,
                                course = democourse,
                                role = student,
                                date = '2013-01-02')
    Registration.find_or_create(person = jane,
                                course = democourse,
                                role = student,
                                date = '2013-01-03')
    Registration.find_or_create(person = tedt,
                                course = democourse,
                                role = faculty,
                                date = '2013-01-04')
    a1 = Assignment.find_or_create(course = democourse,
                                   nth = 1,
                                   name = 'week 1',
                                   uriname = 'week_1',
                                   due = '2013-01-20',
                                   blurb = 'Do chap 1 exercises 1 to 10.')
    a2 = Assignment.find_or_create(course = democourse,
                                   nth = 1,
                                   name = 'week 2',
                                   uriname = 'week_2',
                                   due = '2013-01-27',
                                   blurb = 'Write a four part fugue.')
    Work.find_or_create(person = john,
                        assignment = a1,
                        submitted = '2013-01-20 18:19:20',
                        grade = 'B')
    Work.find_or_create(person = jane,
                        assignment = a1,
                        submitted = '2013-01-21 16:01:01',
                        grade = 'B-')
    db_session.commit()
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()

