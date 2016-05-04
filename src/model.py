# -- coding: utf-8 --
"""
 model.py
 
 sqlalchemy database model for umber

 --- examples / tests ---
 
 To initialize the database and run the tests from the command line,
 from the 'umber' folder.

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
 ...   print "{} is a {}.".format(users[x].name, roles[x])
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

 A raw SQL query for raw data looks like this, which returns a list of tuples.
 >>> db_session.execute(
 ...   'SELECT c.name, c.credits FROM Course AS c WHERE c.path=="demo";'
 ...   ).fetchall()
 [(u'Demo Course', 0)]
 
 Or sqlalchemy objects can be returned with a snippet of SQL which would go
 after WHERE in something like 'SELECT * FROM Course WHERE ...'
 In this example, the :p marker is replaced by the corresponding data
 from params(), the .one() method returns the first matching Course,
 and the .name extracts the course's name.
 >>> Course.filter('path==:p').params(p='demo').one().name
 u'Demo Course'

 The shorter way to do the same thing is just the following.
 But sometimes having access to the SQL itself is useful.
 >>> Course.find_by(path='demo').name
 u'Demo Course'

 >>> db_session.remove()       # close the session nicely.
 
 --- sqlalchemy ORM discussion and issues ---
 
 The documentation is at 
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
      >> jane = Person(name='Jane')   # create a sqlalchemy object
      >> db_session.add(jane)         # stick it in the current session
      >> db_session.commit()          # output it to the sql database
 
 However, I've set things up (see below) so that the second step
 happens automatically when an object is created.

      # my default 
      >> jane = Person(name='Jane')   # create object & add to db_session.new
      >> db_session.commit()          # output it to the sql database

 Another sqlalchemy "gotcha" is its find_by (and similar methods)
 behavior, which doesn't look in db_session, and only finds
 new objects after they're committed. That would suggest that
 find_by only looks in the sql database. However, it does return objects
 from db_session.dirty which have been pulled from the sql
 database and which contain uncommitted changes. This seems
 inconsistent to me.
 
      >> jane = Person(name='Jane')  # new person
      >> db_session.new              # not yet committed
      IdentitySet([<Person name='Jane' id=4408204944>])
      >> jane.username
      'jane'
      >> Person.find_all_by(username='jane')  # doesn't find jane
      []

      >> john = Person.find_by(username='johnsmith')
      >> john.name
      u'Johnny Smith'
      >> john.name = 'John New Smith'   # changed
      >> db_session.dirty               # not yet commited
      IdentitySet([<Person name='John New Name' ...>])
      >> Person.find_by(username='johnsmith').name
      'John New Name'                   # finds data not in database yet(!)

 I think what's going on is that sqlalchemy's IdentitySet
 is making sure that there aren't two johnsmith objects
 in db_session with the same id.

 I don't much like this behavior - it isn't what I expect -
 but haven't (yet) modified my sqlalchemy objects to look in
 db_session.new. Instead, I'll just committ early & often.
      
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

 --- database definition ---
 
 In this project, the database tables themselves and their schema
 are defined with SQL, in database/create_umber_db.sql. Then the
 parent Umber class automatically defines the methods and matching
 fields within each inherited Person, Course, etc object.
 
 Often this is done the other way around, with the database tables defined
 by the python classes, and the SQL generated automatically. That workflow
 is described at flask.pocoo.org/docs/patterns/sqlalchemy, where the model
 is something like
 
      class User(Base):
          __tablename__ = 'users'
          id = Column(Integer, primary_key=True)
          name = Column(Integer, unique=True)
          # and so on

 In that paradigm, the sqlite (or other) database itself would be
 created automatically with something like

       Base.metadata.create_all(bind=engine)

 But here I'm starting with the raw SQL table definitions,
 all of which are in the <os_base>/database/ folder
 
      CREATE TABLE Person (
          person_id INTEGER PRIMARY KEY NOT NULL,
          username TEXT UNIQUE NOT NULL,
          # and so on )
          
 Then in the code below, the sqlalchemy ORM classes 'autoload'
 the sqlite table definitions and generate object interfaces
 such as Person.username. This seems a better division of
 responsibility between the SQLite and SqlAlchemy worlds,
 allowing me to define a single base class for all my
 database ORM classes.

 --- other notes ---
 
 The Person and AnonymousPerson classes are consistent with
 Flask-Login's expectations; see its docss and umber.py.

 User authentication is handled with either
    * password hashes in the database
    * python-ldap to connect to the campus info   TODO
  
"""

