"""
 admintools.py

 utilities to add users, courses, etc.

--- courses_jan2018.csv ----
name,name_as_title,path,faculty
Programming Workshop,Programming<br>Workshop,spring2018/workshop,mahoney
Jim's Tutorials,Jim's<br>Tutorials,spring2018/jims_tutorials,mahoney
...

--- students_2018.csv ---
name,username,course
Chris T,ct,modern_physics
Jeff A,jeffa,modern_physics
...

--- users.csv ---------
name,username
John Smith,jsmith

interactively create users.csv from nook html listing
and then add them to umber's sql database :

  $ cd /var/www/umber
  $ . env/production
  $ umber_console
  >>> from admintools import *
  >>> os.chdir('/var/www/cours/etc/misc') # folder for .html , .csv
  >>> users = parse_directory('nookfile.html')
  >>> make_csv(users, 'users.csv')
  >>> add_users('users.csv')

"""
from model import Course, Person
import csv, random, re, sys, os

term = '2020-09-01'       # CHANGEME
termfolder = 'fall2020'   # CHANGEME

def read_csv(filename):
    """ Return list of dicts from file.csv """
    lines = []
    with open(filename) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for line in csv_reader:
            lines.append(line)
    return lines

def pwd(): return os.getcwd()
def cd(folder): os.chdir(folder); return None

def make_faculty():
    Person.create_person(
        username = 'mahoney',
        name = 'Jim Mahoney',
        email = 'jimmahoney@bennington.edu',
        password = '..henri..',  # RESETME!
        is_admin = True
    )
    #Person.create_person(
    #    username = 'matt',
    #    name = 'Matt Ollis',
    #    email = 'matt@marlboro.edu',
    #    password = 'matt*05344*'
    #)
    #Person.create_person(
    #    username = 'kminden',
    #    name = 'Kaethe Minden',
    #    email = 'kminden@marlboro.edu',
    #    password = 'kminden*05344*'
    #)

def make_courses(csvfilename='courses_jan2018.csv'):
    """ create courses from a .csv file defining them """
    # csvfile : name, name_as_title, path, faculty
    for row in csv.DictReader(open(csvfilename)):
        course = Course.create_course(
            name = row['name'],
            name_as_title = row['name_as_title'],
            path = row['path'],
            start = term,
            copy_generic = True
            )
        faculty = Person.by_username(row['faculty'])
        course.enroll(faculty, 'faculty', spring2018)

def read_populi_csv(csvfilename):
    """ Return user data from student populi csv export """
    # populi csv export fields :
    #   "Student ID",Prefix,"First Name","Preferred Name",
    #   "Middle Name","Last Name","Former Name",Email,
    #   Street,City,State,ZIP,Country,Phone,Type,"Receives Mail"
    # If there is a 'Preferred Name', use that as the first,
    # then let 'name' be 'first last'. Ignore (prefix, middle, former)
    # Return fields for (username,name,email,password)
    result = []
    for row in csv.DictReader(open(csvfilename)):
        name = (row['Preferred Name'] or row['First Name']) + \
               ' ' + row['Last Name']
        email = row['Email']
        result.append({'name':name, 'email':email})
    return result

def email_to_username(email):
    return email.split('@')[0]

def add_users(csvfilename, read_csv=read_populi_csv,
              course=None, date='2020-09-01'):
    """ create users and optionally enroll in a course """
    users = read_csv(csvfilename)
    for user in users:
        username = email_to_username(user['email'])
        student = Person.create_person(name=user['name'],
                                       email=user['email'],
                                       username=username,
                                       password='')
        if course:
            course.enroll(student, 'student',
                          datestring=date, create_work=True)

def parse_directory(filename):
    """ read html file (nook directory listing),
        return users as [{'name':..., 'username':...},...] """
    try:
        file = open(filename)
        html = file.read()
        file.close()
    except:
        return []
    users = []
    for match in re.finditer(r'<b>([^<]+)</b>.*?mailto:([^@]+)@', html):
        groups = match.groups()
        users.append({'name':groups[0], 'username':groups[1]})
    users.sort(key=lambda x:x['username'])
    return users

def make_csv(userdict, csvfilename):
    """ create csv file from user dictionary """
    csv = open(csvfilename, 'w')
    cs.write('name,username\n')
    for u in userdict:
        csv.write("{},{}\n".format(u['name'], u['username']))
    csv.close()
