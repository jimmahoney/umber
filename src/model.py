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
from utilities import project_path

DATABASE_PATH = 'sqlite:///' + project_path + '/database/umber.db'

engine = create_engine(DATABASE_PATH)
db_session = scoped_session(sessionmaker(autocommit = False, 
                                         autoflushf = False, 
                                         bind = engine))

class Umber(object):
    """ All of this project's database objects inherit from this class. """

    def __init__(self):
        """ Always add a new object to the current database session. """
        db_session.add(self)

    @declared_attr
    def __tablename__(cls):
        """ Set name of database table from class name """
        # e.g. "class Person" corresponds to SQL table 'Person'
        return cls.__name__

    # Define fields in each table for each column automatically,
    # e.g. Person.name , since Person table has a 'name' column.
    __table_args__ = {'autoload':True, 'autoload_with': engine}

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
        
    def __repr__(self):
        """ Default object representation """
        # e.g. <Person name='Philip J. Fry' id=xxxx>
        try:
            return "<{} name='{}' id={}>".format(self.__class__.__name__,
                                                 self.name, id(self))
        except:
            return "<{} id={}>".format(self.__class__.__name__, id(self))
            
Base = declarative_base(cls=Umber)
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
           
class Person(Base):
    # columns: person_id, ldap_id, username, firstname, lastname, email,
    #          password, crypto, notes
    # relations: courses, works
                
    def __init__(*args, **kwargs):
        Base.__init__(*args, **kwargs)
                    
class Role(Base):
    # columns: role_id, name, rank
                        
    def __init__(*args, **kwargs):
        Base.__init__(*args, **kwargs)
                            
class Course(Base):
    # columns: course_id, name, name_as_title, directory, credits,
    #          start_date, end_date, assignments_md5, active, notes
    # relations: persons, assignments
    
    def __init__(*args, **kwargs):
        Base.__init__(*args, **kwargs)
                                    
class Registration(Base):
    # columns: registration_id, person_id, course_id, role_id,
    #          date, midterm, grade, credits, status
    # relations: person, course, role
    
    def __init__(*args, **kwargs):
        Base.__init__(*args, **kwargs)
  
class Assignment(Base):
    # columns: assignment_id, course_id, name, uriname, due, nth,
    #          blurb, active, notes
    # relations: course
    
    def __init__(*args, **kwargs):
        Base.__init__(*args, **kwargs)

class Work(Base):
    # columns: work_id, person_id, assignment_id, submitted, 
    #          studentLastSeen, studentLastModified,
    #          facultyLastSeen, facultyLastModified,
    #          grade, notes
    # relations: person, assignment, course

    def __init__(*args, **kwargs):
        Base.__init__(*args, **kwargs)
  
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

# if __name__ == "__main__":
#     import doctest
#     doctest.testmod()