import os
from random import randint
from flask import Markup
from sqlalchemy import create_engine, orm
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from werkzeug.security import generate_password_hash, check_password_hash
from settings import os_root, os_base, url_base, db_path  # ./settings.py

## If I decide to modify find_by and similar methods to
## return not-yet-committed objects in db_session.new, then
## I expect I'll need IdentitySet since that's what those
## methods return :
# from sqlalchemy.util import IdentitySet

db_engine = create_engine(db_path, convert_unicode = True)
db_session = scoped_session(sessionmaker(autocommit = False, 
                                         autoflush = False, 
                                         bind = db_engine))

# date used for objects like Course when none is specified.
default_date = '2001-01-01'

def month_to_semester(month):
    """ Convert two digit string month '01' to '12' to semester """
    if '01' <= month <= '04':
        return 'Spring'
    elif '05' <= month <= '08':
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

    ## SqlAlchemy does *not* call __init__ for its inherited objects,
    ## do don't put any initialization here. In other words,
    ## con't uncomment this __init__ because that won't work.
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
        """ Return a SqlAlchemy column object """
        # e.g. Person.col('name') is same as Person.name
        return cls.__dict__[column]

    # Now define shortcut methods for several database retrieval operations
    # using sqlalchemy's query, filter, like, one, all, e.g. Class.filter()
    # rather than the more verbose Class.query.filter()
    
    @classmethod
    def all(cls, *args, **kwargs):
        return cls.query.all(*args, **kwargs)
    
    @classmethod
    def filter(cls, *args, **kwargs):
        return cls.query.filter(*args, **kwargs)
    
    @classmethod
    def filter_like(cls, **kwargs):
        """ Return query made using SQL 'LIKE' matches in column=like_value """
        # e.g. query = Person.query_like(name = '%Fry%')
        q = cls.query
        for (column, like_value) in kwargs:
            q = q.filter(cls.col(column).like(like_value))
        return q
        
    @classmethod
    def filter_by(cls, **kwargs):
        """ Return query.filter_by(column=value, column=value, ...) """
        return cls.query.filter_by(**kwargs)
    
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
        if 'password' in kwargs:
            kwargs['password'] = generate_password_hash(kwargs['password'])
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
        """ Set nondatabase data """
        self.logged_in = logged_in
        self.role = role
    
def anonymous_person():
    anony = Person(name=u'anon', username=u'anon')
    db_session.expunge(anony)   # don't write this one to the database
    anony.set_status(logged_in=False)
    anony.anonymous = True
    return anony

