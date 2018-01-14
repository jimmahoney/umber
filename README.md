umber
=====

a course management web app built with python Flask, sqlite3, and git.

development & testing
---------------------

    $ source env/activate  # turn on python environment & set shell variables 
    $ umber_init_db        # create database with default test data
    $ umber_test           # run software doc tests
    
    $ umber_console        # interact with database from command line
    >>> democourse
    <Course name='Demo Course' ...>
    >>> democourse.assignments
    >>> democourse.persons
    >>> john = Person.get(username='johnsmith')
    <Person name = 'Johnny Smith' ...>
    # See src/model.py for more examples

    $ umber_server  # then visit http://127.0.0.1:5000/umber/demo/home

production
----------

   ... coming ...

----------------------------------------------------------
Jim Mahoney | cs.marlboro.edu | Jan 2018 | MIT License
