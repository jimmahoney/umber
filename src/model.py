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

DATABASE = 'sqlite:///' + project_path + '/database/umber.db'

engine = create_engine(DATABASE)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine))

class Umber(object):
  """ All of this project's database objects inherit from this class. """

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

  # Define shortcut methods for querying
  # e.g. Class.filter(...) rather than Class.query.filter(...)
  # for several of query's methods.

  @classmethod
  def filter(cls, *args):
    return cls.query.filter(*args)

  @classmethod
  def filter_by(cls, *args):
    return cls.query.filter_by(*args)

  @classmethod
  def all(cls, *args):
    return cls.query.all(*args)

  @classmethod
  def query_by(cls, column, value):
    """ Return query object with column == value """
    return cls.query.filter(cls.col(column) == value)  

  @classmethod
  def find_by(cls, column, value):
    """ Return database object with column=value """
    # e.g. Person.find_by('name', 'Philip J. Fry')
    # (Throws an error if there's more than one.)
    return cls.query_by(column, value).one()

  @classmethod
  def find_all_by(cls, column, value):
    """ Return list of database objects with column=value """
    # e.g. Package.find_all_by('weight', 1.5)
    return cls.query_by(column, value).all()

  @classmethod
  def query_like(cls, column, like_value):
    """ Return query with SQL_LIKE(column, like_value) """
    return cls.query.filter(cls.col(column).like(like_value))

  @classmethod
  def find_like(cls, column, like_value):
    """ Return the database object with column LIKE like_value. """
    # e.g. Person.find_like('name', '%Fry%')
    # (Throw an error if there's more than one.)
    return cls.query_like(column, like_value).one()

  @classmethod
  def find_all_like(cls, column, like_value):
    """ Return list objects with column LIKE like_value. """
    return cls.query_by(column, like_value).all()

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
  pass

class Role(Base):
  # columns: role_id, name, rank
  pass

class Course(Base):
  # columns: course_id, name, name_as_title, directory, credits,
  #          start_date, end_date, assignments_md5, active, notes
  # relations: persons, assignments
  pass

class Registration(Base):
  # columns: registration_id, person_id, course_id, role_id,
  #          date, midterm, grade, credits, status
  # relations: person, course, role
  pass

class Assignment(Base):
  # columns: assignment_id, course_id, name, uriname, due, nth,
  #          blurb, active, notes
  # relations: course
  pass

class Work(Base):
  # columns: work_id, person_id, assignment_id, submitted, 
  #          studentLastSeen, studentLastModified,
  #          facultyLastSeen, facultyLastModified,
  #          grade, notes
  # relations: person, assignment, course
  pass

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

