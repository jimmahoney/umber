# -- coding: utf-8 --
"""
 model2.py
 
 data classes for the umber app, built on the pewee ORM with a sqlite3 database

 >>> 
  
"""

from settings import db_path
from peewee import SqliteDatabase

db = SqliteDatabase(db_path)

class UnknownField(object):
    pass

class BaseModel(Model):
    class Meta:
        database = db
        
    @classmethod
    def first(cls):
        return cls.select().first()
    
    @classmethod
    def all(cls):
        return list(cls.select().execute())

class Person(BaseModel):
    class Meta:
        db_table = 'Person'

    crypto = TextField()
    email = TextField()                
    ldap = IntegerField(db_column='ldap_id', index=True)
    name = TextField()
    notes = TextField()
    password = TextField()
    person = PrimaryKeyField(db_column='person_id')
    username = TextField(unique=True)
    
    # -- Jim's extensions --
    
    def works(self, course):
        query = (Work.select().
                     .where( Work.person == self,
                             Work.course == course ))
        return list(query.execute())
        
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

    def prepared(self):
        query = (Person.select()
                       .join(Registration)
                       .where(Registration.course == self))
        self.persons = list(query.execute())
            
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

    
if __name__ == '__main__':
    import doctest
    doctest.testmod()

    
# ------------------------------------------------------
# peewee database notes
#
# * installation
#     $ pip install peewee
#
# * features
#     playhouse.flask_utils : open/close db correctly during web request
#     playhouse.reflection  : extracting classes from an existing database
#
# * foreign keys and relationships
#     the correspondance between database column names and class fields
#     is set explicitly in the pewee class definition.
      See the docs for ForeignKeyField
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
#    To extend their classes, the __init__ method is problematic
#    because it runs before the field data has been loaded.
#    Peewee data classes have a prepared() method which
#    is called after that data is loaded ... which is
#    the right place to put what would otherwise go in __init__.
#