rolename_map = {'admin':           'admin',
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
rolenames = set(rolename_map.keys())
    
def normalize_rolename(rolename):
    """ Return one of the 5 standard names in place of possible variations """
    return rolename_map[rolename]

Role_name_rank = {'admin':5, 'faculty':4, 'student':3, 'guest':2, 'visitor':1}

def rolename_rank(rolename):
    """ Return numeric value corresponding to rolename or variation.
        >>> rolename_rank('any')
        1
    """
    # For a given role which has access rights (i.e. student),
    # people whose role is that or higher (i.e. student, faculty, admin)
    # will be allowed access. (This behavior is implemented in page.py)
    return Role_name_rank.get(normalize_rolename(rolename))

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
    # relations: persons, assignments
    # derived: url, semester, os_fullpath, userdict, roledict, name_title
    def __init__(self, *args, **kwargs):
        # print "debug: Course.__init__ kwargs = {}".format(kwargs)
        kwargs['name'] = kwargs.get('name') or randstring('randcourse')
        kwargs['name_as_title'] = kwargs.get('name_as_title') or kwargs['name']
        if 'path' not in kwargs:   # Note : '' is a valid path ('Umber' course)
            kwargs['path'] = kwargs['name'].replace(' ', '_')
        kwargs['start_date'] = kwargs.get('start_date') or default_date
        umber_object_init(self, *args, **kwargs)
        self.init_derived()
    @orm.reconstructor
    def init_derived(self):
        self.url = self._url()
        self.name_title = Markup(self.name_as_title)
        self.semester = self._semester()
        self.os_fullpath = self._os_fullpath()
        self.userdict = self._userdict()
        self.roledict = self._roledict()
    def _semester(self):
        month = self.start_date[5:7]
        year = self.start_date[0:4]
        return month_to_semester(month) + ' ' + year
    def _url(self):
        if self.path == '':
            return '/'.join([url_base, 'home'])
        else:
            return '/'.join([url_base, self.path, 'home'])
        #url_path = '/' + self.path if self.path != '' else ''
        #return '/' + url_base + url_path + '/home'
    def _os_fullpath(self):
        if self.path == '':
            # skip self.path; else end up with trailing /
            os_base
        else:
            return os.path.join(os_base, self.path)
    def _userdict(self):
        """ Course.find_by(name=...).userdict[username] => user """
        return {p.username: p for p in self.persons}
    def _roledict(self):
        """ Course.find_by(name=...).roledict[username] => 'rolestring' """
        result = {}
        for p in self.persons:
            try:
                result[p.username] = \
                    Registration.find_by(course=self, person=p).role.name
            except:
                pass
        return result
    
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

Person.registrations = relationship(Registration)
Person.works = relationship(Work)
Person.courses = relationship(Course, viewonly = True,
                              secondary = Registration.__table__)

Course.assignments = relationship(Assignment)
Course.persons = relationship(Person, viewonly = True,
                              secondary = Registration.__table__)

Registration.person = relationship(Person)
Registration.course = relationship(Course)
Registration.role = relationship(Role)

Assignment.course = relationship(Course)

Work.person = relationship(Person)
Work.assignment = relationship(Assignment)

def populate_db():
    """ Create and commit the default database objects """
    #
    # This sets up
    #    * Roles
    #    * Course 'umber'
    #    * Course 'demo' and its sample Persons,
    #      Registrations, Assignments, and Works.
    #
    # The sqlite database must already exist before this is run.
    # Create it with database/init_db.
    #
    # populate_db() is mostly idempotent; that is, runing multiple times
    # is no different than running it once. The one thing that will
    # change is the random seeds for the demo course sample users.
    #
    # Although objects don't have *_id fields until after they've been
    # committed to the database, and it's those *_id fields that are used in
    # the relations between objects, SqlAlchemy will fill in the relations
    # properly if they're all committed at the end.
    #
    print " Populating database with default data."
    Role.init_database()
    student = Role.named('student')
    faculty = Role.named('faculty')    
    umbercourse = Course.find_or_create(name = 'Umber',
                                        path = '',
                                        start_date = default_date)
    democourse = Course.find_or_create(name = 'Demo Course',
                                       name_as_title = 'Demo<br>Course',
                                       path = 'demo',
                                       start_date = '2013-01-01')
    jane = Person.find_or_create(username = 'janedoe',
                                 name = 'Jane Q. Doe',
                                 email = 'janedoe@fake.address')
    john = Person.find_or_create(username = 'johnsmith',
                                 name = 'Johnny Smith',
                                 email = 'johnsmith@fake.address')
    ted  = Person.find_or_create(username = 'tedteacher',
                                 name = 'Ted Teacher',
                                 email = 'ted@fake.address')
    # The hashed seeded passwords are different each time,
    # so they shouldn't be put in args to find_or_create. Otherwise, the
    # new passwords won't be found and duplicate people would be created.
    jane.set_password('test')
    john.set_password('test')
    ted.set_password('test')
    Registration.find_or_create(person = john,
                                course = democourse,
                                role = student,
                                date = '2013-01-02')
    Registration.find_or_create(person = jane,
                                course = democourse,
                                role = student,
                                date = '2013-01-03')
    Registration.find_or_create(person = ted,
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

