#
# peewee python classes corresponding to the sql database,
# generated (except for these top comments) with
#
#    $ python -m pwiz -e sqlite3 umber.db > pwiz_model.py
#
# This code here is not used directly, but is instead is the
# starting place for the class definitions in ../src/model.py

from peewee import *

database = SqliteDatabase('umber.db', **{})

class UnknownField(object):
    pass

class BaseModel(Model):
    class Meta:
        database = database

class Course(BaseModel):
    active = IntegerField()
    assignments_md5 = TextField()
    course = PrimaryKeyField(db_column='course_id')
    credits = IntegerField()
    end_date = TextField()
    name = TextField()
    name_as_title = TextField()
    notes = TextField()
    path = TextField(unique=True)
    start_date = TextField()
    class Meta:
        db_table = 'Course'

class Assignment(BaseModel):
    active = IntegerField()
    assignment = PrimaryKeyField(db_column='assignment_id')
    blurb = TextField()
    course = ForeignKeyField(db_column='course_id', rel_model=Course, to_field='course')
    due = TextField(null=True)
    name = TextField()
    notes = TextField()
    nth = IntegerField(null=True)
    uriname = TextField()

    class Meta:
        db_table = 'Assignment'

class Person(BaseModel):
    crypto = TextField()
    email = TextField()
    ldap = IntegerField(db_column='ldap_id', index=True)
    name = TextField()
    notes = TextField()
    password = TextField()
    person = PrimaryKeyField(db_column='person_id')
    username = TextField(unique=True)

    class Meta:
        db_table = 'Person'

class Role(BaseModel):
    name = TextField()
    rank = IntegerField()
    role = PrimaryKeyField(db_column='role_id')

    class Meta:
        db_table = 'Role'

class Registration(BaseModel):
    course = ForeignKeyField(db_column='course_id', rel_model=Course, to_field='course')
    credits = IntegerField()
    date = TextField(null=True)
    grade = TextField()
    midterm = TextField()
    person = ForeignKeyField(db_column='person_id', rel_model=Person, to_field='person')
    registration = PrimaryKeyField(db_column='registration_id')
    role = ForeignKeyField(db_column='role_id', rel_model=Role, to_field='role')
    status = TextField()

    class Meta:
        db_table = 'Registration'

class Work(BaseModel):
    assignment = ForeignKeyField(db_column='assignment_id', rel_model=Assignment, to_field='assignment')
    facultylastmodified = TextField(db_column='facultyLastModified')
    facultylastseen = TextField(db_column='facultyLastSeen')
    grade = TextField()
    notes = TextField()
    person = ForeignKeyField(db_column='person_id', rel_model=Person, to_field='person')
    studentlastmodified = TextField(db_column='studentLastModified')
    studentlastseen = TextField(db_column='studentLastSeen')
    submitted = TextField()
    work = PrimaryKeyField(db_column='work_id')

    class Meta:
        db_table = 'Work'

