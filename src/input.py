# -*- coding: utf-8 -*-
"""
 input.py

 utility scripts to read in users and courses

"""
from model import Course, Person
import csv

default_date = '2018-01-20'

def input_courses(csvfilename):
    """ create courses from a .csv file defining them """
    with row in csv.DictReader(open(csvfilename)):
        name = row['name']
        name_as_title = row['name_as_title']
        path = row['path']
        start = default_date
        Course.create_course(
            name = name,
            name_as_title = name_as_title,
            path = path,
            start = default_date,
            copy_generic = True
            )

def input_people(csvfilename):
    """ create users from a .csv file defining them """
    with row in csv.DictReader(open(csvfilename)):
        username = 
        name = row['name']
        email = row.get('email', username+'@marlboro.edu')
        password = row.get('password', username+'*05344*')  # CHANGEME
        Person.create_person(
            username = row['username'],
            name = row['name']
            email = username+'@marlboro.edu'
            password = password
            )
        coursepath = row['coursepath']




