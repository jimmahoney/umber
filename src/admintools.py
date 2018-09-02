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
  >>> from adminscripts import *
  >>> os.chdir('/var/www/cours/etc/misc') # folder for .html , .csv
  >>> users = parse_directory('nookfile.html')
  >>> make_csv(users, 'users.csv')
  >>> add_users('users.csv')

"""
from model import Course, Person
import csv, random, re, sys

term = '2018-09-01'       # CHANGEME
termfolder = 'fall2018'   # CHANGEME

def make_faculty():
    Person.create_person(
        username = 'mahoney',
        name = 'Jim Mahoney',
        email = 'mahoney@marlboro.edu',
        password = 'mahoney*05344*',
        is_admin = True
    )
    Person.create_person(
        username = 'matt',
        name = 'Matt Ollis',
        email = 'matt@marlboro.edu',
        password = 'matt*05344*'
    )
    Person.create_person(
        username = 'kminden',
        name = 'Kaethe Minden',
        email = 'kminden@marlboro.edu',
        password = 'kminden*05344*'
    )

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
        
def add_users(csvfilename, passwd=False, enroll=False):
    """ create users from a .csv file defining them """
    # csvfile: username, name, (if enroll) course
    for row in csv.DictReader(open(csvfilename)):
        if passwd:
            password = row['username'] + '*05344*'  # i.e. mahoney*05344*
        else:
            password = '' # blank => make random passwd in Person.create_person
        student = Person.create_person(
            username = row['username'],
            name = row['name'],
            email = row['username'] + '@marlboro.edu',
            password = password)
        if enroll:
            course = Course.get(path = termfolder + '/' + row['course'])
            course.enroll(student, 'student', term)

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

