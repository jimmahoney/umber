# -- coding: utf-8 --
"""
 sqlalchemy database model for umber

 --- examples / tests ---
 
 To initialize the database and run the tests from the command line :

   $ pwd
   .../umber
   $ . env/bin/activate
   (env)$ cd database; ./init_db; cd ..
   copying previous database to umber.db_old
   initializing umber.db
   (env)$ python src/model.py -v
   ...
   Test passed.

 The tests and manual database changes can also be run in the console;
 run ./console from the umber directory.
   
 >>> populate_db()
 Populating database with default Roles and test data.
 
 >>> john = Person.find_by(username = 'johnsmith')      # get table row
 >>> print john.name                                    # display column
 Johnny Smith
 >>> john.name = 'John Z. Smith'                        # modify column
 >>> db_session.flush()                                 # save changes
 
 >>> demo = Course.find_by(name = 'Demo Course')
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
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from settings import project_path
from werkzeug.security import generate_password_hash, check_password_hash

db_path = 'sqlite:///' + project_path + '/database/umber.db'
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
            return "<{} name='{}' id={}>".format(self.__class__.__name__,
                                                 self.name, id(self))
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
    #
    Base.__init__(self, *args, **kwargs)
    db_session.add(self)

class Person(Base):
    # columns: person_id, ldap_id, username, firstname, lastname, email,
    #          password, crypto, notes
    # relations: courses, works
    # implements Flask-Login's 'User Class' 
    #   with is_authenticated(), is_active(), is_anonymous(), get_id()
    # password scheme from http://flask.pocoo.org/snippets/54/
    def __init__(self, *args, **kwargs):
        umber_object_init(self, *args, **kwargs)
        self.logged_in = False
    def is_authenticated(self):           # for Flask-Login
        self.logged_in = True
    def is_active(self):                  # for Flask-Login
        return self.is_authenticated():     
    def is_anonymous(self):               # for Flask-Login
        return self.__class__.__name__ == 'AnonymousPerson'
    def get_id(self):                     # for Flask-Login; stored in session
        return unicode(self.username)
    def set_password(self, passwordtext):
        self.password = generate_password_hash(passwordtext)
        db_session.commit()
    def check_password(self, passwordtext):
        return check_password_hash(self.password, passwordtext)
        

class AnonymousPerson(Person):
    pass

class Role(Base):
    # columns: role_id, name, rank
    __init__ = umber_object_init
                            
class Course(Base):
    # columns: course_id, name, name_as_title, directory, credits,
    #          start_date, end_date, assignments_md5, active, notes
    # relations: persons, assignments
    __init__ = umber_object_init
    def uri(self):
        return ' URI '
                                        
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

Person.courses = relationship(Course, viewonly = True,
                              secondary = Registration.__table__)
Person.works = relationship(Work)

Course.persons = relationship(Person, viewonly = True,
                              secondary = Registration.__table__)
Course.assignments = relationship(Assignment)

Registration.person = relationship(Person)
Registration.course = relationship(Course)
Registration.role = relationship(Role)

Assignment.course = relationship(Course)

Work.person = relationship(Person)
Work.assignment = relationship(Assignment)

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
    print "Populating database with default Roles and test data."
    for (what, digit) in (('admin', 5), 
                          ('administrator', 5),
                          ('faculty', 4),
                          ('students', 3), 
                          ('student', 3),
                          ('guests', 2), 
                          ('guest', 2),
                          ('anonymous', 1), 
                          ('all', 1)):
        Role.find_or_create(name = what, rank = digit)
    db_session.commit()
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
                                       directory = '/demo_course',
                                       start_date = '2006-01-01')
    db_session.commit()
    Registration.find_or_create(person_id = john.person_id,
                                course_id = democourse.course_id,
                                role_id = student.role_id,
                                date = '2006-01-02')
    Registration.find_or_create(person_id = jane.person_id,
                                course_id = democourse.course_id,
                                role_id = student.role_id,
                                date = '2006-01-03')
    Registration.find_or_create(person_id = tedt.person_id,
                                course_id = democourse.course_id,
                                role_id = faculty.role_id,
                                date = '2006-01-04')
    a1 = Assignment.find_or_create(course_id = democourse.course_id,
                                   nth = 1,
                                   name = 'week 1',
                                   uriname = 'week_1',
                                   due = '2006-01-20',
                                   blurb = 'Do chap 1 exercises 1 to 10.')
    a2 = Assignment.find_or_create(course_id = democourse.course_id,
                                   nth = 1,
                                   name = 'week 2',
                                   uriname = 'week_2',
                                   due = '2006-01-27',
                                   blurb = 'Write a four part fugue.')
    db_session.commit()
    Work.find_or_create(person_id = john.person_id,
                        assignment_id = a1.assignment_id,
                        submitted = '2006-01-20 18:19:20',
                        grade = 'B')
    Work.find_or_create(person_id = jane.person_id,
                        assignment_id = a1.assignment_id,
                        submitted = '2006-01-21 16:01:01',
                        grade = 'B-')
    db_session.commit()    


if __name__ == "__main__":
    import doctest
    doctest.testmod()

"""
-- initialize database & run tests --
    
thirty-two:~$ cd academics/umber/
Trying:
    populate_db()
Expecting:
    Populating database with default Roles and test data.
ok
Trying:
    john = Person.find_by(username = 'johnsmith')      # get table row
Expecting nothing
ok
Trying:
    print john.name                                    # display column
Expecting:
    Johnny Smith
ok
Trying:
    john.name = 'John Z. Smith'                        # modify column
Expecting nothing
ok
Trying:
    db_session.flush()                                 # save changes
Expecting nothing
ok
Trying:
    demo = Course.find_by(name = 'Demo Course')
Expecting nothing
ok
Trying:
    demo.name = 'Demo Course - new name'
Expecting nothing
ok
Trying:
    db_session.flush()
Expecting nothing
ok
Trying:
    Course.find_all_by(name = 'Demo Course')           # Now can't find it.
Expecting:
    []
ok
Trying:
    print john.courses[0].name
Expecting:
    Demo Course - new name
ok
Trying:
    print Registration.find_by(person = john, course = demo).role.name
Expecting:
    student
ok
Trying:
    db_session.rollback()     # Undo these uncommited database modifications,
Expecting nothing
ok
Trying:
    db_session.remove()       # and close the session nicely.
Expecting nothing
ok
20 items had no tests:
    __main__.Assignment
    __main__.Course
    __main__.Person
    __main__.Registration
    __main__.Role
    __main__.Umber
    __main__.Umber.__repr__
    __main__.Umber.all
    __main__.Umber.col
    __main__.Umber.filter
    __main__.Umber.filter_by
    __main__.Umber.filter_like
    __main__.Umber.find_all_by
    __main__.Umber.find_all_like
    __main__.Umber.find_by
    __main__.Umber.find_like
    __main__.Umber.find_or_create
    __main__.Work
    __main__.populate_db
    __main__.umber_object_init
1 items passed all tests:
  13 tests in __main__
13 tests in 21 items.
13 passed and 0 failed.

(env)thirty-two:umber$ 

"""
