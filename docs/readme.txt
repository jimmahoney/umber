umber
=====

Umber is a file based wiki-like course managment system with a
markdown flavor.

running it
==========

Install it following the notes in ../env/install_notes.txt.

The virtual python environment is in ./venv;
my environment setup scripts and notes are in ./env.

development
-----------

From the umber folder, activate the python and umber shell enviroment.

  $ . env/activate_development

Then

  (env)$ umber_test
  OR
  (env)$ umber_console
  OR
  (env)$ umber_server  # and visit http://127.0.0.1:5000/courses/demo/home 

production
----------

On cs.marlboro.college, as of May 2020 I'm running it under apache
with mod_wsgi ; see ../env/install_notes.txt for the (messy) details
of how to set up the apache environment and what to put in the apache
config files and src/umber.wsgi.

Here are a few examples of interacting with the database manually
from the console.

  $ cd /var/www/umber ( application root on cs.marlboro.college )
  $ . env/activate_production
  (env)$ umber_console
  #
  # Edit a user's name and save changes to database
  #
  >>> jim = Person.get(username='mahoney')
  >>> jim.name
  >>> 'Jim Mahoney'
  >>> jim.name = 'James H Mahoney'
  >>> jim.save()
  #
  # List courses, then find users in one of them.
  #
  >>> for c in Course.all():
  ...   print(c.semester + '|' + c.name + '|' + str(c.course_id))  
  Spring 2018|Umber|1
  Spring 2018|Programming Workshop|2
  Spring 2018|Jim's Tutorials|3
  ...
  >>> workshop2018 = Course.get(course_id=2)
  >>> [student.username for student in workshop2018.students]
  ['barborah', 'jtuttle', 'mkatz', 'njunco', 'nweeks']

---------------------------------------------------------------
  







