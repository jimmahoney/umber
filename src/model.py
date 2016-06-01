# -- coding: utf-8 --
"""
 model.py
 
 The data class definitons and methods,
 built on the pewee ORM with a sqlite3 database.

 The following tests assumes that the database has been created
 and that populate_database() has been run; see ../database/init_db.
   
 The script ../bin/umber_test runs these and other tests.

   # Find the people and their role in a course given its name.
   >>> democourse = Course.get(Course.name == 'Demo Course')
   >>> for (person, role) in sorted(democourse.person_to_role.items(),
   ...                              key = lambda x: x[0].name):
   ...   print "{} is {} in {}.".format(person.name,
   ...                                  role.name, democourse.name)
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

 Jim Mahoney | mahoney@marlboro.edu | MIT License
"""

from settings import db_path
from werkzeug.security import generate_password_hash, check_password_hash
from peewee import SqliteDatabase, Model, BaseModel, \
     TextField, IntegerField, PrimaryKeyField, ForeignKeyField

db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db   # (peewee requires this 'database' name)

    def __repr__(self):
        # e.g. 
        fields = ', '.join(map(lambda x: '{}={}'.format(x[0],x[1]),
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
        
    crypto = TextField()
    email = TextField()                
    ldap = IntegerField(db_column='ldap_id', index=True)
    name = TextField()
    notes = TextField()
    password = TextField()
    username = TextField(unique=True)

    def set_password(self, passwordtext):
        self.password = generate_password_hash(passwordtext)
        
    def works(self, course):
        query = (Work.select()
                     .where( Work.person == self,
                             Work.course == course ))
        return list(query.execute())

    def set_password(self, passwordtext):
        self.password = generate_password_hash(passwordtext)
        self.save()
        
    def check_password(self, passwordtext):
        return check_password_hash(self.password, passwordtext)

    def set_status(self, logged_in=True, role=''):
        self.logged_in = logged_in    # not in database
        self.role = role              # not in database

    # -- Flask-Login methods --
    
    def is_authenticated(self):
        try:
            return self.logged_in
        except:
            return False
        
    def is_active(self):
        return self.is_authenticated()
    
    def is_anonymous(self):
        try:
            return self.anonymous
        except:
            return False
        
    def get_id(self):
        if self.username == None:
            return unicode('')
        else:
            return unicode(self.username)

def anonymous_person():
    # Not saved to database since .save() is not called.
    anon = Person(name=u'anonymous', username=u'anonymous')
    anon.set_status(logged_in=False)
    anon.anonymous = True
    return anon

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
        self.person_to_role = {reg.person : reg.role
            for reg in (Registration.select(Registration.person,
                                            Registration.role)
                                    .where(Registration.course == self))}
        #persons_query = (Person.select()
        #                       .join(Registration)
        #                       .where(Registration.course == self))
        #self.persons = list(persons_query.execute())
        #self.username_to_person = {p.username : p for p in self.persons}
        #self.rolename_to_persons = \
        #  {role.name : list(Person.select()
        #                          .join(Registration)
        #                          .where((Registration.course == self) &
        #                                 (Registration.role == role))
        #                          .execute()) \
        #   for role in Role.all()}

class Page(BaseModel):
    class Meta:
        db_table = 'Page'

    page_id = PrimaryKeyField(db_column='page_id')
                                
    as_html = TextField()
    content_hash = IntegerField()
    notes = TextField()
    path = TextField(unique=True)

    course = ForeignKeyField(rel_model=Course,
                             db_column='course_id',
                             to_field='course_id')

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

    name_rank = {'admin': 5,
                 'faculty': 4,
                 'student': 3,
                 'guest': 2,
                 'visitor': 1
                 }
    name_alias = {'admin':           'admin',
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
    @staticmethod
    def unalias(alias):
        """ Convert alias to its standard role name. """
        return Role.name_alias[alias]

    @staticmethod
    def create_defaults():
        with db.transaction():
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
    page = ForeignKeyField(rel_model=Page,
                           db_column='page_id',
                           to_field='page_id')


def populate_database():
    """ Create (and commit) the default database objects """
    #
    # Put some initial data into the database tables:
    # Roles, Course 'demo' and its example Persons,
    # Registrations, Assignments, and Works.
    #
    # The Roles data must be in place for the login system to work.
    # The rest of this is just for examples and tests.
    #
    # The sqlite database must already exist before this is run.
    # Create it with ../database/init_db.
    #
    # populate_db() is mostly idempotent; that is, runing multiple times
    # is no different than running it once. The one thing that will
    # change is the random seeds for the demo course sample users.

    print "* Populating database with default data."
    
    Role.create_defaults()
    
    with db.transaction():
        
        student = Role.get(name = 'student')
        faculty = Role.get(name = 'faculty')
        
        (democourse, created) = Course.get_or_create(
                name = 'Demo Course',
                name_as_title = 'Demo<br>Course',
                path = 'demo',
                start_date = '2013-01-01')
        
        (jane, created) = Person.get_or_create(
            username = 'janedoe',
            name = 'Jane Q. Doe',
            email = 'janedoe@fake.address')
        
        (john, created) = Person.get_or_create(
            username = 'johnsmith',
            name = 'Johnny Smith',
            email = 'johnsmith@fake.address')
        
        (ted, created)  = Person.get_or_create(
            username = 'tedteacher',
            name = 'Ted Teacher',
            email = 'ted@fake.address')
        
        # The hashed seeded passwords are different each time,
        # so they shouldn't be put in args to find_or_create. Otherwise, the
        # new passwords won't be found and duplicate people would be created.
        jane.set_password('test')
        john.set_password('test')
        ted.set_password('test')
        
        Registration.get_or_create(
            person = john,
            course = democourse,
            role = student,
            date = '2013-01-02')
        
        Registration.get_or_create(
            person = jane,
            course = democourse,
            role = student,
            date = '2013-01-03')
        
        Registration.get_or_create(
            person = ted,
            course = democourse,
            role = faculty,
            date = '2013-01-04')
        
        (assign1, created) = Assignment.get_or_create(
            course = democourse,
            nth = 1,
            name = 'week 1',
            uriname = 'week_1',
            due = '2013-01-20',
            blurb = 'Do chap 1 exercises 1 to 10.')
        
        (assign2, created) = Assignment.get_or_create(
            course_id = democourse,
            nth = 1,
            name = 'week 2',
            uriname = 'week_2',
            due = '2013-01-27',
            blurb = 'Write a four part fugue.')
        
        Work.get_or_create(
            person = john,
            assignment = assign1,
            submitted = '2013-01-20 18:19:20',
            grade = 'B')
        
        Work.get_or_create(
            person = jane,
            assignment = assign1,
            submitted = '2013-01-21 16:01:01',
            grade = 'B-')


if __name__ == '__main__':
    import doctest
    doctest.testmod()


# ------------------------------------------------------
# peewee database notes
#
# * installation
#     $ pip install peewee
#
# * its source : https://github.com/coleifer/peewee
#
# * features
#     playhouse.flask_utils : open/close db correctly during web request
#     playhouse.reflection  : extracting classes from an existing database
#
# * foreign keys and relationships
#     the correspondance between database column names and class fields
#     is set explicitly in the pewee class definition.
#     See the docs for ForeignKeyField
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
# * transactions
#    See http://docs.peewee-orm.com/en/latest/peewee/transactions.html :
#    peewee has some syntax for marking blocks as atomic
#    However, peewee's sqlite egine, based on pysql, is autocommit
#    by default and somewhat awkward to use otherwise.
#    (Turning off autocommit requires explict "begin" or "transaction".)
#    The suggested syntax is either
#      with db.transaction():
#        do_stuff()
#    or
#      @db.transaction()
#      def do():
#        stuff()
#    I think the "with" syntax is clearer - see
#    http://effbot.org/zone/python-with-statement.htm
#    for a discussion of what it is for in python -
#    and doesn't require a function definition.
#
# * get
#    peewee spells "find" as "get".
#    In other ORMs, get seems to often be only "get by id",
#    whereas find() or fetch() is by select() specifications.
#
# * flask
#    See docs.peewee-orm.com/en/latest/peewee/playhouse.html#flask-utils .
#    "automatically set up request ... handlers to ensure your connections
#    are managed properly"
#
#      from playhouse.flask_utils import FlaskDB
#      db = SqliteDatabase(db_path)
#      app = Flask(__name__)
#      flask_db = FlaskDB(app)
#
#    BUT it seems that this approach expects that flask_db
#    is in all the model meta information ... and that in
#    that case, testing the database or accessing it from
#    the command line doesn't work.
#
#    Looking at the source code, all that this really does is set
#       app.before_request(self.connect_db)
#       app.teardown_request(self.close_db)
#    where   connect_db => "database.connect()"
#    and    close_db    => "if not database.is_closed(): database.close()"
#    ... which seems simple enough for me to do myself in the flask app.
#
