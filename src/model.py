# -- coding: utf-8 --
"""
 sqlalchemy database model for umber

  In sqlalchemy's view of the world, db_session holds 
  the local memory state of this thread's interaction with the database.
  Objects (e.g. a Person or Course, corresponding to a row in a sql table) 
  exist in both the session and the database. When the two are synchronized
  depends on the database settings and explicit transaction calls :

   autoflush  : do model changes get added to session automatically?
   autocommit : do model changes get written to database automatically?
   db_session.flush() outputs to database, but does not complete transaction.
   db_session.commit() completes an atomic transaction (calls .flush() too)

 The interface between the sqlite database and the object API is essentially

   sqlite -- engine -- db_session -- Umber
                                     [Person, Course, Assignment, ...]

 The find_or_create() methods from other relational database models
 (i.e. Rails ActiveRecord) corresponds roughly to the 'merge' concept 
 in sqlalchemy, which syncs a local session object with the database.
   jon = Person(name='Jon Smith')   # local, session object - not in db yet
   jon = db_session.merge(jon)      # sync session with db
 However, this approach assumes that the local jon was uniquely
 identified (including primary key) by its creation ... which is problematic.
 But probably a better approach is something like
   jon = Person.find_by('name', 'Jon Smith')     # find
   if not jon:      
       jon = Person(name = 'Jon Smith')           # or create
       db_session.add(jon)                             & put in session
   db_session.commit()                           # save (or  with flush())
 TODO: put some sort of cls.find_or_create into Umber() ?
 
 See ../database/ for the sqlite schemas and default population
 and planet_express/src/model.py for more examples of sqlalchemy syntax.
 """

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from settings import project_path

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
    # e.g. Person.name , since Person table has a 'name' column.
    __table_args__ = {'autoload':True, 'autoload_with': db_engine}

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
        # Returns None if not found. Throws an error if more than one result found.
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
    Base.__init__(self, *args, **kwargs)
    db_session.add(self)

class Person(Base):
    # columns: person_id, ldap_id, username, firstname, lastname, email,
    #          password, crypto, notes
    # relations: courses, works
    __init__ = umber_object_init
        
class Role(Base):
    # columns: role_id, name, rank
    __init__ = umber_object_init
                            
class Course(Base):
    # columns: course_id, name, name_as_title, directory, credits,
    #          start_date, end_date, assignments_md5, active, notes
    # relations: persons, assignments
    __init__ = umber_object_init
                                        
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

def db_populate():
    """ Create and save initial database objects """
    # The .find*(...) methods look for things in the database,
    # so they must already be committed. (And the *_id fields
    # don't have values until after the object is in the database.)
    # However, when accessing (or setting) related objects directly,
    # other objects may be used, e.g. "work1.person = john".
    for (what, digit) in (('admin', 5), 
                          ('administrator', 5),
                          ('faculty', 4),
                          ('students', 3), 
                          ('student', 3),
                          ('guests', 2), 
                          ('guest', 2),
                          ('anonymous', 1), 
                          ('all', 1)):
        Rank.find_or_create(name = what, rank = digit)
    db_session.commit()
    student = Role.find_by(name='student')   # Can only find after .commit().
    faculty = Role.find_by(name='faculty')    
    jane = Person.find_or_create(username = 'janedoe',
                                 password = 'test',
                                 firstname = 'Jane',
                                 lastname = 'Doe',
                                 name = 'Jane Q. Doe',
                                 email = 'janedoe@fake.address')
    john = Person.find_or_create(username = 'johnsmith',
                                 password = 'test',
                                 firstname = 'John',
                                 lastname = 'Smith',
                                 name = 'Johnny Smith',
                                 email = 'johnsmith@fake.address')
    tedt = Person.find_or_create(username = 'tedteacher',
                                 password = 'test',
                                 firstname = 'Ted',
                                 lastname = 'Teacher',
                                 name = 'TedTeacher',
                                 email = 'ted@fake.address')
    democourse = Course.find_or_create(name = 'Demo Course',
                                       directory = '/course_demo',
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
                        course_id = democourse.course_id,
                        assignment_id = a1.assignment_id,
                        submitted = '2006-01-20 18:34:57',
                        grade = 'ok')
    db_session.commit()    

# if __name__ == "__main__":
#     import doctest
#     doctest.testmod()

